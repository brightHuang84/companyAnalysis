"""Turn raw filings into annual series, announcement flags, and coverage stats."""

from __future__ import annotations

from datetime import date, datetime

import numpy as np
import pandas as pd

from listed_trust.keywords import classify_title, looks_like_platform


def _to_date(value) -> date | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date()


def years_ago(when: date | None, as_of: date) -> float | None:
    if when is None:
        return None
    return (as_of - when).days / 365.25


def time_weight(age_years: float | None) -> float:
    if age_years is None:
        return 0.5
    if age_years <= 3:
        return 1.0
    if age_years <= 7:
        return 0.6
    return 0.35


def _num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def annual_financials(raw: pd.DataFrame, start: date, end: date) -> pd.DataFrame:
    if raw is None or raw.empty or "日期" not in raw.columns:
        return pd.DataFrame()
    frame = raw.copy()
    frame["日期"] = pd.to_datetime(frame["日期"], errors="coerce")
    frame = frame.dropna(subset=["日期"])
    frame = frame[frame["日期"].dt.month == 12]
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    frame = frame[(frame["日期"] >= start_ts) & (frame["日期"] <= end_ts)]
    frame = frame.sort_values("日期")
    for col in frame.columns:
        if col == "日期":
            continue
        frame[col] = _num(frame[col])
    return frame.reset_index(drop=True)


def annual_em(raw: pd.DataFrame, start: date, end: date) -> pd.DataFrame:
    if raw is None or raw.empty or "REPORT_DATE" not in raw.columns:
        return pd.DataFrame()
    frame = raw.copy()
    frame["REPORT_DATE"] = pd.to_datetime(frame["REPORT_DATE"], errors="coerce")
    frame = frame.dropna(subset=["REPORT_DATE"])
    frame = frame[frame["REPORT_DATE"].dt.month == 12]
    frame = frame[
        (frame["REPORT_DATE"] >= pd.Timestamp(start))
        & (frame["REPORT_DATE"] <= pd.Timestamp(end))
    ]
    frame = frame.sort_values("REPORT_DATE")
    return frame.reset_index(drop=True)


def metric_stats(series: pd.Series) -> dict[str, float | None]:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return {"n": 0, "mean": None, "median": None, "std": None, "last": None}
    return {
        "n": int(len(values)),
        "mean": float(values.mean()),
        "median": float(values.median()),
        "std": float(values.std(ddof=0)) if len(values) > 1 else 0.0,
        "last": float(values.iloc[-1]),
    }


def cagr(first: float | None, last: float | None, periods: int) -> float | None:
    if first is None or last is None or first <= 0 or last <= 0 or periods <= 0:
        return None
    return (last / first) ** (1 / periods) - 1


def classify_notices(notices: pd.DataFrame, as_of: date) -> pd.DataFrame:
    if notices is None or notices.empty:
        return pd.DataFrame(
            columns=[
                "date",
                "title",
                "category",
                "dimension",
                "severity",
                "delta",
                "label",
                "age_years",
                "weight",
                "url",
            ]
        )
    rows = []
    for _, row in notices.iterrows():
        title = str(row.get("公告标题", "") or "")
        rule = classify_title(title)
        if rule is None:
            continue
        when = _to_date(row.get("公告日期"))
        age = years_ago(when, as_of)
        weight = time_weight(age)
        rows.append(
            {
                "date": when.isoformat() if when else None,
                "title": title,
                "category": str(row.get("公告类型", "") or ""),
                "dimension": rule.dimension,
                "severity": rule.severity,
                "delta": round(rule.delta * weight, 3),
                "raw_delta": rule.delta,
                "label": rule.label,
                "age_years": None if age is None else round(age, 2),
                "weight": weight,
                "url": str(row.get("网址", "") or ""),
            }
        )
    return pd.DataFrame(rows)


def diminish(deltas: list[float]) -> float:
    total = 0.0
    for i, value in enumerate(sorted(deltas, key=lambda x: abs(x), reverse=True)):
        total += value * (0.55**i if i else 1.0)
    return total


def insider_summary(insiders: pd.DataFrame, start: date) -> dict:
    if insiders is None or insiders.empty:
        return {"buy_count": 0, "sell_count": 0, "net_shares": 0.0, "rows": 0}
    frame = insiders.copy()
    date_col = "变动日期" if "变动日期" in frame.columns else None
    qty_col = "变动数" if "变动数" in frame.columns else None
    if date_col is None or qty_col is None:
        return {"buy_count": 0, "sell_count": 0, "net_shares": 0.0, "rows": int(len(frame))}
    frame[date_col] = pd.to_datetime(frame[date_col], errors="coerce")
    frame[qty_col] = pd.to_numeric(frame[qty_col], errors="coerce").fillna(0)
    frame = frame[frame[date_col] >= pd.Timestamp(start)]
    buys = frame[frame[qty_col] > 0]
    sells = frame[frame[qty_col] < 0]
    return {
        "buy_count": int(len(buys)),
        "sell_count": int(len(sells)),
        "net_shares": float(frame[qty_col].sum()),
        "rows": int(len(frame)),
    }


def dividend_coverage(dividends: pd.DataFrame, start: date, years: int) -> dict:
    if dividends is None or dividends.empty or "报告期" not in dividends.columns:
        return {"years_paid": 0, "coverage": 0.0, "mean_yield": None}
    frame = dividends.copy()
    frame["报告期"] = pd.to_datetime(frame["报告期"], errors="coerce")
    frame = frame.dropna(subset=["报告期"])
    frame = frame[frame["报告期"] >= pd.Timestamp(start)]
    cash_col = "现金分红-现金分红比例"
    if cash_col in frame.columns:
        frame[cash_col] = pd.to_numeric(frame[cash_col], errors="coerce")
        paid = frame[frame[cash_col].fillna(0) > 0]
    else:
        paid = frame
    years_paid = int(paid["报告期"].dt.year.nunique()) if len(paid) else 0
    yield_col = "现金分红-股息率"
    mean_yield = None
    if yield_col in paid.columns and len(paid):
        mean_yield = float(pd.to_numeric(paid[yield_col], errors="coerce").mean())
    return {
        "years_paid": years_paid,
        "coverage": years_paid / max(years, 1),
        "mean_yield": mean_yield,
    }


