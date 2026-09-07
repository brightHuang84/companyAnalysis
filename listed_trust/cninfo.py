"""Download original CNINFO filings (PDF) instead of relying on title-only feeds."""

from __future__ import annotations

import json
import re
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

from listed_trust.ingest import CACHE_DIR, ROOT, retry

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "http://www.cninfo.com.cn",
    "Referer": "http://www.cninfo.com.cn/new/commonUrl/pageOfSearch?url=disclosure/list/search",
}

PDF_BASE = "http://static.cninfo.com.cn/"
SEARCH_URL = "http://www.cninfo.com.cn/new/information/topSearch/query"
QUERY_URL = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
CST = timezone(timedelta(hours=8))

SKIP_TITLE = ("英文", "摘要", "取消", "已取消", "更正公告")

PERIODIC_CATEGORIES = {
    "annual": "category_ndbg_szsh",
    "semi": "category_bndbg_szsh",
    "q1": "category_yjdbg_szsh",
    "q3": "category_sjdbg_szsh",
}


def _session() -> requests.Session:
    session = requests.Session()
    session.headers.update(HEADERS)
    return session


def resolve_org(code: str) -> dict:
    code = str(code).zfill(6)
    cache = CACHE_DIR / code / "cninfo_org.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))

    def _fetch() -> dict:
        session = _session()
        response = session.post(SEARCH_URL, data={"keyWord": code}, timeout=30)
        response.raise_for_status()
        rows = response.json()
        for row in rows:
            if str(row.get("code")) == code:
                return row
        raise RuntimeError(f"CNINFO orgId not found for {code}")

    payload = retry(_fetch)
    cache.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def _column(code: str) -> str:
    return "sse" if code.startswith("6") else "szse"


def query_announcements(
    code: str,
    *,
    start: date,
    end: date,
    category: str = "",
    searchkey: str = "",
) -> list[dict]:
    code = str(code).zfill(6)
    org = resolve_org(code)
    org_id = org["orgId"]
    session = _session()
    rows: list[dict] = []
    page = 1
    while True:
        data = {
            "pageNum": str(page),
            "pageSize": "30",
            "column": _column(code),
            "tabName": "fulltext",
            "plate": "",
            "stock": f"{code},{org_id}",
            "searchkey": searchkey,
            "secid": "",
            "category": category,
            "trade": "",
            "seDate": f"{start.isoformat()}~{end.isoformat()}",
            "sortName": "",
            "sortType": "",
            "isHLtitle": "true",
        }

        def _post(payload=data):
            response = session.post(QUERY_URL, data=payload, timeout=45)
            response.raise_for_status()
            return response.json()

        payload = retry(_post)
        batch = payload.get("announcements") or []
        rows.extend(batch)
        total_pages = int(payload.get("totalpages") or 1)
        if page >= total_pages or not batch:
            break
        page += 1
        time.sleep(0.25)
    return rows


def _keep_full_chinese(title: str) -> bool:
    text = re.sub(r"<[^>]+>", "", title or "")
    if any(token in text for token in SKIP_TITLE):
        return False
    if "正文" in text and "报告" in text:
        return False
    return True


def _normalize(row: dict, kind: str) -> dict:
    title = re.sub(r"<[^>]+>", "", row.get("announcementTitle") or "")
    ts = row.get("announcementTime")
    published = None
    if ts:
        published = datetime.fromtimestamp(int(ts) / 1000, tz=CST).date().isoformat()
    adjunct = row.get("adjunctUrl") or ""
    return {
        "id": str(row.get("announcementId") or ""),
        "title": title,
        "kind": kind,
        "published": published,
        "adjunct_type": row.get("adjunctType"),
        "adjunct_size_kb": row.get("adjunctSize"),
        "pdf_url": (PDF_BASE + adjunct) if adjunct else None,
        "adjunct_url": adjunct,
    }


def list_corpus(code: str, years: int = 10, as_of: date | None = None) -> list[dict]:
    code = str(code).zfill(6)
    as_of = as_of or date.today()
    start = date(as_of.year - years, 1, 1)
    seen: set[str] = set()
    items: list[dict] = []

    def add(kind: str, rows: list[dict]) -> None:
        for row in rows:
            item = _normalize(row, kind)
            if not item["id"] or item["id"] in seen:
                continue
            if not _keep_full_chinese(item["title"]):
                continue
            if not item["pdf_url"]:
                continue
            seen.add(item["id"])
            items.append(item)

    for kind, category in PERIODIC_CATEGORIES.items():
        add(kind, query_announcements(code, start=start, end=as_of, category=category))
        time.sleep(0.2)
    add("esg", query_announcements(code, start=start, end=as_of, searchkey="ESG"))
    add("csr", query_announcements(code, start=start, end=as_of, searchkey="社会责任报告"))
    add("promise", query_announcements(code, start=start, end=as_of, searchkey="承诺"))
    items.sort(key=lambda x: x.get("published") or "", reverse=True)
    return items


def download_corpus(code: str, years: int = 10) -> dict:
    code = str(code).zfill(6)
    folder = ROOT / "data" / "filings" / code
    folder.mkdir(parents=True, exist_ok=True)
    items = list_corpus(code, years=years)
    session = _session()
    saved = []
    for item in items:
        filename = f"{item['published']}_{item['id']}_{item['kind']}.pdf"
        path = folder / filename
        item["local_pdf"] = str(path)
        if path.exists() and path.stat().st_size > 1024:
            item["download"] = "cached"
            saved.append(item)
            continue
        if not item["pdf_url"]:
            item["download"] = "missing_url"
            saved.append(item)
            continue

        def _get(url=item["pdf_url"]):
            response = session.get(url, timeout=120)
            response.raise_for_status()
            if len(response.content) < 1024:
                raise RuntimeError("PDF too small")
            return response.content

        try:
            content = retry(_get)
            path.write_bytes(content)
            item["download"] = "ok"
            item["bytes"] = len(content)
        except Exception as exc:  # noqa: BLE001
            item["download"] = f"error:{type(exc).__name__}"
            item["error"] = str(exc)[:300]
        saved.append(item)
        time.sleep(0.35)

    manifest = folder / "manifest.json"
    manifest.write_text(json.dumps(saved, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = sum(1 for x in saved if x.get("download") in {"ok", "cached"})
    return {"code": code, "folder": str(folder), "count": len(saved), "downloaded": ok, "items": saved}
