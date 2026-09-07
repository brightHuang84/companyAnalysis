const LINE_FILTERS = [
  { id: "all", label: "全部产品" },
  { id: "office", label: "Office / 365" },
  { id: "cloud", label: "Azure / 云" },
  { id: "windows", label: "Windows" },
  { id: "gaming", label: "Xbox" },
  { id: "search", label: "搜索" },
];

const GRAIN = {
  "10k": "10-K",
  earnings: "业绩会",
  company: "公司口径",
  third_party: "第三方",
  derived: "倒推",
  estimate: "估算",
  list_price: "标价",
  none: "未披露",
};

const state = { line: "all", data: null };

function grainBadge(grain) {
  return `<span class="badge">${esc(GRAIN[grain] || grain || "—")}</span>`;
}

function yi(usdM) {
  if (usdM == null) return "—";
  const n = Number(usdM) / 100;
  return n >= 10 ? n.toFixed(0) : n.toFixed(1);
}

function table(headers, rows) {
  if (!rows.length) {
    return `<thead><tr>${headers.map((h) => `<th>${esc(h)}</th>`).join("")}</tr></thead><tbody><tr><td colspan="${headers.length}">当前产品线没有这一列数字，或年报没给。</td></tr></tbody>`;
  }
  return `<thead><tr>${headers.map((h) => `<th>${esc(h)}</th>`).join("")}</tr></thead><tbody>${rows
    .map((row) => `<tr>${row.map((cell) => `<td>${cell}</td>`).join("")}</tr>`)
    .join("")}</tbody>`;
}

function matchLine(row) {
  return state.line === "all" || row.line === state.line;
}

function renderHero(data) {
  const op = data.operating || {};
  const copilot = [...(op.seats || [])].reverse().find((s) => /Copilot 付费席位/.test(s.name));
  const seats = [...(op.seats || [])].reverse().find((s) => s.name.includes("商业付费席位") && s.grain !== "derived");
  const azure = (data.azure || {}).years || [];
  const lastAzure = azure[azure.length - 1];
  const share = [...(op.share || [])].reverse().find((s) => s.line === "cloud");
  document.getElementById("hero").innerHTML = [
    ["FY26 Azure", lastAzure ? `${yi(lastAzure.revenue)} 亿美元` : "—"],
    ["M365 商业席位", seats ? `${seats.value}${seats.unit}` : "—"],
    ["Copilot 付费席位", copilot ? `${copilot.value}${copilot.unit}` : "—"],
    ["Azure 云份额", share ? `${share.value}%` : "—"],
  ]
    .map(([k, v]) => `<div class="stat"><b>${esc(v)}</b><span>${esc(k)}</span></div>`)
    .join("");
}

function renderShare(op) {
  document.getElementById("share-note").textContent =
    "年报不印市场份额表。Windows / Bing 用 Statcounter 流量份额，Azure 用 Synergy 云基础设施份额。";
  const rows = (op.share || []).filter(matchLine).map((s) => [
    `FY${s.fy}`,
    esc(s.name),
    `<b>${esc(String(s.value))}${esc(s.unit || "")}</b>`,
    grainBadge(s.grain),
    esc(s.source || ""),
  ]);
  document.getElementById("share-table").innerHTML = table(
    ["财年", "指标", "份额", "来源", "出处"],
    rows
  );
}

function renderSeats(op) {
  document.getElementById("seat-note").textContent =
    "10-K KPI 给的是席位同比增速。绝对席位只在业绩会报过几次；消费订阅数 FY2026 Q1 起从 KPI 拿掉。";
  const growthRows = (op.seat_growth || []).map((s) => [
    `FY${s.fy}`,
    s.m365_comm_pct == null ? "—" : `${s.m365_comm_pct}%`,
    s.m365_cons_pct == null ? "年报未给" : `${s.m365_cons_pct}%`,
    grainBadge(s.grain),
    esc(s.source || ""),
  ]);
  document.getElementById("seat-growth-table").innerHTML = table(
    ["财年", "M365 商业席位同比", "消费订阅同比", "来源", "出处"],
    growthRows
  );
  const seatRows = (op.seats || []).filter(matchLine).map((s) => [
    `FY${s.fy}`,
    esc(s.as_of || ""),
    esc(s.name),
    `<b>${esc(String(s.value))} ${esc(s.unit || "")}</b>`,
    grainBadge(s.grain),
    esc(s.source || ""),
  ]);
  document.getElementById("seat-table").innerHTML = table(
    ["财年", "时点", "指标", "数量", "来源", "出处"],
    seatRows
  );
  const arpuRows = (op.implied_arpu || []).filter(matchLine).map((s) => [
    `FY${s.fy}`,
    `约 ${s.seats_m} 百万席`,
    `${yi(s.revenue_usd_m)} 亿美元营收`,
    `<b>$${s.usd_per_month}/月</b>`,
    grainBadge(s.grain),
    esc(s.note || ""),
  ]);
  document.getElementById("arpu-table").innerHTML = table(
    ["财年", "席位口径", "对应营收", "混合 ARPU", "来源", "说明"],
    arpuRows
  );
}

