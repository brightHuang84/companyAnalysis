"""Serialize credibility and sustainability reports to JSON and Markdown."""

from __future__ import annotations

import json
import math
from datetime import date, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from listed_trust.ingest import ROOT
from listed_trust.keywords import DIMENSIONS

REPORT_DIR = ROOT / "reports"


def _json_default(value: Any):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, (np.floating, np.integer)):
        value = value.item()
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if isinstance(value, np.ndarray):
        return value.tolist()
    try:
        if pd.isna(value):
            return None
    except (ValueError, TypeError):
        pass
    return str(value)


def to_jsonable(report: dict) -> dict:
    return json.loads(json.dumps(report, default=_json_default, ensure_ascii=False))


def render_markdown(report: dict) -> str:
    cred = report["credibility"]
    sus = report["sustainability"]
    biz = report.get("business") or {}
    cov = report.get("coverage") or {}
    snap = report.get("financial_snapshot") or {}
    lines = [
        f"# {report.get('name') or report['code']}（{report['code']}）可信度与可持续报告",
        "",
        f"- 分析截止日：{report.get('as_of')}",
        f"- 上市日期：{report.get('list_date') or '未知'}；上市年限：{report.get('years_listed') or '未知'}",
        f"- 窗口：过去 {report.get('window_years')} 年定期报告指标 + 全量公告标题",
        f"- 板块：{report.get('exchange') or ''} {report.get('board') or ''} {report.get('industry') or ''}",
        "",
        "## 总评",
        "",
        f"- **公司可信度 {cred['score']}**（{_band_text(cred['band'])}）：承诺与披露是否可核对、监管与治理是否干净。",
        f"- **公司可持续 {sus['score']}**（{_band_text(sus['band'])}）：生意是否能在不收割利益相关方的前提下延续。",
        "",
        f"**主营**：{biz.get('主营业务') or '未取得'}",
        f"**经营范围**：{biz.get('经营范围') or '未取得'}",
        "",
        "## 七维得分",
        "",
        "| 维度 | 得分 | 档位 | 证据置信 | 摘要 |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for key in DIMENSIONS:
        dim = report["dimensions"][key]
        summary = str(dim.get("summary") or "").replace("|", "/")
        lines.append(
            f"| {dim['label']} | {dim['score']} | {dim['band']} | {dim['confidence']} | {summary} |"
        )
    fin = sus.get("financial") or {}
    lines += [
        "",
        f"财务可持续分项：{fin.get('score')}（{fin.get('band')}）。",
        "",
        "## 财务快照（年报口径，窗口内）",
        "",
        _snap_line("毛利率", snap.get("gross_margin")),
        _snap_line("净利率", snap.get("net_margin")),
        _snap_line("ROE", snap.get("roe")),
        _snap_line("资产负债率", snap.get("leverage")),
        _snap_line("经营现金流/净利润", snap.get("cash_to_ni")),
        f"- 收入复合增速：{_pct(snap.get('revenue_cagr'))}",
        f"- 净利润复合增速：{_pct(snap.get('profit_cagr'))}",
        f"- 现金分红覆盖：{report.get('dividends', {}).get('years_paid')} 年 / 窗口 {report.get('window_years')} 年",
        "",
        "## 关键公告时间线",
        "",
    ]
    timeline = report.get("timeline") or []
    if not timeline:
        lines.append("窗口内未命中监管处罚、质量事故、控制权或审计意见等关键词。")
    else:
        lines.append("| 日期 | 维度 | 级别 | 标签 | 标题 |")
        lines.append("| --- | --- | --- | --- | --- |")
        for item in timeline[:20]:
            title = str(item.get("title") or "").replace("|", "/")
            lines.append(
                f"| {item.get('date')} | {item.get('dimension')} | {item.get('severity')} | {item.get('label')} | {title} |"
            )
    lines += [
        "",
        "## 数据覆盖与局限",
        "",
        f"- 年报财务指标行数（代理）：{cov.get('annual_reports_proxy')}",
        f"- 公告条数：{cov.get('notices')}",
        f"- 标题命中的行为事件：{cov.get('classified_flags')}",
        f"- ESG 记录：{'有' if cov.get('esg') else '无'}",
        "",
    ]
    for limit in cov.get("limitations") or []:
        lines.append(f"- {limit}")
    lines.append("")
    return "\n".join(lines)


def _band_text(band: str) -> str:
    return band or ""


def _pct(value) -> str:
    if value is None:
        return "不足"
    return f"{value:.1%}"


def _snap_line(label: str, stats: dict | None) -> str:
    stats = stats or {}
    mean = stats.get("mean")
    last = stats.get("last")
    if mean is None and last is None:
        return f"- {label}：数据不足"
    mean_s = "n/a" if mean is None else f"{mean:.2f}"
    last_s = "n/a" if last is None else f"{last:.2f}"
    return f"- {label}：窗口均值 {mean_s}，最近一期 {last_s}"


def write_report(report: dict, out_dir: Path | None = None) -> tuple[Path, Path]:
    out_dir = out_dir or REPORT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = to_jsonable(report)
    stem = f"{payload['code']}_{payload.get('as_of')}"
    json_path = out_dir / f"{stem}.json"
    md_path = out_dir / f"{stem}.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(payload), encoding="utf-8")
    return json_path, md_path
