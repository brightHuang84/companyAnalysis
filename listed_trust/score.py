"""Score seven behavioral dimensions, then roll up credibility and sustainability."""

from __future__ import annotations

from typing import Any

import pandas as pd

from listed_trust.features import extract_features, nan_to_none
from listed_trust.ingest import ingest_company
from listed_trust.keywords import DIMENSION_LABELS
from listed_trust.universe import lookup_company

BASE_SCORE = 58.0

CREDIBILITY_WEIGHTS = {
    "business_model": 0.16,
    "conduct": 0.24,
    "board": 0.18,
    "culture": 0.14,
    "employees": 0.10,
    "consumers": 0.10,
    "users": 0.08,
}

SUSTAINABILITY_WEIGHTS = {
    "business_model": 0.26,
    "conduct": 0.10,
    "board": 0.14,
    "culture": 0.10,
    "employees": 0.14,
    "consumers": 0.13,
    "users": 0.13,
}


def clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def _band(score: float) -> str:
    if score >= 80:
        return "高"
    if score >= 65:
        return "中高"
    if score >= 50:
        return "中"
    if score >= 35:
        return "中低"
    return "低"


def _confidence(evidence_n: int, coverage_ok: bool) -> str:
    if evidence_n >= 8 and coverage_ok:
        return "高"
    if evidence_n >= 3:
        return "中"
    return "低"


def _metric_delta(stats: dict, *, high_good: bool, good: float, weak: float, scale: float) -> tuple[float, str]:
    last = stats.get("last")
    mean = stats.get("mean")
    value = mean if mean is not None else last
    if value is None:
        return 0.0, "数据不足"
    if high_good:
        if value >= good:
            return scale, f"{value:.2f}（偏强）"
        if value <= weak:
            return -scale, f"{value:.2f}（偏弱）"
        return 0.0, f"{value:.2f}"
    if value <= good:
        return scale, f"{value:.2f}（风险低）"
    if value >= weak:
        return -scale, f"{value:.2f}（风险高）"
    return 0.0, f"{value:.2f}"


def _stability_delta(stats: dict, tight: float, loose: float) -> tuple[float, str]:
    std = stats.get("std")
    mean = stats.get("mean")
    if std is None or mean is None or stats.get("n", 0) < 3:
        return 0.0, "稳定性样本不足"
    if std <= tight:
        return 6.0, f"标准差 {std:.2f}，结构稳定"
    if std >= loose:
        return -7.0, f"标准差 {std:.2f}，波动偏大"
    return 0.0, f"标准差 {std:.2f}"


def _flag_adjustment(flags: pd.DataFrame, dimension: str) -> tuple[float, list[dict], int]:
    if flags is None or flags.empty:
        return 0.0, [], 0
    subset = flags[flags["dimension"] == dimension].copy()
    if subset.empty:
        return 0.0, [], 0
    grouped = []
    for label, group in subset.groupby("label"):
        deltas = group["delta"].tolist()
        # First event full weight, repeats decay.
        ordered = sorted(deltas, key=lambda x: abs(x), reverse=True)
        total = 0.0
        for i, value in enumerate(ordered):
            total += value if i == 0 else value * (0.5**i)
        latest = group.sort_values("date", ascending=False).iloc[0]
        grouped.append(
            {
                "label": str(label),
                "severity": str(latest.get("severity") or ""),
                "count": int(len(group)),
                "delta": round(total, 2),
                "latest_date": latest.get("date"),
                "latest_title": latest.get("title"),
            }
        )
    delta = sum(item["delta"] for item in grouped)
    evidence = sorted(grouped, key=lambda x: abs(x["delta"]), reverse=True)[:8]
    return delta, evidence, int(len(subset))


def _shrink_to_neutral(score: float, confidence: str) -> float:
    if confidence == "低":
        return round(0.55 * score + 0.45 * 50, 1)
    if confidence == "中":
        return round(0.85 * score + 0.15 * 50, 1)
    return round(score, 1)


