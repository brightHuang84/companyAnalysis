"""Attach original annual-report letters (translated) to each Microsoft fiscal year.

US 10-Ks have no A-share「董事会报告」chapter. The closest original text is the
Letter to Shareholders in the glossy annual report, or Item 7 MD&A Overview when
the letter is not out yet. Summaries are not used.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MSFT = ROOT / "data" / "issuers" / "MSFT"
OUT = MSFT / "board_reports.json"
EVENTS = MSFT / "events_1986_2026.json"
FY_PATH = MSFT / "financials_fy.json"

# Board / CEO execution. Dates are the public announcement or effective date.
GOVERNANCE = [
    {
        "date": "1975-04-04",
        "fy": None,
        "title": "微软成立",
        "who": "Bill Gates / Paul Allen",
        "detail": "Gates 与 Allen 合伙成立公司。此后直到上市，Gates 同时是事实上的董事长和首席执行官。",
    },
    {
        "date": "1981-06-25",
        "fy": None,
        "title": "改组为华盛顿州公司",
        "who": "Bill Gates",
        "detail": "从合伙改成股份公司，给后来的期权池和 IPO 铺治理结构。",
    },
    {
        "date": "1986-03-13",
        "fy": 1986,
        "title": "纳斯达克上市，公众公司治理开始",
        "who": "董事长兼 CEO：Bill Gates",
        "detail": "发行价 21 美元，融资约 6100 万美元。Gates 继续兼任董事长与 CEO，董事会对公众股东负责。",
    },
    {
        "date": "2000-01-13",
        "fy": 2000,
        "title": "Ballmer 接任 CEO，Gates 改任董事长兼首席软件架构师",
        "who": "CEO：Steve Ballmer · 董事长：Bill Gates",
        "detail": "第一次把日常经营和产品愿景拆开。反垄断案进行中，董事会选择内部交班而不是空降。",
    },
    {
        "date": "2000-11",
        "fy": 2001,
        "title": "Paul Allen 离开董事会",
        "who": "联合创始人离任董事",
        "detail": "Allen 1983 年已离开经营，2000 年底退出董事会，创始人双核变成 Gates 一人在董事会里代表创办世代。",
    },
    {
        "date": "2003-01-16",
        "fy": 2003,
        "title": "首次现金分红（当时按年派，每股拆前 0.16 美元）",
        "who": "董事会批准资本回报政策",
        "detail": "从「只回购、不分红」改成向股东派现。标志桌面现金牛进入回流阶段；后来改成季度分红，并在 2004 年加了特别分红。",
    },
    {
        "date": "2004-07-20",
        "fy": 2005,
        "title": "每股 3 美元特别分红，约 320 亿美元",
        "who": "董事会一次性返还现金",
        "detail": "当时美国公司史上最大规模现金分红之一。董事会判断账上现金已超过再投资需要。",
    },
    {
        "date": "2008-06-27",
        "fy": 2008,
        "title": "Gates 卸任全职，保留董事长",
        "who": "董事长：Bill Gates · CEO：Steve Ballmer",
        "detail": "Gates 把日常工程权交给 Ballmer 团队，自己把时间转向基金会。董事会结构没变，执行重心彻底落到 CEO。",
    },
    {
        "date": "2013-08-23",
        "fy": 2014,
        "title": "Ballmer 宣布一年内退休",
        "who": "董事会启动 CEO 遴选",
        "detail": "Windows 8 / Surface / 诺基亚路线受挫后，董事会接受交班。公开说内部优先，最终仍选了内部的 Nadella。",
    },
    {
        "date": "2014-02-04",
        "fy": 2014,
        "title": "Nadella 任 CEO；Gates 卸任董事长；Thompson 任独立董事董事长",
        "who": "CEO：Satya Nadella · 董事长：John W. Thompson",
        "detail": "第一次出现独立董事董事长。Gates 留任董事并当顾问。Ballmer 随后在 2014 年离开董事会。",
    },
    {
        "date": "2014-08",
        "fy": 2015,
        "title": "Ballmer 离开董事会",
        "who": "前 CEO 不再任董事",
        "detail": "交班完成。此后董事会不再同时坐着两任前 CEO（Gates 仍在，直到 2020）。",
    },
    {
        "date": "2020-03-13",
        "fy": 2020,
        "title": "Gates 离开董事会",
        "who": "创始人退出董事席",
        "detail": "公开理由是把时间给基金会和气候变化。董事会失去创办人席位，独立董事占比升到最高。",
    },
    {
        "date": "2021-06-16",
        "fy": 2021,
        "title": "Nadella 兼任董事长，Thompson 改任首席独立董事",
        "who": "董事长兼 CEO：Satya Nadella",
        "detail": "云转型被董事会视为已站稳，重新允许 CEO 兼董事长。Thompson 留下做独立制衡。",
    },
    {
        "date": "2023-11-17",
        "fy": 2024,
        "title": "OpenAI 董事会危机：微软公开承接团队，随后获观察员席",
        "who": "Nadella 代表董事会对外执行",
        "detail": "不是改微软自己的董事会，但是当年最重要的治理动作：把 AI 伙伴的治理风险当成自身执行事项处理。",
    },
]

LETTERS_DIR = MSFT / "letters"


def load_letters() -> tuple[dict[int, dict], dict[int, dict]]:
    """Load translated/official original letters. Not summaries."""
    by_fy: dict[int, dict] = {}
    missing: dict[int, dict] = {}
    for path in sorted(LETTERS_DIR.glob("fy*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for row in data.get("years") or []:
            by_fy[int(row["fy"])] = row
        for row in data.get("missing") or []:
            missing[int(row["fy"])] = row
    return by_fy, missing



def fy_of(date: str) -> int:
    raw = str(date).split("/")[0]
    year = int(raw[:4])
    if len(raw) == 4:
        return year
    month = int(raw[5:7])
    return year if month <= 6 else year + 1


def _pct(num, den):
    if num is None or den in (None, 0):
        return None
    return round(100.0 * float(num) / float(den), 1)


def _yoy(cur, prev):
    if cur is None or prev in (None, 0):
        return None
    return round(100.0 * (float(cur) - float(prev)) / float(prev), 1)


def _money(value):
    if value is None:
        return None
    n = float(value)
    if abs(n) >= 100:
        yi = n / 100.0
        text = f"{yi:.0f}" if yi >= 10 else f"{yi:.1f}"
        return f"{text} 亿美元"
    return f"{n:.0f} 百万美元"


def leaders_on(iso: str) -> tuple[str, str]:
    if iso < "2000-01-13":
        return "Bill Gates", "Bill Gates"
    if iso < "2014-02-04":
        return "Steve Ballmer", "Bill Gates"
    if iso < "2021-06-16":
        return "Satya Nadella", "John W. Thompson"
    return "Satya Nadella", "Satya Nadella"


def event_fy(row: dict) -> int:
    date = str(row.get("date") or "")
    # Annual earnings sit in late July, after the FY close they report.
    if date.startswith("2026-07-29"):
        return 2026
    if date.startswith("2026-07-06"):
        return 2026
    return fy_of(date)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build() -> dict:
    fy_payload = load_json(FY_PATH)
    letters, letter_missing = load_letters()
    events = load_json(EVENTS).get("events") or []
    years_fin = {int(r["fy"]): r for r in fy_payload.get("years") or []}
    prev = None
    by_fy: dict[int, list] = {}
    for ev in events:
        fy = event_fy(ev)
        by_fy.setdefault(fy, []).append(
            {"date": ev.get("date"), "type": ev.get("type"), "event": ev.get("event")}
        )

    gov_by_fy: dict[int, list] = {}
    timeline = []
    for item in GOVERNANCE:
        fy = item.get("fy")
        row = {
            "date": item["date"],
            "fy": fy,
            "title": item["title"],
            "who": item["who"],
            "detail": item["detail"],
        }
        timeline.append(row)
        if fy:
            gov_by_fy.setdefault(int(fy), []).append(row)

    reports = []
    for fy in sorted(years_fin):
        fin = years_fin[fy]
        letter = letters.get(fy) or {}
        gap = letter_missing.get(fy) or {}
        ceo, chair = leaders_on(f"{fy}-06-30")
        yoy_rev = _yoy(fin.get("revenue"), (prev or {}).get("revenue") if prev else None)
        op_m = _pct(fin.get("operating_income"), fin.get("revenue"))
        net_m = _pct(fin.get("net_income"), fin.get("revenue"))
        has_letter = bool(letter.get("paragraphs"))
        reports.append(
            {
                "fy": fy,
                "period": f"{fy - 1}-07-01 ~ {fy}-06-30",
                "ceo": ceo,
                "chair": chair,
                "letter_author": letter.get("author") or ceo,
                "letter_role": letter.get("role") or "",
                "letter_date": letter.get("date") or "",
                "source_kind": letter.get("source_kind")
                or ("当年无可用电子原文" if gap else "未找到原文"),
                "source": letter.get("source") or gap.get("note") or "当年年报电子原文未能取得。",
                "source_url": letter.get("source_url") or "",
                "greeting": letter.get("greeting") or "",
                "paragraphs": list(letter.get("paragraphs") or []),
                "unavailable": None if has_letter else (gap.get("note") or "当年年报电子原文未能取得，不编造概要。"),
                "board_moves": gov_by_fy.get(fy, []),
                "year_events": by_fy.get(fy, []),
                "financials": {
                    "revenue_usd_m": fin.get("revenue"),
                    "revenue_yoy_pct": yoy_rev,
                    "rd_usd_m": fin.get("rd"),
                    "operating_income_usd_m": fin.get("operating_income"),
                    "op_margin_pct": op_m,
                    "net_income_usd_m": fin.get("net_income"),
                    "net_margin_pct": net_m,
                    "capex_usd_m": fin.get("capex"),
                    "revenue_text": _money(fin.get("revenue")),
                    "operating_income_text": _money(fin.get("operating_income")),
                    "net_income_text": _money(fin.get("net_income")),
                },
            }
        )
        prev = fin

    payload = {
        "issuer": "Microsoft Corporation",
        "ticker": "MSFT",
        "as_of": fy_payload.get("as_of"),
        "fiscal_year_end": fy_payload.get("fiscal_year_end") or "June 30",
        "method": (
            "美国 10-K 没有 A 股「董事会报告」科目。这里按财年贴年报里致股东信的中文："
            "有官方中文就用官方中文，否则把英文原文译出，不另写概要。"
            "图文年报还没出时用 10-K 管理层讨论与分析的概述原文翻译。"
            "电子档找不到的年份标明缺口，不编造。"
        ),
        "year_count": len(reports),
        "governance": timeline,
        "years": reports,
    }
    return payload


def write_report_md(payload: dict) -> None:
    reports_dir = ROOT / "reports"
    reports_dir.mkdir(exist_ok=True)
    path = reports_dir / "MSFT_board_reports_2026-09-07.md"
    lines = [
        "# 微软董事会报告（按财年）",
        "",
        payload["method"],
        "",
        f"覆盖 FY{payload['years'][0]['fy']}–FY{payload['years'][-1]['fy']}，共 {payload['year_count']} 年。",
        "页：`docs/company.html`。数据：`data/issuers/MSFT/board_reports.json`，由 `listed_trust/enrich_board_reports.py` 写入。",
        "",
        "## 董事会执行时间线",
        "",
    ]
    for row in payload["governance"]:
        fy = f"FY{row['fy']} · " if row.get("fy") else ""
        lines.append(f"- **{row['date']}** {fy}{row['title']} — {row['who']}")
        lines.append(f"  {row['detail']}")
    lines += ["", "## 各年原文", ""]
    for y in payload["years"]:
        fin = y["financials"]
        yoy = fin.get("revenue_yoy_pct")
        yoy_s = f"，营收同比 {yoy:+.1f}%" if yoy is not None else ""
        lines.append(f"### FY{y['fy']}（{y['period']}）")
        lines.append("")
        lines.append(
            f"CEO {y['ceo']} · 董事长 {y['chair']} · {y['source_kind']} · "
            f"营收 {fin.get('revenue_text')}{yoy_s} · 营业利润率 {fin.get('op_margin_pct')}%。"
        )
        lines.append("")
        if y.get("source_url"):
            lines.append(f"来源：{y['source']} · {y['source_url']}")
            lines.append("")
        if y.get("unavailable"):
            lines.append(y["unavailable"])
            lines.append("")
            continue
        if y.get("greeting"):
            lines.append(y["greeting"])
            lines.append("")
        for para in y.get("paragraphs") or []:
            lines.append(para)
            lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {path}")


def main() -> None:
    payload = build()
    empty = [y["fy"] for y in payload["years"] if not y.get("paragraphs") and not y.get("unavailable")]
    if empty:
        raise SystemExit(f"missing original letter text for FY {empty}")
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report_md(payload)
    print(f"wrote {OUT} ({payload['year_count']} years, {len(payload['governance'])} governance rows)")


if __name__ == "__main__":
    main()
