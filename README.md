# 上市公司年报译文

主页按公司检索年报译文。点进一家公司，先看每年年报链接和几句原文提炼；点开某一年，读完整译文，并保留能核对的营收、利润和产品构成图表。

当前公开样本：微软（NASDAQ: MSFT），FY1986–FY2026。有官方中文用官方中文，否则译英文致股东信；图文年报未出时用 10-K 管理层讨论概述。

## 本地查看

```bash
python3 listed_trust/enrich_product_lines.py
python3 listed_trust/enrich_board_reports.py
python3 listed_trust/export_site.py
python3 -m http.server 8080 --directory docs
```

打开 http://127.0.0.1:8080/ （主页搜索）、http://127.0.0.1:8080/company.html （微软各年年报）。

## 网上发布

仓库 Settings → Pages → Source 选 **GitHub Actions**。推送到 `main` 后会自动部署。

## 改内容

只改 `data/issuers/MSFT/letters/` 里的年报译文，或改 `listed_trust/enrich_board_reports.py` 的装配逻辑、`data/issuers/MSFT/financials_fy.json` 的年度账本、`listed_trust/enrich_product_lines.py` 的产品营收，然后运行上面的生成命令。

不要手改 `docs/board_reports.json`。它由 enrich + export 生成。
