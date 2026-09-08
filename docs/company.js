const DECADES = [
  { id: "all", label: "全部年份" },
  { id: "1980", label: "1986–89" },
  { id: "1990", label: "1990s" },
  { id: "2000", label: "2000s" },
  { id: "2010", label: "2010s" },
  { id: "2020", label: "2020s" },
];

const MIX_IDS = new Set([
  "server_cloud", "azure", "m365_comm", "office", "xbox", "gaming",
  "windows", "windows_devices", "linkedin", "search",
]);

const state = { decade: "all", fy: null, data: null, products: null, pushUrl: false };

function decadeOfFy(fy) {
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
  return years.filter((y) => decadeOfFy(y.fy) === state.decade);
}

function yi(usdM) {
  if (usdM == null) return "—";
  const n = Number(usdM) / 100;
  return n >= 10 ? n.toFixed(0) : n.toFixed(1);
}

function excerpt(y, n = 168) {
  if (y.unavailable) return y.unavailable;
  const paras = (y.paragraphs || []).filter((p) => p.length > 18 || /[。；！？]$/.test(p));
  const text = paras.slice(0, 2).join("");
  if (!text) return "当年原文待核。";
  return text.length > n ? `${text.slice(0, n).replace(/[，、；：.\s]+$/, "")}…` : text;
}

function yearHref(fy) {
  const params = new URLSearchParams();
  params.set("fy", String(fy));
  if (state.decade !== "all") params.set("d", state.decade);
  return `?${params.toString()}`;
}

function indexHref() {
  if (state.decade === "all") return "company.html";
  return `?d=${encodeURIComponent(state.decade)}`;
}

function sparkHtml(years, selectedFy) {
  const max = Math.max(...years.map((y) => (y.financials && y.financials.revenue_usd_m) || 0), 1);
  return `<div class="spark">${years.map((y) => {
    const val = (y.financials && y.financials.revenue_usd_m) || 0;
    const pct = Math.max(3, Math.round((val / max) * 100));
    const on = y.fy === selectedFy ? "on" : "";
    return `<a class="${on}" href="${esc(yearHref(y.fy))}" data-fy="${y.fy}" title="FY${y.fy} · ${esc(yi(val))} 亿美元"><i style="height:${pct}%"></i></a>`;
  }).join("")}</div>`;
}

function renderHero(data) {
  const years = data.years || [];
  const last = years[years.length - 1];
  const first = years[0];
  const rev = last && last.financials ? last.financials.revenue_text : "—";
  document.getElementById("hero").innerHTML = [
    ["覆盖财年", first && last ? `FY${first.fy}–${last.fy}` : "—"],
    ["年报译文", `${years.length} 份`],
    ["最新营收", rev || "—"],
    ["现任", last ? last.ceo : "—"],
  ]
    .map(([k, v]) => `<div class="stat"><b>${esc(v)}</b><span>${esc(k)}</span></div>`)
    .join("");
}

function renderOiChart() {
  const el = document.getElementById("oi-chart");
  const products = state.products;
  if (!products || !products.lines || !products.parents_now) {
    el.innerHTML = `<p class="note">分部利润图暂缺。</p>`;
    return;
  }
  const era2 = [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026];
  const office = Object.fromEntries((products.lines.office.years || []).map((r) => [r.fy, r.operating_income]));
  const cloud = Object.fromEntries((products.lines.cloud.years || []).map((r) => [r.fy, r.operating_income]));
  const mpc = Object.fromEntries((products.parents_now.more_personal_computing.years || []).map((r) => [r.fy, r.operating_income]));
  const max = Math.max(...era2.map((y) => (office[y] || 0) + (cloud[y] || 0) + (mpc[y] || 0)), 1);
  el.innerHTML = era2.map((fy) => {
    const a = office[fy] || 0;
    const b = cloud[fy] || 0;
    const c = mpc[fy] || 0;
    const tot = a + b + c;
    return `<a class="stack-row" href="${esc(yearHref(fy))}" data-fy="${fy}">
      <span class="bar-label">FY${fy}</span>
      <span class="bar-track stack">
        <i class="p1" style="width:${(a / max) * 100}%"></i>
        <i class="p2" style="width:${(b / max) * 100}%"></i>
        <i class="p3" style="width:${(c / max) * 100}%"></i>
      </span>
      <span class="bar-val">${esc(yi(tot))}</span>
    </a>`;
  }).join("");
}

