const DECADES = [
  { id: "all", label: "全部年份" },
  { id: "1980", label: "1986–89" },
  { id: "1990", label: "1990s" },
  { id: "2000", label: "2000s" },
  { id: "2010", label: "2010s" },
  { id: "2020", label: "2020s" },
];

const KIND = {
  股东信综述: "ok",
  "年报+事件综合": "",
  "年报+招股+事件综合": "",
  "业绩稿+10-K MD&A": "warn",
};

const state = { decade: "all", fy: null, data: null };

function decadeOf(fy) {
  if (fy < 1990) return "1980";
  if (fy < 2000) return "1990";
  if (fy < 2010) return "2000";
  if (fy < 2020) return "2010";
  return "2020";
}

function pills(el, items, current, key) {
  el.innerHTML = items
    .map(
      (item) =>
        `<button type="button" class="${item.id === current ? "on" : ""}" data-key="${key}" data-id="${esc(item.id)}">${esc(item.label)}</button>`
    )
    .join("");
}

function filtered() {
  const years = state.data.years || [];
  if (state.decade === "all") return years;
  return years.filter((y) => decadeOf(y.fy) === state.decade);
}

function renderHero(data) {
  const years = data.years || [];
  const last = years[years.length - 1];
  const first = years[0];
  const moves = (data.governance || []).filter((g) => g.fy);
  document.getElementById("hero").innerHTML = [
    ["覆盖财年", first && last ? `FY${first.fy}–${last.fy}` : "—"],
    ["年度报告", `${years.length} 份`],
    ["执行节点", `${moves.length} 条`],
    ["现任", last ? (last.ceo === last.chair ? `${last.ceo} 兼董事长` : last.ceo) : "—"],
  ]
    .map(([k, v]) => `<div class="stat"><b>${esc(v)}</b><span>${esc(k)}</span></div>`)
    .join("");
}

function renderTimeline(data) {
  const el = document.getElementById("timeline");
  el.innerHTML = (data.governance || [])
    .map((row) => {
      const fy = row.fy ? `<span>FY${row.fy}</span>` : `<span>上市前</span>`;
      return `<li>
        <div class="meta">${esc(row.date)} ${fy}</div>
        <div class="title">${esc(row.title)}</div>
        <p class="note">${esc(row.who)}</p>
        <p>${esc(row.detail)}</p>
      </li>`;
    })
    .join("");
}

function renderList(rows) {
  document.getElementById("count").textContent = `共 ${rows.length} 个财年`;
  const html = rows
    .map((y) => {
      const on = y.fy === state.fy ? "active" : "";
      const yoy = y.financials && y.financials.revenue_yoy_pct;
      const yoyText = yoy == null ? "" : ` · ${yoy > 0 ? "+" : ""}${yoy}%`;
      return `<li>
        <button type="button" class="${on}" data-fy="${y.fy}">
          <div class="meta"><span>FY${y.fy}</span><span>${esc(y.source_kind)}</span></div>
          <div class="title">${esc(y.ceo)} · ${esc((y.financials && y.financials.revenue_text) || "")}${esc(yoyText)}</div>
        </button>
      </li>`;
    })
    .join("");
  document.getElementById("list").innerHTML = html || `<li class="empty">这一年代没有报告。</li>`;
}

function ul(items) {
  if (!items || !items.length) return "<p class=\"note\">当年台账没有单独列出的进展条目。</p>";
  return `<ul>${items.map((t) => `<li>${esc(t)}</li>`).join("")}</ul>`;
}

function eventList(items) {
  if (!items || !items.length) return "<p class=\"note\">这一年台账没有单独的物质事件，进展主要来自年报口径。</p>";
  return `<ul class="year-events">${items
    .map(
      (ev) =>
        `<li><span class="meta">${esc(ev.date)} · ${esc(ev.type)}</span> ${esc(ev.event)}</li>`
    )
    .join("")}</ul>`;
}

function boardMoves(items) {
  if (!items || !items.length) return "<p class=\"note\">这一年没有董事长、CEO 或分红政策层面的执行节点。</p>";
  return items
    .map(
      (row) => `<p><b>${esc(row.date)} ${esc(row.title)}</b> — ${esc(row.who)}。${esc(row.detail)}</p>`
    )
    .join("");
}

