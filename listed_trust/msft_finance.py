"""Attach FY financial context and decision-return fields to Microsoft events."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "data" / "issuers" / "MSFT"
FY_PATH = ROOT / "financials_fy.json"
LINES_PATH = ROOT / "product_lines.json"

RETURN_TONE = {
    "高回报": "success",
    "正回报": "success",
    "部分回收": "info",
    "减值收场": "danger",
    "战略未兑现": "danger",
    "监管成本": "warning",
    "中性": "neutral",
    "未核实": "warning",
}

# Same order as events_1986_2026.json. date is a checksum.
OVERLAYS: list[dict] = [
    {
        "date": "1986-02",
        "product": "雷德蒙德总部",
        "outlay_kind": "资本开支（未单列）",
        "outlay_usd_m": None,
        "outlay_text": "园区造价未在招股材料里单列成一项可核对的产品投资。",
        "return_grade": "中性",
        "return_summary": "这是产能和治理基础设施，不是产品利润中心。上市当年公司营收 1.98 亿美元、研发约 1100 万美元、营业利润率约 31%。校园本身不产生回报率，只降低后来的扩张摩擦。",
    },
    {
        "date": "1986-03-13",
        "product": "公众公司资本结构",
        "outlay_kind": "股权融资（流入）",
        "outlay_usd_m": 61,
        "outlay_text": "IPO 融资约 6100 万美元（流入，不是费用）。",
        "return_grade": "正回报",
        "return_summary": "融资金额相对后来的微软很小，换到的是期权定价、并购货币和披露纪律。FY1986 净利率约 20%。上市本身兑现了资本目标；产品垄断是 1990 年代 Windows/Office 做出来的，不能记在 IPO 账上。",
    },
    {
        "date": "1987-04-02",
        "product": "OS/2（对冲 Windows）",
        "outlay_kind": "公司研发（当年）",
        "outlay_usd_m": None,
        "outlay_text": "与 IBM 的联合开发费用未单列。",
        "return_grade": "战略未兑现",
        "return_summary": "FY1987 公司研发 3800 万美元，约占营收 11%。OS/2 没有成为企业标准，投入被 Windows 线吸收。财务上这是一次失败的平台押注，但对冲让微软没有把全部研发绑在 IBM 日程上。",
    },
    {
        "date": "1987-07",
        "product": "PowerPoint / Office",
        "outlay_kind": "并购对价",
        "outlay_usd_m": 14,
        "outlay_text": "收购 Forethought 对价约 1400 万美元（当时报道口径）。",
        "return_grade": "高回报",
        "return_summary": "对价约 FY1988 公司研发 7000 万美元的两成、营收 5.91 亿美元的 2%。PowerPoint 补齐套装第三件，Office 后来成为比 Windows 更稳的利润中心。FY2026 生产力与业务流程分部营业利润 839 亿美元。按已披露对价，这是四十年里回报倍数最高的并购之一。",
    },
    {
        "date": "1987-12-09",
        "product": "Windows 2.0",
        "outlay_kind": "公司研发（当年）",
        "outlay_usd_m": None,
        "outlay_text": "Windows 单品研发未单列。",
        "return_grade": "部分回收",
        "return_summary": "FY1988 研发 7000 万美元、营业利润率约 32%。2.0 自己没有打开图形界面市场，真正的财务爆发在 3.0。作为迭代费用，被 1990 年之后的授权收入覆盖。",
    },
    {
        "date": "1988-03",
        "product": "Windows 图形界面（诉讼）",
        "outlay_kind": "法律费用（未单列）",
        "outlay_usd_m": None,
        "outlay_text": "应诉费用未在年报单列。",
        "return_grade": "正回报",
        "return_summary": "法律开支相对后来的桌面垄断租金很小。胜诉去掉外观专利墙，让 3.0/95 的高毛利授权能继续卖。这是用诉讼成本保护软件利润池。",
    },
    {
        "date": "1990-05-22",
        "product": "Windows 3.0",
        "outlay_kind": "公司研发（当年）",
        "outlay_usd_m": None,
        "outlay_text": "3.0 单品研发未单列。",
        "return_grade": "高回报",
        "return_summary": "FY1990 营收 11.8 亿美元、研发 1.81 亿、营业利润率约 33%、净利率约 24%。3.0 把图形 PC 做成规模市场，后续 Office、IE、反垄断都建立在这次装机量上。公司没有披露 3.0 开发成本，但此后十年的利润跃迁对得上这条产品线。",
    },
    {
        "date": "1990-06",
        "product": "桌面垄断（监管）",
        "outlay_kind": "监管应对",
        "outlay_usd_m": None,
        "outlay_text": "FTC 调查本身无罚金。",
        "return_grade": "监管成本",
        "return_summary": "调查没有立刻改利润表。财务含义是：高利润率开始变成可被起诉的对象。当时净利率约 24%，已经高于普通工业公司，这是后来司法部案的经济背景。",
    },
    {
        "date": "1990-11-19",
        "product": "Office 套装",
        "outlay_kind": "公司研发（当年）",
        "outlay_usd_m": None,
        "outlay_text": "套装是定价与捆绑，不是一笔新的资本开支。",
        "return_grade": "高回报",
        "return_summary": "把已有 Word/Excel/PowerPoint 捆成套装价，边际开发成本低、对单一产品对手的杀伤高。FY2026 该分部营业利润率约 60%。这是四十年里最干净的定价权决策之一。",
    },
    {
        "date": "1991-09",
        "product": "Microsoft Research",
        "outlay_kind": "公司研发（编制）",
        "outlay_usd_m": None,
        "outlay_text": "实验室预算含在公司研发里，未单列。",
        "return_grade": "中性",
        "return_summary": "FY1991 研发 2.35 亿美元，约占营收 13%。研究院是用桌面利润养长期题目，不按项目回收。财务上是费用中心；战略上对冲产品部门短周期。不能记成产品回报。",
    },
    {
        "date": "1992-04-06",
        "product": "Windows 3.1",
        "outlay_kind": "公司研发（当年）",
        "outlay_usd_m": None,
        "outlay_text": "3.1 单品研发未单列。",
        "return_grade": "高回报",
        "return_summary": "FY1992 营收 27.6 亿美元、净利率约 26%。3.1 巩固 3.0 的授权机器，开发费用被已经铺开的 OEM 合同摊薄。",
    },
    {
        "date": "1993-07-27",
        "product": "Windows NT / 企业服务器",
        "outlay_kind": "公司研发（当年）",
        "outlay_usd_m": None,
        "outlay_text": "NT 内核工程未单列；当年公司研发 4.70 亿美元。",
        "return_grade": "高回报",
        "return_summary": "FY1993 研发占营收约 13%，营业利润率约 35%。NT 当时不赚钱，但是后来服务器、Active Directory、Azure 的祖先。按近端产品收入未兑现；按四十年企业利润池，这是最大的长周期正回报之一。",
    },
    {
        "date": "1994-07",
        "product": "Windows 授权（同意令）",
        "outlay_kind": "监管约束",
        "outlay_usd_m": None,
        "outlay_text": "同意令没有罚款，限制的是合同捆绑。",
        "return_grade": "监管成本",
        "return_summary": "纸面限制几乎没改利润率：FY1994 营业利润率约 37%。公司改走技术集成。财务上这是用法律成本换时间，IE 捆绑的利润后来被 1998 年大案部分吐回。",
    },
    {
        "date": "1995-08-24",
        "product": "Windows 95 / Internet Explorer",
        "outlay_kind": "公司研发（当年）",
        "outlay_usd_m": None,
        "outlay_text": "Win95 与 IE 单品研发未单列；当年公司研发 8.60 亿美元。",
        "return_grade": "高回报",
        "return_summary": "FY1995 营收 59.4 亿美元、毛利率约 85%、营业利润率约 34%。消费 PC 换代带来授权量跃迁；IE 零价格捆绑赢了浏览器份额。商业上高回报，监管或有负债在 1998–2001 年兑现为诉讼与行为救济，不是一次性减值。",
    },
    {
        "date": "1995-12-15",
        "product": "MSNBC / 消费媒体",
        "outlay_kind": "合资出资（未单列总额）",
        "outlay_usd_m": None,
        "outlay_text": "合资出资与后续退出对价未在本台账核到完整现金流。",
        "return_grade": "战略未兑现",
        "return_summary": "FY1995 净利率约 24%，公司有利润养媒体实验。MSNBC 没有成为利润中心，微软后来退出新闻合资。按「客厅入口」未兑现；对当年利润表冲击有限。",
    },
    {
        "date": "1997-08-06",
        "product": "Office for Mac / IE on Mac",
        "outlay_kind": "战略投资",
        "outlay_usd_m": 150,
        "outlay_text": "向苹果投资 1.5 亿美元。",
        "return_grade": "部分回收",
        "return_summary": "1.5 亿大约是 FY1997 净利润 34.5 亿的 4%。近端保住 Mac Office 溢价和 IE 默认位置；远端苹果活下来后用 iPhone 拿走移动。按现金金额很小、按平台对冲最终反噬。",
    },
    {
        "date": "1997-12-31",
        "product": "Hotmail / 消费身份",
        "outlay_kind": "并购对价",
        "outlay_usd_m": 400,
        "outlay_text": "收购 Hotmail 约 4 亿美元。",
        "return_grade": "部分回收",
        "return_summary": "对价约当年净利润的 12%。买到用户和身份，没有买到消费互联网利润中心。品牌后来并入 Outlook。按用户数兑现，按利润率未兑现。",
    },
    {
        "date": "1998-05-18",
        "product": "Windows + IE 捆绑",
        "outlay_kind": "监管诉讼",
        "outlay_usd_m": None,
        "outlay_text": "美国案以行为救济为主，不是欧式巨额罚金。",
        "return_grade": "监管成本",
        "return_summary": "FY1998 营业利润率约 46%。诉讼费和合规是维持桌面利润池的成本。公司没有被拆分，Office 与 Windows 继续同一张利润表，这是本案最大的财务结果。",
    },
    {
        "date": "1998-06-25",
        "product": "Windows 98",
        "outlay_kind": "公司研发（当年）",
        "outlay_usd_m": None,
        "outlay_text": "98 单品研发未单列。",
        "return_grade": "高回报",
        "return_summary": "把 IE 绑得更深，延长 95 的授权周期。FY1998 营收 145 亿美元、净利率约 31%。产品利润兑现；同一捆绑成为司法部核心事实。",
    },
    {
        "date": "1999-11-05",
        "product": "操作系统垄断（事实认定）",
        "outlay_kind": "监管诉讼",
        "outlay_usd_m": None,
        "outlay_text": "事实认定不是罚单。",
        "return_grade": "监管成本",
        "return_summary": "FY1999 营业利润约 100 亿美元、利润率约 51%，是软件垄断租金的高峰。认定本身不改当年利润，但把「高利润 = 可拆分」写成法庭事实。",
    },
    {
        "date": "2000-01-13",
        "product": "管理层交接",
        "outlay_kind": "无单列现金",
        "outlay_usd_m": None,
        "outlay_text": "CEO 交接不是资本开支。",
        "return_grade": "中性",
        "return_summary": "FY2000 营收 230 亿美元、营业利润率约 48%。鲍尔默时期做成了企业协议和 Xbox 入场，也留下搜索、手机、广告并购的减值。财务评价要看后续项目，不看这一天。",
    },
    {
        "date": "2000-02-17",
        "product": "Windows 2000",
        "outlay_kind": "公司研发（当年）",
        "outlay_usd_m": None,
        "outlay_text": "NT 5.0 工程未单列；当年研发 37.8 亿美元。",
        "return_grade": "高回报",
        "return_summary": "企业目录和服务器许可把高毛利从消费升级周期改成多年合同。这是后来商业云的利润模板。",
    },
    {
        "date": "2000-04-03",
        "product": "公司完整性（谢尔曼法）",
        "outlay_kind": "监管诉讼",
        "outlay_usd_m": None,
        "outlay_text": "违法认定不是罚款。",
        "return_grade": "监管成本",
        "return_summary": "若拆分令生效，Office 与 Windows 变成对手，四十年后的套件捆绑利润不会存在。保住一体化是本案对股东最大的财务事件。",
    },
    {
        "date": "2000-06-07",
        "product": "公司完整性（拆分令）",
        "outlay_kind": "监管诉讼",
        "outlay_usd_m": None,
        "outlay_text": "初审拆分令后来被推翻。",
        "return_grade": "正回报",
        "return_summary": "上诉成功保住同一张利润表。财务上等于避免了强制分拆高利润产品线。诉讼费用相对拆分损失可以忽略。",
    },
    {
        "date": "2000-09-14",
        "product": "Windows ME",
        "outlay_kind": "公司研发（当年）",
        "outlay_usd_m": None,
        "outlay_text": "ME 单品研发未单列。",
        "return_grade": "战略未兑现",
        "return_summary": "消费线最后一次叠在 9x 内核上，口碑差、生命周期短。开发费用被 XP 迅速替代，属于沉没的代际浪费，金额无法从年报拆出。",
    },
    {
        "date": "2001-09-06",
        "product": "公司完整性（不再拆分）",
        "outlay_kind": "监管结果",
        "outlay_usd_m": None,
        "outlay_text": "司法部改行为救济，无拆分、无欧式罚金。",
        "return_grade": "正回报",
        "return_summary": "美国路径用行为救济换公司完整。相对欧盟后来累计超过 20 亿欧元的罚金，美国案对利润表更便宜，对捆绑结构更宽松。",
    },
    {
        "date": "2001-10-25",
        "product": "Windows XP",
        "outlay_kind": "公司研发（当年）",
        "outlay_usd_m": None,
        "outlay_text": "XP 单品研发未单列；FY2002 研发 43.1 亿美元。",
        "return_grade": "高回报",
        "return_summary": "此后近十年桌面主力，摊薄 NT/2000 的工程成本。XP 延长周期本身就是高毛利授权的折旧机器。",
    },
    {
        "date": "2001-11-02",
        "product": "Windows 捆绑（和解）",
        "outlay_kind": "监管和解",
        "outlay_usd_m": None,
        "outlay_text": "同意令要求分享 API、设监察组，不改捆绑代码。",
        "return_grade": "监管成本",
        "return_summary": "合规成本有限，产品利润结构基本不动。财务上是便宜的和解；后来欧盟证明：不改代码仍会被罚执行。",
    },
    {
        "date": "2001-11-15",
        "product": "Xbox",
        "outlay_kind": "硬件补贴 + 公司研发",
        "outlay_usd_m": None,
        "outlay_text": "主机按亏损价出货；首代开发与营销费用未在 10-K 单列成一条。",
        "return_grade": "部分回收",
        "return_summary": "入场费是多年硬件亏损，换内容平台。FY2026 更多个人计算分部营业利润 144 亿美元，但当季 Xbox 内容与服务 -10%。二十五年后仍不是公司利润引擎，也没有把游戏做成 Azure 那种回收曲线。",
    },
    {
        "date": "2002-11-01",
        "product": "Windows 捆绑（和解落地）",
        "outlay_kind": "监管和解",
        "outlay_usd_m": None,
        "outlay_text": "法院大体接受联邦和解。",
        "return_grade": "监管成本",
        "return_summary": "和解落地让 XP 周期的高利润继续进账。FY2002 营业利润率约 42%。",
    },
    {
        "date": "2004-03-24",
        "product": "Windows Media Player / 服务器互操作",
        "outlay_kind": "监管罚金",
        "outlay_usd_m": 610,
        "outlay_text": "4.972 亿欧元，约合 6.1 亿美元（按当时汇率约数）。",
        "return_grade": "监管成本",
        "return_summary": "罚金约 FY2004 净利润 82 亿美元的 7%。播放器没打赢 iPod/后来的流媒体；服务器互操作罚款买的是时间。钱吐了一部分垄断租金，产品线没有因此变成利润中心。",
    },
    {
        "date": "2005-11-22",
        "product": "Xbox 360",
        "outlay_kind": "硬件补贴 + 公司研发",
        "outlay_usd_m": None,
        "outlay_text": "360 开发与早期红灯返修成本未单列。",
        "return_grade": "部分回收",
        "return_summary": "FY2006 研发 65.8 亿美元。360 赢了那一代主机战争的一部分，硬件仍常按补贴卖。游戏至今不是高利润分部的主引擎。",
    },
    {
        "date": "2006-07",
        "product": "服务器互操作（未执行）",
        "outlay_kind": "监管罚金",
        "outlay_usd_m": 356,
        "outlay_text": "约 2.805 亿欧元，约合 3.6 亿美元。",
        "return_grade": "监管成本",
        "return_summary": "这是「承诺了却不执行」的罚金，不是产品投资。钱纯流出，没有对应资产。",
    },
    {
        "date": "2006-11-14",
        "product": "Zune",
        "outlay_kind": "公司研发（当年）",
        "outlay_usd_m": None,
        "outlay_text": "Zune 单品研发与存货未在 10-K 单列成可持续产品线。",
        "return_grade": "战略未兑现",
        "return_summary": "FY2007 研发 71.2 亿美元。Zune 没打过 iPod，后来停产。消费硬件窗口错过，费用沉没。",
    },
    {
        "date": "2007-01-30",
        "product": "Windows Vista",
        "outlay_kind": "公司研发（当年）",
        "outlay_usd_m": None,
        "outlay_text": "Vista 工程是当时最大的系统项目之一，费用未单列。",
        "return_grade": "战略未兑现",
        "return_summary": "FY2007 营收 511 亿美元、营业利润率约 36%。升级慢、口碑差，授权节奏被打断，直到 Windows 7 才修复。开发成本被拉长摊销，近端回报差。",
    },
    {
        "date": "2007-05-18",
        "product": "在线广告（aQuantive）",
        "outlay_kind": "并购对价",
        "outlay_usd_m": 6000,
        "outlay_text": "宣布约 60 亿美元收购 aQuantive。",
        "return_grade": "减值收场",
        "return_summary": "对价约 FY2007 净利润 141 亿美元的 43%。2012 年几乎全额减值约 62 亿美元。搜索广告未翻盘。这是鲍尔默时代最干净的财务失败之一。",
    },
    {
        "date": "2008-02-01",
        "product": "搜索 + 门户（雅虎）",
        "outlay_kind": "未成交出价",
        "outlay_usd_m": 44600,
        "outlay_text": "出价约 446 亿美元，交易未成。",
        "return_grade": "正回报",
        "return_summary": "未花钱本身就是财务结果：446 亿约为 FY2008 净利润 177 亿的 2.5 倍。后来搜索仍没翻盘，说明这不是「买便宜了」，而是搜索窗口已经关上。躲开的是一笔更大的可能减值。",
    },
    {
        "date": "2008-02-27",
        "product": "互操作承诺（定期罚金）",
        "outlay_kind": "监管罚金",
        "outlay_usd_m": 1270,
        "outlay_text": "定期罚金 8.99 亿欧元，后减至 8.60 亿，约合 12.7 亿美元。",
        "return_grade": "监管成本",
        "return_summary": "约占 FY2008 净利润的 7%。纯合规失败成本，没有产品资产。",
    },
    {
        "date": "2008-06-27",
        "product": "管理层交接",
        "outlay_kind": "无单列现金",
        "outlay_usd_m": None,
        "outlay_text": "职务调整不是投资。",
        "return_grade": "中性",
        "return_summary": "FY2008 营业利润率约 37%。财务叙事仍由鲍尔默的并购与手机线主导，直到 2014 年。",
    },
    {
        "date": "2008-09-02",
        "product": "浏览器（IE vs Chrome）",
        "outlay_kind": "公司研发（浏览器）",
        "outlay_usd_m": None,
        "outlay_text": "IE 研发含在公司研发；无单独亏损科目。",
        "return_grade": "战略未兑现",
        "return_summary": "浏览器战争的装机优势此后被削。IE/Edge 没有成为独立利润中心，Windows 入口价值下降。",
    },
    {
        "date": "2009-05-28",
        "product": "Bing",
        "outlay_kind": "公司研发（当年）",
        "outlay_usd_m": None,
        "outlay_text": "搜索研发与流量获取成本未拆成 Bing 利润表。",
        "return_grade": "战略未兑现",
        "return_summary": "FY2009 研发 90.1 亿美元，约占营收 15%。Bing 后来有搜索广告利润贡献，但从未翻盘 Google。按「赢下搜索」未兑现；按「有一块广告毛利」只是部分回收。",
    },
    {
        "date": "2009-10-22",
        "product": "Windows 7",
        "outlay_kind": "公司研发（当年）",
        "outlay_usd_m": None,
        "outlay_text": "7 的工程是 Vista 之后的修复性发布。",
        "return_grade": "高回报",
        "return_summary": "修复升级意愿，恢复 OEM 授权节奏。FY2010 营业利润率回到约 39%。这是用一代产品把 Vista 沉没成本部分捞回。",
    },
    {
        "date": "2009-12",
        "product": "浏览器选择屏",
        "outlay_kind": "监管承诺",
        "outlay_usd_m": None,
        "outlay_text": "2009 年承诺本身无新罚金；2013 年违反后再罚。",
        "return_grade": "监管成本",
        "return_summary": "选择屏直接削弱 IE 默认税。财务损失是份额，不是当场罚单；2013 年把承诺失败变成 5.61 亿欧元现金流出。",
    },
    {
        "date": "2010-02-01",
        "product": "Azure / 智能云",
        "outlay_kind": "公司研发 + 后来的资本开支",
        "outlay_usd_m": None,
        "outlay_text": "2010 年商用时亏损；单年云研发未单列。FY2026 云资本开支 1159 亿美元。",
        "return_grade": "高回报",
        "return_summary": "FY2010 智能云还埋在服务器业务里，公司营业利润率约 39%。十六年后来：Azure 全年破 1000 亿美元，智能云营业利润 570 亿美元。这是四十年里回收期最长、金额最大的产品正回报。前期利润表看起来像费用，不能按前三年 ROI 否决。",
    },
    {
        "date": "2010-06",
        "product": "Kin 手机",
        "outlay_kind": "产品开发（未单列）",
        "outlay_usd_m": None,
        "outlay_text": "约 48 天停售；开发成本未在 10-K 单列。",
        "return_grade": "减值收场",
        "return_summary": "典型的短周期沉没成本。金额相对诺基亚减值很小，但模式相同：消费入口错过，用关停止损。",
    },
    {
        "date": "2010-11",
        "product": "Windows Phone",
        "outlay_kind": "公司研发（当年）",
        "outlay_usd_m": None,
        "outlay_text": "手机系统研发未单列。",
        "return_grade": "战略未兑现",
        "return_summary": "FY2011 研发 90.4 亿美元。系统晚于 iPhone/Android，后来靠买诺基亚硬件补，再减记。软件投入没有形成许可利润。",
    },
    {
        "date": "2011-02",
        "product": "Windows Phone + 诺基亚渠道",
        "outlay_kind": "联盟（预付/补贴未全披露）",
        "outlay_usd_m": None,
        "outlay_text": "对诺基亚的平台补贴与预付款未在本条核到完整总额。",
        "return_grade": "战略未兑现",
        "return_summary": "结盟是给即将失败的系统买渠道，财务结局写在 2015 年 76 亿美元减记里。",
    },
    {
        "date": "2011-05-10",
        "product": "Skype / 消费通信",
        "outlay_kind": "并购对价",
        "outlay_usd_m": 8500,
        "outlay_text": "85 亿美元现金。",
        "return_grade": "战略未兑现",
        "return_summary": "对价约 FY2011 净利润 232 亿美元的 37%。买到入口，养十四年，2025 年品牌杀掉并入 Teams。通信利润最终落在商业套件，不在 Skype 商标。按独立产品回报未兑现。",
    },
    {
        "date": "2012-10-26",
        "product": "Surface",
        "outlay_kind": "存货与硬件毛利",
        "outlay_usd_m": None,
        "outlay_text": "自有硬件资本与存货按年进入更多个人计算分部，未单列 Surface 利润表。",
        "return_grade": "部分回收",
        "return_summary": "RT 路线 2013 年减记 9 亿美元。后续 Pro/Laptop 活在 MPC 分部里，毛利率远低于软件。硬件保住了 Windows 设备叙事，不是高回报引擎。",
    },
    {
        "date": "2012-10-26",
        "product": "Windows 8",
        "outlay_kind": "公司研发（当年）",
        "outlay_usd_m": None,
        "outlay_text": "Win8 与 Surface 同日；系统工程未单列。FY2012 研发 98.1 亿美元。",
        "return_grade": "战略未兑现",
        "return_summary": "磁贴界面伤害桌面升级。FY2012 营业利润率因 aQuantive 减值掉到约 30%。Win8 没有恢复 Vista 之后那种授权跃迁，要等到 Win10。",
    },
    {
        "date": "2013-03-06",
        "product": "浏览器选择屏（违反承诺）",
        "outlay_kind": "监管罚金",
        "outlay_usd_m": 730,
        "outlay_text": "5.61 亿欧元，约合 7.3 亿美元。微软未上诉。",
        "return_grade": "监管成本",
        "return_summary": "约占 FY2013 净利润 219 亿美元的 3%。这是执行失败的现金流出，没有换到产品资产。",
    },
    {
        "date": "2013-07-18",
        "product": "Surface RT",
        "outlay_kind": "存货减记",
        "outlay_usd_m": 900,
        "outlay_text": "存货减记约 9 亿美元。",
        "return_grade": "减值收场",
        "return_summary": "一次性承认这代卖不掉。9 亿约 FY2013 净利润的 4%。止损干净，保护后续 Surface Pro 叙事。",
    },
    {
        "date": "2013-08-23",
        "product": "管理层交接",
        "outlay_kind": "无单列现金",
        "outlay_usd_m": None,
        "outlay_text": "退休公告不是投资。",
        "return_grade": "中性",
        "return_summary": "鲍尔默任内做成企业协议，留下广告、手机减值。财务换挡发生在纳德拉上任之后。",
    },
    {
        "date": "2013-09-02",
        "product": "诺基亚手机",
        "outlay_kind": "并购对价",
        "outlay_usd_m": 7200,
        "outlay_text": "宣布约 72 亿美元买诺基亚手机业务。",
        "return_grade": "减值收场",
        "return_summary": "对价约 FY2013 净利润的 33%。2015 年减记约 76 亿美元并裁员约 7800 人。手机利润从未出现。",
    },
    {
        "date": "2013-11-22",
        "product": "Xbox One",
        "outlay_kind": "硬件补贴 + 公司研发",
        "outlay_usd_m": None,
        "outlay_text": "主机仍按平台补贴模式。",
        "return_grade": "部分回收",
        "return_summary": "延续 Xbox 财务结构：硬件近零毛利，内容与服务才有利润。FY2026 内容与服务已经失血，说明这一代没有把游戏做成可独立支撑 687 亿美元并购的引擎。",
    },
    {
        "date": "2014-02-04",
        "product": "云优先战略",
        "outlay_kind": "战略转向（费用已在研发/资本开支）",
        "outlay_usd_m": None,
        "outlay_text": "人事任命本身无对价。",
        "return_grade": "高回报",
        "return_summary": "FY2014 营业利润率约 32%。之后十年：营收从 868 亿美元到 FY2026 的 3318 亿美元，营业利润率从约 32% 升到 47%。云与跨平台 Office 对得上数字；消费硬件与游戏并购对不上。",
    },
    {
        "date": "2014-03",
        "product": "Office 跨平台",
        "outlay_kind": "公司研发（当年）",
        "outlay_usd_m": None,
        "outlay_text": "iPad 版是把套件从 Windows 许可税改成席位订阅。",
        "return_grade": "高回报",
        "return_summary": "放弃「Office 只为 Windows 引流」，扩大可付费设备池。FY2026 生产力分部营收 1400 亿美元、营业利润率约 60%。这是纳德拉时期最清晰的产品利润决策。",
    },
    {
        "date": "2014-04-25",
        "product": "诺基亚设备与服务",
        "outlay_kind": "并购交割",
        "outlay_usd_m": 7200,
        "outlay_text": "交割同一笔约 72 亿美元交易。",
        "return_grade": "减值收场",
        "return_summary": "交割后一年内减记。现金已经出去，利润从未进来。",
    },
    {
        "date": "2014-09-15",
        "product": "Minecraft",
        "outlay_kind": "并购对价",
        "outlay_usd_m": 2500,
        "outlay_text": "25 亿美元收购 Mojang。",
        "return_grade": "高回报",
        "return_summary": "对价约 FY2014 净利润 221 亿美元的 11%。长生命周期内容，持续贡献游戏与社区，没有出现诺基亚式减记。相对 Activision 的 687 亿，这是游戏并购里少数对得上价格的。",
    },
    {
        "date": "2015",
        "product": "诺基亚手机业务",
        "outlay_kind": "商誉/资产减记",
        "outlay_usd_m": 7600,
        "outlay_text": "减记约 76 亿美元，裁员约 7800 人。",
        "return_grade": "减值收场",
        "books_role": "76 亿美元减记直接打进 FY2015 利润表。这一年营业利润率掉到约 19%、净利率约 13%，主因就是这笔诺基亚决策，不是无关的背景数字。",
        "return_summary": "FY2015 营业利润率掉到约 19%、净利率约 13%，主因就是这笔减记。手机战略的财务句号。",
    },
    {
        "date": "2015-07-29",
        "product": "Windows 10",
        "outlay_kind": "公司研发 + 免费升级（递延收入）",
        "outlay_usd_m": None,
        "outlay_text": "向 Win7/8.1 免费升级，近端让 OEM/升级收入递延。",
        "return_grade": "高回报",
        "return_summary": "FY2016 重述后营收 912 亿美元，低于 FY2015 的 936 亿，免费升级可见于报表。换到的是装机更新与后来的 365/云入口。按近端许可收入是让利；按平台续命是正回报。",
    },
    {
        "date": "2016-06-13",
        "product": "LinkedIn",
        "outlay_kind": "并购对价",
        "outlay_usd_m": 26200,
        "outlay_text": "262 亿美元。",
        "return_grade": "正回报",
        "return_summary": "对价约 FY2016 净利润 205 亿美元的 1.3 倍。FY2026 第四季 LinkedIn 营收仍 +12%，落在高利润的生产力分部。没有减记。回收期长，但资产还在产生订阅与广告。",
    },
    {
        "date": "2016-11-02",
        "product": "Teams / 365 协作",
        "outlay_kind": "公司研发（当年）",
        "outlay_usd_m": None,
        "outlay_text": "研发含在 Office 365；后来用套件捆绑铺量。",
        "return_grade": "高回报",
        "return_summary": "边际分发成本低，附着在已经高利润的 365 席位上。商业上是 Skype 收购真正的利润出口；监管上变成 2025 年欧盟拆绑。财务兑现，法律或有成本另计。",
    },
    {
        "date": "2018-06",
        "product": "GitHub / 开发者漏斗",
        "outlay_kind": "并购对价",
        "outlay_usd_m": 7500,
        "outlay_text": "75 亿美元。",
        "return_grade": "高回报",
        "return_summary": "对价约 FY2018 营业利润 351 亿美元的 21%。FY2026 业绩稿：GitHub Copilot 5000 万用户，开发者流向 Azure。没有减记。这是为云利润池买入口，不是为独立 SaaS 利润表。",
    },
    {
        "date": "2019",
        "product": "OpenAI / Azure AI",
        "outlay_kind": "战略投资（首笔）",
        "outlay_usd_m": None,
        "outlay_text": "2019 年起投；金额在后续合同里加码。首笔不是 2023 年媒体口径的 100 亿。",
        "return_grade": "部分回收",
        "return_summary": "早期支票相对当时利润表不大。真正的财务暴露在 2023 年加码和 FY2025–FY2026 的权益法损益：FY2025 投资亏损 36 亿美元、FY2026 净收益 50 亿美元（业绩稿非 GAAP 调节）。云增量对得上；排他后来被拆。",
    },
    {
        "date": "2020-06-26",
        "product": "实体零售",
        "outlay_kind": "关店止损",
        "outlay_usd_m": None,
        "outlay_text": "零售店是费用中心，关闭减少租金与编制。",
        "return_grade": "正回报",
        "return_summary": "软件/云公司开实体店很少赚到零售利润。关店是费用收缩，对毛利率和营业利润率是正贡献。",
    },
    {
        "date": "2020-08",
        "product": "TikTok 美国业务",
        "outlay_kind": "未成交洽购",
        "outlay_usd_m": None,
        "outlay_text": "交易未成，无交割对价。",
        "return_grade": "中性",
        "return_summary": "没有形成并购现金流出。也没有买到短视频消费入口。对利润表中性。",
    },
    {
        "date": "2020-11-10",
        "product": "Xbox Series X/S",
        "outlay_kind": "硬件补贴 + 公司研发",
        "outlay_usd_m": None,
        "outlay_text": "主机周期继续补贴。",
        "return_grade": "部分回收",
        "return_summary": "FY2021 更多个人计算仍有利润，但游戏没有改变公司利润结构。后续 Activision 天价与 2026 年内容收入下降，说明这代主机没有单独撑起游戏投资回报。",
    },
    {
        "date": "2020-12",
        "product": "云与身份安全",
        "outlay_kind": "事故成本（未单列）",
        "outlay_usd_m": None,
        "outlay_text": "SolarWinds 响应、客户赔偿与工程补丁未单列总额。",
        "return_grade": "中性",
        "return_summary": "安全事故是云订阅的负外部性。FY2020 营业利润率约 37%，账本仍强。不能用利润高证明安全投入足够。",
    },
    {
        "date": "2021-03",
        "product": "Exchange / 企业邮件",
        "outlay_kind": "事故成本（未单列）",
        "outlay_usd_m": None,
        "outlay_text": "Hafnium 补丁与响应费用未单列。",
        "return_grade": "中性",
        "return_summary": "企业邮件是高粘性许可，事故增加运维费用、不改分部利润结构。风险在信任，不在当年毛利率。",
    },
    {
        "date": "2021-04-12",
        "product": "Nuance / 医疗语音与 AI",
        "outlay_kind": "并购对价",
        "outlay_usd_m": 19700,
        "outlay_text": "约 197 亿美元。",
        "return_grade": "部分回收",
        "return_summary": "对价约 FY2021 净利润 613 亿美元的 32%。资产并入生产力/云的医疗场景，尚未出现减记，也尚未在 10-K 单列成可看到回收期的利润中心。按战略协同部分兑现，按对价回收未完成。",
    },
    {
        "date": "2021-09",
        "product": "ZeniMax / 贝塞斯达",
        "outlay_kind": "并购对价",
        "outlay_usd_m": 7500,
        "outlay_text": "收购 ZeniMax 约 75 亿美元量级。",
        "return_grade": "部分回收",
        "return_summary": "内容库买贵还是买对，要看后续工作室是否贡献净现金流。2024–2026 游戏裁员与剥离，降低这笔投资的回收确定性。",
    },
    {
        "date": "2021-10-05",
        "product": "Windows 11",
        "outlay_kind": "公司研发（当年）",
        "outlay_usd_m": None,
        "outlay_text": "TPM 门槛牺牲一部分升级量。FY2021 研发 207 亿美元。",
        "return_grade": "部分回收",
        "return_summary": "商业 Windows 仍随 365 走；消费 OEM 在 FY2026 第四季 -7%。系统还在贡献 MPC 利润，但不再是增长引擎。",
    },
    {
        "date": "2022-01",
        "product": "Activision / Xbox 内容",
        "outlay_kind": "并购对价（宣布）",
        "outlay_usd_m": 68700,
        "outlay_text": "宣布收购 Activision Blizzard，后以约 687 亿美元交割。",
        "return_grade": "战略未兑现",
        "return_summary": "对价超过 FY2022 净利润 727 亿美元的 90%，相当于 FY2026 整个更多个人计算分部营业利润 144 亿的约 5 倍。交割后裁员、剥离、内容收入下降。按已公布报表，回收尚未开始。",
    },
    {
        "date": "2023-01",
        "product": "编制收缩",
        "outlay_kind": "重组费用",
        "outlay_usd_m": None,
        "outlay_text": "裁员补偿进入营业费用，总额随各季变动。",
        "return_grade": "正回报",
        "return_summary": "FY2023 营收增速放缓到约 7%，营业利润率仍约 42%。裁员是保利润率。按财务兑现；按组织稳定未兑现。",
    },
    {
        "date": "2023-01-23",
        "product": "OpenAI / Copilot / Azure OpenAI",
        "outlay_kind": "战略投资",
        "outlay_usd_m": 10000,
        "outlay_text": "公司确认多年、数十亿美元；100 亿是媒体汇总口径。",
        "return_grade": "部分回收",
        "return_summary": "FY2026：Azure 破 1000 亿美元，M365 Copilot 付费席位超 3000 万；同年 OpenAI 投资给净利润 +50 亿美元，上年是 -36 亿。云增量对得上，投资损益波动大，API 排他 2026 年被拆。不能把 Azure 全部增量都记成这一笔支票。",
    },
    {
        "date": "2023-04-26",
        "product": "Activision 交易（受阻）",
        "outlay_kind": "交易成本 / 延迟",
        "outlay_usd_m": None,
        "outlay_text": "CMA 禁止延长了桥贷与不确定性，不是罚金。",
        "return_grade": "监管成本",
        "return_summary": "延迟增加了成交成本，没有减少最终 687 亿美元对价。监管没有帮股东把价格砍下来。",
    },
    {
        "date": "2023-10-13",
        "product": "Activision Blizzard",
        "outlay_kind": "并购交割",
        "outlay_usd_m": 68700,
        "outlay_text": "约 687 亿美元交割。",
        "return_grade": "战略未兑现",
        "return_summary": "FY2024 起商誉大幅上升。游戏部门 2024-01 裁约 9%，2026-07 再裁并剥离工作室。FY2026 第四季 Xbox 内容与服务 -10%。对价相对分部利润过重，目前按未回收记账。",
    },
    {
        "date": "2023-11-17",
        "product": "OpenAI 治理危机",
        "outlay_kind": "关系维护（无新对价）",
        "outlay_usd_m": None,
        "outlay_text": "公开承接团队，数日后回归。",
        "return_grade": "中性",
        "return_summary": "没有新的大额现金。保护的是已经记下的投资与 Azure 分发。财务上是保险动作，不是新的 ROI 项目。",
    },
    {
        "date": "2024-01",
        "product": "Xbox / Activision 整合",
        "outlay_kind": "重组费用",
        "outlay_usd_m": None,
        "outlay_text": "游戏部门裁约 1900 人（约 9%）。",
        "return_grade": "减值收场",
        "return_summary": "交割后立刻去重叠，说明 687 亿里有一块买的是重复编制。这是把并购溢价的一部分立刻费用化。",
    },
    {
        "date": "2024-05/06",
        "product": "Windows Recall / 消费 AI",
        "outlay_kind": "公司研发（当年）",
        "outlay_usd_m": None,
        "outlay_text": "Recall 工程含在 FY2024 研发 295 亿美元里，未单列。",
        "return_grade": "战略未兑现",
        "return_summary": "推迟上市、默认关闭。消费端 Windows AI 没有变成可核对的增量许可。FY2024 公司营业利润率 45% 来自云与 365，不是 Recall。",
    },
    {
        "date": "2024",
        "product": "自身租户安全",
        "outlay_kind": "事故成本（未单列）",
        "outlay_usd_m": None,
        "outlay_text": "Midnight Blizzard 响应费用未单列。",
        "return_grade": "中性",
        "return_summary": "身份层既是卖给企业的高利润产品，也是出事点。利润率证明卖得出去，不证明事故成本已经内化。",
    },
    {
        "date": "2024",
        "product": "Teams 拆绑",
        "outlay_kind": "监管让步（收入口径）",
        "outlay_usd_m": None,
        "outlay_text": "提供不含 Teams 的套件，可能压低捆绑 ARPU。",
        "return_grade": "监管成本",
        "return_summary": "没有新的巨额罚金，代价是套件定价权。FY2026 生产力分部营业利润率仍约 60%，说明拆绑还没有打穿利润池。",
    },
    {
        "date": "2025-05-05",
        "product": "Skype → Teams",
        "outlay_kind": "品牌终止（对价已在 2011 年支付）",
        "outlay_usd_m": 8500,
        "outlay_text": "停服；2011 年 85 亿美元对价不再有独立品牌回收。",
        "return_grade": "战略未兑现",
        "return_summary": "买入口、养十年、品牌杀掉。通信利润留在 Teams/365。按 85 亿独立资产回报：未兑现。",
    },
    {
        "date": "2025",
        "product": "编制收缩",
        "outlay_kind": "重组费用",
        "outlay_usd_m": None,
        "outlay_text": "两轮合计约裁 1.5 万人。",
        "return_grade": "正回报",
        "return_summary": "FY2025 营收 2817 亿美元、营业利润率 46%、净利率 36%。利润高增长与大规模裁员同时发生。按财务兑现；按组织稳定未兑现。",
    },
    {
        "date": "2025-09-12",
        "product": "Teams 捆绑（承诺决定）",
        "outlay_kind": "监管承诺",
        "outlay_usd_m": 0,
        "outlay_text": "承诺决定结案，未新处巨额罚金。",
        "return_grade": "监管成本",
        "return_summary": "用拆绑换免罚，比 2004–2013 年的现金罚单便宜。利润率暂时保住，定价权被写进承诺。",
    },
    {
        "date": "2026-01",
        "product": "Windows 11 Copilot / Recall",
        "outlay_kind": "公司研发（当年）",
        "outlay_usd_m": None,
        "outlay_text": "收缩铺量属独家/匿名源，公司未逐条官宣。",
        "return_grade": "未核实",
        "return_summary": "若属实，是消费端 AI 投入没有转化成可核对增量收入。FY2026 研发 356 亿美元、资本开支 1159 亿美元，主回收在 Azure 与 365，不在 Windows 消费 Copilot。",
    },
    {
        "date": "2026-04",
        "product": "OpenAI 分发权",
        "outlay_kind": "合同重订",
        "outlay_usd_m": None,
        "outlay_text": "API 不再独占；微软仍为大股东。",
        "return_grade": "部分回收",
        "return_summary": "排他溢价被拆，Azure 仍是主要分发之一。FY2026 投资损益转正 50 亿美元。云项目对得上；「独家模型供给」不再是可核对的财务护城河。",
    },
    {
        "date": "2026-07-06",
        "product": "Xbox / 工作室",
        "outlay_kind": "重组 + 减值（当季）",
        "outlay_usd_m": None,
        "outlay_text": "再裁约 4800 人；Xbox 侧约 3200；当季业绩稿提及 Xbox 减值。",
        "return_grade": "减值收场",
        "return_summary": "与 687 亿美元交割对照：内容收入 -10%，继续去工作室。游戏并购的财务句号还没写完，方向是收缩而不是回收。",
    },
    {
        "date": "2026-07-29",
        "product": "公司账本（云 vs 消费）",
        "outlay_kind": "年报核验",
        "outlay_usd_m": None,
        "outlay_text": "FY26 业绩稿：营收 3318 亿美元；研发 356 亿；资本开支 1159 亿。",
        "return_grade": "高回报",
        "books_role": "这条事件就是 FY2026 业绩发布。下面的营收、研发、利润率就是这份年报本身，不是拿来当别的产品的背景。",
        "return_summary": "毛利率 67.9%，营业利润率 46.8%，净利率 40.3%。生产力营业利润 839 亿、智能云 570 亿、更多个人计算 144 亿。账本证明云和 365 做成了；同一季 Windows OEM -7%、Xbox 内容与服务 -10%，不能外推消费端与游戏并购也兑现。",
    },
    {
        "date": "2026-08",
        "product": "Entra ID",
        "outlay_kind": "事故成本（未核实）",
        "outlay_usd_m": None,
        "outlay_text": "CVE-2026-69836 影响面未独立核实。",
        "return_grade": "未核实",
        "return_summary": "身份层是商业云高利润的一部分。漏洞的财务损失（补丁、客户流失、诉讼）默认未核实，不能用分部利润率抵消。",
    },
]

# Same order as OVERLAYS. Checksum: len == 91.
LINE_IDS = [
    "company",  # 0 HQ
    "company",  # 1 IPO
    "windows",  # 2 OS/2
    "office",  # 3 PowerPoint
    "windows",  # 4 Win 2.0
    "windows",  # 5 look-and-feel
    "windows",  # 6 Win 3.0
    "windows",  # 7 FTC
    "office",  # 8 Office suite
    "company",  # 9 MSR
    "windows",  # 10 Win 3.1
    "cloud",  # 11 NT
    "windows",  # 12 consent decree
    "windows",  # 13 Win95/IE
    "company",  # 14 MSNBC
    "office",  # 15 Office Mac
    "search",  # 16 Hotmail
    "windows",  # 17 IE bundling
    "windows",  # 18 Win98
    "windows",  # 19 findings of fact
    "company",  # 20 Ballmer CEO
    "windows",  # 21 Win2000
    "company",  # 22 Sherman
    "company",  # 23 breakup
    "windows",  # 24 ME
    "company",  # 25 no breakup
    "windows",  # 26 XP
    "windows",  # 27 settlement
    "gaming",  # 28 Xbox
    "windows",  # 29 settlement final
    "windows",  # 30 WMP / interoperability
    "gaming",  # 31 Xbox 360
    "cloud",  # 32 server interoperability fine
    "devices",  # 33 Zune
    "windows",  # 34 Vista
    "search",  # 35 aQuantive
    "search",  # 36 Yahoo
    "windows",  # 37 periodic penalty
    "company",  # 38 Gates day-to-day
    "windows",  # 39 Chrome
    "search",  # 40 Bing
    "windows",  # 41 Win7
    "windows",  # 42 browser ballot
    "cloud",  # 43 Azure
    "devices",  # 44 Kin
    "devices",  # 45 Windows Phone
    "devices",  # 46 Nokia channel
    "office",  # 47 Skype
    "devices",  # 48 Surface
    "windows",  # 49 Win8
    "windows",  # 50 ballot violation
    "devices",  # 51 Surface RT
    "company",  # 52 Nadella
    "devices",  # 53 Nokia phones
    "gaming",  # 54 Xbox One
    "cloud",  # 55 cloud first
    "office",  # 56 Office iPad
    "devices",  # 57 Nokia D&S
    "gaming",  # 58 Minecraft
    "devices",  # 59 Nokia impairment
    "windows",  # 60 Win10
    "office",  # 61 LinkedIn
    "office",  # 62 Teams
    "cloud",  # 63 GitHub
    "cloud",  # 64 OpenAI
    "devices",  # 65 retail
    "company",  # 66 TikTok
    "gaming",  # 67 Series X/S
    "cloud",  # 68 identity security
    "office",  # 69 Exchange
    "office",  # 70 Nuance
    "gaming",  # 71 ZeniMax
    "windows",  # 72 Win11
    "gaming",  # 73 Activision bid
    "company",  # 74 layoffs 2023
    "cloud",  # 75 Copilot
    "gaming",  # 76 CMA block
    "gaming",  # 77 Activision close
    "cloud",  # 78 OpenAI board
    "gaming",  # 79 Activision integration
    "windows",  # 80 Recall
    "cloud",  # 81 Midnight Blizzard
    "office",  # 82 Teams unbundle
    "office",  # 83 Skype sunset
    "company",  # 84 layoffs 2025
    "office",  # 85 Teams commitments
    "windows",  # 86 Copilot+ PC
    "cloud",  # 87 OpenAI distribution
    "gaming",  # 88 Xbox studios
    "company",  # 89 FY26 earnings
    "cloud",  # 90 Entra
]


def fy_of(date: str) -> int:
    raw = str(date).split("/")[0]
    year = int(raw[:4])
    if len(raw) == 4:
        return year
    month = int(raw[5:7])
    return year if month <= 6 else year + 1


def _pct(num: float | None, den: float | None) -> float | None:
    if num is None or den in (None, 0):
        return None
    return round(100.0 * float(num) / float(den), 1)


def _money(value: float | int | None) -> str:
    if value is None:
        return "未披露"
    n = float(value)
    if abs(n) >= 100:
        yi = n / 100.0
        text = f"{yi:.0f}" if yi >= 10 else f"{yi:.1f}"
        return f"{text} 亿美元"
    if abs(n) >= 1:
        return f"{n:.0f} 百万美元"
    return f"{n} 百万美元"


def event_cash_label(overlay: dict) -> str:
    kind = overlay["outlay_kind"]
    cash = overlay["outlay_usd_m"]
    if cash is not None:
        return f"{kind} {_money(cash)}"
    return f"{kind}：年报未单列金额"


def explain_books(overlay: dict, company: dict) -> str:
    if overlay.get("books_role"):
        return overlay["books_role"]
    product = overlay["product"]
    fy = company["fy"]
    rev = company["revenue_usd_m"]
    rd = company["rd_usd_m"]
    op = company.get("op_margin_pct")
    kind = overlay["outlay_kind"]
    cash = overlay["outlay_usd_m"]
    scale = (
        f"旁边列出的 FY{fy} 营收 {_money(rev)}、研发 {_money(rd)}"
        + (f"、营业利润率 {op}%" if op is not None else "")
        + f"，是微软全公司年报，不是「{product}」自己的利润表。"
    )
    if cash is not None:
        share = 100.0 * float(cash) / float(rev) if rev else 0
        share_s = f"{share:.1f}%" if share < 10 else f"{share:.0f}%"
        if "流入" in kind:
            return (
                f"这条事件能核对的现金是融资流入 {_money(cash)}，约占当年公司营收 {share_s}。"
                f"{scale}当年利润率用来看公司当时已经赚不赚钱，不能把当年净利率记成上市的产品回报。"
            )
        if "未成交" in kind:
            return (
                f"这条事件是出价 {_money(cash)}，交易没成，账上没有这笔流出。"
                f"{scale}拿金额去比营收，只是为了看这单如果成交会有多大。"
            )
        if "罚金" in kind:
            return (
                f"这条事件能核对的现金是罚金 {_money(cash)}，约占当年公司营收 {share_s}。"
                f"{scale}利润率不是这条监管事件的成绩；它只说明罚款相对当时利润池大不大。"
            )
        if "减记" in kind or "减值" in kind:
            return (
                f"这条事件能核对的数字是减记 {_money(cash)}，约占当年公司营收 {share_s}，等于把以前的投资从账上划掉。"
                f"{scale}若同一年利润率明显下滑，往往有一部分就是这笔减记，不再只是背景。"
            )
        return (
            f"这条事件能核对的现金是{kind} {_money(cash)}，约占当年公司营收 {share_s}。"
            f"{scale}当年利润率主要来自当时已经在卖的产品，不是这笔新交易当天就开始贡献。"
            "判定回报要看后来这笔资产有没有变成利润，或有没有减记。"
        )
    if "研发" in kind:
        return (
            f"「{product}」的开发费没有从年报里拆出来。当年全公司研发是 {_money(rd)}，所有产品加在一起，里面有这条，但不知道占多少。"
            f"{scale}不能用当年营业利润率当这条产品的投资回报率。"
        )
    return (
        f"这条事件在年报里没有单独的对价或产品利润科目。"
        f"{scale}列出来是为了标明决策发生时公司有多大、利润厚不厚——买不买得起、罚不罚得起——不是说这些数字是这条事件做出来的。"
    )


def load_fy() -> dict[int, dict]:
    payload = json.loads(FY_PATH.read_text(encoding="utf-8"))
    out: dict[int, dict] = {}
    for row in payload["years"]:
        fy = int(row["fy"])
        rev = row["revenue"]
        gp = row.get("gross_profit")
        rd = row["rd"]
        oi = row["operating_income"]
        ni = row["net_income"]
        out[fy] = {
            "fy": fy,
            "revenue_usd_m": rev,
            "gross_profit_usd_m": gp,
            "rd_usd_m": rd,
            "operating_income_usd_m": oi,
            "net_income_usd_m": ni,
            "capex_usd_m": row.get("capex"),
            "gross_margin_pct": _pct(gp, rev),
            "rd_pct": _pct(rd, rev),
            "op_margin_pct": _pct(oi, rev),
            "net_margin_pct": _pct(ni, rev),
        }
    return out


def nearest_fy(fy: int, table: dict[int, dict]) -> dict:
    if fy in table:
        return table[fy]
    years = sorted(table)
    pick = min(years, key=lambda y: abs(y - fy))
    row = dict(table[pick])
    row["fy_note"] = f"无 FY{fy} 完整序列，用 FY{pick} 作最近年报背景。"
    return row


def load_lines() -> dict:
    return json.loads(LINES_PATH.read_text(encoding="utf-8"))


GRAIN_LABEL = {
    "10k": "10-K",
    "earnings": "业绩会",
    "company": "公司口径",
    "third_party": "第三方",
    "derived": "倒推",
    "estimate": "估算",
    "list_price": "标价（价目表）",
    "none": "年报不披露",
}


def _web_for_line(catalog: dict, line_id: str) -> list[dict]:
    out: list[dict] = []
    for m in (catalog.get("web_metrics") or {}).get("metrics") or []:
        if m.get("line") != line_id:
            continue
        value, unit = m.get("value"), m.get("unit") or ""
        display = f"{value} {unit}".strip()
        out.append(
            {
                "id": m.get("id"),
                "name": m["name"],
                "display": f"{display}（{m.get('as_of') or ''}）",
                "grain": m.get("grain"),
                "grain_label": GRAIN_LABEL.get(m.get("grain"), m.get("grain") or ""),
                "source": m.get("source") or "",
                "note": m.get("note") or "",
            }
        )
    operating = catalog.get("operating") or {}
    latest_share = [s for s in operating.get("share") or [] if s.get("line") == line_id]
    if latest_share:
        s = latest_share[-1]
        out.append(
            {
                "id": f"share-{line_id}",
                "name": s["name"],
                "display": f"{s['value']}{s.get('unit') or ''}（FY{s['fy']}）",
                "grain": s.get("grain"),
                "grain_label": GRAIN_LABEL.get(s.get("grain"), s.get("grain") or ""),
                "source": s.get("source") or "",
                "note": "份额年表在产品线页。年报没有市场份额表。",
            }
        )
    latest_seat = [s for s in operating.get("seats") or [] if s.get("line") == line_id]
    if latest_seat:
        s = latest_seat[-1]
        out.append(
            {
                "id": f"seats-{line_id}",
                "name": s["name"],
                "display": f"{s['value']} {s.get('unit') or ''}（{s.get('as_of') or 'FY' + str(s['fy'])}）",
                "grain": s.get("grain"),
                "grain_label": GRAIN_LABEL.get(s.get("grain"), s.get("grain") or ""),
                "source": s.get("source") or "",
                "note": "订阅/席位年表在产品线页。",
            }
        )
    latest_price = [
        p
        for p in operating.get("prices") or []
        if p.get("line") == line_id and p.get("price_usd_mo") is not None
    ]
    if latest_price:
        p = latest_price[-1]
        out.append(
            {
                "id": f"price-{line_id}",
                "name": p["sku"],
                "display": f"${p['price_usd_mo']}/用户/月（FY{p['fy']} 标价）",
                "grain": p.get("grain"),
                "grain_label": GRAIN_LABEL.get(p.get("grain"), p.get("grain") or ""),
                "source": p.get("source") or "",
                "note": "单价年表在产品线页。10-K 不列美元标价。",
            }
        )
    return out


def _stat_row(fy: int, label: str, revenue: float, oi: float) -> dict:
    return {
        "fy": int(fy),
        "label": label,
        "revenue_usd_m": revenue,
        "operating_income_usd_m": oi,
        "op_margin_pct": _pct(oi, revenue),
    }


def _year_note(line: dict, fy: int) -> tuple[dict | None, str]:
    years = line.get("years") or []
    if not years:
        return None, "年报没有这条产品线的单独营业利润。"
    by_fy = {int(row["fy"]): row for row in years}
    if fy in by_fy:
        row = by_fy[fy]
        return _stat_row(row["fy"], row["label"], row["revenue"], row["operating_income"]), (
            f"事件所在 FY{fy} 能核对的最细一级，是 {row['label']} 的分部营业利润，不是单品。"
        )
    first_fy = min(by_fy)
    last_fy = max(by_fy)
    if fy < first_fy:
        first = by_fy[first_fy]
        return None, (
            f"FY{fy} 年报还没有分部营业利润。能核对的最早数字是 FY{first_fy} "
            f"{first['label']} 营业利润 {_money(first['operating_income'])}"
            f"（营收 {_money(first['revenue'])}）。"
        )
    if 2014 <= fy <= 2015:
        prev = by_fy.get(2013)
        nxt = by_fy.get(2016)
        bits = [f"FY{fy} 前后分部口径切过，和相邻年不完全可比。"]
        if prev:
            bits.append(
                f"切之前 FY2013 {prev['label']} 营业利润 {_money(prev['operating_income'])}。"
            )
        if nxt:
            bits.append(
                f"切之后 FY2016 {nxt['label']} 营业利润 {_money(nxt['operating_income'])}。"
            )
        return None, "".join(bits)
    if fy > last_fy:
        last = by_fy[last_fy]
        return None, (
            f"FY{last_fy} 之后这条线不再单列营业利润。最后一次单列是 FY{last_fy} "
            f"{last['label']} 营业利润 {_money(last['operating_income'])}"
            f"（营收 {_money(last['revenue'])}）。"
        )
    before = [row for row in years if int(row["fy"]) <= fy]
    pick = before[-1] if before else min(years, key=lambda row: abs(int(row["fy"]) - fy))
    return None, (
        f"FY{fy} 没有这一口径。最接近的是 FY{pick['fy']} {pick['label']} "
        f"营业利润 {_money(pick['operating_income'])}。"
    )


def product_line_snapshot(line_id: str, fy: int, product: str, catalog: dict) -> dict:
    lines = catalog["lines"]
    parents = catalog["parents_now"]
    revenue_tables = catalog.get("product_revenue") or {}
    line = lines[line_id]
    paragraphs: list[str] = []
    at_event = None
    latest = None
    revenue_only: list[dict] = []

    if line_id == "company":
        paragraphs.append(
            f"「{product}」不是一条可核对的产品利润中心。微软能拆出来的营业利润停在三个分部，不是这件事自己。"
        )
        for parent in parents.values():
            paragraphs.append(
                f"FY2026 {parent['name']} 营业利润 {_money(parent['fy2026_operating_income'])}"
                f"（营收 {_money(parent['fy2026_revenue'])}，"
                f"利润率 {_pct(parent['fy2026_operating_income'], parent['fy2026_revenue'])}%）。"
            )
        latest = _stat_row(
            2026,
            "三个分部合计（对账前）",
            sum(p["fy2026_revenue"] for p in parents.values()),
            sum(p["fy2026_operating_income"] for p in parents.values()),
        )
        return {
            "id": line_id,
            "name": line["name"],
            "grain": line["profit_grain"],
            "paragraphs": paragraphs,
            "at_event": None,
            "latest": latest,
            "revenue_only": [],
        }

    paragraphs.append(line["profit_grain"])
    at_event, year_note = _year_note(line, fy)
    if at_event:
        paragraphs.append(
            f"事件所在 FY{at_event['fy']}，{at_event['label']} 营业利润 "
            f"{_money(at_event['operating_income_usd_m'])}"
            f"（营收 {_money(at_event['revenue_usd_m'])}"
            + (
                f"，利润率 {at_event['op_margin_pct']}%"
                if at_event["op_margin_pct"] is not None
                else ""
            )
            + f"）。这是分部合计，不是「{product}」单品。"
        )
    else:
        paragraphs.append(year_note)

    parent_key = line.get("parent_now")
    parent = parents.get(parent_key) if parent_key else None
    if parent:
        latest = _stat_row(
            2026,
            parent["name"],
            parent["fy2026_revenue"],
            parent["fy2026_operating_income"],
        )
        buried = line_id in {"windows", "gaming", "search", "devices"}
        if buried:
            paragraphs.append(
                f"FY2026 这条线的利润已经并进「{parent['name']}」："
                f"分部营业利润 {_money(parent['fy2026_operating_income'])}"
                f"（营收 {_money(parent['fy2026_revenue'])}，"
                f"利润率 {_pct(parent['fy2026_operating_income'], parent['fy2026_revenue'])}%），"
                "里面混着 Windows、Xbox、搜索和设备，不能再拆成这条产品。"
            )
        else:
            paragraphs.append(
                f"FY2026 {parent['name']} 营业利润 {_money(parent['fy2026_operating_income'])}"
                f"（营收 {_money(parent['fy2026_revenue'])}，"
                f"利润率 {_pct(parent['fy2026_operating_income'], parent['fy2026_revenue'])}%）。"
                f"仍不是「{product}」单品。"
            )

    fy_key = str(fy if str(fy) in revenue_tables else 2026)
    for item in revenue_tables.get(fy_key, []):
        if item.get("line") != line_id:
            continue
        revenue_only.append(
            {
                "name": item["name"],
                "revenue_usd_m": item["revenue"],
                "nested": bool(item.get("nested")),
            }
        )
    if revenue_only:
        bits = "、".join(
            f"{item['name']} {_money(item['revenue_usd_m'])}"
            + ("（含在上一行里，不另加总）" if item.get("nested") else "")
            for item in revenue_only
        )
        year_label = fy_key if fy_key != "2026" else "2026"
        paragraphs.append(
            f"更细的产品年报给营收、不给利润。FY{year_label}：{bits}。"
        )

    web_rows = _web_for_line(catalog, line_id)
    if web_rows:
        paragraphs.append(
            "年报利润表没有的规模，去业绩会、监测机构和媒体补，并标明是不是公司自己说的："
        )
        for item in web_rows[:6]:
            paragraphs.append(
                f"{item['name']}：{item['display']} · {item['grain_label']} · {item['source']}"
            )

    return {
        "id": line_id,
        "name": line["name"],
        "grain": line["profit_grain"],
        "paragraphs": paragraphs,
        "at_event": at_event,
        "latest": latest,
        "revenue_only": revenue_only,
        "web": web_rows,
    }


def attach_finance(events: list[dict]) -> list[dict]:
    if len(events) != len(OVERLAYS):
        raise SystemExit(f"finance overlay count {len(OVERLAYS)} != events {len(events)}")
    if len(LINE_IDS) != len(OVERLAYS):
        raise SystemExit(f"product line count {len(LINE_IDS)} != overlays {len(OVERLAYS)}")
    table = load_fy()
    catalog = load_lines()
    attached: list[dict] = []
    for event, overlay, line_id in zip(events, OVERLAYS, LINE_IDS):
        if event["date"] != overlay["date"]:
            raise SystemExit(
                f"finance date mismatch: event {event['date']} vs overlay {overlay['date']}"
            )
        fy = fy_of(event["date"])
        company = nearest_fy(fy, table)
        finance = {
            "fy": int(company["fy"]),
            "product": overlay["product"],
            "outlay_kind": overlay["outlay_kind"],
            "outlay_usd_m": overlay["outlay_usd_m"],
            "outlay_text": overlay["outlay_text"],
            "event_cash": event_cash_label(overlay),
            "books_role": explain_books(overlay, company),
            "product_line": product_line_snapshot(
                line_id, int(company["fy"]), overlay["product"], catalog
            ),
            "return_grade": overlay["return_grade"],
            "return_tone": RETURN_TONE.get(overlay["return_grade"], "neutral"),
            "return_summary": overlay["return_summary"],
            "company": company,
            "note": "全公司年报用来对照规模。产品利润只写年报真正单列的分部。单品利润没有就不编；份额、席位、订阅去网上补，并标明来源。",
        }
        row = dict(event)
        row["finance"] = finance
        attached.append(row)
    return attached