def score_business(feat: dict) -> dict:
    score = BASE_SCORE
    notes = []
    d, text = _stability_delta(feat["gross_margin"], tight=4, loose=12)
    score += d
    notes.append({"item": "毛利率稳定性", "detail": text, "delta": d})
    d, text = _metric_delta(feat["cash_to_ni"], high_good=True, good=80, weak=20, scale=9)
    score += d
    notes.append({"item": "经营现金流/净利润", "detail": text, "delta": d})
    d, text = _metric_delta(feat["non_main"], high_good=False, good=8, weak=25, scale=6)
    score += d
    notes.append({"item": "非主营比重", "detail": text, "delta": d})
    d, text = _metric_delta(feat["main_profit_share"], high_good=True, good=80, weak=40, scale=5)
    score += d
    notes.append({"item": "主营利润比重", "detail": text, "delta": d})
    if feat.get("consecutive_rev_decline", 0) >= 3:
        score -= 10
        notes.append({"item": "收入连续下滑", "detail": f"{feat['consecutive_rev_decline']} 年", "delta": -10})
    elif feat.get("consecutive_rev_decline", 0) == 2:
        score -= 5
        notes.append({"item": "收入连续下滑", "detail": "2 年", "delta": -5})
    cagr = feat.get("revenue_cagr")
    if cagr is not None:
        delta = 6 if cagr >= 0.08 else (2 if cagr >= 0.03 else (-6 if cagr < -0.05 else 0))
        score += delta
        notes.append({"item": "收入复合增速", "detail": f"{cagr:.1%}", "delta": delta})
    flag_delta, flag_ev, flag_n = _flag_adjustment(feat["flags"], "business_model")
    score += flag_delta
    evidence_n = flag_n + feat["annual_rows"]
    confidence = _confidence(evidence_n, feat["annual_rows"] >= 6)
    return _pack("business_model", score, confidence, notes, flag_ev, evidence_n)