function finBox(fin) {
  if (!fin) return "";
  const cells = [
    ["营收", fin.revenue_text],
    ["同比", fin.revenue_yoy_pct == null ? "—" : `${fin.revenue_yoy_pct > 0 ? "+" : ""}${fin.revenue_yoy_pct}%`],
    ["营业利润", fin.operating_income_text],
    ["营业利润率", fin.op_margin_pct == null ? "—" : `${fin.op_margin_pct}%`],
    ["净利润", fin.net_income_text],
    ["净利率", fin.net_margin_pct == null ? "—" : `${fin.net_margin_pct}%`],
  ];
  if (fin.capex_usd_m != null) cells.push(["资本开支", (fin.capex_usd_m / 100).toFixed(0) + " 亿美元"]);
  return `<div class="fin">${cells
    .map(([k, v]) => `<div class="stat"><b>${esc(v)}</b><span>${esc(k)}</span></div>`)
    .join("")}</div>`;
}

function renderDetail(rows) {
  const el = document.getElementById("detail");
  const y = rows.find((r) => r.fy === state.fy) || rows[rows.length - 1];
  if (!y) {
    el.innerHTML = `<p class="empty">没有可显示的财年。</p>`;
    return;
  }
  state.fy = y.fy;
  const kindClass = KIND[y.source_kind] || "";
  el.innerHTML = `
    <p class="kicker">FY${y.fy} · ${esc(y.period)}</p>
    <h2>${esc(y.letter_author)}：当年报告</h2>
    <p>
      <span class="badge ${kindClass}">${esc(y.source_kind)}</span>
      CEO ${esc(y.ceo)} · 董事长 ${esc(y.chair)}
    </p>
    ${finBox(y.financials)}
    <h3>当时环境</h3>
    <p>${esc(y.environment)}</p>
    <h3>项目进展</h3>
    ${ul(y.progress)}
    <h3>未来展望</h3>
    <p>${esc(y.outlook)}</p>
    <h3>这一年的董事会执行</h3>
    ${boardMoves(y.board_moves)}
    <h3>这一年台账里的物质事件</h3>
    ${eventList(y.year_events)}
    <p class="note">来源：${esc(y.source)} · <a href="msft.html">打开事件台账</a> · <a href="products.html">产品线数字</a></p>
  `;
}

function syncUrl() {
  const params = new URLSearchParams();
  if (state.fy) params.set("fy", String(state.fy));
  if (state.decade !== "all") params.set("d", state.decade);
  const qs = params.toString();
  history.replaceState(null, "", qs ? `?${qs}` : location.pathname);
}

function render() {
  pills(document.getElementById("decades"), DECADES, state.decade, "decade");
  const rows = filtered();
  if (state.fy && !rows.some((y) => y.fy === state.fy) && rows.length) {
    state.fy = rows[rows.length - 1].fy;
  }
  renderList(rows);
  renderDetail(rows);
  syncUrl();
}

document.getElementById("decades").addEventListener("click", (e) => {
  const btn = e.target.closest("button[data-id]");
  if (!btn) return;
  state.decade = btn.dataset.id;
  render();
});

document.getElementById("list").addEventListener("click", (e) => {
  const btn = e.target.closest("button[data-fy]");
  if (!btn) return;
  state.fy = Number(btn.dataset.fy);
  render();
});

fetch("./board_reports.json")
  .then((r) => r.json())
  .then((data) => {
    state.data = data;
    const params = new URLSearchParams(location.search);
    if (params.get("d")) state.decade = params.get("d");
    if (params.get("fy")) state.fy = Number(params.get("fy"));
    else if (data.years && data.years.length) state.fy = data.years[data.years.length - 1].fy;
    renderHero(data);
    renderTimeline(data);
    render();
  })
  .catch(() => {
    document.getElementById("detail").innerHTML =
      `<p class="empty">读不到董事会报告。请用本地预览命令打开，不要直接双击 HTML。</p>`;
  });
