"""Merge Microsoft event analyses into JSON, markdown, and canvas."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT_REPO = Path(__file__).resolve().parents[1]
if str(ROOT_REPO) not in sys.path:
    sys.path.insert(0, str(ROOT_REPO))

import importlib.util

_spec = importlib.util.spec_from_file_location(
    "msft_finance", Path(__file__).with_name("msft_finance.py")
)
_msft_finance = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_msft_finance)
attach_finance = _msft_finance.attach_finance

ROOT = ROOT_REPO / "data" / "issuers" / "MSFT"
CANVAS = Path(
    "/home/bright/.cursor/projects/home-bright-cryto/canvases/microsoft-event-trust.canvas.tsx"
)
FINANCE_CANVAS = Path(
    "/home/bright/.cursor/projects/home-bright-cryto/canvases/microsoft-decision-returns.canvas.tsx"
)
REPORT = ROOT_REPO / "reports" / "MSFT_event_decisions_1986_2026.md"
LEDGER = ROOT_REPO / "reports" / "MSFT_40year_ledger_2026-09-07.md"

GRADE_TONE = {
    "兑现": "success",
    "部分兑现": "info",
    "未兑现": "danger",
    "被强制修正": "warning",
    "未核实": "neutral",
    "中性": "neutral",
}


def decade(date: str) -> str:
    year = int(date[:4])
    if year < 1990:
        return "1986"
    if year < 2000:
        return "1990"
    if year < 2010:
        return "2000"
    if year < 2020:
        return "2010"
    return "2020"


def _fmt_pct(value) -> str:
    return "—" if value is None else f"{value:.1f}%"


def _fmt_usd_m(value) -> str:
    if value is None:
        return "—"
    n = float(value)
    if abs(n) >= 100:
        yi = n / 100.0
        text = f"{yi:.0f}" if yi >= 10 else f"{yi:.1f}"
        return f"{text} 亿美元"
    if abs(n) >= 1:
        return f"{n:.0f} 百万美元"
    return f"{n} 百万美元"


def _finance_markdown(fin: dict) -> str:
    co = fin["company"]
    pl = fin.get("product_line") or {}
    lines = [
        f"**这条事件自己的钱：** {fin.get('event_cash') or fin['outlay_kind']}",
        "",
        fin["outlay_text"],
        "",
        "**和当年年报的关系**",
        "",
        fin.get("books_role") or fin.get("note") or "",
        "",
        f"**这条产品线带给公司多少利润 · {pl.get('name') or '未归线'}**",
        "",
    ]
    for para in pl.get("paragraphs") or []:
        lines += [para, ""]
    lines += [
        f"**事后回收：{fin['return_grade']}**",
        "",
        fin["return_summary"],
        "",
        (
            f"对照用的全公司 FY{fin['fy']} 年报（不是本事件利润表）："
            f"营收 {_fmt_usd_m(co['revenue_usd_m'])}，研发 {_fmt_usd_m(co['rd_usd_m'])}"
            f"（占营收 {_fmt_pct(co['rd_pct'])}），毛利率 {_fmt_pct(co['gross_margin_pct'])}，"
            f"营业利润率 {_fmt_pct(co['op_margin_pct'])}，净利率 {_fmt_pct(co['net_margin_pct'])}。"
        ),
    ]
    return "\n".join(lines)


def load_details() -> list[dict]:
    parts = [
        ROOT / "analysis_00_30.json",
        ROOT / "analysis_31_60.json",
        ROOT / "analysis_61_90.json",
    ]
    out: list[dict] = []
    for path in parts:
        out.extend(json.loads(path.read_text(encoding="utf-8")))
    return out


def merge() -> list[dict]:
    base = json.loads((ROOT / "events_1986_2026.json").read_text(encoding="utf-8"))
    details = load_details()
    if len(base["events"]) != len(details):
        raise SystemExit(f"count mismatch {len(base['events'])} vs {len(details)}")
    merged: list[dict] = []
    for i, (event, analysis) in enumerate(zip(base["events"], details)):
        if event["date"] != analysis["date"]:
            raise SystemExit(f"date mismatch {i}: {event['date']} vs {analysis['date']}")
        src = event if event.get("background") else analysis
        merged.append(
            {
                "id": str(i),
                "date": event["date"],
                "type": event["type"],
                "event": event["event"],
                "news": event["news"],
                "verify": event["verify"],
                "decade": decade(event["date"]),
                "background": src["background"],
                "why": src["why"],
                "why_note": src.get("why_note") or analysis.get("why_note", ""),
                "options": src.get("options") or analysis.get("options", []),
                "decisions": src.get("decisions") or analysis.get("decisions", []),
                "effect_near": src["effect_near"],
                "effect_far": src["effect_far"],
                "grade": src.get("grade") or analysis["grade"],
                "tone": GRADE_TONE.get(src.get("grade") or analysis["grade"], "neutral"),
            }
        )
    merged = attach_finance(merged)
    payload = {
        "issuer": base["issuer"],
        "ticker": base["ticker"],
        "exchange": base["exchange"],
        "ipo": base["ipo"],
        "as_of": "2026-09-07",
        "event_count": len(merged),
        "method": (
            "每条物质事件四段：当时背景、决策原因、决策目录（备选/实选）、"
            "近端与最终效果。财务栏写这条事件自己的钱、它和当年全公司年报的关系，"
            "以及这条产品线能核对到的分部营业利润。微软不披露 Windows / Azure / Xbox 单品利润。"
            "更细的产品 10-K 给营收；席位增速在年报 KPI 里；绝对席位、标价和市场份额按年表另列并标明来源。"
        ),
        "analysis_fields": [
            "background",
            "why",
            "why_note",
            "options",
            "decisions",
            "effect_near",
            "effect_far",
            "grade",
            "finance",
        ],
        "events": [
            {key: row[key] for key in row if key not in ("id", "decade", "tone")}
            for row in merged
        ],
    }
    (ROOT / "events_1986_2026.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return merged


def write_markdown(merged: list[dict], grades: Counter) -> None:
    titles = {
        "1986": "1986–1989",
        "1990": "1990–1999",
        "2000": "2000–2009",
        "2010": "2010–2019",
        "2020": "2020–2026",
    }
    lines = [
        "# 微软四十年：逐条背景、决策目录与效果",
        "",
        "截止 2026-09-07。91 条物质事件全部按同一套字段写开：**当时背景、决策原因、决策目录（当时可走的路 / 实际拍板）、近端效果、最终效果、财务回报**。",
        "",
        "决策原因里凡未写进新闻稿或监管原文的，在「原因核验」标明推断或未核实。效果判定：兑现 / 部分兑现 / 未兑现 / 被强制修正 / 未核实。",
        "",
        "财务口径：微软不披露单品研发与单品营业利润。每条先写**这条事件自己的钱**，再写**它和当年全公司年报是什么关系**，再写**这条产品线带给公司多少利润**。能核对的最细一级是分部营业利润。更细产品 10-K 给营收；席位/订阅增速在年报 KPI；绝对席位、公开标价和市场份额按年列在产品线页，并标明来源。",
        "",
        (
            f"判定汇总：兑现 {grades['兑现']}，部分兑现 {grades['部分兑现']}，"
            f"未兑现 {grades['未兑现']}，被强制修正 {grades['被强制修正']}，"
            f"未核实 {grades['未核实']}。"
        ),
        "",
        "可逐条点开的台账在画布。机器可读：`data/issuers/MSFT/events_1986_2026.json`。",
        "",
    ]
    current = None
    for row in merged:
        if row["decade"] != current:
            current = row["decade"]
            lines += [f"## {titles[current]}", ""]
        lines += [
            f"### {row['date']} · {row['type']} · {row['event']}",
            "",
            f"**效果判定：{row['grade']}** · **财务回报：{row['finance']['return_grade']}** · 新闻对照：{row['news']} · 事实核验：{row['verify']}",
            "",
            "**当时背景**",
            "",
            row["background"],
            "",
            "**决策原因**",
            "",
            row["why"],
            "",
            f"*原因核验：{row['why_note']}*",
            "",
            "**决策目录 · 当时可走的路**",
            "",
        ]
        lines += [f"- {item}" for item in row["options"]]
        lines += ["", "**决策目录 · 实际拍板**", ""]
        lines += [f"- {item}" for item in row["decisions"]]
        lines += [
            "",
            "**近端效果**",
            "",
            row["effect_near"],
            "",
            "**最终效果**",
            "",
            row["effect_far"],
            "",
            "**财务回报**",
            "",
            _finance_markdown(row["finance"]),
            "",
            f"*口径：{row['finance']['note']}*",
            "",
        ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_canvas(merged: list[dict], grades: Counter) -> None:
    if not CANVAS.parent.exists():
        return
    events_js = json.dumps(merged, ensure_ascii=False, indent=2)
    chart = "[{ name: \"事件条数\", data: [%d, %d, %d, %d, %d] }]" % (
        grades["兑现"],
        grades["部分兑现"],
        grades["未兑现"],
        grades["被强制修正"],
        grades["未核实"],
    )
    mixed = grades["部分兑现"] + grades["被强制修正"]
    canvas = """import {
  BarChart,
  Callout,
  Card,
  CardBody,
  CardHeader,
  H1,
  H2,
  H3,
  Pill,
  Row,
  Select,
  Stack,
  Stat,
  Table,
  Text,
  useCanvasState,
} from "cursor/canvas";