def score_conduct(feat: dict) -> dict:
    score = BASE_SCORE + 4  # listed company baseline: continuous disclosure
    notes = [
        {"item": "持续信息披露", "detail": f"窗口内公告 {feat['notice_count']} 份", "delta": 4}
    ]
    flag_delta, flag_ev, flag_n = _flag_adjustment(feat["flags"], "conduct")
    score += flag_delta
    reds = [e for e in flag_ev if e["severity"] == "red"]
    if any(e["label"] == "监管立案" for e in reds):
        score = min(score, 42)
        notes.append({"item": "硬约束", "detail": "窗口内出现立案调查，可信度上限 42", "delta": 0})
    if any("信息披露违法" in e["label"] or "行政处罚" in e["label"] for e in reds):
        score = min(score, 50)
        notes.append({"item": "硬约束", "detail": "窗口内出现处罚/虚假陈述，可信度上限 50", "delta": 0})
    flags = feat["flags"]
    recent_n = 0
    if flags is not None and not flags.empty:
        conduct_flags = flags[flags["dimension"] == "conduct"]
        if "age_years" in conduct_flags.columns and len(conduct_flags):
            recent_n = int((pd.to_numeric(conduct_flags["age_years"], errors="coerce").fillna(99) <= 3).sum())
    if recent_n == 0 and feat["notice_count"] >= 20:
        score += 6
        notes.append({"item": "近三年无监管红旗", "detail": "近三年标题未命中处罚/问询/立案", "delta": 6})
    elif flag_n == 0 and feat["notice_count"] >= 20:
        score += 6
        notes.append({"item": "无监管红旗", "detail": "标题层未命中处罚/问询类公告", "delta": 6})
    evidence_n = flag_n + min(feat["notice_count"] // 20, 6)
    confidence = _confidence(max(evidence_n, feat["notice_count"] // 10), feat["notice_count"] >= 30)
    return _pack("conduct", score, confidence, notes, flag_ev, evidence_n)


def score_board(feat: dict) -> dict:
    score = BASE_SCORE
    notes = []
    insiders = feat["insiders"]
    if insiders["rows"]:
        if insiders["sell_count"] > insiders["buy_count"] * 2 and insiders["sell_count"] >= 5:
            score -= 7
            notes.append({"item": "董监高减持", "detail": f"卖 {insiders['sell_count']} / 买 {insiders['buy_count']}", "delta": -7})
        elif insiders["buy_count"] > insiders["sell_count"]:
            score += 4
            notes.append({"item": "董监高增持占优", "detail": f"买 {insiders['buy_count']} / 卖 {insiders['sell_count']}", "delta": 4})
        else:
            notes.append({"item": "董监高持股变动", "detail": f"买 {insiders['buy_count']} / 卖 {insiders['sell_count']}", "delta": 0})
    holders = feat.get("shareholders") or []
    if holders:
        top = holders[0]
        ratio = top.get("占总股本持股比例")
        try:
            ratio_f = float(ratio)
            if ratio_f >= 40:
                score += 3
                notes.append({"item": "控股集中度", "detail": f"第一大股东 {ratio_f:.1f}%", "delta": 3})
            elif ratio_f < 15:
                score -= 3
                notes.append({"item": "股权分散", "detail": f"第一大股东 {ratio_f:.1f}%", "delta": -3})
        except (TypeError, ValueError):
            pass
    flag_delta, flag_ev, flag_n = _flag_adjustment(feat["flags"], "board")
    score += flag_delta
    evidence_n = flag_n + (1 if insiders["rows"] else 0) + (1 if holders else 0)
    confidence = _confidence(evidence_n, True)
    return _pack("board", score, confidence, notes, flag_ev, evidence_n)


def score_culture(feat: dict) -> dict:
    score = BASE_SCORE
    notes = []
    d, text = _metric_delta(feat["expense_ratio"], high_good=False, good=12, weak=30, scale=5)
    score += d
    notes.append({"item": "三项费用比重", "detail": text, "delta": d})
    d, text = _metric_delta(feat["cash_to_sales"], high_good=True, good=15, weak=3, scale=5)
    score += d
    notes.append({"item": "经营现金流/收入", "detail": text, "delta": d})
    flag_delta, flag_ev, flag_n = _flag_adjustment(feat["flags"], "culture")
    score += flag_delta
    if any(e["label"] == "非标审计意见" for e in flag_ev):
        score = min(score, 40)
        notes.append({"item": "硬约束", "detail": "非标审计意见，管理文化上限 40", "delta": 0})
    evidence_n = flag_n + feat["annual_rows"]
    confidence = _confidence(evidence_n, feat["annual_rows"] >= 6)
    return _pack("culture", score, confidence, notes, flag_ev, evidence_n)


def score_employees(feat: dict) -> dict:
    score = 54.0  # weaker baseline: employee treatment is poorly disclosed in titles
    notes = [{"item": "披露缺口", "detail": "年报全文中的薪酬/社保/流失率尚未逐页解析，主要依赖公告标题与 ESG 社会分", "delta": 0}]
    esg = feat.get("esg") or {}
    social = esg.get("social") if esg else None
    if social is not None:
        delta = 8 if social >= 80 else (3 if social >= 65 else (-8 if social < 50 else 0))
        score += delta
        notes.append({"item": "华证 ESG 社会分", "detail": f"{social:.1f}", "delta": delta})
    flag_delta, flag_ev, flag_n = _flag_adjustment(feat["flags"], "employees")
    score += flag_delta
    if flag_n == 0:
        notes.append({"item": "劳动相关公告", "detail": "窗口内未命中裁员/仲裁/事故标题", "delta": 0})
    evidence_n = flag_n + (3 if social is not None else 0)
    confidence = _confidence(evidence_n, social is not None or flag_n > 0)
    return _pack("employees", score, confidence, notes, flag_ev, evidence_n)


def score_consumers(feat: dict) -> dict:
    score = 56.0
    notes = [{"item": "披露缺口", "detail": "客诉率、返修率、广告处罚全文未入库，主要依赖召回/质量/虚假宣传类公告", "delta": 0}]
    flag_delta, flag_ev, flag_n = _flag_adjustment(feat["flags"], "consumers")
    score += flag_delta
    if flag_n == 0 and feat["notice_count"] >= 30:
        score += 5
        notes.append({"item": "无质量红旗", "detail": "窗口内未命中召回/虚假宣传/重大质量标题", "delta": 5})
    evidence_n = flag_n + min(feat["notice_count"] // 40, 3)
    confidence = _confidence(max(evidence_n, 2), feat["notice_count"] >= 30)
    return _pack("consumers", score, confidence, notes, flag_ev, evidence_n)


def score_users(feat: dict) -> dict:
    notes = []
    flag_delta, flag_ev, flag_n = _flag_adjustment(feat["flags"], "users")
    if not feat.get("is_platform"):
        score = 52.0 + flag_delta
        notes.append(
            {
                "item": "企业类型",
                "detail": "主营描述未显示平台/互联网用户模式，用户维度证据天然偏少，分数向中性收缩",
                "delta": 0,
            }
        )
        confidence = "低" if flag_n == 0 else "中"
        packed = _pack("users", score, confidence, notes, flag_ev, flag_n)
        packed["not_applicable"] = flag_n == 0
        return packed
    score = BASE_SCORE + flag_delta
    notes.append({"item": "平台/用户型业务", "detail": feat.get("business_text", "")[:80], "delta": 0})
    if flag_n == 0:
        score += 4
        notes.append({"item": "无数据安全红旗", "detail": "未命中泄露/App 违规/网安审查标题", "delta": 4})
    confidence = _confidence(flag_n + 2, True)
    return _pack("users", score, confidence, notes, flag_ev, flag_n)


def _pack(dimension: str, score: float, confidence: str, notes: list, flags: list, evidence_n: int) -> dict:
    raw = clamp(score)
    final = _shrink_to_neutral(raw, confidence)
    return {
        "id": dimension,
        "label": DIMENSION_LABELS[dimension],
        "score": final,
        "raw_score": round(raw, 1),
        "band": _band(final),
        "confidence": confidence,
        "evidence_n": evidence_n,
        "notes": notes,
        "flags": flags,
        "summary": _summarize(DIMENSION_LABELS[dimension], final, notes, flags),
    }


def _summarize(label: str, score: float, notes: list, flags: list) -> str:
    drivers = [n for n in notes if n.get("delta")]
    drivers = sorted(drivers, key=lambda n: abs(n["delta"]), reverse=True)[:2]
    material = [f for f in flags if abs(float(f.get("delta") or 0)) >= 2.5]
    flag_txt = ""
    if material:
        top = material[0]
        flag_txt = f"；公告信号：{top['label']}×{top['count']}"
    drive_txt = "；".join(f"{d['item']} {d['detail']}" for d in drivers) if drivers else "窗口内无显著加减分项"
    return f"{label} {score:.0f} 分（{_band(score)}）。{drive_txt}{flag_txt}。"


def financial_sustainability(feat: dict) -> dict:
    score = BASE_SCORE
    notes = []
    d, text = _metric_delta(feat["leverage"], high_good=False, good=45, weak=75, scale=8)
    score += d
    notes.append({"item": "资产负债率", "detail": text, "delta": d})
    d, text = _metric_delta(feat["current_ratio"], high_good=True, good=1.5, weak=0.9, scale=6)
    score += d
    notes.append({"item": "流动比率", "detail": text, "delta": d})
    d, text = _metric_delta(feat["roe"], high_good=True, good=12, weak=4, scale=7)
    score += d
    notes.append({"item": "净资产收益率", "detail": text, "delta": d})
    div = feat["dividends"]
    if div["coverage"] >= 0.8:
        score += 6
        notes.append({"item": "分红连续性", "detail": f"{div['years_paid']} 年有现金分红", "delta": 6})
    elif div["coverage"] <= 0.2:
        score -= 5
        notes.append({"item": "分红连续性", "detail": "窗口内极少现金分红", "delta": -5})
    profit_cagr = feat.get("profit_cagr")
    if profit_cagr is not None:
        delta = 5 if profit_cagr >= 0.08 else (-6 if profit_cagr < -0.08 else 0)
        score += delta
        notes.append({"item": "净利润复合增速", "detail": f"{profit_cagr:.1%}", "delta": delta})
    return {
        "score": round(clamp(score), 1),
        "band": _band(clamp(score)),
        "notes": notes,
    }


def weighted_sum(dimensions: dict[str, dict], weights: dict[str, float]) -> float:
    usable = {
        key: weight
        for key, weight in weights.items()
        if not dimensions[key].get("not_applicable")
    }
    total_w = sum(usable.values()) or 1.0
    total = 0.0
    for key, weight in usable.items():
        total += dimensions[key]["score"] * (weight / total_w)
    return round(total, 1)


def analyze_company(
    code: str,
    years: int = 10,
    with_esg: bool = True,
    listing: dict | None = None,
) -> dict[str, Any]:
    code = str(code).zfill(6)
    bundle = ingest_company(code, years=years, with_esg=with_esg)
    feat = extract_features(bundle)
    dimensions = {
        "business_model": score_business(feat),
        "conduct": score_conduct(feat),
        "board": score_board(feat),
        "culture": score_culture(feat),
        "employees": score_employees(feat),
        "consumers": score_consumers(feat),
        "users": score_users(feat),
    }
    fin = financial_sustainability(feat)
    credibility = weighted_sum(dimensions, CREDIBILITY_WEIGHTS)
    sustainability = round(0.72 * weighted_sum(dimensions, SUSTAINABILITY_WEIGHTS) + 0.28 * fin["score"], 1)
    if listing is None:
        listing = lookup_company(code)
    name = listing.get("name") or code
    coverage = {
        "annual_reports_proxy": feat["annual_rows"],
        "notices": feat["notice_count"],
        "classified_flags": feat["flag_count"],
        "esg": feat["esg"] is not None,
        "insider_rows": feat["insiders"]["rows"],
        "limitations": [
            "年报/半年报/ESG 报告 PDF 正文尚未逐句抽取，文化、员工、消费者、用户四维目前以公告标题 + 财务指标 + ESG 评分为主。",
            "问询函正文、处罚决定书全文、客诉与诉讼细节需要监管函件与裁判文书库补齐。",
            "分数是证据加权的研究框架，不是投资建议，也不能替代律师/审计尽调。",
        ],
    }
    return {
        "code": code,
        "name": name,
        "list_date": listing.get("list_date"),
        "years_listed": listing.get("years_listed"),
        "exchange": listing.get("exchange"),
        "board": listing.get("board"),
        "industry": listing.get("industry"),
        "as_of": feat["as_of"],
        "window_years": years,
        "business": feat["business"],
        "is_platform": feat["is_platform"],
        "credibility": {
            "score": credibility,
            "band": _band(credibility),
            "weights": CREDIBILITY_WEIGHTS,
        },
        "sustainability": {
            "score": sustainability,
            "band": _band(sustainability),
            "weights": SUSTAINABILITY_WEIGHTS,
            "financial": fin,
        },
        "dimensions": dimensions,
        "coverage": coverage,
        "shareholders": feat["shareholders"],
        "dividends": feat["dividends"],
        "insiders": feat["insiders"],
        "esg": feat["esg"],
        "financial_snapshot": {
            "gross_margin": feat["gross_margin"],
            "net_margin": feat["net_margin"],
            "roe": feat["roe"],
            "leverage": feat["leverage"],
            "cash_to_ni": feat["cash_to_ni"],
            "revenue_cagr": nan_to_none(feat["revenue_cagr"]),
            "profit_cagr": nan_to_none(feat["profit_cagr"]),
        },
        "timeline": _timeline(feat["flags"]),
    }


def _timeline(flags: pd.DataFrame) -> list[dict]:
    if flags is None or flags.empty:
        return []
    frame = flags.sort_values(["date", "delta"], ascending=[False, True]).head(25)
    rows = []
    for _, row in frame.iterrows():
        rows.append(
            {
                "date": row.get("date"),
                "dimension": DIMENSION_LABELS.get(row.get("dimension"), row.get("dimension")),
                "severity": row.get("severity"),
                "label": row.get("label"),
                "delta": float(row.get("delta") or 0),
                "title": row.get("title"),
            }
        )
    return rows
