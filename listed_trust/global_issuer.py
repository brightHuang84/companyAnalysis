"""Overseas-generic issuer analysis: events first, filings second.

This is the market-agnostic layer. China A-share CNINFO ingest remains
optional. A US/EU issuer is scored from:

- regulator filings (SEC 8-K/10-K, EU decisions)
- product and project milestones
- independent market feedback
- how the company responded
- labor, security, consumer, and board conduct

Financial statements corroborate claims. They are not the primary object.
"""

from __future__ import annotations

EVENT_TYPES = {
    "product_project": "新产品/重大项目及进展",
    "market_feedback": "产品市场与用户反馈",
    "company_response": "公司处置与纠偏",
    "m_and_a": "并购与联盟",
    "regulatory": "监管与诉讼",
    "security": "安全与隐私事故",
    "labor": "员工与组织",
    "leadership": "董事会与管理层",
    "capital": "资本开支与股东回报",
}

STAKEHOLDERS = {
    "employees": "员工",
    "consumers": "消费者",
    "users": "用户/租户",
    "partners": "开发者与合作方",
    "regulators": "监管",
    "shareholders": "股东",
}

SOURCES = {
    "US": ["SEC EDGAR 10-K/10-Q/8-K/DEF 14A", "earnings release", "DOJ/FTC", "CISA"],
    "EU": ["Commission decisions", "DMA/DSA", "national CNIL/ICO"],
    "global": ["company press", "independent trade press", "court dockets"],
}

# Required fields on every material event. Causal "why" is never auto-true.
EVENT_ANALYSIS_FIELDS = {
    "background": "当时背景：市场、技术、监管、公司内部约束",
    "why": "决策原因：公开口径与可核对事实",
    "why_note": "原因核验：公开记录 / 部分推断 / 未核实",
    "options": "决策目录-备选：当时公开可辨认的几条路",
    "decisions": "决策目录-实选：实际拍板的可执行条目",
    "effect_near": "近端效果：一年内市场与监管反应",
    "effect_far": "最终效果：后续产品、账本、承诺是否对上",
    "grade": "效果判定：兑现 / 部分兑现 / 未兑现 / 被强制修正 / 中性 / 外部冲击",
}
