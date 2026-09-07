const resultsEl = document.getElementById("results");
const wrapEl = document.getElementById("results-wrap");
const titleEl = document.getElementById("results-title");
const hintEl = document.getElementById("search-hint");
const qEl = document.getElementById("q");
const catalogEl = document.getElementById("catalog");

let catalog = { issuers: [] };
let ledgers = [];

function resultUrl(hit) {
  return `${hit.page}?e=${hit.i}&q=${encodeURIComponent(qEl.value.trim())}`;
}

function renderResults(hits, q) {
  const show = q.trim().length > 0;
  wrapEl.hidden = !show;
  if (!show) {
    resultsEl.innerHTML = "";
    return;
  }
  titleEl.textContent = hits.length ? `搜索结果 · ${hits.length} 条` : "搜索结果";
  if (!hits.length) {
    resultsEl.innerHTML = `<li class="empty-row">没有找到「${esc(q)}」。可换 IE、Azure、欧盟、裁员、诺基亚 再试。</li>`;
    return;
  }
  resultsEl.innerHTML = hits.map((hit) => `
    <li>
      <a href="${esc(resultUrl(hit))}">
        <div class="meta">
          <span>${esc(hit.ticker)}</span>
          <span>${esc(hit.date)}</span>
          <span>${esc(hit.type)}</span>
          <span class="badge ${gradeClass(hit.grade)}">${esc(hit.grade)}</span>
        </div>
        <div class="title">${esc(hit.event)}</div>
        <p class="snippet">${esc(hit.snippet)}</p>
      </a>
    </li>
  `).join("");
}

function runSearch() {
  const q = qEl.value;
  const hits = ledgers.flatMap((pack) =>
    searchEvents(pack.events, q, pack.issuer).map((row) => ({
      ...row,
      ticker: pack.ticker,
      page: pack.page,
    }))
  );
  renderResults(hits, q);
}

function renderCatalog() {
  const issuerCards = catalog.issuers.map((co) => `
    <a class="card" href="${esc(co.page)}">
      <p class="kicker">${esc(co.exchange)} · ${esc(co.ticker)}</p>
      <h3>${esc(co.name)}</h3>
      <p>上市 ${esc(co.ipo)} · ${esc(String(co.event_count))} 条物质事件</p>
      <p class="note">打开台账，按年代和判定翻阅。</p>
    </a>
  `).join("");
  const extra = `
    <a class="card" href="products.html">
      <p class="kicker">MSFT · 产品线</p>
      <h3>份额、订阅、单价</h3>
      <p>按年列出席位增速、绝对席位、公开标价和第三方份额。</p>
      <p class="note">年报给增速和营收；标价和市场份额另行标注来源。</p>
    </a>
    <a class="card" href="company.html">
      <p class="kicker">MSFT · 公司信息</p>
      <h3>董事会报告</h3>
      <p>每年一份：当时环境、项目进展、未来展望，外加董事会执行时间线。</p>
      <p class="note">美股没有 A 股「董事会报告」科目，用股东信和年报 MD&A 按财年对齐。</p>
    </a>`;
  catalogEl.innerHTML = issuerCards + extra;
}

document.getElementById("search-form").addEventListener("submit", (e) => {
  e.preventDefault();
  runSearch();
});
qEl.addEventListener("input", () => {
  runSearch();
});

const params = new URLSearchParams(location.search);
if (params.get("q")) qEl.value = params.get("q");

Promise.all([
  fetch("./catalog.json").then((r) => r.json()),
]).then(async (data) => {
  catalog = data[0];
  const total = catalog.issuers.reduce((n, c) => n + (c.event_count || 0), 0);
  hintEl.textContent = `当前可检索 ${catalog.issuers.map((c) => c.name).join("、")}，共 ${total} 条。`;
  renderCatalog();
  ledgers = await Promise.all(
    catalog.issuers.map(async (co) => {
      const payload = await fetch("./" + co.json).then((r) => r.json());
      return {
        ticker: co.ticker,
        page: co.page,
        issuer: payload.issuer,
        events: payload.events || [],
      };
    })
  );
  if (qEl.value.trim()) runSearch();
}).catch(() => {
  hintEl.textContent = "读不到目录。请用本地预览命令打开，不要直接双击 HTML。";
});
