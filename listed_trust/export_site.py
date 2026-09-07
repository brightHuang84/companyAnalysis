"""Copy issuer ledgers into docs/ for the public static site."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
MSFT = ROOT / "data" / "issuers" / "MSFT" / "events_1986_2026.json"


def main() -> None:
    DOCS.mkdir(exist_ok=True)
    dest = DOCS / "msft.json"
    shutil.copyfile(MSFT, dest)
    fy = ROOT / "data" / "issuers" / "MSFT" / "financials_fy.json"
    if fy.exists():
        shutil.copyfile(fy, DOCS / "financials_fy.json")
    lines = ROOT / "data" / "issuers" / "MSFT" / "product_lines.json"
    if lines.exists():
        shutil.copyfile(lines, DOCS / "product_lines.json")
    payload = json.loads(MSFT.read_text(encoding="utf-8"))
    catalog = {
        "as_of": payload.get("as_of"),
        "issuers": [
            {
                "ticker": payload.get("ticker", "MSFT"),
                "name": payload.get("issuer", "Microsoft Corporation"),
                "slug": "msft",
                "exchange": payload.get("exchange", "NASDAQ"),
                "ipo": payload.get("ipo"),
                "event_count": payload.get("event_count", len(payload.get("events", []))),
                "json": "msft.json",
                "page": "msft.html",
            }
        ],
    }
    (DOCS / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"copied {catalog['issuers'][0]['event_count']} events -> {dest}")


if __name__ == "__main__":
    main()
