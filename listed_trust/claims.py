"""Pull promises, forecasts and causal explanations out of filing text.

Nothing here is treated as true. Every extracted statement is a claim that
must be verified later, or marked unverified.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from listed_trust.ingest import ROOT

# Keep windows short enough to stay human-readable in the ledger.
WINDOW = 280

PROMISE_RE = re.compile(
    r"((?:公司|本公司|控股股东|实际控制人|董事|监事|高级管理人员|独立)[^\n。]{0,40}承诺[^\n。]{0,180}[。；]?)"
)
PROMISE_ITEM_RE = re.compile(r"(承诺事项[^\n]{0,80}|尚未履行完毕的承诺[^\n]{0,80})")
PAYOUT_RE = re.compile(
    r"((?:现金分红|利润分配)[^\n。]{0,40}(?:不低于|不少于|不少于|不少于)[^\n。]{0,80}[。；]?)"
)
FORECAST_RE = re.compile(
    r"((?:预计|计划|拟|将于|力争)[^\n。]{0,12}(?:实现|完成|回购|增长|下降|投产|分红|增持)[^\n。]{0,140}[。；]?)"
)
EXPLAIN_RE = re.compile(
    r"((?:同比|较上年|较去年).{0,24}(?:增长|下降|减少|增加|上升).{0,20}(?:主要(?:原因|系)|系由于|主要因为|主要受)[^\n。]{0,180}[。；]?)"
)
CAUSE_RE = re.compile(
    r"((?:下降|减少|增长|增加)[^\n。]{0,20}主要(?:原因|系)[^\n。]{0,180}[。；]?)"
)
FACT_RE = re.compile(
    r"(实现(?:营业)?收入[^\n。]{0,80}[。；]?|归属于?上市公司股东的净利润[^\n。]{0,80}[。；]?)"
)

KIND_PATTERNS = (
    ("promise", PROMISE_RE),
    ("promise", PROMISE_ITEM_RE),
    ("payout_policy", PAYOUT_RE),
    ("forecast", FORECAST_RE),
    ("explanation", EXPLAIN_RE),
    ("explanation", CAUSE_RE),
    ("fact", FACT_RE),
)


def _clip(text: str) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) > WINDOW:
        return compact[: WINDOW - 1] + "…"
    return compact


def _claim_id(kind: str, title: str, snippet: str) -> str:
    raw = f"{kind}|{title}|{snippet}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def extract_from_text(text: str, *, title: str, source: dict) -> list[dict]:
    claims = []
    seen: set[str] = set()
    for kind, pattern in KIND_PATTERNS:
        for match in pattern.finditer(text):
            snippet = _clip(match.group(1) if match.lastindex else match.group(0))
            if len(snippet) < 12:
                continue
            key = snippet[:80]
            if key in seen:
                continue
            seen.add(key)
            claims.append(
                {
                    "id": _claim_id(kind, title, snippet),
                    "kind": kind,
                    "status": "unverified",
                    "must_verify": True,
                    "snippet": snippet,
                    "source_title": title,
                    "source_kind": source.get("kind"),
                    "published": source.get("published"),
                    "report_year": source.get("report_year"),
                    "text_path": source.get("text_path"),
                    "pdf": source.get("local_pdf"),
                }
            )
    return claims


def extract_claims(code: str) -> dict:
    code = str(code).zfill(6)
    folder = ROOT / "data" / "filings" / code
    extracted = json.loads((folder / "extracted.json").read_text(encoding="utf-8"))
    claims: list[dict] = []
    for item in extracted:
        path = Path(item["text_path"])
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        claims.extend(extract_from_text(text, title=item.get("title") or "", source=item))
    out = folder / "claims.json"
    payload = {"code": code, "count": len(claims), "claims": claims}
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload
