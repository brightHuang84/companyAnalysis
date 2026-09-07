# 上市公司事件台账

从上市第一天起整理物质事件：当时背景、决策原因、决策目录、最终效果。财务写这条事件自己的钱、它和当年全公司年报的关系，以及这条产品线能核对到的分部营业利润。微软不披露 Windows / Azure / Xbox 单品利润。

当前公开样本：微软（NASDAQ: MSFT），1986–2026，91 条。

## 本地查看

```bash
python3 listed_trust/export_site.py
python3 -m http.server 8080 --directory docs
```

打开 http://127.0.0.1:8080/ （主页搜索）和 http://127.0.0.1:8080/msft.html （台账）。

## 网上发布

仓库 Settings → Pages → Source 选 **GitHub Actions**。推送到 `main` 后会自动部署。

## 改内容

只改 `data/issuers/MSFT/events_1986_2026.json` 里的叙事，或改 `listed_trust/msft_finance.py` 里的财务回报、`data/issuers/MSFT/financials_fy.json` 里的年度账本，然后运行：

```bash
python3 listed_trust/build_msft_detail.py
python3 listed_trust/export_site.py
```

不要手改 `docs/msft.json`。
