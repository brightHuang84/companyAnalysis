# 上市公司事件台账

从上市第一天起整理物质事件：当时背景、决策原因、决策目录、最终效果。财务只用来核验。

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

只改 `data/issuers/MSFT/events_1986_2026.json`，然后运行 `python3 listed_trust/export_site.py`。不要手改 `docs/msft.json`。
