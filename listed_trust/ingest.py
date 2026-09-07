"""Fetch and cache filings, announcements, and governance series."""

from __future__ import annotations

import json
import time
from datetime import date
from pathlib import Path
from typing import Any, Callable, TypeVar

import pandas as pd

T = TypeVar("T")

ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / "data" / "cache"


def retry(fn: Callable[[], T], times: int = 3, delay: float = 1.6) -> T:
    last: Exception | None = None
    for attempt in range(times):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - upstream APIs fail in many ways
            last = exc
            time.sleep(delay * (attempt + 1))
    assert last is not None
    raise last


def _cache_path(code: str, name: str) -> Path:
    folder = CACHE_DIR / code
    folder.mkdir(parents=True, exist_ok=True)
    return folder / name


def _read_csv(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    return pd.read_csv(path)


def _write_csv(path: Path, frame: pd.DataFrame) -> pd.DataFrame:
    frame.to_csv(path, index=False)
    return frame


def em_symbol(code: str) -> str:
    return f"{code}.SH" if code.startswith("6") else f"{code}.SZ"


def gdfx_symbol(code: str) -> str:
    return f"sh{code}" if code.startswith("6") else f"sz{code}"


def fetch_business(code: str) -> dict[str, str]:
    path = _cache_path(code, "business.json")
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    import akshare as ak

    frame = retry(lambda: ak.stock_zyjs_ths(symbol=code))
    row = frame.iloc[0].to_dict() if len(frame) else {}
    payload = {str(k): "" if pd.isna(v) else str(v) for k, v in row.items()}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def fetch_financials(code: str) -> pd.DataFrame:
    path = _cache_path(code, "financial_sina.csv")
    cached = _read_csv(path)
    if cached is not None:
        return cached
    import akshare as ak

    frame = retry(lambda: ak.stock_financial_analysis_indicator(symbol=code))
    return _write_csv(path, frame)


def fetch_financials_em(code: str) -> pd.DataFrame:
    path = _cache_path(code, "financial_em.csv")
    cached = _read_csv(path)
    if cached is not None:
        return cached
    import akshare as ak

    frame = retry(
        lambda: ak.stock_financial_analysis_indicator_em(
            symbol=em_symbol(code), indicator="按报告期"
        )
    )
    return _write_csv(path, frame)


def fetch_dividends(code: str) -> pd.DataFrame:
    path = _cache_path(code, "dividends.csv")
    cached = _read_csv(path)
    if cached is not None:
        return cached
    import akshare as ak

    frame = retry(lambda: ak.stock_fhps_detail_em(symbol=code))
    return _write_csv(path, frame)


def fetch_notices(code: str, start: date, end: date) -> pd.DataFrame:
    path = _cache_path(code, f"notices_{start.year}_{end.year}.csv")
    cached = _read_csv(path)
    if cached is not None:
        return cached
    import akshare as ak

    chunks: list[pd.DataFrame] = []
    for year in range(start.year, end.year + 1):
        begin = f"{year}-01-01"
        finish = f"{year}-12-31"
        try:
            piece = retry(
                lambda y0=begin, y1=finish: ak.stock_individual_notice_report(
                    security=code, symbol="全部", begin_date=y0, end_date=y1
                )
            )
        except Exception:
            piece = pd.DataFrame()
        if piece is not None and len(piece):
            chunks.append(piece)
        time.sleep(0.35)
    frame = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame(
        columns=["代码", "名称", "公告标题", "公告类型", "公告日期", "网址"]
    )
    if "公告日期" in frame.columns:
        frame["公告日期"] = pd.to_datetime(frame["公告日期"], errors="coerce")
        frame = frame.drop_duplicates(subset=["公告标题", "公告日期"]).sort_values(
            "公告日期", ascending=False
        )
    return _write_csv(path, frame)


def fetch_insiders(code: str) -> pd.DataFrame:
    path = _cache_path(code, "insiders.csv")
    cached = _read_csv(path)
    if cached is not None:
        return cached
    import akshare as ak

    def _load() -> pd.DataFrame:
        if code.startswith("6"):
            return ak.stock_share_hold_change_sse(symbol=code)
        return ak.stock_share_hold_change_szse(symbol=code)

    try:
        frame = retry(_load)
    except Exception:
        frame = pd.DataFrame()
    return _write_csv(path, frame)


def fetch_shareholders(code: str, as_of: date | None = None) -> pd.DataFrame:
    path = _cache_path(code, "shareholders.csv")
    cached = _read_csv(path)
    if cached is not None:
        return cached
    import akshare as ak

    as_of = as_of or date.today()
    report_date = f"{as_of.year - 1}1231"
    try:
        frame = retry(
            lambda: ak.stock_gdfx_top_10_em(symbol=gdfx_symbol(code), date=report_date)
        )
    except Exception:
        frame = pd.DataFrame()
    return _write_csv(path, frame)


def fetch_esg(code: str) -> pd.DataFrame:
    market_path = CACHE_DIR / "esg_hz_sina.csv"
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    market = _read_csv(market_path)
    if market is None:
        import akshare as ak

        market = retry(lambda: ak.stock_esg_hz_sina())
        _write_csv(market_path, market)
    symbol = em_symbol(code)
    if "股票代码" not in market.columns:
        return pd.DataFrame()
    subset = market[market["股票代码"].astype(str) == symbol].copy()
    return subset


def ingest_company(
    code: str,
    years: int = 10,
    with_esg: bool = True,
    as_of: date | None = None,
) -> dict[str, Any]:
    code = str(code).zfill(6)
    as_of = as_of or date.today()
    start = date(as_of.year - years, 1, 1)
    payload: dict[str, Any] = {
        "code": code,
        "as_of": as_of.isoformat(),
        "window_start": start.isoformat(),
        "years": years,
        "business": fetch_business(code),
        "financials": fetch_financials(code),
        "financials_em": fetch_financials_em(code),
        "dividends": fetch_dividends(code),
        "notices": fetch_notices(code, start, as_of),
        "insiders": fetch_insiders(code),
        "shareholders": fetch_shareholders(code, as_of),
        "esg": fetch_esg(code) if with_esg else pd.DataFrame(),
    }
    return payload
