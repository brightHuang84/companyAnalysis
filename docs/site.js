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
  ].join("\n");
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
