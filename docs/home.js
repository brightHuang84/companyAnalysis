const resultsEl = document.getElementById("results");
const wrapEl = document.getElementById("results-wrap");
const titleEl = document.getElementById("results-title");
const hintEl = document.getElementById("search-hint");
const qEl = document.getElementById("q");
const catalogEl = document.getElementById("catalog");

let catalog = { issuers: [] };
let reports = [];

function resultUrl(hit) {
  return `${hit.page}?fy=${hit.fy}&q=${encodeURIComponent(qEl.value.trim())}`;
}

function renderResults(hits, q) {
  const show = q.trim().length > 0;
  wrapEl.hidden = !show;
  if (!show) {
    resultsEl.innerHTML = "";
    return;
  }
  titleEl.textContent = hits.length ? `搜索结果 · ${hits.length} 份` : "搜索结果";
  if (!hits.length) {
    resultsEl.innerHTML = `<li class="empty-row">没有找到「${esc(q)}」。可换 Azure、Windows、人工智能、分红 再试。</li>`;
    return;
  }
  resultsEl.innerHTML = hits.map((hit) => `
    <li>
      <a href="${esc(resultUrl(hit))}">
        <div class="meta">
          <span>${esc(hit.ticker)}</span>
          <span>FY${esc(hit.fy)}</span>
          <span class="badge ${kindClass(hit.source_kind)}">${esc(hit.source_kind)}</span>
        </div>
        <div class="title">${esc(hit.issuer)} · FY${esc(hit.fy)} 年报</div>
        <p class="snippet">${esc(hit.snippet)}</p>
      </a>
    </li>
  `).join("");
}

function runSearch() {
  const q = qEl.value;
  const hits = reports.flatMap((pack) =>
    searchReports(pack.years, q, pack.issuer).map((row) => ({
      ...row,
      ticker: pack.ticker,
      issuer: pack.issuer,
      page: pack.page,
    }))
  );
  renderResults(hits, q);
}

function renderCatalog() {
  catalogEl.innerHTML = catalog.issuers.map((co) => `
    <a class="card" href="${esc(co.page)}">
      <p class="kicker">${esc(co.exchange)} · ${esc(co.ticker)}</p>
      <h3>${esc(co.name)}</h3>
      <p>上市 ${esc(co.ipo)} · ${esc(String(co.report_count))} 份年报译文</p>
      <p class="note">按年打开链接和提炼，点进去读全文和图表。</p>
    </a>
  `).join("");
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
  const total = catalog.issuers.reduce((n, c) => n + (c.report_count || 0), 0);
  hintEl.textContent = `当前可检索 ${catalog.issuers.map((c) => c.name).join("、")} 年报译文，共 ${total} 份。`;
  renderCatalog();
  reports = await Promise.all(
    catalog.issuers.map(async (co) => {
      const payload = await fetch("./" + co.json).then((r) => r.json());
      return {
        ticker: co.ticker,
        page: co.page,
        issuer: payload.issuer || co.name,
        years: payload.years || [],
      };
    })
  );
  if (qEl.value.trim()) runSearch();
}).catch(() => {
  hintEl.textContent = "读不到目录。请用本地预览命令打开，不要直接双击 HTML。";
});
