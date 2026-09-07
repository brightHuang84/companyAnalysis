"""Screen A-share issuers listed for at least a given number of years."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pandas as pd

from listed_trust.ingest import retry


def _parse_date(value) -> date | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip().replace("/", "-")
    if not text or text in {"nan", "NaT", "None"}:
        return None
    if len(text) == 8 and text.isdigit():
        text = f"{text[:4]}-{text[4:6]}-{text[6:]}"
    try:
        return datetime.strptime(text[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def load_listed_companies() -> pd.DataFrame:
    import akshare as ak

    sh = retry(lambda: ak.stock_info_sh_name_code(symbol="主板A股"))
    sh = sh.rename(
        columns={"证券代码": "code", "证券简称": "name", "上市日期": "list_date"}
    )[["code", "name", "list_date"]]
    sh["exchange"] = "SH"
    sh["board"] = "主板"

    try:
        kcb = retry(lambda: ak.stock_info_sh_name_code(symbol="科创板"))
        kcb = kcb.rename(
            columns={"证券代码": "code", "证券简称": "name", "上市日期": "list_date"}
        )[["code", "name", "list_date"]]
        kcb["exchange"] = "SH"
        kcb["board"] = "科创板"
    except Exception:
        kcb = pd.DataFrame(columns=["code", "name", "list_date", "exchange", "board"])

    sz = retry(lambda: ak.stock_info_sz_name_code(symbol="A股列表"))
    sz = sz.rename(
        columns={
            "A股代码": "code",
            "A股简称": "name",
            "A股上市日期": "list_date",
            "板块": "board",
            "所属行业": "industry",
        }
    )
    keep = [c for c in ["code", "name", "list_date", "board", "industry"] if c in sz.columns]
    sz = sz[keep]
    sz["exchange"] = "SZ"
    if "industry" not in sz.columns:
        sz["industry"] = ""

    frame = pd.concat([sh, kcb, sz], ignore_index=True)
    frame["code"] = frame["code"].astype(str).str.zfill(6)
    frame["name"] = frame["name"].astype(str).str.replace(" ", "", regex=False)
    frame["list_date"] = frame["list_date"].map(_parse_date)
    if "industry" not in frame.columns:
        frame["industry"] = ""
    frame["risk_flag"] = frame["name"].str.contains(r"ST|退市|\*ST", regex=True)
    frame = frame.drop_duplicates(subset=["code"]).sort_values("code").reset_index(drop=True)
    return frame


def screen_universe(min_years: int = 10, as_of: date | None = None) -> pd.DataFrame:
    as_of = as_of or date.today()
    frame = load_listed_companies()
    try:
        cutoff = date(as_of.year - min_years, as_of.month, as_of.day)
    except ValueError:
        cutoff = date(as_of.year - min_years, as_of.month, 28)
    frame["years_listed"] = frame["list_date"].map(
        lambda d: round((as_of - d).days / 365.25, 1) if isinstance(d, date) else None
    )
    eligible = frame[frame["list_date"].notna() & (frame["list_date"] <= cutoff)].copy()
    eligible["eligible"] = True
    return eligible.reset_index(drop=True)


DEFAULT_UNIVERSE_PATH = Path(__file__).resolve().parents[1] / "data" / "universe.csv"


def save_universe(path: Path | None = None, min_years: int = 10) -> pd.DataFrame:
    path = path or DEFAULT_UNIVERSE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    universe = screen_universe(min_years=min_years)
    universe.to_csv(path, index=False)
    return universe


def load_cached_universe(path: Path | None = None) -> pd.DataFrame | None:
    path = path or DEFAULT_UNIVERSE_PATH
    if not path.exists():
        return None
    frame = pd.read_csv(path, dtype={"code": str})
    frame["code"] = frame["code"].astype(str).str.zfill(6)
    return frame


def lookup_company(code: str) -> dict:
    code = str(code).zfill(6)
    frame = load_cached_universe()
    if frame is None:
        try:
            frame = screen_universe(min_years=0)
        except Exception:
            return {}
    hit = frame[frame["code"] == code]
    if hit.empty:
        return {}
    row = hit.iloc[0].to_dict()
    list_date = row.get("list_date")
    if hasattr(list_date, "isoformat"):
        row["list_date"] = list_date.isoformat()
    elif list_date is not None:
        row["list_date"] = str(list_date)[:10]
    for k, v in list(row.items()):
        if isinstance(v, float) and pd.isna(v):
            row[k] = None
    return row
