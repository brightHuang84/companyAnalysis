"""Attach 10-K product-offering history and web-sourced operating metrics.

Microsoft's 10-K still does not publish Windows / Azure / Xbox operating profit.
This script does not invent those profits. It adds (a) the product-revenue table
the 10-K already prints, (b) earnings-call operating metrics, and (c) third-party
share / subscriber figures, each tagged with grain + source.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINES_PATH = ROOT / "data" / "issuers" / "MSFT" / "product_lines.json"

# 10-K "Revenue classified by significant product and service offerings".
# FY2024 reclassified: Office split commercial/consumer; Windows+Devices combined;
# Gaming renamed XBOX. Earlier Dynamics sat inside Other until the FY2023 recast.
OFFERINGS = [
    {
        "fy": 2016,
        "items": [
            {"id": "office", "name": "Office 产品与云服务", "revenue": 23868, "line": "office"},
            {"id": "server_cloud", "name": "服务器与云服务（含 Azure）", "revenue": 19062, "line": "cloud"},
            {"id": "windows", "name": "Windows", "revenue": 17548, "line": "windows"},
            {"id": "gaming", "name": "游戏", "revenue": 9202, "line": "gaming"},
            {"id": "devices", "name": "设备（含诺基亚收尾 / Surface）", "revenue": 7888, "line": "devices"},
            {"id": "enterprise", "name": "企业服务", "revenue": 5659, "line": "cloud"},
            {"id": "search", "name": "搜索广告", "revenue": 5428, "line": "search"},
            {"id": "other", "name": "其他（当时含 Dynamics）", "revenue": 2499, "line": "office"},
        ],
    },
    {
        "fy": 2017,
        "items": [
            {"id": "office", "name": "Office 产品与云服务", "revenue": 25573, "line": "office"},
            {"id": "server_cloud", "name": "服务器与云服务（含 Azure）", "revenue": 21649, "line": "cloud"},
            {"id": "windows", "name": "Windows", "revenue": 18593, "line": "windows"},
            {"id": "gaming", "name": "游戏", "revenue": 9051, "line": "gaming"},
            {"id": "enterprise", "name": "企业服务", "revenue": 5542, "line": "cloud"},
            {"id": "search", "name": "搜索广告", "revenue": 6219, "line": "search"},
            {"id": "devices", "name": "设备 / Surface", "revenue": 5062, "line": "devices"},
            {"id": "linkedin", "name": "LinkedIn", "revenue": 2271, "line": "office"},
            {"id": "other", "name": "其他（当时含 Dynamics）", "revenue": 2611, "line": "office"},
        ],
    },
    {
        "fy": 2018,
        "items": [
            {"id": "office", "name": "Office 产品与云服务", "revenue": 28316, "line": "office"},
            {"id": "server_cloud", "name": "服务器与云服务（含 Azure）", "revenue": 26129, "line": "cloud"},
            {"id": "windows", "name": "Windows", "revenue": 19518, "line": "windows"},
            {"id": "gaming", "name": "游戏", "revenue": 10353, "line": "gaming"},
            {"id": "search", "name": "搜索广告", "revenue": 7012, "line": "search"},
            {"id": "linkedin", "name": "LinkedIn", "revenue": 5259, "line": "office"},
            {"id": "enterprise", "name": "企业服务", "revenue": 5846, "line": "cloud"},
            {"id": "devices", "name": "设备 / Surface", "revenue": 5134, "line": "devices"},
            {"id": "other", "name": "其他（当时含 Dynamics）", "revenue": 2793, "line": "office"},
        ],
    },
    {
        "fy": 2019,
        "items": [
            {"id": "server_cloud", "name": "服务器与云服务（含 Azure）", "revenue": 32622, "line": "cloud"},
            {"id": "office", "name": "Office 产品与云服务", "revenue": 31769, "line": "office"},
            {"id": "windows", "name": "Windows", "revenue": 20395, "line": "windows"},
            {"id": "gaming", "name": "游戏", "revenue": 11386, "line": "gaming"},
            {"id": "search", "name": "搜索广告", "revenue": 7628, "line": "search"},
            {"id": "linkedin", "name": "LinkedIn", "revenue": 6754, "line": "office"},
            {"id": "enterprise", "name": "企业服务", "revenue": 6124, "line": "cloud"},
            {"id": "devices", "name": "设备 / Surface", "revenue": 6095, "line": "devices"},
            {"id": "other", "name": "其他（当时含 Dynamics）", "revenue": 3070, "line": "office"},
        ],
    },
    {
        "fy": 2020,
        "items": [
            {"id": "server_cloud", "name": "服务器与云服务（含 Azure）", "revenue": 41379, "line": "cloud"},
            {"id": "office", "name": "Office 产品与云服务", "revenue": 35316, "line": "office"},
            {"id": "windows", "name": "Windows", "revenue": 22294, "line": "windows"},
            {"id": "gaming", "name": "游戏", "revenue": 11575, "line": "gaming"},
            {"id": "linkedin", "name": "LinkedIn", "revenue": 8077, "line": "office"},
            {"id": "search", "name": "搜索广告", "revenue": 7740, "line": "search"},
            {"id": "devices", "name": "设备 / Surface", "revenue": 6457, "line": "devices"},
            {"id": "enterprise", "name": "企业服务", "revenue": 6409, "line": "cloud"},
            {"id": "other", "name": "其他（当时含 Dynamics）", "revenue": 3768, "line": "office"},
        ],
    },
    {
        "fy": 2021,
        "items": [
            {"id": "server_cloud", "name": "服务器与云服务（含 Azure）", "revenue": 52589, "line": "cloud"},
            {"id": "office", "name": "Office 产品与云服务", "revenue": 39872, "line": "office"},
            {"id": "windows", "name": "Windows", "revenue": 22488, "line": "windows"},
            {"id": "gaming", "name": "游戏", "revenue": 15370, "line": "gaming"},
            {"id": "linkedin", "name": "LinkedIn", "revenue": 10289, "line": "office"},
            {"id": "search", "name": "搜索与新闻广告", "revenue": 9267, "line": "search"},
            {"id": "enterprise", "name": "企业服务", "revenue": 6943, "line": "cloud"},
            {"id": "devices", "name": "设备 / Surface", "revenue": 7143, "line": "devices"},
            {"id": "dynamics", "name": "Dynamics", "revenue": 3754, "line": "office"},
            {"id": "other", "name": "其他", "revenue": 373, "line": "company"},
        ],
    },
    {
        "fy": 2022,
        "items": [
            {"id": "server_cloud", "name": "服务器与云服务（含 Azure）", "revenue": 67350, "line": "cloud"},
            {"id": "office", "name": "Office 产品与云服务", "revenue": 44862, "line": "office"},
            {"id": "windows", "name": "Windows", "revenue": 24732, "line": "windows"},
            {"id": "gaming", "name": "游戏", "revenue": 16230, "line": "gaming"},
            {"id": "linkedin", "name": "LinkedIn", "revenue": 13816, "line": "office"},
            {"id": "search", "name": "搜索与新闻广告", "revenue": 11591, "line": "search"},
            {"id": "enterprise", "name": "企业服务", "revenue": 7407, "line": "cloud"},
            {"id": "devices", "name": "设备 / Surface", "revenue": 7306, "line": "devices"},
            {"id": "dynamics", "name": "Dynamics", "revenue": 4687, "line": "office"},
            {"id": "other", "name": "其他", "revenue": 289, "line": "company"},
        ],
    },
    {
        "fy": 2023,
        "items": [
            {"id": "server_cloud", "name": "服务器与云服务（含 Azure）", "revenue": 79970, "line": "cloud"},
            {"id": "office", "name": "Office 产品与云服务", "revenue": 48728, "line": "office"},
            {"id": "windows", "name": "Windows", "revenue": 21507, "line": "windows"},
            {"id": "gaming", "name": "游戏", "revenue": 15466, "line": "gaming"},
            {"id": "linkedin", "name": "LinkedIn", "revenue": 15145, "line": "office"},
            {"id": "search", "name": "搜索与新闻广告", "revenue": 12208, "line": "search"},
            {"id": "enterprise", "name": "企业服务", "revenue": 7722, "line": "cloud"},
            {"id": "devices", "name": "设备 / Surface", "revenue": 5521, "line": "devices"},
            {"id": "dynamics", "name": "Dynamics", "revenue": 5437, "line": "office"},
            {"id": "other", "name": "其他", "revenue": 211, "line": "company"},
        ],
    },
    {
        "fy": 2024,
        "items": [
            {"id": "server_cloud", "name": "服务器与云服务（含 Azure）", "revenue": 79828, "line": "cloud"},
            {"id": "m365_comm", "name": "Microsoft 365 商业", "revenue": 76969, "line": "office"},
            {"id": "xbox", "name": "Xbox", "revenue": 21503, "line": "gaming"},
            {"id": "windows_devices", "name": "Windows 与设备", "revenue": 17026, "line": "windows"},
            {"id": "linkedin", "name": "LinkedIn", "revenue": 16372, "line": "office"},
            {"id": "search", "name": "搜索广告", "revenue": 12306, "line": "search"},
            {"id": "enterprise", "name": "企业与合作伙伴服务", "revenue": 7594, "line": "cloud"},
            {"id": "dynamics", "name": "Dynamics", "revenue": 6831, "line": "office"},
            {"id": "m365_cons", "name": "Microsoft 365 消费", "revenue": 6648, "line": "office"},
            {"id": "other", "name": "其他", "revenue": 45, "line": "company"},
        ],
    },
    {
        "fy": 2025,
        "items": [
            {"id": "server_cloud", "name": "服务器与云服务（含 Azure）", "revenue": 98435, "line": "cloud"},
            {"id": "m365_comm", "name": "Microsoft 365 商业", "revenue": 87767, "line": "office"},
            {"id": "xbox", "name": "Xbox", "revenue": 23455, "line": "gaming"},
            {"id": "linkedin", "name": "LinkedIn", "revenue": 17812, "line": "office"},
            {"id": "windows_devices", "name": "Windows 与设备", "revenue": 17314, "line": "windows"},
            {"id": "search", "name": "搜索广告", "revenue": 13878, "line": "search"},
            {"id": "dynamics", "name": "Dynamics", "revenue": 7827, "line": "office"},
            {"id": "enterprise", "name": "企业与合作伙伴服务", "revenue": 7760, "line": "cloud"},
            {"id": "m365_cons", "name": "Microsoft 365 消费", "revenue": 7404, "line": "office"},
            {"id": "azure", "name": "Azure（公司首次给出全年美元）", "revenue": 75000, "line": "cloud", "nested": True},
            {"id": "other", "name": "其他", "revenue": 72, "line": "company"},
        ],
    },
    {
        "fy": 2026,
        "items": [
            {"id": "server_cloud", "name": "服务器与云服务（含 Azure）", "revenue": 129425, "line": "cloud"},
            {"id": "m365_comm", "name": "Microsoft 365 商业", "revenue": 101997, "line": "office"},
            {"id": "xbox", "name": "Xbox", "revenue": 21790, "line": "gaming"},
            {"id": "linkedin", "name": "LinkedIn", "revenue": 19817, "line": "office"},
            {"id": "windows_devices", "name": "Windows 与设备", "revenue": 17084, "line": "windows"},
            {"id": "search", "name": "搜索广告", "revenue": 15176, "line": "search"},
            {"id": "m365_cons", "name": "Microsoft 365 消费", "revenue": 9175, "line": "office"},
            {"id": "dynamics", "name": "Dynamics", "revenue": 9006, "line": "office"},
            {"id": "enterprise", "name": "企业与合作伙伴服务", "revenue": 8260, "line": "cloud"},
            {"id": "azure", "name": "Azure（后续披露的全年美元）", "revenue": 101900, "line": "cloud", "nested": True},
            {"id": "other", "name": "其他", "revenue": 109, "line": "company"},
        ],
    },
]

MICROSOFT_CLOUD = [
    {"fy": 2016, "revenue": 9500, "label": "商业云（当时口径，尚未并入 LinkedIn 商业）"},
    {"fy": 2017, "revenue": 16200, "label": "Microsoft Cloud（后续 10-K 重述，含 LinkedIn 商业）"},
    {"fy": 2018, "revenue": 26600, "label": "Microsoft Cloud"},
    {"fy": 2019, "revenue": 38100, "label": "Microsoft Cloud"},
    {"fy": 2020, "revenue": 51700, "label": "Microsoft Cloud"},
    {"fy": 2021, "revenue": 69100, "label": "Microsoft Cloud"},
    {"fy": 2022, "revenue": 91400, "label": "Microsoft Cloud"},
    {"fy": 2023, "revenue": 111600, "label": "Microsoft Cloud"},
    {"fy": 2024, "revenue": 137700, "label": "Microsoft Cloud"},
    {"fy": 2025, "revenue": 168900, "label": "Microsoft Cloud"},
    {"fy": 2026, "revenue": 214400, "label": "Microsoft Cloud"},
]

AZURE = [
    {
        "fy": 2025,
        "revenue": 75000,
        "growth_pct": 34,
        "note": "公司第一次给出 Azure 全年美元：超过 750 亿美元，同比约 +34%。",
    },
    {
        "fy": 2026,
        "revenue": 101900,
        "growth_pct": 41,
        "q4_revenue": 29400,
        "note": "业绩会说全年破 1000 亿、同比 +41%（相对 750 亿约等于 1058 亿）。随后公司披露全年约 1019 亿、FY26 Q4 单季 294 亿。这里用后续披露的全年数。",
    },
]

# Hardware vs content compiled from Microsoft quarterly earnings, not a 10-K OI line.
# FY2026 hardware = FY2025 hardware × (1 − 0.29); content is the residual against 10-K Xbox total.
XBOX_SPLIT = [
    {"fy": 2015, "total": 9034, "content": 4935, "hardware": 4099, "grain": "earnings"},
    {"fy": 2016, "total": 9202, "content": 5695, "hardware": 3449, "grain": "earnings"},
    {"fy": 2017, "total": 9051, "content": 6338, "hardware": 2714, "grain": "earnings"},
    {"fy": 2018, "total": 10353, "content": 7575, "hardware": 2778, "grain": "earnings"},
    {"fy": 2019, "total": 11386, "content": 8974, "hardware": 2412, "grain": "earnings"},
    {"fy": 2020, "total": 11575, "content": 9915, "hardware": 1660, "grain": "earnings"},
    {"fy": 2021, "total": 15370, "content": 12173, "hardware": 3197, "grain": "earnings"},
    {"fy": 2022, "total": 16230, "content": 12523, "hardware": 3707, "grain": "earnings"},
    {"fy": 2023, "total": 15466, "content": 12186, "hardware": 3280, "grain": "earnings"},
    {"fy": 2024, "total": 21503, "content": 18310, "hardware": 2860, "grain": "earnings"},
    {"fy": 2025, "total": 23455, "content": 21308, "hardware": 2147, "grain": "earnings"},
    {
        "fy": 2026,
        "total": 21790,
        "content": 20266,
        "hardware": 1524,
        "grain": "derived",
        "note": "10-K：Xbox 全年 218 亿，内容与服务 -5%，硬件 -29%。硬件按 FY2025 的 21.47 亿 × 0.71 得到 15.24 亿，内容用总额倒减。",
    },
]

WEB_METRICS = [
    {
        "id": "azure_fy26",
        "line": "cloud",
        "name": "Azure 全年营收",
        "value": 1019,
        "unit": "亿美元",
        "as_of": "FY2026",
        "grain": "company",
        "source": "微软业绩会称全年破 1000 亿、同比 +41%；随后披露全年约 1019 亿、Q4 294 亿",
        "url": "https://fortune.com/2026/07/29/microsoft-azure-100-billion-annual-revenue-earnings-revenue-cloud-ai/",
        "note": "不是智能云全部分部。智能云 FY2026 营收 1378 亿，Azure 约占四分之三。营业利润仍不单列。",
    },
    {
        "id": "azure_fy25",
        "line": "cloud",
        "name": "Azure 全年营收",
        "value": 750,
        "unit": "亿美元",
        "as_of": "FY2025",
        "grain": "company",
        "source": "微软 FY2025 业绩，第一次给出 Azure 全年美元",
        "url": "https://fortune.com/2025/07/30/microsoft-earnings-azure-cloud-computing-artificial-intelligence/",
        "note": "此前十几年只给增速，不给金额。",
    },
    {
        "id": "azure_share_q2_2026",
        "line": "cloud",
        "name": "全球云基础设施份额",
        "value": 20,
        "unit": "%",
        "as_of": "2026 Q2",
        "grain": "third_party",
        "source": "Synergy Research Group，当季市场 1430 亿美元",
        "url": "https://www.srgresearch.com/articles/q2-cloud-market-passes-143-billion-highest-growth-rate-in-eight-years",
        "note": "AWS 28%、Google Cloud 15%。年报没有份额。Azure 份额同比持平，Google 在抢。",
    },
    {
        "id": "ms_cloud_gm_q4_fy26",
        "line": "cloud",
        "name": "Microsoft Cloud 毛利率",
        "value": 65,
        "unit": "%",
        "as_of": "FY2026 Q4",
        "grain": "earnings",
        "source": "FY2026 Q4 业绩会，CFO Amy Hood",
        "url": "https://www.microsoft.com/en-us/investor/events/fy-2026/earnings-fy-2026-q4",
        "note": "好于公司自己的指引，但同比下降：结构转向 Azure + AI 基建。这是云组合毛利，不是 Azure 营业利润。",
    },
    {
        "id": "foundry_customers",
        "line": "cloud",
        "name": "Azure AI Foundry 客户",
        "value": 100000,
        "unit": "家",
        "as_of": "FY2026 Q4",
        "grain": "earnings",
        "source": "Nadella FY2026 Q4 业绩会",
        "url": "https://www.microsoft.com/en-us/investor/events/fy-2026/earnings-fy-2026-q4",
        "note": "营收同比翻倍。不是利润。",
    },
    {
        "id": "github_users",
        "line": "cloud",
        "name": "GitHub 用户",
        "value": 225,
        "unit": "百万",
        "as_of": "FY2026 Q4",
        "grain": "earnings",
        "source": "Nadella FY2026 Q4 业绩会",
        "url": "https://www.microsoft.com/en-us/investor/events/fy-2026/earnings-fy-2026-q4",
        "note": "年报不单列 GitHub 营收。2018 年 75 亿美元买下。",
    },
    {
        "id": "github_copilot_users",
        "line": "cloud",
        "name": "GitHub Copilot 用户",
        "value": 50,
        "unit": "百万",
        "as_of": "FY2026 Q4",
        "grain": "earnings",
        "source": "Nadella FY2026 Q4 业绩会",
        "url": "https://www.microsoft.com/en-us/investor/events/fy-2026/earnings-fy-2026-q4",
        "note": "用户数，不是付费席位，也不是营收。",
    },
    {
        "id": "github_rev_est_2024",
        "line": "cloud",
        "name": "GitHub 年经常性收入（第三方估算）",
        "value": 20,
        "unit": "亿美元",
        "as_of": "2024",
        "grain": "estimate",
        "source": "分析师/媒体估算，微软不披露",
        "url": "https://www.skillademia.com/statistics/github-statistics/",
        "note": "大约 2022 年 10 亿 → 2024 年 20 亿+。不要当年报。对 75 亿收购价，即使估准也只是入口，真正回收看 Azure。",
    },
    {
        "id": "m365_comm_seats",
        "line": "office",
        "name": "Microsoft 365 商业付费席位",
        "value": 450,
        "unit": "百万+",
        "as_of": "FY2026 Q2",
        "grain": "earnings",
        "source": "微软 FY2026 Q2 业绩：超过 4.50 亿",
        "url": "https://office365itpros.com/2026/07/30/fy26-q4-microsoft-results/",
        "note": "Q4 只给席位同比 +6%，不再报总数。按 4.50 亿 × 1.06 粗算约 4.64 亿，那是推算。",
    },
    {
        "id": "m365_comm_seats_yoy",
        "line": "office",
        "name": "M365 商业席位同比",
        "value": 6,
        "unit": "%",
        "as_of": "FY2026 Q4",
        "grain": "earnings",
        "source": "Hood FY2026 Q4 业绩会",
        "url": "https://www.microsoft.com/en-us/investor/events/fy-2026/earnings-fy-2026-q4",
        "note": "增量主要在中小企业和一线员工 SKU，ARPU 较低。",
    },
    {
        "id": "copilot_seats",
        "line": "office",
        "name": "Microsoft 365 Copilot 付费席位",
        "value": 30,
        "unit": "百万+",
        "as_of": "FY2026 Q4",
        "grain": "earnings",
        "source": "Nadella FY2026 Q4：超过 3000 万，净增席位环比翻倍以上",
        "url": "https://www.microsoft.com/en-us/Investor/earnings/FY-2026-Q4/press-release-webcast",
        "note": "Q2 约 1500 万、Q3 约 2000 万、Q4 超 3000 万。年报不披露 Copilot 营收。相对约 4.5 亿商业席位，渗透大约 6–7%。",
    },
    {
        "id": "copilot_list_arr",
        "line": "office",
        "name": "Copilot 标价粗算 ARR",
        "value": 108,
        "unit": "亿美元",
        "as_of": "FY2026 Q4",
        "grain": "derived",
        "source": "3000 万席位 × 标价 30 美元/月 × 12。微软未披露成交价。",
        "url": "https://aibusinessweekly.net/p/microsoft-copilot-statistics",
        "note": "这是标价上限，不是公司数字。企业折扣、E7 捆绑、未全量开通都会把实收打下去。",
    },
    {
        "id": "agent365",
        "line": "office",
        "name": "Agent 365 已注册代理",
        "value": 40,
        "unit": "百万",
        "as_of": "FY2026 Q4",
        "grain": "earnings",
        "source": "Nadella：上线约两个月，近 4000 万代理",
        "url": "https://www.microsoft.com/en-us/investor/events/fy-2026/earnings-fy-2026-q4",
        "note": "注册数，不是收入。",
    },
    {
        "id": "linkedin_members",
        "line": "office",
        "name": "LinkedIn 注册会员",
        "value": 13,
        "unit": "亿",
        "as_of": "2026",
        "grain": "company",
        "source": "LinkedIn 公开口径，多家转引",
        "url": "https://sproutsocial.com/insights/linkedin-statistics/",
        "note": "FY2026 LinkedIn 营收 198 亿美元在 10-K。会员数年报不作为财务科目。",
    },
    {
        "id": "dynamics_fy26",
        "line": "office",
        "name": "Dynamics 产品与云服务营收",
        "value": 90,
        "unit": "亿美元",
        "as_of": "FY2026",
        "grain": "10k",
        "source": "FY2026 10-K 产品表",
        "url": "https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm",
        "note": "Dynamics 365 全年 +18%。有营收、无单品营业利润。",
    },
    {
        "id": "windows_desktop_share",
        "line": "windows",
        "name": "全球桌面操作系统流量份额",
        "value": 62.7,
        "unit": "%",
        "as_of": "2026-08",
        "grain": "third_party",
        "source": "Statcounter Global Stats",
        "url": "https://gs.statcounter.com/os-market-share/desktop/worldwide",
        "note": "流量份额不是装机量。2026 年 Unknown 类别升高，真实 Windows 使用可能被低估。年报只有 Windows 与设备合计营收 171 亿美元。",
    },
    {
        "id": "windows_oem_q4",
        "line": "windows",
        "name": "Windows OEM 与设备营收同比",
        "value": -7,
        "unit": "%",
        "as_of": "FY2026 Q4",
        "grain": "earnings",
        "source": "FY2026 Q4 业绩稿",
        "url": "https://www.microsoft.com/en-us/Investor/earnings/FY-2026-Q4/press-release-webcast",
        "note": "消费 PC 授权在失血。利润仍埋在「更多个人计算」。",
    },
    {
        "id": "game_pass_official",
        "line": "gaming",
        "name": "Game Pass 订阅（公司最后一次公布）",
        "value": 34,
        "unit": "百万",
        "as_of": "2024-02",
        "grain": "company",
        "source": "Xbox 官方播客 / The Verge",
        "url": "https://www.theverge.com/2024/2/15/23570040/microsoft-xbox-game-pass-subscriber-numbers-34-million",
        "note": "含原 Xbox Live Gold 转 Game Pass Core。此后业绩会不再报订阅数。",
    },
    {
        "id": "game_pass_2026",
        "line": "gaming",
        "name": "Game Pass 订阅（媒体）",
        "value": 30,
        "unit": "百万",
        "as_of": "2026-07",
        "grain": "third_party",
        "source": "Bloomberg / WSJ，公司未官宣",
        "url": "https://www.videogameschronicle.com/news/xbox-game-pass-has-reportedly-lost-millions-of-users-since-2024/",
        "note": "相对 2024 年 3400 万约少 400 万。法庭材料里微软曾规划 2026 年约 7700 万，对不上。",
    },
    {
        "id": "game_pass_rev_fy25",
        "line": "gaming",
        "name": "Game Pass 全年营收",
        "value": 50,
        "unit": "亿美元",
        "as_of": "FY2025",
        "grain": "earnings",
        "source": "Nadella FY2025 业绩会：nearly $5 billion for the first time",
        "url": "https://www.gadgets360.com/games/news/xbox-game-pass-revenue-usd-5-billion-first-time-fy-2025-microsoft-earnings-call-8993673",
        "note": "FY2026 未再给金额，只说 Game Pass 增长部分抵消了内容下滑。",
    },
    {
        "id": "xbox_mau_fy25",
        "line": "gaming",
        "name": "Xbox 跨平台月活",
        "value": 500,
        "unit": "百万",
        "as_of": "FY2025",
        "grain": "earnings",
        "source": "Nadella FY2025 业绩会",
        "url": "https://www.gadgets360.com/games/news/xbox-game-pass-revenue-usd-5-billion-first-time-fy-2025-microsoft-earnings-call-8993673",
        "note": "月活不是利润。FY2026 内容与服务 Q4 -10%，硬件全年 -29%。",
    },
    {
        "id": "xbox_hw_fy26",
        "line": "gaming",
        "name": "Xbox 硬件营收（倒推）",
        "value": 15.2,
        "unit": "亿美元",
        "as_of": "FY2026",
        "grain": "derived",
        "source": "10-K：硬件 -29%；基数为季度拆出的 FY2025 硬件 21.47 亿",
        "url": "https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm",
        "note": "大约十年最低。内容与服务倒减约 203 亿。硬件近零毛利，买 Activision 的回收只能看内容。",
    },
    {
        "id": "bing_share",
        "line": "search",
        "name": "全球搜索流量份额",
        "value": 4.3,
        "unit": "%",
        "as_of": "2026-07",
        "grain": "third_party",
        "source": "Statcounter，桌面+移动",
        "url": "https://gs.statcounter.com/search-engine-market-share/desktop-mobile/worldwide/",
        "note": "Google 约 91%。FY2026 搜索广告营收 152 亿，但份额二十年没翻盘。",
    },
    {
        "id": "search_ex_tac_q4",
        "line": "search",
        "name": "搜索广告（不含流量获取成本）同比",
        "value": 10,
        "unit": "%",
        "as_of": "FY2026 Q4",
        "grain": "earnings",
        "source": "FY2026 Q4 业绩稿",
        "url": "https://www.microsoft.com/en-us/Investor/earnings/FY-2026-Q4/press-release-webcast",
        "note": "有增长，没有份额突破。",
    },
    {
        "id": "rpo",
        "line": "company",
        "name": "商业剩余履约义务",
        "value": 6780,
        "unit": "亿美元",
        "as_of": "FY2026 Q4",
        "grain": "earnings",
        "source": "FY2026 Q4 业绩稿，同比 +84%",
        "url": "https://www.microsoft.com/en-us/Investor/earnings/FY-2026-Q4/press-release-webcast",
        "note": "合同存量，不是当期利润。几乎全部增量来自非前沿模型公司客户。",
    },
]


# 年报 KPI 给增速多于给绝对数。绝对席位、标价、份额按年另列，并标来源。
SEAT_GROWTH = [
    {"fy": 2015, "m365_comm_pct": 74, "grain": "earnings", "source": "Office 365 Commercial seat growth，YCharts 汇总自业绩"},
    {"fy": 2016, "m365_comm_pct": 45, "grain": "earnings", "source": "Office 365 Commercial seat growth"},
    {"fy": 2017, "m365_comm_pct": 31, "grain": "10k", "source": "10-K / 业绩 KPI：Office 365 Commercial seat growth"},
    {"fy": 2018, "m365_comm_pct": 29, "grain": "10k", "source": "10-K / 业绩 KPI"},
    {"fy": 2019, "m365_comm_pct": 23, "grain": "10k", "source": "10-K / 业绩 KPI"},
    {"fy": 2020, "m365_comm_pct": 15, "grain": "10k", "source": "10-K / 业绩 KPI"},
    {"fy": 2021, "m365_comm_pct": 17, "grain": "10k", "source": "10-K / 业绩 KPI"},
    {"fy": 2022, "m365_comm_pct": 14, "grain": "10k", "source": "10-K / 业绩 KPI"},
    {"fy": 2023, "m365_comm_pct": 11, "grain": "10k", "source": "FY2023 10-K：Office 365 Commercial seat growth 11%"},
    {"fy": 2024, "m365_comm_pct": 7, "grain": "10k", "source": "10-K / 业绩 KPI：Microsoft 365 Commercial seats"},
    {"fy": 2025, "m365_comm_pct": 6, "m365_cons_pct": 8, "grain": "10k", "source": "FY2025 业绩：商业席位 +6%，消费订阅 8900 万、+8%"},
    {"fy": 2026, "m365_comm_pct": 6, "m365_cons_pct": 7, "grain": "10k", "source": "FY2026 10-K MD&A：商业席位 +6%，消费订阅 +7%。Q1 起不再把消费订阅数当 KPI"},
]

SEATS = [
    {"fy": 2017, "line": "office", "name": "Office 365 商业付费席位", "value": 100, "unit": "百万", "as_of": "2017-04", "grain": "earnings", "source": "Nadella / 业绩会里程碑"},
    {"fy": 2020, "line": "office", "name": "Office 365 商业付费席位", "value": 200, "unit": "百万", "as_of": "2019-10", "grain": "earnings", "source": "业绩会里程碑"},
    {"fy": 2022, "line": "office", "name": "Office 365 商业付费席位", "value": 300, "unit": "百万", "as_of": "2021-12", "grain": "earnings", "source": "业绩会里程碑"},
    {"fy": 2023, "line": "office", "name": "Office 365 商业付费席位", "value": 382, "unit": "百万", "as_of": "2023-04", "grain": "earnings", "source": "FY2023 Q3 业绩"},
    {"fy": 2024, "line": "office", "name": "Office 365 商业付费席位", "value": 400, "unit": "百万+", "as_of": "2024-01", "grain": "earnings", "source": "Nadella FY2024 Q2：over 400 million"},
    {"fy": 2026, "line": "office", "name": "Microsoft 365 商业付费席位", "value": 446, "unit": "百万", "as_of": "FY2026 Q1", "grain": "earnings", "source": "FY2026 Q2 稿回顾上季"},
    {"fy": 2026, "line": "office", "name": "Microsoft 365 商业付费席位", "value": 450, "unit": "百万+", "as_of": "FY2026 Q2", "grain": "earnings", "source": "FY2026 Q2 业绩会。Q4 只报 +6%，不再报总数"},
    {"fy": 2026, "line": "office", "name": "Microsoft 365 商业付费席位（按 +6% 粗算）", "value": 464, "unit": "百万", "as_of": "FY2026 Q4", "grain": "derived", "source": "Q2「超过 4.50 亿」× 半年约 3%"},
    {"fy": 2021, "line": "office", "name": "Microsoft 365 消费订阅", "value": 50, "unit": "百万+", "as_of": "2021-04", "grain": "earnings", "source": "FY2021 Q3 业绩会"},
    {"fy": 2025, "line": "office", "name": "Microsoft 365 消费订阅", "value": 89, "unit": "百万", "as_of": "FY2025", "grain": "earnings", "source": "FY2025 Q4 业绩：8900 万、+8%。此后公司不再报总数"},
    {"fy": 2026, "line": "office", "name": "Microsoft 365 消费订阅", "value": 90, "unit": "百万+", "as_of": "FY2026 Q1", "grain": "earnings", "source": "FY2026 Q1 业绩会：超过 9000 万、+7%"},
    {"fy": 2026, "line": "office", "name": "Microsoft 365 消费订阅", "value": 95, "unit": "百万", "as_of": "FY2026 Q3", "grain": "earnings", "source": "FY2026 Q3 业绩：nearly 95 million"},
    {"fy": 2026, "line": "office", "name": "Microsoft 365 Copilot 付费席位", "value": 15, "unit": "百万", "as_of": "FY2026 Q2", "grain": "earnings", "source": "FY2026 Q2 业绩会，第一次给绝对数"},
    {"fy": 2026, "line": "office", "name": "Microsoft 365 Copilot 付费席位", "value": 20, "unit": "百万+", "as_of": "FY2026 Q3", "grain": "earnings", "source": "FY2026 Q3 业绩会"},
    {"fy": 2026, "line": "office", "name": "Microsoft 365 Copilot 付费席位", "value": 30, "unit": "百万+", "as_of": "FY2026 Q4", "grain": "earnings", "source": "FY2026 10-K / 业绩稿"},
    {"fy": 2017, "line": "office", "name": "LinkedIn 会员", "value": 500, "unit": "百万", "as_of": "2017-04", "grain": "company", "source": "LinkedIn 官方"},
    {"fy": 2019, "line": "office", "name": "LinkedIn 会员", "value": 645, "unit": "百万", "as_of": "2019-08", "grain": "company", "source": "LinkedIn 官方"},
    {"fy": 2021, "line": "office", "name": "LinkedIn 会员", "value": 774, "unit": "百万", "as_of": "2021-07", "grain": "company", "source": "LinkedIn 官方"},
    {"fy": 2023, "line": "office", "name": "LinkedIn 会员", "value": 950, "unit": "百万+", "as_of": "FY2023", "grain": "10k", "source": "FY2023 10-K Item 1：over 950 million members"},
    {"fy": 2025, "line": "office", "name": "LinkedIn 会员", "value": 12, "unit": "亿", "as_of": "FY2025", "grain": "10k", "source": "FY2025 年报致股东信：1.2 billion members"},
    {"fy": 2026, "line": "office", "name": "LinkedIn 会员", "value": 13, "unit": "亿", "as_of": "FY2026", "grain": "earnings", "source": "FY2026 Q3 业绩：1.3 billion"},
    {"fy": 2021, "line": "windows", "name": "Windows 10 月活设备", "value": 13, "unit": "亿+", "as_of": "2021-04", "grain": "earnings", "source": "FY2021 Q3 业绩会"},
    {"fy": 2026, "line": "windows", "name": "Windows 11 用户", "value": 10, "unit": "亿", "as_of": "FY2026 Q2", "grain": "earnings", "source": "FY2026 Q2 业绩会，同比 +45%"},
    {"fy": 2026, "line": "windows", "name": "Windows 月活设备", "value": 16, "unit": "亿+", "as_of": "FY2026 Q3", "grain": "earnings", "source": "FY2026 Q3 业绩会"},
    {"fy": 2022, "line": "gaming", "name": "Game Pass 订阅", "value": 25, "unit": "百万", "as_of": "2022 初", "grain": "company", "source": "微软此前官方数，The Verge 对照"},
    {"fy": 2024, "line": "gaming", "name": "Game Pass 订阅", "value": 34, "unit": "百万", "as_of": "2024-02", "grain": "company", "source": "Xbox 官方播客。此后 10-K / 业绩不再报订阅数"},
    {"fy": 2026, "line": "gaming", "name": "Game Pass 订阅（媒体）", "value": 30, "unit": "百万", "as_of": "2026-07", "grain": "third_party", "source": "Bloomberg / WSJ，公司未官宣"},
    {"fy": 2025, "line": "gaming", "name": "Xbox 跨平台月活", "value": 500, "unit": "百万", "as_of": "FY2025", "grain": "earnings", "source": "Nadella FY2025 业绩会"},
    {"fy": 2026, "line": "cloud", "name": "GitHub 用户", "value": 225, "unit": "百万", "as_of": "FY2026 Q4", "grain": "earnings", "source": "Nadella FY2026 Q4"},
    {"fy": 2026, "line": "cloud", "name": "GitHub Copilot 用户", "value": 50, "unit": "百万", "as_of": "FY2026 Q4", "grain": "earnings", "source": "Nadella FY2026 Q4。用户≠付费席位"},
    {"fy": 2026, "line": "search", "name": "Bing 月活", "value": 10, "unit": "亿", "as_of": "FY2026 Q3", "grain": "earnings", "source": "FY2026 Q3：第一次到 10 亿月活"},
]

PRICES = [
    {"fy": 2011, "line": "office", "sku": "Office 365 / M365 企业套件", "price_usd_mo": None, "note": "Spataro：2011–2022 年企业套件标价基本未涨", "grain": "company"},
    {"fy": 2017, "line": "office", "sku": "Microsoft 365 E3", "price_usd_mo": 32, "grain": "list_price", "source": "商业价目表（不在 10-K）"},
    {"fy": 2017, "line": "office", "sku": "Microsoft 365 E5", "price_usd_mo": 57, "grain": "list_price", "source": "商业价目表"},
    {"fy": 2017, "line": "office", "sku": "Office 365 E3", "price_usd_mo": 20, "grain": "list_price", "source": "商业价目表"},
    {"fy": 2017, "line": "office", "sku": "Office 365 E5", "price_usd_mo": 35, "grain": "list_price", "source": "商业价目表"},
    {"fy": 2017, "line": "office", "sku": "Microsoft 365 Business Basic", "price_usd_mo": 5, "grain": "list_price", "source": "商业价目表"},
    {"fy": 2017, "line": "gaming", "sku": "Xbox Game Pass（当时单档）", "price_usd_mo": 9.99, "grain": "list_price", "source": "2017-06 上线"},
    {"fy": 2019, "line": "gaming", "sku": "Xbox Game Pass Ultimate", "price_usd_mo": 14.99, "grain": "list_price", "source": "2019-06 推出 Ultimate"},
    {"fy": 2022, "line": "office", "sku": "Microsoft 365 E3", "price_usd_mo": 36, "grain": "list_price", "source": "2022-03-01 涨价，E3 $32→$36；E5 仍 $57"},
    {"fy": 2022, "line": "office", "sku": "Microsoft 365 E5", "price_usd_mo": 57, "grain": "list_price", "source": "2022-03 未涨，用来拉开与 E3 的级差"},
    {"fy": 2022, "line": "office", "sku": "Office 365 E3", "price_usd_mo": 23, "grain": "list_price", "source": "2022-03 $20→$23"},
    {"fy": 2022, "line": "office", "sku": "Office 365 E5", "price_usd_mo": 38, "grain": "list_price", "source": "2022-03 $35→$38"},
    {"fy": 2022, "line": "office", "sku": "Microsoft 365 Business Basic", "price_usd_mo": 6, "grain": "list_price", "source": "2022-03 $5→$6"},
    {"fy": 2022, "line": "office", "sku": "Microsoft 365 Business Premium", "price_usd_mo": 22, "grain": "list_price", "source": "2022-03 $20→$22"},
    {"fy": 2023, "line": "gaming", "sku": "Xbox Game Pass Ultimate", "price_usd_mo": 16.99, "grain": "list_price", "source": "2023-08 上调 $2"},
    {"fy": 2024, "line": "office", "sku": "Microsoft 365 Copilot（企业附加）", "price_usd_mo": 30, "grain": "list_price", "source": "2023-11 商用，标价 $30/用户/月，须叠在 E3/E5 或商业版上。10-K 不列单价"},
    {"fy": 2024, "line": "cloud", "sku": "GitHub Copilot Individual", "price_usd_mo": 10, "grain": "list_price", "source": "GitHub 价目表"},
    {"fy": 2024, "line": "cloud", "sku": "GitHub Copilot Business", "price_usd_mo": 19, "grain": "list_price", "source": "GitHub 价目表"},
    {"fy": 2024, "line": "cloud", "sku": "GitHub Copilot Enterprise", "price_usd_mo": 39, "grain": "list_price", "source": "GitHub 价目表"},
    {"fy": 2024, "line": "gaming", "sku": "Xbox Game Pass Ultimate", "price_usd_mo": 19.99, "grain": "list_price", "source": "2024-07 上调"},
    {"fy": 2025, "line": "gaming", "sku": "Xbox Game Pass Ultimate", "price_usd_mo": 29.99, "grain": "list_price", "source": "2025-10 三档改价，Ultimate 到 $29.99"},
    {"fy": 2026, "line": "office", "sku": "Microsoft 365 E3", "price_usd_mo": 39, "grain": "list_price", "source": "2026-07-01 $36→$39。10-K 只说 ARPU 上升，不写美元单价"},
    {"fy": 2026, "line": "office", "sku": "Microsoft 365 E5", "price_usd_mo": 60, "grain": "list_price", "source": "2026-07-01 $57→$60"},
    {"fy": 2026, "line": "office", "sku": "Office 365 E3", "price_usd_mo": 26, "grain": "list_price", "source": "2026-07 $23→$26"},
    {"fy": 2026, "line": "office", "sku": "Office 365 E5", "price_usd_mo": 41, "grain": "list_price", "source": "2026-07 $38→$41"},
    {"fy": 2026, "line": "office", "sku": "Microsoft 365 F3", "price_usd_mo": 10, "grain": "list_price", "source": "2026-07 $8→$10，一线员工 SKU"},
    {"fy": 2026, "line": "office", "sku": "Microsoft 365 Business Basic", "price_usd_mo": 7, "grain": "list_price", "source": "2026-07 $6→$7"},
    {"fy": 2026, "line": "office", "sku": "Microsoft 365 Business Standard", "price_usd_mo": 14, "grain": "list_price", "source": "2026-07 $12.50→$14"},
    {"fy": 2026, "line": "office", "sku": "Microsoft 365 Copilot（企业附加）", "price_usd_mo": 30, "grain": "list_price", "source": "2026 标价未涨，仍 $30；叠在 E3 上全包 $69，叠在 E5 上 $90"},
    {"fy": 2026, "line": "gaming", "sku": "Xbox Game Pass Ultimate", "price_usd_mo": 22.99, "grain": "list_price", "source": "涨到 $29.99 后回调。Essential $9.99 / Premium $14.99 / Ultimate $22.99"},
    {"fy": 2026, "line": "cloud", "sku": "Azure", "price_usd_mo": None, "grain": "none", "note": "按用量计价，10-K 和价目表都没有单一「Azure 单价」。"},
    {"fy": 2026, "line": "windows", "sku": "Windows OEM", "price_usd_mo": None, "grain": "none", "note": "OEM 授权价按机型/地区合同走，10-K 不披露单价。"},
]

SHARE = [
    {"fy": 2016, "line": "windows", "name": "全球桌面 OS 流量份额", "value": 83, "unit": "%", "grain": "third_party", "source": "Statcounter 量级（流量≠装机）"},
    {"fy": 2018, "line": "windows", "name": "全球桌面 OS 流量份额", "value": 77, "unit": "%", "grain": "third_party", "source": "Statcounter"},
    {"fy": 2020, "line": "windows", "name": "全球桌面 OS 流量份额", "value": 77, "unit": "%", "grain": "third_party", "source": "Statcounter"},
    {"fy": 2022, "line": "windows", "name": "全球桌面 OS 流量份额", "value": 75, "unit": "%", "grain": "third_party", "source": "Statcounter"},
    {"fy": 2024, "line": "windows", "name": "全球桌面 OS 流量份额", "value": 73, "unit": "%", "grain": "third_party", "source": "Statcounter"},
    {"fy": 2025, "line": "windows", "name": "全球桌面 OS 流量份额", "value": 72, "unit": "%", "grain": "third_party", "source": "Statcounter 2025 初"},
    {"fy": 2026, "line": "windows", "name": "全球桌面 OS 流量份额", "value": 62.7, "unit": "%", "grain": "third_party", "source": "Statcounter 2026-08。Unknown 升高，真实 Windows 可能被低估"},
    {"fy": 2018, "line": "cloud", "name": "云基础设施份额", "value": 13, "unit": "%", "grain": "third_party", "source": "Synergy 量级"},
    {"fy": 2020, "line": "cloud", "name": "云基础设施份额", "value": 19, "unit": "%", "grain": "third_party", "source": "Synergy"},
    {"fy": 2022, "line": "cloud", "name": "云基础设施份额", "value": 23, "unit": "%", "grain": "third_party", "source": "Synergy"},
    {"fy": 2024, "line": "cloud", "name": "云基础设施份额", "value": 21, "unit": "%", "grain": "third_party", "source": "Synergy"},
    {"fy": 2025, "line": "cloud", "name": "云基础设施份额", "value": 21, "unit": "%", "grain": "third_party", "source": "Synergy Q4 2025"},
    {"fy": 2026, "line": "cloud", "name": "云基础设施份额", "value": 20, "unit": "%", "grain": "third_party", "source": "Synergy 2026 Q2：AWS 28%、Azure 20%、Google 15%"},
    {"fy": 2016, "line": "search", "name": "全球搜索流量份额", "value": 3, "unit": "%", "grain": "third_party", "source": "Statcounter 量级"},
    {"fy": 2020, "line": "search", "name": "全球搜索流量份额", "value": 3, "unit": "%", "grain": "third_party", "source": "Statcounter"},
    {"fy": 2024, "line": "search", "name": "全球搜索流量份额", "value": 4, "unit": "%", "grain": "third_party", "source": "Statcounter"},
    {"fy": 2026, "line": "search", "name": "全球搜索流量份额", "value": 4.3, "unit": "%", "grain": "third_party", "source": "Statcounter 2026-07，Google 约 91%"},
]

IMPLIED_ARPU = [
    {
        "fy": 2024,
        "line": "office",
        "seats_m": 400,
        "revenue_usd_m": 76969,
        "usd_per_year": 192,
        "usd_per_month": 16.0,
        "grain": "derived",
        "note": "FY2024 Microsoft 365 商业营收 769.69 亿 / 约 4.00 亿席位。是混合 ARPU，含 E5 和 F 系列，不是 E3 标价。",
    },
    {
        "fy": 2026,
        "line": "office",
        "seats_m": 450,
        "revenue_usd_m": 101997,
        "usd_per_year": 227,
        "usd_per_month": 18.9,
        "grain": "derived",
        "note": "FY2026 商业营收 1020 亿 / Q2「超过 4.50 亿」席位。若年席用 4.64 亿粗算则约 $18.3/月。10-K 只说 ARPU 被 Copilot 和 E5 拉高，不给美元。",
    },
]


def _money_yi(usd_m: float) -> str:
    yi = usd_m / 100.0
    if yi >= 10:
        return f"{yi:.0f} 亿美元"
    return f"{yi:.1f} 亿美元"


def enrich(catalog: dict) -> dict:
    catalog = dict(catalog)
    catalog["as_of"] = "2026-09-07"
    catalog["note"] = (
        "年报能核对的最细营业利润仍是分部：2006–2013 五条线，2016 起三条。"
        "Windows / Azure / Xbox / Copilot 仍然没有单品营业利润。"
        "但 10-K 产品表、业绩会席位/用户、以及 Statcounter / Synergy 等网上口径，可以把产品规模补到比分部更细。"
        "网上数字全部标来源：company / earnings / 10k / third_party / derived / estimate。推算不当成年报。"
    )
    catalog["method"] = catalog["note"]
    catalog["offerings"] = {
        "unit": "USD millions",
        "note": (
            "来源：各年 10-K「Revenue classified by significant product and service offerings」。"
            "FY2024 改过分类：Office 拆成商业/消费，Windows 与设备合并，Gaming 改称 Xbox。"
            "Dynamics 在 FY2023 重述里才从 Other 拆出。相邻年不完全可比。"
            "Azure 全年美元不是这条表的独立行，FY2025–FY2026 另列，且 nested，不计入合计。"
        ),
        "years": OFFERINGS,
    }
    catalog["microsoft_cloud"] = {
        "unit": "USD millions",
        "note": (
            "10-K 脚注里的 Microsoft Cloud：Azure 及其他云、Microsoft 365 商业云、"
            "LinkedIn 商业部分、Dynamics 365。FY2016 还是「商业云」、口径更窄。"
            "这是组合营收，不是 Azure 单品，也没有组合营业利润。"
        ),
        "years": MICROSOFT_CLOUD,
    }
    catalog["azure"] = {
        "unit": "USD millions",
        "note": "FY2025 以前只给 Azure 增速。营业利润始终不单列。",
        "years": AZURE,
    }
    catalog["xbox_split"] = {
        "unit": "USD millions",
        "note": (
            "内容与服务 vs 硬件来自季度业绩拆解汇总，不是 10-K 营业利润。"
            "FY2024 起含 Activision。FY2026 硬件按 -29% 倒推。"
        ),
        "years": XBOX_SPLIT,
    }
    catalog["web_metrics"] = {
        "note": "年报利润表没有的规模：席位、份额、订阅、用户、第三方估算。",
        "metrics": WEB_METRICS,
    }
    catalog["operating"] = {
        "note": (
            "三张年表：份额、订阅/席位、单价。"
            "10-K 真正按年给的是席位/订阅增速和「ARPU 上升」这种叙事，很少给绝对席位，几乎从不给美元单价或市场份额表。"
            "绝对席位来自业绩会里程碑；单价来自公开价目表；份额来自 Statcounter / Synergy。"
            "没有的年份留空，不编造。"
        ),
        "seat_growth": SEAT_GROWTH,
        "seats": SEATS,
        "prices": PRICES,
        "share": SHARE,
        "implied_arpu": IMPLIED_ARPU,
    }
    cloud_line = catalog["lines"]["cloud"]
    cloud_line["profit_grain"] = (
        "2006–2013 为 Server and Tools 分部营业利润。2016 年起为智能云。"
        "Azure 没有单独营业利润。FY2025 公司第一次给出 Azure 全年 750 亿美元；"
        "FY2026 后续披露约 1019 亿美元，利润仍含在智能云 570 亿里。"
        "云基础设施份额看 Synergy，不看年报。"
    )
    gaming_line = catalog["lines"]["gaming"]
    gaming_line["profit_grain"] = (
        "2006–2013 为 Entertainment and Devices 分部营业利润。"
        "2016 年起游戏利润并进「更多个人计算」。年报给 Xbox 营收；"
        "内容与服务 vs 硬件要自己从季度稿加总。Game Pass 订阅公司 2024-02 以后不再报。"
    )
    windows_line = catalog["lines"]["windows"]
    windows_line["profit_grain"] = (
        "2006–2013 为 Client / Windows 分部营业利润。2016 年起并进「更多个人计算」。"
        "FY2024 起 10-K 把 Windows 与设备并成一行。桌面份额来自 Statcounter，不是装机普查。"
    )
    search_line = catalog["lines"]["search"]
    search_line["profit_grain"] = (
        "2006–2013 为 Online Services 分部营业利润，多数年份亏损。"
        "2016 年起并进「更多个人计算」，年报只再披露搜索广告营收。"
        "全球搜索份额看 Statcounter：Bing 仍在 4% 上下。"
    )
    office_line = catalog["lines"]["office"]
    office_line["profit_grain"] = (
        "2006–2013 为 Microsoft Business Division。2016 年起为生产力与业务流程。"
        "这是分部利润，不是 PowerPoint / Teams / Copilot 单品。"
        "Copilot 付费席位、M365 商业席位来自业绩会；Copilot 营收年报不披露。"
    )
    devices_line = catalog["lines"]["devices"]
    devices_line["profit_grain"] = (
        "年报几乎没有 Surface 单独营业利润。FY2016–FY2023 10-K 有 Devices 营收行；"
        "FY2024 起并进 Windows 与设备。诺基亚减记打进 FY2015 公司利润表。"
    )
    extras = {
        "2024": [
            {"id": "enterprise", "name": "企业与合作伙伴服务", "revenue": 7594, "line": "cloud", "oi": None},
            {"id": "other", "name": "其他", "revenue": 45, "line": "company", "oi": None},
        ],
        "2025": [
            {"id": "azure", "name": "Azure（公司首次全年美元）", "revenue": 75000, "line": "cloud", "oi": None, "nested": True},
            {"id": "enterprise", "name": "企业与合作伙伴服务", "revenue": 7760, "line": "cloud", "oi": None},
            {"id": "other", "name": "其他", "revenue": 72, "line": "company", "oi": None},
        ],
        "2026": [
            {"id": "azure", "name": "Azure（后续披露全年美元）", "revenue": 101900, "line": "cloud", "oi": None, "nested": True},
            {"id": "enterprise", "name": "企业与合作伙伴服务", "revenue": 8260, "line": "cloud", "oi": None},
            {"id": "other", "name": "其他", "revenue": 109, "line": "company", "oi": None},
        ],
    }

    def _merge_items(rows, extra):
        by_id = {r["id"]: i for i, r in enumerate(rows)}
        out = list(rows)
        for item in extra:
            if item["id"] in by_id:
                out[by_id[item["id"]]] = item
                continue
            if item["id"] == "azure":
                placed = False
                new = []
                for row in out:
                    new.append(row)
                    if row["id"] == "server_cloud":
                        new.append(item)
                        placed = True
                out = new if placed else out + [item]
                by_id = {r["id"]: i for i, r in enumerate(out)}
            else:
                out.append(item)
                by_id[item["id"]] = len(out) - 1
        return out

    for year, extra in extras.items():
        catalog["product_revenue"][year] = _merge_items(
            catalog["product_revenue"][year], extra
        )
    return catalog


def metrics_for(line_id: str) -> list[dict]:
    return [m for m in WEB_METRICS if m["line"] == line_id]


def offering_for(line_id: str, fy: int) -> list[dict]:
    years = {row["fy"]: row for row in OFFERINGS}
    row = years.get(fy) or years.get(2026)
    return [item for item in row["items"] if item.get("line") == line_id and not item.get("nested")]


def main() -> None:
    catalog = json.loads(LINES_PATH.read_text(encoding="utf-8"))
    catalog = enrich(catalog)
    LINES_PATH.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("wrote", LINES_PATH, "metrics", len(WEB_METRICS), "offerings", len(OFFERINGS))


if __name__ == "__main__":
    main()