function renderYearCards(rows) {
  document.getElementById("count").textContent = `共 ${rows.length} 个财年`;
  const html = [...rows].reverse().map((y) => {
    const yoy = y.financials && y.financials.revenue_yoy_pct;
    const yoyText = yoy == null ? "" : ` · ${yoy > 0 ? "+" : ""}${yoy}%`;
    const rev = (y.financials && y.financials.revenue_text) || "";
    return `<a class="year-card" href="${esc(yearHref(y.fy))}" data-fy="${y.fy}">
      <div class="meta">
        <span>FY${y.fy}</span>
        <span class="badge ${kindClass(y.source_kind)}">${esc(y.source_kind)}</span>
      </div>
      <div class="title">${esc(y.letter_author || y.ceo)} · ${esc(rev)}${esc(yoyText)}</div>
      <p class="excerpt">${esc(excerpt(y))}</p>
    </a>`;
  }).join("");
  document.getElementById("years").innerHTML = html || `<p class="empty">这一年代没有报告。</p>`;
}

function letterBody(y) {
  if (y.unavailable) {
    return `<p class="callout">${esc(y.unavailable)}</p>`;
  }
  const parts = [];
  if (y.greeting) parts.push(`<p class="letter-greeting">${esc(y.greeting)}</p>`);
  (y.paragraphs || []).forEach((para) => {
    const short = para.length <= 18 && !/[。；！？]$/.test(para);
    parts.push(short ? `<h4>${esc(para)}</h4>` : `<p>${esc(para)}</p>`);
  });
  return `<div class="letter">${parts.join("")}</div>`;
}

function finCells(fin) {
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
  return cells
    .map(([k, v]) => `<div class="stat"><b>${esc(v)}</b><span>${esc(k)}</span></div>`)
    .join("");
}

function mixHtml(fy) {
  const years = (state.products && state.products.offerings && state.products.offerings.years) || [];
  const hit = years.find((row) => row.fy === fy);
  if (!hit) return "";
  const items = hit.items.filter((i) => MIX_IDS.has(i.id));
  if (!items.length) return "";
  const max = Math.max(...items.map((i) => i.revenue), 1);
  const rows = items.map((i) => {
    const pct = Math.max(2, Math.round((Number(i.revenue) / max) * 100));
    return `<div class="bar-row"><span class="bar-label">${esc(i.name)}</span><span class="bar-track"><i class="${i.nested ? "nested" : ""}" style="width:${pct}%"></i></span><span class="bar-val">${esc(yi(i.revenue))}</span></div>`;
  }).join("");
  return `<h2 class="section-title">FY${fy} 产品营收</h2><p class="hint">10-K 产品表。单位：亿美元。Azure 单独行不另加总。</p>${rows}`;
}

function renderIndex() {
  document.body.classList.remove("reading");
  document.getElementById("index-view").hidden = false;
  document.getElementById("report-view").hidden = true;
  document.getElementById("page-title").textContent = "微软年报，一年一份";
  document.getElementById("page-lede").hidden = false;
  document.getElementById("hero").hidden = false;
  document.title = "微软年报译文";
  pills(document.getElementById("decades"), DECADES, state.decade, "decade");
  document.getElementById("rev-spark").innerHTML = sparkHtml(state.data.years || [], null);
  renderOiChart();
  renderYearCards(filtered());
}

