const DECADES = [
  { id: "all", label: "全部年代" },
  { id: "1986", label: "1986–89" },
  { id: "1990", label: "1990–99" },
  { id: "2000", label: "2000–09" },
  { id: "2010", label: "2010–19" },
  { id: "2020", label: "2020–26" },
];

const TYPES = ["全部类型", "产品", "监管", "并购", "员工", "安全", "其他"];
const OTHER = new Set(["联盟", "管理层", "公司", "资本", "项目", "产品反馈", "诉讼", "竞争"]);
const GRADES = ["全部判定", "兑现", "部分兑现", "未兑现", "被强制修正", "未核实"];
const RETURNS = ["全部回报", "高回报", "正回报", "部分回收", "减值收场", "战略未兑现", "监管成本", "中性", "未核实"];

const params = new URLSearchParams(location.search);
const state = {
  decade: "all",
  type: "全部类型",
  grade: "全部判定",
  ret: "全部回报",
  q: params.get("q") || "",
  sel: Number.parseInt(params.get("e") || "0", 10) || 0,
  data: null,
};

function matchesType(row, type) {
  if (type === "全部类型") return true;
  if (type === "其他") return OTHER.has(row.type);
  return row.type === type;
}

function filtered() {
  const q = state.q.trim().toLowerCase();
  return state.data.events
    .map((row, i) => ({ ...row, i, decade: decadeOf(row.date) }))
    .filter((row) => {
      if (state.decade !== "all" && row.decade !== state.decade) return false;
      if (!matchesType(row, state.type)) return false;
      if (state.grade !== "全部判定" && row.grade !== state.grade) return false;
      if (state.ret !== "全部回报" && (row.finance || {}).return_grade !== state.ret) return false;
      if (!q) return true;
      return haystack(row).toLowerCase().includes(q);
    });
}

function syncUrl() {
  const next = new URLSearchParams();
  if (state.q.trim()) next.set("q", state.q.trim());
  if (state.sel) next.set("e", String(state.sel));
  const qs = next.toString();
  history.replaceState(null, "", qs ? `msft.html?${qs}` : "msft.html");
}

function pills(el, items, current, key) {
  el.innerHTML = "";
  items.forEach((item) => {
    const id = typeof item === "string" ? item : item.id;
    const label = typeof item === "string" ? item : item.label;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = label;
    btn.className = id === current ? "on" : "";
    btn.onclick = () => {
      state[key] = id;
      render();
    };
    el.appendChild(btn);
  });
}

function renderStats() {
  const events = state.data.events;
  const returns = {};
  events.forEach((e) => {
    const g = (e.finance || {}).return_grade;
    if (g) returns[g] = (returns[g] || 0) + 1;
  });
  document.getElementById("stats").innerHTML = [
    ["已上市", "40 年"],
    ["物质事件", String(events.length)],
    ["高回报 / 正回报", String((returns["高回报"] || 0) + (returns["正回报"] || 0))],
    ["减值 / 未兑现", String((returns["减值收场"] || 0) + (returns["战略未兑现"] || 0))],
    ["FY26 营业利润率", "46.8%"],
  ].map(([k, v]) => `<div class="stat"><b>${v}</b><span>${k}</span></div>`).join("");
}

function renderList(rows) {
  document.getElementById("count").textContent = state.q.trim()
    ? `搜索「${state.q.trim()}」· ${rows.length} 条`
    : `当前 ${rows.length} 条`;
  const ol = document.getElementById("list");
  ol.innerHTML = "";
  rows.forEach((row) => {
    const li = document.createElement("li");
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = row.i === state.sel ? "active" : "";
    btn.innerHTML = `<div class="meta"><span>${esc(row.date)}</span><span>${esc(row.type)}</span><span>${esc((row.finance || {}).return_grade || row.grade)}</span></div><div class="title">${esc(row.event)}</div>`;
    btn.onclick = () => { state.sel = row.i; render(); };
    li.appendChild(btn);
    ol.appendChild(li);
  });
}

function pct(value) {
  return value == null ? "—" : `${value}%`;
}

function usdM(value) {
  if (value == null) return "—";
  const n = Number(value);
  if (Math.abs(n) >= 100) {
    const yi = n / 100;
    const text = yi >= 10 ? yi.toFixed(0) : yi.toFixed(1);
    return `${text} 亿美元`;
  }
  return `${Math.round(n)} 百万美元`;
}

