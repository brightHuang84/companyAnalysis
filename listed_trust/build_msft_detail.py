"""Merge Microsoft event analyses into JSON, markdown, and canvas."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path("/home/bright/cryto/data/issuers/MSFT")
CANVAS = Path(
    "/home/bright/.cursor/projects/home-bright-cryto/canvases/microsoft-event-trust.canvas.tsx"
)
REPORT = Path("/home/bright/cryto/reports/MSFT_event_decisions_1986_2026.md")

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
        merged.append(
            {
                "id": str(i),
                "date": event["date"],
                "type": event["type"],
                "event": event["event"],
                "news": event["news"],
                "verify": event["verify"],
                "decade": decade(event["date"]),
                "background": analysis["background"],
                "why": analysis["why"],
                "why_note": analysis["why_note"],
                "options": analysis["options"],
                "decisions": analysis["decisions"],
                "effect_near": analysis["effect_near"],
                "effect_far": analysis["effect_far"],
                "grade": analysis["grade"],
                "tone": GRADE_TONE.get(analysis["grade"], "neutral"),
            }
        )
    payload = {
        "issuer": base["issuer"],
        "ticker": base["ticker"],
        "exchange": base["exchange"],
        "ipo": base["ipo"],
        "as_of": "2026-09-07",
        "event_count": len(merged),
        "method": (
            "每条物质事件四段：当时背景、决策原因、决策目录（备选/实选）、"
            "近端与最终效果。原因栏区分公开口径与推断。效果按承诺与可核对结果判定。"
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
        "截止 2026-09-07。91 条物质事件全部按同一套字段写开：**当时背景、决策原因、决策目录（当时可走的路 / 实际拍板）、近端效果、最终效果**。",
        "",
        "决策原因里凡未写进新闻稿或监管原文的，在「原因核验」标明推断或未核实。效果判定：兑现 / 部分兑现 / 未兑现 / 被强制修正 / 未核实。",
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
            f"**效果判定：{row['grade']}** · 新闻对照：{row['news']} · 事实核验：{row['verify']}",
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
        ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_canvas(merged: list[dict], grades: Counter) -> None:
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
          91 条物质事件全部写开。先选年代，再点开一条：当时背景、为什么那么拍板、桌上有哪几条路、实际拍了什么、后来对没对上。
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
            headers={["日期", "类型", "事件", "效果判定"]}
            rows={filtered.map((row) => [row.date, row.type, row.event, row.grade])}
            rowTone={filtered.map((row) => row.tone)}
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
            <CardHeader trailing={<Text size="small">{selected.grade}</Text>}>
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
                <Text tone="tertiary" size="small">
                  新闻对照：{selected.news} · 事实核验：{selected.verify}
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


def main() -> None:
    merged = merge()
    grades = Counter(row["grade"] for row in merged)
    write_markdown(merged, grades)
    write_canvas(merged, grades)
    print("grades", dict(grades))
    print("json", (ROOT / "events_1986_2026.json").stat().st_size)
    print("md", REPORT.stat().st_size)
    print("canvas", CANVAS.stat().st_size)


if __name__ == "__main__":
    main()
