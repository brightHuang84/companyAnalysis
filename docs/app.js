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

const params = new URLSearchParams(location.search);
const state = {
  decade: "all",
  type: "全部类型",
  grade: "全部判定",
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
  const grades = {};
  events.forEach((e) => { grades[e.grade] = (grades[e.grade] || 0) + 1; });
  document.getElementById("stats").innerHTML = [
    ["已上市", "40 年"],
    ["物质事件", String(events.length)],
    ["兑现", String(grades["兑现"] || 0)],
    ["未兑现", String(grades["未兑现"] || 0)],
    ["部分 / 强制修正", String((grades["部分兑现"] || 0) + (grades["被强制修正"] || 0))],
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
    btn.innerHTML = `<div class="meta"><span>${esc(row.date)}</span><span>${esc(row.type)}</span><span>${esc(row.grade)}</span></div><div class="title">${esc(row.event)}</div>`;
    btn.onclick = () => { state.sel = row.i; render(); };
    li.appendChild(btn);
    ol.appendChild(li);
  });
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
    <p class="note">新闻对照：${esc(row.news)} · 事实核验：${esc(row.verify)}</p>
  `;
}

function render() {
  pills(document.getElementById("decades"), DECADES, state.decade, "decade");
  pills(document.getElementById("types"), TYPES, state.type, "type");
  pills(document.getElementById("grades"), GRADES, state.grade, "grade");
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