function financeBlock(fin) {
  if (!fin) return "";
  const co = fin.company || {};
  const pl = fin.product_line || {};
  const paras = (pl.paragraphs || []).map((p) => `<p>${esc(p)}</p>`).join("");
  const at = pl.at_event || null;
  const latest = pl.latest || null;
  const lineStats = [];
  if (at) {
    lineStats.push(`<div class="stat"><b>${esc(usdM(at.operating_income_usd_m))}</b><span>FY${esc(at.fy)} ${esc(at.label)} 营业利润</span></div>`);
    lineStats.push(`<div class="stat"><b>${esc(pct(at.op_margin_pct))}</b><span>该分部当年利润率</span></div>`);
  }
  if (latest && (!at || at.fy !== latest.fy || at.label !== latest.label)) {
    lineStats.push(`<div class="stat"><b>${esc(usdM(latest.operating_income_usd_m))}</b><span>FY${esc(latest.fy)} ${esc(latest.label)} 营业利润</span></div>`);
    lineStats.push(`<div class="stat"><b>${esc(pct(latest.op_margin_pct))}</b><span>该分部最新利润率</span></div>`);
  }
  (pl.revenue_only || []).forEach((item) => {
    lineStats.push(`<div class="stat"><b>${esc(usdM(item.revenue_usd_m))}</b><span>${esc(item.name)} 营收（无利润）</span></div>`);
  });
  return `
    <h3>这条决策动了哪笔钱</h3>
    <p><b>${esc(fin.event_cash || fin.outlay_kind)}</b></p>
    <p>${esc(fin.outlay_text || "")}</p>
    <h3>和当年年报是什么关系</h3>
    <p>${esc(fin.books_role || "")}</p>
    <h3>这条产品线带给公司多少利润 · ${esc(pl.name || "")}</h3>
    ${paras}
    ${lineStats.length ? `<div class="fin">${lineStats.join("")}</div>` : ""}
    <h3>事后回收 · ${esc(fin.return_grade)}</h3>
    <p>${esc(fin.return_summary)}</p>
    <p class="note">下面不是这条产品的利润表，是微软全公司 FY${esc(fin.fy)} 年报，用来对照当时公司有多大。</p>
    <div class="fin">
      <div class="stat"><b>FY${esc(fin.fy)}</b><span>全公司财年</span></div>
      <div class="stat"><b>${esc(usdM(co.revenue_usd_m))}</b><span>全公司营收</span></div>
      <div class="stat"><b>${esc(usdM(co.rd_usd_m))}</b><span>全公司研发</span></div>
      <div class="stat"><b>${esc(pct(co.rd_pct))}</b><span>研发 / 营收</span></div>
      <div class="stat"><b>${esc(pct(co.gross_margin_pct))}</b><span>全公司毛利率</span></div>
      <div class="stat"><b>${esc(pct(co.op_margin_pct))}</b><span>全公司营业利润率</span></div>
      <div class="stat"><b>${esc(pct(co.net_margin_pct))}</b><span>全公司净利率</span></div>
    </div>
  `;
}

function ul(items) {
  if (!items || !items.length) return "";
  return "<ul>" + items.map((x) => `<li>${esc(x)}</li>`).join("") + "</ul>";
}

function renderDetail(rows) {
  const el = document.getElementById("detail");
  const row = state.data.events[state.sel];
  const visible = rows.some((r) => r.i === state.sel);
  if (!row || !visible) {
    if (rows[0]) {
      state.sel = rows[0].i;
      return render();
    }
    el.innerHTML = `<p class="empty">没有符合筛选的事件。清空搜索或换一个年代。</p>`;
    return;
  }
  el.innerHTML = `
    <p>
      <span class="badge ${gradeClass(row.grade)}">${esc(row.grade)}</span>
      <span class="badge ${returnClass((row.finance || {}).return_grade)}">${esc((row.finance || {}).return_grade || "")}</span>
      <span class="badge">${esc(row.type)}</span>
      <span class="badge">${esc(row.date)}</span>
    </p>
    <h2>${esc(row.event)}</h2>
    <h3>当时背景</h3>
    <p>${esc(row.background)}</p>
    <h3>决策原因</h3>
    <p>${esc(row.why)}</p>
    <p class="note">${esc(row.why_note || "")}</p>
    <h3>决策目录 · 当时可走的路</h3>
    ${ul(row.options)}
    <h3>决策目录 · 实际拍板</h3>
    ${ul(row.decisions)}
    <h3>近端效果</h3>
    <p>${esc(row.effect_near)}</p>
    <h3>最终效果</h3>
    <p>${esc(row.effect_far)}</p>
    ${financeBlock(row.finance)}
    <p class="note">新闻对照：${esc(row.news)} · 事实核验：${esc(row.verify)}</p>
  `;
}

function render() {
  pills(document.getElementById("decades"), DECADES, state.decade, "decade");
  pills(document.getElementById("types"), TYPES, state.type, "type");
  pills(document.getElementById("grades"), GRADES, state.grade, "grade");
  pills(document.getElementById("returns"), RETURNS, state.ret, "ret");
  const rows = filtered();
  renderList(rows);
  renderDetail(rows);
  syncUrl();
}

const qEl = document.getElementById("q");
qEl.value = state.q;
document.getElementById("search-form").addEventListener("submit", (e) => {
  e.preventDefault();
  state.q = qEl.value;
  render();
});
qEl.addEventListener("input", (e) => {
  state.q = e.target.value;
  render();
});

fetch("./msft.json")
  .then((r) => r.json())
  .then((data) => {
    state.data = data;
    if (state.sel < 0 || state.sel >= data.events.length) state.sel = 0;
    renderStats();
    render();
  })
  .catch(() => {
    document.getElementById("detail").innerHTML =
      "<p class=\"empty\">读不到 msft.json。请用本地预览命令打开，不要直接双击 HTML。</p>";
  });
