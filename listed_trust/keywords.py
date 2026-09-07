"""Map filing and announcement language onto the seven analysis dimensions."""

from __future__ import annotations

from dataclasses import dataclass

DIMENSIONS = (
    "business_model",
    "conduct",
    "board",
    "culture",
    "employees",
    "consumers",
    "users",
)

DIMENSION_LABELS = {
    "business_model": "经营模式",
    "conduct": "行为准则",
    "board": "董事会行为",
    "culture": "管理文化",
    "employees": "对待员工",
    "consumers": "对待消费者",
    "users": "对待用户",
}

PLATFORM_HINTS = (
    "互联网",
    "电子商务",
    "在线",
    "平台",
    "软件",
    "信息科技",
    "数据服务",
    "云计算",
    "网络游戏",
    "社交",
    "APP",
    "移动应用",
    "网络科技",
)


@dataclass(frozen=True)
class TitleRule:
    dimension: str
    severity: str  # red | watch | green
    delta: float
    patterns: tuple[str, ...]
    label: str


# More specific phrases first. First match wins per title.
TITLE_RULES: tuple[TitleRule, ...] = (
    TitleRule("conduct", "red", -18, ("立案调查", "立案告知", "被立案"), "监管立案"),
    TitleRule("conduct", "red", -16, ("行政处罚", "行政监管措施", "监管措施决定"), "行政处罚/监管措施"),
    TitleRule("conduct", "red", -14, ("公开谴责", "通报批评"), "交易所纪律处分"),
    TitleRule("conduct", "red", -14, ("虚假陈述", "信息披露违法", "欺诈发行"), "信息披露违法"),
    TitleRule("conduct", "red", -12, ("警示函",), "监管警示函"),
    TitleRule("conduct", "red", -12, ("承诺未履行", "未能履行承诺", "违反承诺"), "承诺未履行"),
    TitleRule("conduct", "red", -10, ("违规减持", "超比例减持"), "违规减持"),
    TitleRule("conduct", "watch", -6, ("问询函", "监管工作函"), "监管问询"),
    TitleRule("conduct", "watch", -5, ("关注函",), "监管关注函"),
    TitleRule("conduct", "watch", -4, ("退市风险警示", "可能被实施退市", "*ST"), "退市风险"),
    TitleRule("conduct", "green", 4, ("承诺履行完毕", "完成承诺", "履行承诺的进展"), "承诺履行"),
    TitleRule("culture", "red", -12, ("无法表示意见", "否定意见", "拒绝表示意见"), "非标审计意见"),
    TitleRule("culture", "red", -10, ("保留意见",), "保留意见"),
    TitleRule("culture", "watch", -8, ("持续经营重大不确定性", "带强调事项段的无保留", "带有持续经营"), "持续经营不确定性"),
    TitleRule("culture", "red", -12, ("会计差错更正", "前期差错", "追溯重述", "财务重述"), "会计差错/重述"),
    TitleRule("culture", "watch", -3, ("更换会计师事务所", "变更会计师事务所", "解聘会计师"), "更换审计机构"),
    TitleRule("culture", "red", -12, ("内部控制否定意见", "内控否定", "财务报告内部控制重大缺陷", "非财务报告内部控制重大缺陷"), "内控重大缺陷"),
    TitleRule("culture", "green", 3, ("标准无保留意见", "内部控制审计报告（标准）"), "标准审计意见"),
    TitleRule("board", "red", -10, ("实控人变更", "实际控制人发生变更", "控股股东变更"), "控制权变更"),
    TitleRule("board", "watch", -5, ("董事长辞职", "董事长辞任", "董事长变动"), "董事长变动"),
    TitleRule("board", "watch", -4, ("独立董事辞职", "独立董事辞任", "独董辞职"), "独董辞职"),
    TitleRule("board", "watch", -3, ("董事辞职", "董事辞任", "监事辞职", "高管辞职", "总经理辞"), "董监高辞职"),
    TitleRule("board", "watch", -4, ("股权质押", "股票质押", "补充质押"), "股权质押"),
    TitleRule("board", "watch", -5, ("股东借款", "财务资助", "关联担保", "提供担保暨关联"), "关联融资/担保"),
    TitleRule("board", "green", 4, ("股权激励", "限制性股票激励", "股票期权激励"), "股权激励"),
    TitleRule("board", "green", 5, ("控股股东增持", "实际控制人增持", "董事增持", "高管增持"), "内部人增持"),
    TitleRule("board", "watch", -4, ("控股股东减持", "实际控制人减持", "董事减持", "高管减持"), "内部人减持"),
    TitleRule("business_model", "watch", -5, ("经营范围变更", "变更经营范围"), "经营范围变更"),
    TitleRule("business_model", "watch", -4, ("战略转型", "出售资产", "剥离", "终止经营"), "业务收缩/转型"),
    TitleRule("business_model", "watch", -4, ("重大资产重组",), "重大重组"),
    TitleRule("business_model", "green", 3, ("重大合同", "中标", "日常经营重大合同"), "重大经营合同"),
    TitleRule("employees", "green", 5, ("员工持股计划", "职工持股"), "员工持股"),
    TitleRule("employees", "watch", -8, ("拖欠工资", "劳动仲裁", "劳务纠纷", "裁员"), "劳动争议/裁员"),
    TitleRule("employees", "watch", -6, ("安全生产事故", "工伤", "安全事故"), "安全生产"),
    TitleRule("employees", "green", 3, ("集体合同", "员工培训"), "员工制度"),
    TitleRule("consumers", "red", -14, ("产品召回", "主动召回", "责令召回"), "产品召回"),
    TitleRule("consumers", "red", -12, ("虚假宣传", "广告违法", "消费欺诈"), "消费欺诈/虚假宣传"),
    TitleRule("consumers", "watch", -8, ("质量问题", "食品安全", "不合格", "缺陷产品"), "质量/安全问题"),
    TitleRule("consumers", "watch", -5, ("消费者投诉", "3·15", "315"), "消费者投诉"),
    TitleRule("users", "red", -14, ("数据泄露", "个人信息泄露", "网络安全事件"), "数据/网络安全事件"),
    TitleRule("users", "watch", -8, ("个人信息保护", "隐私政策", "App违法", "APP违法"), "用户数据合规"),
    TitleRule("users", "watch", -6, ("数据安全", "网络安全审查"), "数据安全审查"),
)


def classify_title(title: str) -> TitleRule | None:
    text = title or ""
    for rule in TITLE_RULES:
        for pattern in rule.patterns:
            if pattern not in text:
                continue
            if pattern == "保留意见" and "无保留" in text:
                continue
            return rule
    return None


def looks_like_platform(business_text: str) -> bool:
    text = business_text or ""
    return any(h in text for h in PLATFORM_HINTS)