def latest_esg(esg: pd.DataFrame) -> dict | None:
    if esg is None or esg.empty:
        return None
    frame = esg.copy()
    if "日期" in frame.columns:
        frame["日期"] = pd.to_datetime(frame["日期"], errors="coerce")
        frame = frame.sort_values("日期")
    row = frame.iloc[-1]
    def _f(key: str) -> float | None:
        if key not in row:
            return None
        value = pd.to_numeric(pd.Series([row[key]]), errors="coerce").iloc[0]
        return None if pd.isna(value) else float(value)

    return {
        "date": str(row.get("日期", "")),
        "total": _f("ESG评分"),
        "grade": None if pd.isna(row.get("ESG等级")) else str(row.get("ESG等级")),
        "env": _f("环境"),
        "social": _f("社会"),
        "governance": _f("公司治理"),
    }


def as_percent(stats: dict) -> dict:
    """Sina labels some ratios as percent but stores 1.03 for 103%."""
    out = dict(stats)
    mean = stats.get("mean")
    if mean is None:
        return out
    if abs(mean) <= 5:
        for key in ("mean", "median", "std", "last"):
            if out.get(key) is not None:
                out[key] = float(out[key]) * 100
    return out


def extract_features(bundle: dict) -> dict:
    as_of = date.fromisoformat(bundle["as_of"])
    start = date.fromisoformat(bundle["window_start"])
    years = int(bundle["years"])
    business = bundle.get("business") or {}
    business_text = " ".join(
        str(business.get(k, "") or "") for k in ("主营业务", "产品类型", "经营范围")
    )
    annual = annual_financials(bundle.get("financials"), start, as_of)
    em = annual_em(bundle.get("financials_em"), start, as_of)
    flags = classify_notices(bundle.get("notices"), as_of)
    notices = bundle.get("notices")
    notice_count = 0 if notices is None or notices.empty else int(len(notices))

    def col_stats(name: str) -> dict:
        if annual.empty or name not in annual.columns:
            return metric_stats(pd.Series(dtype=float))
        return metric_stats(annual[name])

    revenue_cagr = None
    profit_cagr = None
    if not em.empty and "TOTALOPERATEREVE" in em.columns:
        rev = pd.to_numeric(em["TOTALOPERATEREVE"], errors="coerce").dropna()
        if len(rev) >= 2:
            revenue_cagr = cagr(float(rev.iloc[0]), float(rev.iloc[-1]), max(len(rev) - 1, 1))
    if not em.empty and "PARENTNETPROFIT" in em.columns:
        profit = pd.to_numeric(em["PARENTNETPROFIT"], errors="coerce").dropna()
        if len(profit) >= 2:
            profit_cagr = cagr(float(profit.iloc[0]), float(profit.iloc[-1]), max(len(profit) - 1, 1))

    consecutive_rev_decline = 0
    if annual.empty is False and "主营业务收入增长率(%)" in annual.columns:
        growth = pd.to_numeric(annual["主营业务收入增长率(%)"], errors="coerce").dropna()
        streak = 0
        for value in growth.iloc[::-1]:
            if value < 0:
                streak += 1
            else:
                break
        consecutive_rev_decline = streak

    return {
        "code": bundle["code"],
        "as_of": bundle["as_of"],
        "years": years,
        "business": business,
        "business_text": business_text,
        "is_platform": looks_like_platform(business_text),
        "annual_rows": int(len(annual)),
        "notice_count": notice_count,
        "flag_count": int(len(flags)),
        "flags": flags,
        "gross_margin": col_stats("销售毛利率(%)"),
        "net_margin": col_stats("销售净利率(%)"),
        "roe": col_stats("净资产收益率(%)"),
        "leverage": col_stats("资产负债率(%)"),
        "current_ratio": col_stats("流动比率"),
        "cash_to_ni": as_percent(col_stats("经营现金净流量与净利润的比率(%)")),
        "cash_to_sales": as_percent(col_stats("经营现金净流量对销售收入比率(%)")),
        "non_main": col_stats("非主营比重"),
        "main_profit_share": col_stats("主营利润比重"),
        "receivable_days": col_stats("应收账款周转天数(天)"),
        "expense_ratio": col_stats("三项费用比重"),
        "revenue_growth": col_stats("主营业务收入增长率(%)"),
        "profit_growth": col_stats("净利润增长率(%)"),
        "revenue_cagr": revenue_cagr,
        "profit_cagr": profit_cagr,
        "consecutive_rev_decline": consecutive_rev_decline,
        "dividends": dividend_coverage(bundle.get("dividends"), start, years),
        "insiders": insider_summary(bundle.get("insiders"), start),
        "shareholders": _shareholder_preview(bundle.get("shareholders")),
        "esg": latest_esg(bundle.get("esg")),
        "annual": annual,
        "em": em,
    }


def _shareholder_preview(frame: pd.DataFrame) -> list[dict]:
    if frame is None or frame.empty:
        return []
    rows = []
    for _, row in frame.head(5).iterrows():
        rows.append({k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()})
    return rows


def nan_to_none(value):
    if value is None:
        return None
    if isinstance(value, (float, np.floating)) and (np.isnan(value) or np.isinf(value)):
        return None
    return value