function renderReport() {
  const years = state.data.years || [];
  const y = years.find((row) => row.fy === state.fy) || years[years.length - 1];
  if (!y) {
    state.fy = null;
    renderIndex();
    return;
  }
  state.fy = y.fy;
  document.body.classList.add("reading");
  document.getElementById("index-view").hidden = true;
  document.getElementById("report-view").hidden = false;
  document.getElementById("page-lede").hidden = true;
  document.getElementById("hero").hidden = true;
  document.getElementById("page-title").textContent = `FY${y.fy} 年报译文`;
  document.title = `微软 FY${y.fy} 年报译文`;

  const idx = years.findIndex((row) => row.fy === y.fy);
  const prev = idx > 0 ? years[idx - 1] : null;
  const next = idx >= 0 && idx < years.length - 1 ? years[idx + 1] : null;
  const signed = y.letter_date ? ` · ${esc(y.letter_date)}` : "";
  const sourceLink = y.source_url
    ? ` · <a href="${esc(y.source_url)}" target="_blank" rel="noopener">打开原文</a>`
    : "";

  document.getElementById("report-nav").innerHTML = [
    `<a href="${esc(indexHref())}" data-back="1">全部财年</a>`,
    prev ? `<a href="${esc(yearHref(prev.fy))}" data-fy="${prev.fy}">FY${prev.fy}</a>` : "",
    next ? `<a href="${esc(yearHref(next.fy))}" data-fy="${next.fy}">FY${next.fy}</a>` : "",
  ].filter(Boolean).join(" · ");

  document.getElementById("report-fin").innerHTML = finCells(y.financials);
  document.getElementById("report-spark").innerHTML = sparkHtml(years, y.fy);
  document.getElementById("report-mix").innerHTML = mixHtml(y.fy);
  document.getElementById("report").innerHTML = `
    <p class="kicker">FY${y.fy} · ${esc(y.period)}</p>
    <h2>${esc(y.letter_author)}${y.letter_role ? " · " + esc(y.letter_role) : ""}</h2>
    <p>
      <span class="badge ${kindClass(y.source_kind)}">${esc(y.source_kind)}</span>
      CEO ${esc(y.ceo)} · 董事长 ${esc(y.chair)}${signed}
    </p>
    <h3>完整译文</h3>
    ${letterBody(y)}
    <p class="note">来源：${esc(y.source)}${sourceLink}</p>
  `;
}

function syncUrl() {
  const params = new URLSearchParams();
  if (state.fy) params.set("fy", String(state.fy));
  if (state.decade !== "all") params.set("d", state.decade);
  const qs = params.toString();
  const url = qs ? `?${qs}` : location.pathname;
  if (state.pushUrl) history.pushState({ fy: state.fy, d: state.decade }, "", url);
  else history.replaceState({ fy: state.fy, d: state.decade }, "", url);
  state.pushUrl = false;
}

function render(fromPop) {
  if (state.fy) renderReport();
  else renderIndex();
  if (!fromPop) syncUrl();
}

function openFy(fy) {
  state.pushUrl = true;
  state.fy = fy;
  render();
}

document.getElementById("decades").addEventListener("click", (e) => {
  const btn = e.target.closest("button[data-id]");
  if (!btn) return;
  state.decade = btn.dataset.id;
  render();
});

document.addEventListener("click", (e) => {
  if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
  const back = e.target.closest("a[data-back]");
  if (back) {
    e.preventDefault();
    state.pushUrl = true;
    state.fy = null;
    render();
    window.scrollTo(0, 0);
    return;
  }
  const a = e.target.closest("a[data-fy]");
  if (!a) return;
  e.preventDefault();
  openFy(Number(a.dataset.fy));
  window.scrollTo(0, 0);
});

window.addEventListener("popstate", () => {
  const params = new URLSearchParams(location.search);
  state.decade = params.get("d") || "all";
  state.fy = params.get("fy") ? Number(params.get("fy")) : null;
  render(true);
});

Promise.all([
  fetch("./board_reports.json").then((r) => r.json()),
  fetch("./product_lines.json").then((r) => r.json()).catch(() => null),
]).then(([data, products]) => {
  state.data = data;
  state.products = products;
  const params = new URLSearchParams(location.search);
  if (params.get("d")) state.decade = params.get("d");
  if (params.get("fy")) state.fy = Number(params.get("fy"));
  renderHero(data);
  render();
}).catch(() => {
  document.getElementById("years").innerHTML =
    `<p class="empty">读不到年报译文。请用本地预览命令打开，不要直接双击 HTML。</p>`;
});
