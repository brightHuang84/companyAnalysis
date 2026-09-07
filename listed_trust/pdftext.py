"""Turn downloaded filing PDFs into searchable plain text."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pymupdf

from listed_trust.ingest import ROOT

YEAR_RE = re.compile(r"(20\d{2})\s*年")


def extract_pdf(path: Path) -> dict:
    doc = pymupdf.open(path)
    pages = []
    empty = 0
    for index, page in enumerate(doc, start=1):
        text = page.get_text("text") or ""
        text = text.replace("\u3000", " ").replace("\xa0", " ")
        pages.append({"page": index, "text": text, "chars": len(text.strip())})
        if len(text.strip()) < 40:
            empty += 1
    full = "\n\n".join(p["text"] for p in pages)
    return {
        "path": str(path),
        "pages": len(pages),
        "chars": len(full),
        "empty_pages": empty,
        "needs_ocr": empty > max(3, len(pages) // 3) or len(full) < 800,
        "text": full,
        "page_chars": [{"page": p["page"], "chars": p["chars"]} for p in pages],
    }


def report_year_from_title(title: str) -> int | None:
    match = YEAR_RE.search(title or "")
    return int(match.group(1)) if match else None


def extract_corpus(code: str) -> dict:
    code = str(code).zfill(6)
    folder = ROOT / "data" / "filings" / code
    manifest_path = folder / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"missing manifest: {manifest_path}")
    items = json.loads(manifest_path.read_text(encoding="utf-8"))
    text_dir = folder / "text"
    text_dir.mkdir(parents=True, exist_ok=True)
    extracted = []
    for item in items:
        if item.get("download") not in {"ok", "cached"}:
            continue
        pdf = Path(item["local_pdf"])
        if not pdf.exists():
            continue
        txt_path = text_dir / (pdf.stem + ".txt")
        meta_path = text_dir / (pdf.stem + ".meta.json")
        if txt_path.exists() and meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        else:
            payload = extract_pdf(pdf)
            txt_path.write_text(payload["text"], encoding="utf-8")
            meta = {k: v for k, v in payload.items() if k != "text"}
            meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        record = {
            **item,
            "text_path": str(txt_path),
            "pages": meta.get("pages"),
            "chars": meta.get("chars"),
            "needs_ocr": meta.get("needs_ocr"),
            "report_year": report_year_from_title(item.get("title") or ""),
        }
        extracted.append(record)
    index_path = folder / "extracted.json"
    index_path.write_text(json.dumps(extracted, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "code": code,
        "count": len(extracted),
        "ocr_needed": sum(1 for x in extracted if x.get("needs_ocr")),
        "items": extracted,
    }