type Decade = "1986" | "1990" | "2000" | "2010" | "2020";
type Kind = "all" | "产品" | "监管" | "并购" | "员工" | "安全" | "其他";
type Tone = "success" | "warning" | "danger" | "info" | "neutral";

type EventRow = {
  id: string;
  date: string;
  type: string;
  event: string;
  news: string;
  verify: string;
  decade: Decade;
  background: string;
  why: string;
  why_note: string;
  options: string[];
  decisions: string[];
  effect_near: string;
  effect_far: string;
  grade: string;
  tone: Tone;
  finance: {
    fy: number;
    product: string;
    outlay_kind: string;
    outlay_usd_m: number | null;
    outlay_text: string;
    event_cash: string;
    books_role: string;
    return_grade: string;
    return_tone: Tone;
    return_summary: string;
    note: string;
    product_line: {
      id: string;
      name: string;
      grain: string;
      paragraphs: string[];
      at_event: {
        fy: number;
        label: string;
        revenue_usd_m: number;
        operating_income_usd_m: number;
        op_margin_pct: number | null;
      } | null;
      latest: {
        fy: number;
        label: string;
        revenue_usd_m: number;
        operating_income_usd_m: number;
        op_margin_pct: number | null;
      } | null;
      revenue_only: { name: string; revenue_usd_m: number }[];
    };
    company: {
      fy: number;
      revenue_usd_m: number;
      gross_profit_usd_m: number | null;
      rd_usd_m: number;
      operating_income_usd_m: number;
      net_income_usd_m: number;
      capex_usd_m: number | null;
      rd_pct: number | null;
      gross_margin_pct: number | null;
      op_margin_pct: number | null;
      net_margin_pct: number | null;
      fy_note?: string;
    };
  };
};

