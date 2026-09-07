"""Verify extracted claims against later filings and audited financials.

Default is unverified. A statement is only marked verified when an independent
number or a later fulfillment disclosure matches. Causal explanations are
never marked true just because the company repeated them.
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

import pandas as pd

from listed_trust.features import annual_em, annual_financials
from listed_trust.ingest import ROOT, fetch_financials, fetch_financials_em

PCT_RE = re.compile(r"(-?[\d]+(?:\.[\d]+)?)\s*%")
YI_RE = re.compile(r"([\d]+(?:\.[\d]+)?)\s*亿元")


def _annual_table(code: str, years: int = 12) -> pd.DataFrame:
    raw = fetch_financials(code)
    as_of = date.today()
    start = date(as_of.year - years, 1, 1)
    return annual_financials(raw, start, as_of)


def _year_row(annual: pd.DataFrame, year: int | None) -> pd.Series | None:
    if year is None or annual is None or annual.empty:
        return None
    target = pd.Timestamp(year, 12, 31)
    hit = annual[annual["日期"] == target]
    if hit.empty:
        return None
    return hit.iloc[0]


def _close(actual: float, claimed: float, tol: float = 0.08) -> bool:
    if claimed == 0:
        return abs(actual) < 1e-6
    return abs(actual - claimed) / max(abs(claimed), 1e-6) <= tol


def _revenue_yi(em: pd.DataFrame, year: int | None) -> float | None:
    if year is None or em is None or em.empty or "TOTALOPERATEREVE" not in em.columns:
        return None
    target = pd.Timestamp(year, 12, 31)
    hit = em[em["REPORT_DATE"] == target]
    if hit.empty:
        return None
    value = pd.to_numeric(hit.iloc[0]["TOTALOPERATEREVE"], errors="coerce")
    if pd.isna(value) or value == 0:
        return None
    return float(value) / 1e8


def _fulfillment_hits(snippet: str, later_texts: list[str]) -> list[str]:
    blob = "\n".join(later_texts)
    hits = []
    if "增持" in snippet and (
        "增持计划实施完毕" in blob or "增持股份结果" in blob or "完成增持" in blob
    ):
        hits.append("后续出现增持结果披露")
    if "回购" in snippet and "回购实施完毕" in blob:
        hits.append("后续出现回购实施完毕")
    if "股权激励" in snippet and re.search(r"股权激励.{0,30}(已实施|实施完毕|已完成)", blob):
        hits.append("后续出现股权激励实施表述")
    return hits


def verify_claims(code: str, years: int = 10) -> dict:
    code = str(code).zfill(6)
    folder = ROOT / "data" / "filings" / code
    payload = json.loads((folder / "claims.json").read_text(encoding="utf-8"))
    extracted = json.loads((folder / "extracted.json").read_text(encoding="utf-8"))
    texts_by_date = []
    for item in extracted:
        published = item.get("published") or ""
        path = Path(item["text_path"])
        if not path.exists():
            continue
        texts_by_date.append((published, path.read_text(encoding="utf-8")[:80000]))
    texts_by_date.sort()
    annual = _annual_table(code, years=years + 2)
    em = annual_em(fetch_financials_em(code), date(date.today().year - years - 2, 1, 1), date.today())

    verified = []
    for claim in payload["claims"]:
        result = dict(claim)
        kind = claim["kind"]
        snippet = claim["snippet"]
        year = claim.get("report_year")
        notes = []
        status = "unverified"
        evidence = []

        if kind == "fact":
            if claim.get("source_kind") != "annual":
                notes.append("非年度报告数字，未与对应季报/半年报科目核对，保持未核实。")
            else:
                row = _year_row(annual, year)
                growth = PCT_RE.search(snippet)
                yi = YI_RE.search(snippet)
                if row is None:
                    notes.append("找不到该报告期年报财务指标，无法核对。")
                elif "收入" in snippet and "同比" in snippet and growth:
                    scale_ok = True
                    rev = _revenue_yi(em, year)
                    if yi and rev is not None:
                        claimed_yi = float(yi.group(1))
                        if claimed_yi < rev * 0.5:
                            notes.append("该句金额远低于全年营收，疑似季度/单品数字，不对全年同比。")
                            scale_ok = False
                    if scale_ok:
                        claimed = float(growth.group(1))
                        if "下降" in snippet or "减少" in snippet:
                            claimed = -claimed
                        actual = row.get("主营业务收入增长率(%)")
                        if pd.notna(actual):
                            actual = float(actual)
                            evidence.append(f"年报口径收入同比 {actual:.2f}%")
                            if abs(actual - claimed) <= 0.35:
                                status = "verified"
                                notes.append("收入同比与财务指标一致。")
                            else:
                                status = "contradicted"
                                notes.append(f"收入同比声称 {claimed}%，财务指标 {actual:.2f}%。")
                elif yi and "收入" in snippet:
                    notes.append("亿元口径需与合并报表绝对额对照，当前接口是增长率/比率，绝对额核对未完成。")
                    status = "partial"
                else:
                    notes.append("句子里没有可对照的量化字段。")
        elif kind in {"promise", "forecast", "payout_policy"}:
            published = claim.get("published") or ""
            later = [text[:40000] for when, text in texts_by_date if when > published]
            hits = _fulfillment_hits(snippet, later)
            row = _year_row(annual, (year or 0) + 1 if year else None)
            if "不低于" in snippet and "分红" in snippet and row is not None:
                payout = row.get("股息发放率(%)")
                bound = PCT_RE.search(snippet)
                if pd.notna(payout) and bound:
                    actual = float(payout)
                    claimed = float(bound.group(1))
                    evidence.append(f"次一年度股息发放率 {actual:.2f}%")
                    if actual + 1e-6 >= claimed * 0.9:
                        status = "verified"
                        notes.append("后续分红比例达到承诺下限（允许 10% 口径差）。")
                    else:
                        status = "contradicted"
                        notes.append(f"承诺下限 {claimed}%，后续股息发放率 {actual:.2f}%。")
            elif hits:
                status = "partial"
                notes.append("后续文件出现履行/完成表述，但未逐条对照金额与截止日期。")
                evidence.extend(hits)
            else:
                notes.append("公开文件中尚未找到可独立核验的履行结果。")
        elif kind == "explanation":
            row = _year_row(annual, year)
            # Causal language is not accepted as true. We only check whether
            # the accompanying direction matches the financials.
            growth = PCT_RE.search(snippet)
            if row is not None and ("收入" in snippet or "营收" in snippet) and growth:
                actual = row.get("主营业务收入增长率(%)")
                claimed = float(growth.group(1))
                if "下降" in snippet or "减少" in snippet:
                    claimed = -abs(claimed)
                if pd.notna(actual) and _close(float(actual), claimed, 0.2):
                    status = "partial"
                    notes.append("变动方向与幅度可与财务指标对照；原因本身无法仅凭年报证实。")
                    evidence.append(f"收入同比 {float(actual):.2f}%")
                elif pd.notna(actual):
                    status = "contradicted"
                    notes.append("解释中的变动幅度与财务指标不一致。")
                else:
                    notes.append("原因陈述缺少独立证据（渠道、需求、政策等需外部数据）。")
            else:
                notes.append("原因陈述缺少独立证据，保持未核实。")
        else:
            notes.append("未知类型，保持未核实。")

        result["status"] = status
        result["notes"] = notes
        result["evidence"] = evidence
        verified.append(result)

    counts = {
        "unverified": 0,
        "partial": 0,
        "verified": 0,
        "contradicted": 0,
    }
    for item in verified:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    out = {
        "code": code,
        "count": len(verified),
        "counts": counts,
        "rule": "默认为未核实。只有独立财务数字或后续履行披露对得上才升格。原因解释不得仅因公司自述而记为真实。",
        "claims": verified,
    }
    path = folder / "verified_claims.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out