function renderPrices(op) {
  document.getElementById("price-note").textContent =
    "10-K 不列美元单价，只说「平均每用户收入上升」。下面是公开价目表标价，企业成交价通常更低。";
  const rows = (op.prices || []).filter(matchLine).map((p) => [
    `FY${p.fy}`,
    esc(p.sku),
    p.price_usd_mo == null ? "无单一单价" : `<b>$${p.price_usd_mo}/用户/月</b>`,
    grainBadge(p.grain),
    esc(p.source || p.note || ""),
  ]);
  document.getElementById("price-table").innerHTML = table(
    ["财年", "SKU", "标价", "来源", "出处"],
    rows
  );
}

function barRow(label, value, max, tone) {
  const pct = max ? Math.max(2, Math.round((Number(value) / max) * 100)) : 0;
  return `<div class="bar-row"><span class="bar-label">${esc(label)}</span><span class="bar-track"><i class="${tone || ""}" style="width:${pct}%"></i></span><span class="bar-val">${esc(yi(value))}</span></div>`;
}

function renderRevenue(data) {
  const years = (data.offerings || {}).years || [];
  const want = new Set(["server_cloud", "azure", "m365_comm", "office", "xbox", "gaming", "windows", "windows_devices", "linkedin", "search"]);
  const latest = years[years.length - 1];
  if (!latest) return;
  const items = latest.items.filter((i) => want.has(i.id) && (state.line === "all" || i.line === state.line));
  const max = Math.max(...items.map((i) => i.revenue), 1);
  document.getElementById("rev-chart").innerHTML =
    `<p class="hint">FY${latest.fy} 产品营收</p>` +
    items.map((i) => barRow(i.name, i.revenue, max, i.nested ? "nested" : "")).join("");

  const ids = [];
  years.forEach((y) => y.items.forEach((i) => {
    if (want.has(i.id) && (state.line === "all" || i.line === state.line) && !ids.includes(i.id)) ids.push(i.id);
  }));
  const names = {};
  years.forEach((y) => y.items.forEach((i) => { names[i.id] = i.name; }));
  const headers = ["产品", ...years.map((y) => String(y.fy))];
  const rows = ids.map((id) => {
    const cells = [esc(names[id])];
    years.forEach((y) => {
      const hit = y.items.find((i) => i.id === id);
      cells.push(hit ? yi(hit.revenue) : "—");
    });
    return cells;
  });
  document.getElementById("rev-table").innerHTML = table(headers, rows);
}

function renderOi(data) {
  const era2 = [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026];
  const office = Object.fromEntries((data.lines.office.years || []).map((r) => [r.fy, r.operating_income]));
  const cloud = Object.fromEntries((data.lines.cloud.years || []).map((r) => [r.fy, r.operating_income]));
  const mpc = Object.fromEntries((data.parents_now.more_personal_computing.years || []).map((r) => [r.fy, r.operating_income]));
  const max = Math.max(...era2.map((y) => (office[y] || 0) + (cloud[y] || 0) + (mpc[y] || 0)), 1);
  document.getElementById("oi-chart").innerHTML = era2.map((y) => {
    const a = office[y] || 0;
    const b = cloud[y] || 0;
    const c = mpc[y] || 0;
    const tot = a + b + c;
    return `<div class="stack-row"><span class="bar-label">FY${y}</span><span class="bar-track stack">
      <i class="p1" style="width:${(a / max) * 100}%"></i>
      <i class="p2" style="width:${(b / max) * 100}%"></i>
      <i class="p3" style="width:${(c / max) * 100}%"></i>
    </span><span class="bar-val">${yi(tot)}</span></div>`;
  }).join("") + `<p class="hint">棕=生产力，深=智能云，浅=更多个人计算。单位：亿美元营业利润。</p>`;
}

function render() {
  const data = state.data;
  const op = data.operating || {};
  pills(document.getElementById("lines"), LINE_FILTERS, state.line, "line");
  renderHero(data);
  renderShare(op);
  renderSeats(op);
  renderPrices(op);
  renderRevenue(data);
  renderOi(data);
  document.getElementById("foot").textContent = data.operating && data.operating.note ? data.operating.note : data.note || "";
}

function pills(el, items, current, key) {
  el.innerHTML = "";
  items.forEach((item) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = item.label;
    btn.className = item.id === current ? "on" : "";
    btn.onclick = () => {
      state[key] = item.id;
      render();
    };
    el.appendChild(btn);
  });
}

fetch("./product_lines.json")
  .then((r) => r.json())
  .then((data) => {
    state.data = data;
    render();
  })
  .catch(() => {
    document.getElementById("foot").textContent = "读不到 product_lines.json。请用本地预览命令打开。";
  });