const OTHER = new Set(["联盟", "管理层", "公司", "资本", "项目", "产品反馈", "诉讼", "竞争"]);

const DECADE_META: Record<Decade, string> = {
  "1986": "1986–89 上市",
  "1990": "1990–99 垄断成型",
  "2000": "2000–09 和解与欧盟",
  "2010": "2010–19 云与手机",
  "2020": "2020–26 AI 与还债",
};

const EVENTS: EventRow[] = """
    canvas += events_js
    canvas += """;

function matchesKind(row: EventRow, kind: Kind): boolean {
  if (kind === "all") return true;
  if (kind === "其他") return OTHER.has(row.type);
  return row.type === kind;
}

export default function MicrosoftEventDecisions() {
  const [decade, setDecade] = useCanvasState<Decade>("decade", "1986");
  const [kind, setKind] = useCanvasState<Kind>("kind", "all");
  const [sel, setSel] = useCanvasState<string>("sel", "0");
  const filtered = EVENTS.filter((row) => row.decade === decade && matchesKind(row, kind));
  const selected = filtered.find((row) => row.id === sel) ?? filtered[0];

  return (
    <Stack gap={24}>
      <Stack gap={8}>
        <H1>微软四十年：背景、决策目录与效果</H1>
        <Text tone="secondary">
          91 条物质事件全部写开。先选年代，再点开一条：当时背景、为什么那么拍板、桌上有哪几条路、实际拍了什么、后来对没对上。财务写这条事件自己的钱、它和当年年报的关系，以及这条产品线能核对到的分部营业利润——不是 Windows / Azure / Xbox 单品利润表。
        </Text>
      </Stack>

      <Row gap={24} wrap>
        <Stat value="91" label="逐条分析的事件" />
        <Stat value=\""""
    canvas += str(grades["兑现"])
    canvas += """\" label="判定兑现" tone="success" />
        <Stat value=\""""
    canvas += str(grades["未兑现"])
    canvas += """\" label="判定未兑现" tone="danger" />
        <Stat value=\""""
    canvas += str(mixed)
    canvas += """\" label="部分兑现 / 强制修正" tone="warning" />
      </Row>

      <Callout tone="warning" title="原因不是自动属实">
        背景和拍板清单尽量对照新闻与监管原文。决策「为什么」凡未写进公开文件的，标成推断或未核实。效果按承诺与事后行为对，不按管理层自我评价。
      </Callout>

      <H2>91 条效果判定</H2>
      <Text tone="secondary" size="small">
        条数 · 来源：本台账逐条判定 · 1986-03-13 至 2026-08 · 未核实 """
    canvas += str(grades["未核实"])
    canvas += """ 条
      </Text>
      <BarChart
        categories={["兑现", "部分兑现", "未兑现", "被强制修正", "未核实"]}
        series={"""
    canvas += chart
    canvas += """}
        height={220}
        showValues
      />

      <H2>选年代，再打开一条决策</H2>
      <Row gap={8} wrap>
        <Pill active={decade === "1986"} onClick={() => setDecade("1986")}>
          {DECADE_META["1986"]}
        </Pill>
        <Pill active={decade === "1990"} onClick={() => setDecade("1990")}>
          {DECADE_META["1990"]}
        </Pill>
        <Pill active={decade === "2000"} onClick={() => setDecade("2000")}>
          {DECADE_META["2000"]}
        </Pill>
        <Pill active={decade === "2010"} onClick={() => setDecade("2010")}>
          {DECADE_META["2010"]}
        </Pill>
        <Pill active={decade === "2020"} onClick={() => setDecade("2020")}>
          {DECADE_META["2020"]}
        </Pill>
      </Row>
      <Row gap={8} wrap>
        <Pill active={kind === "all"} onClick={() => setKind("all")}>
          全部类型
        </Pill>
        <Pill active={kind === "产品"} onClick={() => setKind("产品")}>
          产品
        </Pill>
        <Pill active={kind === "监管"} onClick={() => setKind("监管")}>
          监管
        </Pill>
        <Pill active={kind === "并购"} onClick={() => setKind("并购")}>
          并购
        </Pill>
        <Pill active={kind === "员工"} onClick={() => setKind("员工")}>
          员工
        </Pill>
        <Pill active={kind === "安全"} onClick={() => setKind("安全")}>
          安全
        </Pill>
        <Pill active={kind === "其他"} onClick={() => setKind("其他")}>
          其他
        </Pill>
      </Row>

      {filtered.length > 0 && selected && (
        <Stack gap={16}>
          <Table
            headers={["日期", "类型", "事件", "效果", "财务回报"]}
            rows={filtered.map((row) => [
              row.date,
              row.type,
              row.event,
              row.grade,
              row.finance.return_grade,
            ])}
            rowTone={filtered.map((row) => row.finance.return_tone)}
            striped
            stickyHeader
          />
          <Select
            value={selected.id}
            onChange={setSel}
            options={filtered.map((row) => ({
              value: row.id,
              label: row.date + " · " + row.event,
            }))}
          />
          <Card>
            <CardHeader trailing={<Text size="small">{selected.grade} · {selected.finance.return_grade}</Text>}>
              {selected.date} · {selected.type} · {selected.event}
            </CardHeader>
            <CardBody>
              <Stack gap={16}>
                <Stack gap={6}>
                  <H3>当时背景</H3>
                  <Text>{selected.background}</Text>
                </Stack>
                <Stack gap={6}>
                  <H3>决策原因</H3>
                  <Text>{selected.why}</Text>
                  <Text tone="secondary" size="small">
                    {selected.why_note}
                  </Text>
                </Stack>
                <Stack gap={6}>
                  <H3>决策目录 · 当时可走的路</H3>
                  <Table
                    headers={["备选"]}
                    rows={selected.options.map((item) => [item])}
                    striped
                  />
                </Stack>
                <Stack gap={6}>
                  <H3>决策目录 · 实际拍板</H3>
                  <Table
                    headers={["实选"]}
                    rows={selected.decisions.map((item) => [item])}
                    striped
                  />
                </Stack>
                <Stack gap={6}>
                  <H3>近端效果</H3>
                  <Text>{selected.effect_near}</Text>
                </Stack>
                <Stack gap={6}>
                  <H3>最终效果</H3>
                  <Text>{selected.effect_far}</Text>
                </Stack>
                <Stack gap={6}>
                  <H3>这条决策动了哪笔钱</H3>
                  <Text>{selected.finance.event_cash}</Text>
                  <Text>{selected.finance.outlay_text}</Text>
                </Stack>
                <Stack gap={6}>
                  <H3>和当年年报是什么关系</H3>
                  <Text>{selected.finance.books_role}</Text>
                </Stack>
                <Stack gap={6}>
                  <H3>这条产品线带给公司多少利润 · {selected.finance.product_line.name}</H3>
                  {selected.finance.product_line.paragraphs.map((para, i) => (
                    <Text key={String(i)}>{para}</Text>
                  ))}
                </Stack>
                <Stack gap={6}>
                  <H3>事后回收 · {selected.finance.return_grade}</H3>
                  <Text>{selected.finance.return_summary}</Text>
                  <Text tone="secondary" size="small">
                    对照用的全公司 FY{String(selected.finance.fy)} 年报（不是本事件利润表）：营收{" "}
                    {String(selected.finance.company.revenue_usd_m)} 百万美元 · 研发{" "}
                    {String(selected.finance.company.rd_usd_m)} 百万美元 · 营业利润率{" "}
                    {selected.finance.company.op_margin_pct == null
                      ? "—"
                      : String(selected.finance.company.op_margin_pct) + "%"}
                  </Text>
                </Stack>
                <Text tone="tertiary" size="small">
                  新闻对照：{selected.news} · 事实核验：{selected.verify} · 单品利润年报不单列
                </Text>
              </Stack>
            </CardBody>
          </Card>
        </Stack>
      )}

      <Text tone="tertiary" size="small">
        全文：reports/MSFT_event_decisions_1986_2026.md · JSON：data/issuers/MSFT/events_1986_2026.json
      </Text>
    </Stack>
  );
}
"""
    CANVAS.write_text(canvas, encoding="utf-8")


def _yi(usd_m: float | int) -> float:
    return round(float(usd_m) / 100.0, 1)


def write_finance_canvas(merged: list[dict]) -> None:
    if not FINANCE_CANVAS.parent.exists():
        return
    fy_payload = json.loads((ROOT / "financials_fy.json").read_text(encoding="utf-8"))
    lines_payload = json.loads((ROOT / "product_lines.json").read_text(encoding="utf-8"))
    years = fy_payload["years"]
    returns = Counter(row["finance"]["return_grade"] for row in merged)
    order = ["高回报", "正回报", "部分回收", "减值收场", "战略未兑现", "监管成本", "中性", "未核实"]
    return_chart = json.dumps(
        [{"name": "事件条数", "data": [returns[k] for k in order]}],
        ensure_ascii=False,
    )
    sample = [1986, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2024, 2025, 2026]
    by_fy = {int(row["fy"]): row for row in years}
    cats = [str(y) for y in sample]
    rd_pct = []
    op_pct = []
    for y in sample:
        row = by_fy[y]
        rd_pct.append(round(100.0 * row["rd"] / row["revenue"], 1))
        op_pct.append(round(100.0 * row["operating_income"] / row["revenue"], 1))
    deals = [
        row
        for row in merged
        if (row["finance"]["outlay_usd_m"] or 0) > 0
        and row["finance"]["outlay_kind"] not in ("股权融资（流入）", "未成交出价", "监管承诺")
    ]
    deals.sort(key=lambda r: float(r["finance"]["outlay_usd_m"] or 0), reverse=True)
    deal_rows = json.dumps(
        [
            [
                r["date"],
                r["finance"]["product"],
                _fmt_usd_m(r["finance"]["outlay_usd_m"]),
                r["finance"]["outlay_kind"],
                r["finance"]["return_grade"],
            ]
            for r in deals[:16]
        ],
        ensure_ascii=False,
    )
    deal_tones = json.dumps(
        [r["finance"]["return_tone"] for r in deals[:16]],
        ensure_ascii=False,
    )
    high = returns["高回报"] + returns["正回报"]
    bad = returns["减值收场"] + returns["战略未兑现"]
    by_line = {
        key: {int(row["fy"]): row for row in spec["years"]}
        for key, spec in lines_payload["lines"].items()
    }
    era1 = [2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013]
    era2 = [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]
    era1_series = json.dumps(
        [
            {
                "name": "Windows",
                "data": [_yi(by_line["windows"][y]["operating_income"]) for y in era1],
            },
            {
                "name": "Office",
                "data": [_yi(by_line["office"][y]["operating_income"]) for y in era1],
            },
            {
                "name": "服务器",
                "data": [_yi(by_line["cloud"][y]["operating_income"]) for y in era1],
            },
            {
                "name": "游戏/设备",
                "data": [_yi(by_line["gaming"][y]["operating_income"]) for y in era1],
            },
            {
                "name": "搜索/在线",
                "data": [_yi(by_line["search"][y]["operating_income"]) for y in era1],
            },
        ],
        ensure_ascii=False,
    )
    mpc_years = {
        int(row["fy"]): row
        for row in lines_payload["parents_now"]["more_personal_computing"]["years"]
    }
    era2_series = json.dumps(
        [
            {
                "name": "生产力与业务流程",
                "data": [_yi(by_line["office"][y]["operating_income"]) for y in era2],
            },
            {
                "name": "智能云",
                "data": [_yi(by_line["cloud"][y]["operating_income"]) for y in era2],
            },
            {
                "name": "更多个人计算",
                "data": [_yi(mpc_years[y]["operating_income"]) for y in era2],
            },
        ],
        ensure_ascii=False,
    )
    fy26_rev = lines_payload["product_revenue"]["2026"]
    parent_label = {
        "cloud": "计入智能云",
        "office": "计入生产力与业务流程",
        "gaming": "计入更多个人计算",
        "windows": "计入更多个人计算",
        "search": "计入更多个人计算",
        "devices": "计入更多个人计算",
        "company": "公司其他",
    }
    fy26_rev_rows = json.dumps(
        [
            [
                item["name"],
                _fmt_usd_m(item["revenue"]),
                "含在上一行" if item.get("nested") else "年报不单列",
                parent_label.get(item.get("line"), "—"),
            ]
            for item in fy26_rev
        ],
        ensure_ascii=False,
    )
    canvas = f'''import {{
  BarChart,
  Callout,
  Card,
  CardBody,
  CardHeader,
  H1,
  H2,
  LineChart,
  Row,
  Stack,
  Stat,
  Table,
  Text,
}} from "cursor/canvas";

export default function MicrosoftDecisionReturns() {{
  return (
    <Stack gap={{24}}>
      <Stack gap={{8}}>
        <H1>微软各产品线带给公司多少利润</H1>
        <Text tone="secondary">
          微软不披露 Windows、Office、Azure、Xbox、Copilot 的单品营业利润。能核对的最细一级是分部：2006–2013 年五条线（Windows、Office、服务器、游戏/设备、搜索），2016 年起三条（生产力、智能云、更多个人计算）。更细的产品只有营收。单位：亿美元。
        </Text>
      </Stack>

      <Row gap={{24}} wrap>
        <Stat value="839 亿" label="FY2026 生产力营业利润" tone="success" />
        <Stat value="570 亿" label="FY2026 智能云营业利润" tone="success" />
        <Stat value="144 亿" label="FY2026 更多个人计算营业利润" tone="warning" />
        <Stat value="不单列" label="Windows / Azure / Xbox 各自利润" />
      </Row>

      <Callout tone="warning" title="没有单品利润表">
        PowerPoint、Teams、Azure、Xbox、Bing 都不单独出营业利润。Office 利润是整条生产力分部；Azure 利润含在智能云里；Windows、Xbox、搜索从 2016 年起并进「更多个人计算」。下面的公司研发和利润率是微软整体数字，用来看当时买不买得起，不是这条产品的 ROI。
      </Callout>

      <H2>2006–2013：五条产品线的营业利润</H2>
      <Text tone="secondary" size="small">
        亿美元 · 来源：同期 10-K 分部表 · Windows=Client/Windows Division，Office=Microsoft Business Division，服务器=Server and Tools，游戏=Entertainment and Devices，搜索=Online Services。搜索 2012 年亏损含 aQuantive 减值。分部口径后来切过，不能直接接到 2016 年之后。
      </Text>
      <BarChart
        categories={{{json.dumps([str(y) for y in era1])}}}
        series={{{era1_series}}}
        stacked
        height={{280}}
        valueSuffix=" 亿美元"
      />

      <H2>2016–2026：三个分部的营业利润</H2>
      <Text tone="secondary" size="small">
        亿美元 · 来源：10-K / FY2026 业绩稿 · 生产力含 365、LinkedIn、Dynamics、Teams；智能云含 Azure 与服务器，Azure 没有单独利润；更多个人计算含 Windows、Xbox、搜索、设备。
      </Text>
      <BarChart
        categories={{{json.dumps([str(y) for y in era2])}}}
        series={{{era2_series}}}
        stacked
        height={{280}}
        valueSuffix=" 亿美元"
      />

      <H2>FY2026 更细产品：只有营收，没有利润</H2>
      <Text tone="secondary" size="small">
        来源：FY2026 10-K 产品表 · Azure 全年营收超过 1000 亿美元，利润仍含在智能云 570 亿里
      </Text>
      <Table
        headers={{["产品", "FY2026 营收", "营业利润", "利润记在哪"]}}
        rows={{{fy26_rev_rows}}}
        striped
      />

      <H2>研发占比与公司营业利润率</H2>
      <Text tone="secondary" size="small">
        单位：占营收 % · 来源：年报 / 10-K / FY2026 业绩稿 · 财年截止 6 月 30 日 · FY2016–17 为 ASC 606 重述后比较数
      </Text>
      <LineChart
        categories={{{json.dumps(cats)}}}
        series={{[
          {{ name: "研发 / 营收", data: {json.dumps(rd_pct)} }},
          {{ name: "营业利润率", data: {json.dumps(op_pct)}, tone: "success" }},
        ]}}
        height={{260}}
        valueSuffix="%"
        beginAtZero={{false}}
      />

      <H2>FY2026 三个分部对照</H2>
      <Text tone="secondary" size="small">
        来源：2026-07-29 业绩稿 · 财年 2026 · 这是能核对的最细营业利润，不是 Windows / Azure / Xbox 单品
      </Text>
      <Table
        headers={{["分部", "营收", "营业利润", "营业利润率", "对应产品线"]}}
        rows={{[
          ["生产力与业务流程", "1400 亿美元", "839 亿美元", "60%", "Office 365、LinkedIn、Dynamics、Teams"],
          ["智能云", "1378 亿美元", "570 亿美元", "41%", "Azure、服务器；Azure 全年破 1000 亿，利润不单列"],
          ["更多个人计算", "541 亿美元", "144 亿美元", "27%", "Windows、Xbox、搜索、设备混在一起"],
        ]}}
        rowTone={{["success", "success", "warning"]}}
        striped
      />

      <H2>91 条决策的财务回报判定</H2>
      <Text tone="secondary" size="small">
        条数 · 来源：本台账逐条 · 高回报/正回报 {high}，减值/战略未兑现 {bad} · 1986–2026
      </Text>
      <BarChart
        categories={{{json.dumps(order, ensure_ascii=False)}}}
        series={{{return_chart}}}
        height={{240}}
        showValues
      />

      <H2>已披露大额现金：对价、减值、罚金</H2>
      <Text tone="secondary" size="small">
        按金额排序 · 未成交的雅虎出价 446 亿美元未列入 · 欧元罚金按当时汇率约成美元
      </Text>
      <Table
        headers={{["日期", "对象", "金额", "科目", "回报判定"]}}
        rows={{{deal_rows}}}
        rowTone={{{deal_tones}}}
        striped
        stickyHeader
      />

      <Row gap={{16}} wrap>
        <Card>
          <CardHeader>回收得上的</CardHeader>
          <CardBody>
            <Text>
              Forethought / PowerPoint 约 1400 万美元，变成 Office 利润中心。NT 当时不赚钱，后来是企业云的祖先。Azure 2010 商用时是费用，FY2026 智能云营业利润 570 亿美元。Office 上 iPad、GitHub、Minecraft、LinkedIn 没有减记，并进高利润分部。
            </Text>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>吐回去的</CardHeader>
          <CardBody>
            <Text>
              aQuantive 60 亿买、62 亿减记。诺基亚 72 亿买、76 亿减记。Skype 85 亿买、2025 年停服。Activision 687 亿交割后裁员、剥离，FY2026 第四季 Xbox 内容与服务 -10%。欧盟累计罚金超过 20 亿欧元，买的是时间不是产品。
            </Text>
          </CardBody>
        </Card>
      </Row>

      <Callout tone="info" title="同一张账本，两条曲线">
        公司利润率在云和 365 上创了新高，所以裁员和资本开支都撑得住。更多个人计算分部营业利润只有 144 亿美元，撑不住 687 亿美元的游戏并购。财务核验的结论是：企业云做成了；消费入口、手机、广告、天价游戏多次做不成。
      </Callout>

      <Text tone="tertiary" size="small">
        逐条事件：microsoft-event-trust.canvas.tsx · 全文 reports/MSFT_event_decisions_1986_2026.md · 年度序列 data/issuers/MSFT/financials_fy.json
      </Text>
    </Stack>
  );
}}
'''
    FINANCE_CANVAS.write_text(canvas, encoding="utf-8")


def patch_ledger(merged: list[dict]) -> None:
    if not LEDGER.exists():
        return
    returns = Counter(row["finance"]["return_grade"] for row in merged)
    section = [
        "## 财务核验（决策与产品回报）",
        "",
        "微软不披露 Windows、Office、Xbox、Copilot 的单品研发和单品利润。每条事件的财务栏分四句看：",
        "",
        "1. **这条事件自己的钱**：并购对价、减值、罚金。没有单独科目就写未单列，不把全公司研发当成这条产品的开发费。",
        "2. **和当年年报的关系**：营收、毛利率、营业利润率是微软整体数字，用来看当时买不买得起、罚得起。不是这条产品的利润表。",
        "3. **这条产品线带给公司多少利润**：能核对的最细一级是分部营业利润。2006–2013 年有 Windows、Office、服务器、游戏/设备、搜索五条线；2016 年起只有生产力、智能云、更多个人计算三条。Azure、Xbox、Bing、PowerPoint 都没有单独营业利润。更细产品 10-K 给营收；席位增速在年报 KPI；绝对席位、公开标价和市场份额按年列在产品线页。2014–2015 年口径切过，相邻年不完全可比。",
        "4. **事后回收**：后来这笔资产有没有变成可核对的分部利润，或有没有减记。",
        "",
        (
            f"91 条财务回报判定：高回报 {returns['高回报']}，正回报 {returns['正回报']}，"
            f"部分回收 {returns['部分回收']}，减值收场 {returns['减值收场']}，"
            f"战略未兑现 {returns['战略未兑现']}，监管成本 {returns['监管成本']}，"
            f"中性 {returns['中性']}，未核实 {returns['未核实']}。"
        ),
        "",
        "公司利润率轨迹（财年截止 6 月 30 日）：FY1986 营业利润率约 31%、净利率约 20%；FY1999 营业利润率约 51%（桌面垄断高峰）；FY2015 因诺基亚减记掉到约 19%；FY2026 营收 3318 亿美元、研发 356 亿、资本开支 1159 亿、毛利率 67.9%、营业利润率 46.8%、净利率 40.3%。",
        "",
        "FY2026 分部营业利润：生产力 839 亿美元（利润率约 60%），智能云 570 亿（约 41%，Azure 全年破 1000 亿），更多个人计算 144 亿（约 27%；Windows OEM -7%，Xbox 内容与服务 -10%）。更细产品只有营收：服务器与云 1294 亿、Microsoft 365 商业 1020 亿、Xbox 218 亿、LinkedIn 198 亿、Windows 与设备 171 亿、搜索广告 152 亿。账本证明云和办公软件做成了，不能证明 Windows 消费 AI 与游戏并购兑现。",
        "",
        "对得上价格的决策：PowerPoint（约 1400 万美元）、Office 套装、NT/Azure、Office 跨平台、GitHub（75 亿）、Minecraft（25 亿）、LinkedIn（262 亿，FY26 第四季仍 +12%）。吐回去的：aQuantive 近全额减值、诺基亚减记 76 亿、Skype 停服、Activision 687 亿交割后裁员且内容收入下降。欧盟罚金是垄断租金的部分返还，不是产品投资。",
        "",
        "不要用 2018–2020 某些 XBRL 摘要里大约 300–380 亿美元的数字，那是季度量级被误读成年报。FY2016–FY2017 用 ASC 606 重述后比较数。",
        "",
    ]
    text = LEDGER.read_text(encoding="utf-8")
    start = text.find("## 财务核验")
    end = text.find("## 仍未独立核实")
    if start < 0 or end < 0:
        return
    LEDGER.write_text(text[:start] + "\n".join(section) + "\n" + text[end:], encoding="utf-8")


def main() -> None:
    merged = merge()
    grades = Counter(row["grade"] for row in merged)
    returns = Counter(row["finance"]["return_grade"] for row in merged)
    write_markdown(merged, grades)
    write_canvas(merged, grades)
    write_finance_canvas(merged)
    patch_ledger(merged)
    print("grades", dict(grades))
    print("returns", dict(returns))
    print("json", (ROOT / "events_1986_2026.json").stat().st_size)
    print("md", REPORT.stat().st_size)
    if CANVAS.exists():
        print("canvas", CANVAS.stat().st_size)
    if FINANCE_CANVAS.exists():
        print("finance_canvas", FINANCE_CANVAS.stat().st_size)


if __name__ == "__main__":
    main()
