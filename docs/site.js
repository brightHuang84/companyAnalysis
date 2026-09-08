function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[ch]));
}

function gradeClass(grade) {
  if (grade === "兑现") return "ok";
  if (grade === "未兑现") return "bad";
  if (grade === "部分兑现") return "mid";
  if (grade === "被强制修正") return "warn";
  return "";
}

function returnClass(grade) {
  if (grade === "高回报" || grade === "正回报") return "ok";
  if (grade === "减值收场" || grade === "战略未兑现") return "bad";
  if (grade === "部分回收") return "mid";
  if (grade === "监管成本" || grade === "未核实") return "warn";
  return "";
}

function decadeOf(date) {
  const y = parseInt(String(date).slice(0, 4), 10);
  if (y < 1990) return "1986";
  if (y < 2000) return "1990";
  if (y < 2010) return "2000";
  if (y < 2020) return "2010";
  return "2020";
}

function haystack(row) {
  return [
    row.date, row.type, row.event, row.news, row.verify,
    row.background, row.why, row.why_note,
    row.effect_near, row.effect_far, row.grade,
    ...(row.options || []),
    ...(row.decisions || []),
    row.finance && row.finance.event_cash,
    row.finance && row.finance.books_role,
    row.finance && row.finance.product,
    row.finance && row.finance.return_grade,
    row.finance && row.finance.return_summary,
    row.finance && row.finance.outlay_kind,
    row.finance && row.finance.outlay_text,
    row.finance && row.finance.product_line && row.finance.product_line.name,
    row.finance && row.finance.product_line && (row.finance.product_line.paragraphs || []).join("\n"),
    row.finance && row.finance.product_line && (row.finance.product_line.web || []).map((w) => w.display).join("\n"),
  ].filter(Boolean).join("\n");
}

function snippet(row, q) {
  const text = haystack(row).replace(/\s+/g, " ");
  if (!q) return (row.background || row.event || "").slice(0, 120);
  const lower = text.toLowerCase();
  const needle = q.toLowerCase();
  const at = lower.indexOf(needle);
  if (at < 0) return (row.background || "").slice(0, 120);
  const start = Math.max(0, at - 24);
  const chunk = text.slice(start, at + q.length + 48);
  return (start > 0 ? "…" : "") + chunk + "…";
}

function searchEvents(events, q, issuer) {
  const query = (q || "").trim().toLowerCase();
  if (!query) return [];
  return events
    .map((row, i) => ({ ...row, i, issuer }))
    .filter((row) => haystack(row).toLowerCase().includes(query))
    .map((row) => ({ ...row, snippet: snippet(row, q.trim()) }));
}

function kindClass(kind) {
  if (kind === "年报股东信官方中文") return "ok";
  if (
    kind === "10-K MD&A原文翻译" ||
    kind === "当年无可用电子原文" ||
    kind === "未找到原文"
  ) {
    return "warn";
  }
  return "";
}

function reportHaystack(y) {
  return [
    `FY${y.fy}`,
    String(y.fy),
    y.period,
    y.ceo,
    y.chair,
    y.letter_author,
    y.letter_role,
    y.source_kind,
    y.source,
    y.greeting,
    y.unavailable,
    ...(y.paragraphs || []),
    y.financials && y.financials.revenue_text,
  ]
    .filter(Boolean)
    .join("\n");
}

function reportSnippet(y, q) {
  const text = reportHaystack(y).replace(/\s+/g, " ");
  if (!q) {
    const paras = (y.paragraphs || []).filter((p) => p.length > 18);
    return (paras[0] || y.unavailable || "").slice(0, 120);
  }
  const lower = text.toLowerCase();
  const needle = q.toLowerCase();
  const at = lower.indexOf(needle);
  if (at < 0) return (y.paragraphs && y.paragraphs[0] || "").slice(0, 120);
  const start = Math.max(0, at - 24);
  const chunk = text.slice(start, at + q.length + 48);
  return (start > 0 ? "…" : "") + chunk + "…";
}

function searchReports(years, q, issuer) {
  const query = (q || "").trim().toLowerCase();
  if (!query) return [];
  return (years || [])
    .filter((y) => reportHaystack(y).toLowerCase().includes(query))
    .map((y) => ({ ...y, issuer, snippet: reportSnippet(y, q.trim()) }));
}
