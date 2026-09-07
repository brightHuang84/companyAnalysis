"""Build yearly board-report summaries for Microsoft.

US filers do not have an A-share「董事会报告」line item. This script folds the
shareholder letter (when one exists), 10-K MD&A, and the event ledger into the
same four headings every fiscal year: environment, progress, outlook, plus a
separate board-execution timeline.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MSFT = ROOT / "data" / "issuers" / "MSFT"
OUT = MSFT / "board_reports.json"
EVENTS = MSFT / "events_1986_2026.json"
FY_PATH = MSFT / "financials_fy.json"

# Board / CEO execution. Dates are the public announcement or effective date.
GOVERNANCE = [
    {
        "date": "1975-04-04",
        "fy": None,
        "title": "微软成立",
        "who": "Bill Gates / Paul Allen",
        "detail": "Gates 与 Allen 合伙成立公司。此后直到上市，Gates 同时是事实上的董事长和首席执行官。",
    },
    {
        "date": "1981-06-25",
        "fy": None,
        "title": "改组为华盛顿州公司",
        "who": "Bill Gates",
        "detail": "从合伙改成股份公司，给后来的期权池和 IPO 铺治理结构。",
    },
    {
        "date": "1986-03-13",
        "fy": 1986,
        "title": "纳斯达克上市，公众公司治理开始",
        "who": "董事长兼 CEO：Bill Gates",
        "detail": "发行价 21 美元，融资约 6100 万美元。Gates 继续兼任董事长与 CEO，董事会对公众股东负责。",
    },
    {
        "date": "2000-01-13",
        "fy": 2000,
        "title": "Ballmer 接任 CEO，Gates 改任董事长兼首席软件架构师",
        "who": "CEO：Steve Ballmer · 董事长：Bill Gates",
        "detail": "第一次把日常经营和产品愿景拆开。反垄断案进行中，董事会选择内部交班而不是空降。",
    },
    {
        "date": "2000-11",
        "fy": 2001,
        "title": "Paul Allen 离开董事会",
        "who": "联合创始人离任董事",
        "detail": "Allen 1983 年已离开经营，2000 年底退出董事会，创始人双核变成 Gates 一人在董事会里代表创办世代。",
    },
    {
        "date": "2003-01-16",
        "fy": 2003,
        "title": "首次现金分红（当时按年派，每股拆前 0.16 美元）",
        "who": "董事会批准资本回报政策",
        "detail": "从「只回购、不分红」改成向股东派现。标志桌面现金牛进入回流阶段；后来改成季度分红，并在 2004 年加了特别分红。",
    },
    {
        "date": "2004-07-20",
        "fy": 2005,
        "title": "每股 3 美元特别分红，约 320 亿美元",
        "who": "董事会一次性返还现金",
        "detail": "当时美国公司史上最大规模现金分红之一。董事会判断账上现金已超过再投资需要。",
    },
    {
        "date": "2008-06-27",
        "fy": 2008,
        "title": "Gates 卸任全职，保留董事长",
        "who": "董事长：Bill Gates · CEO：Steve Ballmer",
        "detail": "Gates 把日常工程权交给 Ballmer 团队，自己把时间转向基金会。董事会结构没变，执行重心彻底落到 CEO。",
    },
    {
        "date": "2013-08-23",
        "fy": 2014,
        "title": "Ballmer 宣布一年内退休",
        "who": "董事会启动 CEO 遴选",
        "detail": "Windows 8 / Surface / 诺基亚路线受挫后，董事会接受交班。公开说内部优先，最终仍选了内部的 Nadella。",
    },
    {
        "date": "2014-02-04",
        "fy": 2014,
        "title": "Nadella 任 CEO；Gates 卸任董事长；Thompson 任独立董事董事长",
        "who": "CEO：Satya Nadella · 董事长：John W. Thompson",
        "detail": "第一次出现独立董事董事长。Gates 留任董事并当顾问。Ballmer 随后在 2014 年离开董事会。",
    },
    {
        "date": "2014-08",
        "fy": 2015,
        "title": "Ballmer 离开董事会",
        "who": "前 CEO 不再任董事",
        "detail": "交班完成。此后董事会不再同时坐着两任前 CEO（Gates 仍在，直到 2020）。",
    },
    {
        "date": "2020-03-13",
        "fy": 2020,
        "title": "Gates 离开董事会",
        "who": "创始人退出董事席",
        "detail": "公开理由是把时间给基金会和气候变化。董事会失去创办人席位，独立董事占比升到最高。",
    },
    {
        "date": "2021-06-16",
        "fy": 2021,
        "title": "Nadella 兼任董事长，Thompson 改任首席独立董事",
        "who": "董事长兼 CEO：Satya Nadella",
        "detail": "云转型被董事会视为已站稳，重新允许 CEO 兼董事长。Thompson 留下做独立制衡。",
    },
    {
        "date": "2023-11-17",
        "fy": 2024,
        "title": "OpenAI 董事会危机：微软公开承接团队，随后获观察员席",
        "who": "Nadella 代表董事会对外执行",
        "detail": "不是改微软自己的董事会，但是当年最重要的治理动作：把 AI 伙伴的治理风险当成自身执行事项处理。",
    },
]

# Shareholder-letter / MD&A overlays. Every FY 1986–2026 has a row.
# source_kind: 股东信综述 = public letter exists and this is a condensation;
# 年报+事件综合 = reconstructed from 10-K MD&A and the event ledger.
LETTERS: dict[int, dict] = {
    1986: {
        "author": "Bill Gates",
        "source_kind": "年报+招股+事件综合",
        "source": "1986 年报 / 招股说明书；当年无单独「致股东信」网页档可核原文。",
        "environment": "IBM PC 兼容机把个人电脑从爱好者市场做成企业采购。硬件厂商打价格战，操作系统和办公软件开始可以独立定价。微软刚搬进雷德蒙德，要同时向承销商证明自己是可持续经营的公司。",
        "progress": [
            "纳斯达克上市，融资约 6100 万美元，公众公司治理起步。",
            "MS-DOS 继续给兼容机授权，Windows 1.x 仍弱，图形界面还没成为收入主力。",
            "总部迁到雷德蒙德校园，把研发、销售收拢到可参观的实体。",
        ],
        "outlook": "把图形界面做成下一代平台，并用应用软件（后来的 Office）绑住平台。国际化销售刚开始铺。",
    },
    1987: {
        "author": "Bill Gates",
        "source_kind": "年报+事件综合",
        "source": "FY1987 年报口径 + 台账事件。",
        "environment": "与 IBM 的关系仍是企业市场入场券。图形界面竞赛里苹果、IBM、微软三条线并行。应用软件套装还没成型。",
        "progress": [
            "宣布与 IBM 联合做 OS/2，作为企业桌面对冲。",
            "营收 3.46 亿美元，研发提到 3800 万美元。",
        ],
        "outlook": "OS/2 被写成企业标准候选；Windows 继续作为低端图形层。董事会此时并未押单一平台。",
    },
    1988: {
        "author": "Bill Gates",
        "source_kind": "年报+事件综合",
        "source": "FY1988 年报口径 + 台账事件。",
        "environment": "图形界面版权开始变成诉讼。IBM 路线与自有 Windows 路线的张力加大。",
        "progress": [
            "收购 Forethought，拿到 PowerPoint，补齐后来 Office 的第三件。",
            "发布 Windows 2.0。",
            "苹果起诉 Windows 抄袭 Mac 界面，应诉成为平台保卫战。",
        ],
        "outlook": "继续脚踏 OS/2 与 Windows 两条船；应用软件向套装化走。",
    },
    1989: {
        "author": "Bill Gates",
        "source_kind": "年报+事件综合",
        "source": "FY1989 年报口径。台账该年无单独物质事件。",
        "environment": "PC 进入办公室，局域网开始普及。软件公司的利润率已经明显高于硬件。",
        "progress": [
            "营收 8.04 亿美元，营业利润率约 30%。",
            "Excel、Word 在 Windows / Mac 两端抢份额，为套装做库存。",
        ],
        "outlook": "下一阶段是把图形操作系统做成销量事件，而不是继续当 DOS 的皮肤。",
    },
    1990: {
        "author": "Bill Gates",
        "source_kind": "年报+事件综合",
        "source": "FY1990 年报口径 + 台账事件。",
        "environment": "386 机器让图形界面终于跑得动。监管第一次认真问软件垄断。",
        "progress": [
            "Windows 3.0 发布，图形界面从实验变成可卖的产品。",
            "FTC 启动是否构成软件垄断的调查。",
            "营收 11.83 亿美元，营业利润率约 33%。",
        ],
        "outlook": "把 Windows 做成 OEM 默认，并用 Office 收应用层租金。监管被当成背景噪音，还不是战略约束。",
    },
    1991: {
        "author": "Bill Gates",
        "source_kind": "年报+事件综合",
        "source": "FY1991 年报口径 + 台账事件。",
        "environment": "Windows 3.0 之后，应用层决定谁能把平台锁住。基础研究开始被当成长期护城河。",
        "progress": [
            "Office 把 Word / Excel / PowerPoint 捆成套装（另有 1989 年最早套装口径）。",
            "营收 18.43 亿美元，同比约 +56%。",
        ],
        "outlook": "套装定价会比单件销售更稳；企业协议授权开始成型。",
    },
    1992: {
        "author": "Bill Gates",
        "source_kind": "年报+事件综合",
        "source": "FY1992 年报口径 + 台账事件。",
        "environment": "桌面图形界面进入主流。需要公司级研究机构，不能只靠产品组迭代。",
        "progress": [
            "成立 Microsoft Research。",
            "Windows 3.1 发布，稳定性和 TrueType 让办公场景可用。",
            "营收 27.59 亿美元，营业利润首次突破 10 亿美元。",
        ],
        "outlook": "下一步是企业内核（NT）和消费升级（Chicago / 后来的 Windows 95）。",
    },
    1993: {
        "author": "Bill Gates",
        "source_kind": "年报+事件综合",
        "source": "FY1993 年报口径。NT 正式发布落在下一财年 7 月。",
        "environment": "企业客户要可靠内核和网络，DOS/Windows 3.x 不够。IBM OS/2 仍在抢这一层。",
        "progress": [
            "NT 进入收尾，目标是把微软从消费 GUI 推进到服务器/企业内核。",
            "营收 37.53 亿美元，毛利率可核对，营业利润 13.3 亿美元。",
        ],
        "outlook": "Chicago（Windows 95）做消费爆发，NT 做企业根基，两条线不能混成一个二进制。",
    },
    1994: {
        "author": "Bill Gates",
        "source_kind": "年报+事件综合",
        "source": "FY1994 年报口径 + 台账事件。",
        "environment": "Internet 还没写成公司战略，但企业网络已经是采购理由。司法部开始用同意令管授权条款。",
        "progress": [
            "Windows NT 3.1 发布（1993-07，计入本财年）。",
            "营收 46.49 亿美元，营业利润 17.3 亿美元。",
        ],
        "outlook": "Windows 95 被当成下一财年的消费事件。同意令将限制把其他产品绑死 Windows 授权。",
    },
    1995: {
        "author": "Bill Gates",
        "source_kind": "股东信综述",
        "source": "1995 年报致辞主题（Internet 转向前夜）+ 1994-07 司法部同意令。",
        "environment": "PC 进入家庭前夜。司法部同意令要求授权条款不能把应用绑死在 Windows 上。网景已经把浏览器做成独立层。",
        "progress": [
            "与司法部达成同意令：不得把其他产品绑死 Windows 授权。",
            "Windows 95 在财年末仍未上市（8 月才发布），当年是备货、OEM 谈判和营销铺垫。",
            "营收 59.37 亿美元。",
        ],
        "outlook": "Windows 95 被写成消费操作系统的换代；Internet 在内部还是「要补的功能」，还不是公司中心。",
    },
    1996: {
        "author": "Bill Gates",
        "source_kind": "股东信综述",
        "source": "FY1996 年报；Gates 当年公开把 Internet 提升为战略中心。",
        "environment": "浏览器被看成新平台。网景在企业桌面抢入口。媒体和电信都想做「信息高速公路」。",
        "progress": [
            "Windows 95 + Internet Explorer 进入主流。",
            "与 NBC 组建 MSNBC，试验内容和网络品牌。",
            "营收 86.71 亿美元，同比约 +46%。",
        ],
        "outlook": "把 IE 免费绑进 Windows，用平台反击浏览器层。这是后来反垄断案的核心事实。",
    },
    1997: {
        "author": "Bill Gates",
        "source_kind": "年报+事件综合",
        "source": "FY1997 年报口径。Hotmail 与苹果投资落在下一财年。",
        "environment": "浏览器战争白热化。微软要用门户、邮件、媒体补互联网入口，不能只卖操作系统。",
        "progress": [
            "IE 份额快速上升，Office 继续收企业租金。",
            "营收 113.58 亿美元，营业利润率约 43%。",
        ],
        "outlook": "下一步是买流量入口（邮件）和稳住苹果生态，避免 Mac 成为反微软根据地。",
    },
    1998: {
        "author": "Bill Gates",
        "source_kind": "年报+事件综合",
        "source": "FY1998 年报口径 + 台账事件。",
        "environment": "司法部认为用 Windows 垄断维持并延伸到浏览器。公司公开口径仍是「消费者受益于免费 IE」。",
        "progress": [
            "向苹果投资 1.5 亿美元，IE 成 Mac 默认浏览器。",
            "收购 Hotmail，对价约 4 亿美元。",
            "司法部与 20 州起诉。",
            "Windows 98 发布。",
            "营收 144.84 亿美元。",
        ],
        "outlook": "产品层继续铺 Windows / Office / 门户；法律层变成和产品并行的第二条执行线。",
    },
    1999: {
        "author": "Bill Gates",
        "source_kind": "年报+事件综合",
        "source": "FY1999 年报口径。杰克逊事实认定在下一财年 11 月。",
        "environment": "互联网泡沫把软件估值推到高点。桌面利润率也到了四十年峰值附近。",
        "progress": [
            "营收 197.47 亿美元，营业利润 100.4 亿美元，营业利润率约 51%。",
            "Windows 2000 与 Office 2000 进入企业换代周期。",
        ],
        "outlook": "董事会开始准备 CEO 交班；反垄断判决临近，不能再把法律当公关问题。",
    },
    2000: {
        "author": "Bill Gates / Steve Ballmer",
        "source_kind": "股东信综述",
        "source": "FY2000 年报致辞；2000-01-13 CEO 交班；杰克逊案判决。",
        "environment": "互联网泡沫开始破裂。法院认定微软维持操作系统垄断并试图垄断浏览器。内部要同时换 CEO 和应诉。",
        "progress": [
            "Ballmer 接任 CEO，Gates 改任董事长兼首席软件架构师。",
            "Windows 2000 发布。",
            "杰克逊法官认定违反谢尔曼法，初审令拆成两家公司。",
            "营收 229.56 亿美元；净利润 94.2 亿美元，利润率仍高。",
        ],
        "outlook": "上诉求推翻拆分；产品上把消费线（ME/XP）和企业线分开。交班后 Ballmer 负责执行，Gates 管架构。",
    },
    2001: {
        "author": "Bill Gates / Steve Ballmer",
        "source_kind": "年报+事件综合",
        "source": "FY2001 年报口径 + 台账。XP / Xbox / 和解落在下一财年。",
        "environment": "科网泡沫破裂，企业 IT 开支收缩。Windows ME 被看成失败的消费版。拆分令在上诉中。",
        "progress": [
            "Windows ME 发布，口碑差，加速了 XP 的必要性。",
            "Paul Allen 离开董事会。",
            "营收 252.96 亿美元，净利润从高峰回落。",
        ],
        "outlook": "用 XP 统一消费内核，用 Xbox 进客厅，用和解换掉拆分。",
    },
    2002: {
        "author": "Bill Gates / Steve Ballmer",
        "source_kind": "股东信综述",
        "source": "FY2002 年报；Trustworthy Computing 备忘录与联邦和解。",
        "environment": "9/11 之后安全成为采购条款。Code Red / Nimda 让 Windows 被写成互联网风险。布什政府不再寻求拆分。",
        "progress": [
            "司法部宣布不再寻求拆分，并在 11 月签署联邦和解同意令。",
            "Windows XP 发布，把消费线拉回 NT 内核。",
            "Xbox 北美上市，用硬件补贴进客厅。",
            "Gates 把「可信计算」写成全公司工程优先级。",
        ],
        "outlook": "安全补丁和服务器（.NET / Windows Server）是执行重点；游戏是长期品牌，不是当年利润。",
    },
    2003: {
        "author": "Steve Ballmer",
        "source_kind": "年报+事件综合",
        "source": "FY2003 年报口径 + 联邦和解被法院大体接受。",
        "environment": "企业开始重新买服务器。开源和 Linux 在数据中心冒头。和解条款要改授权和披露行为。",
        "progress": [
            "Kollar-Kotelly 法官大体接受联邦和解。",
            "营收 321.87 亿美元；营业利润因和解与会计口径波动。",
            "董事会 2003-01-16 宣布首次现金分红，3 月派发。",
        ],
        "outlook": "把 Windows Server 和 Office 系统卖进企业协议；用分红证明现金超过再投资需要。",
    },
    2004: {
        "author": "Steve Ballmer",
        "source_kind": "年报+事件综合",
        "source": "FY2004 年报口径 + 欧盟罚款 + 首次分红。",
        "environment": "美国和解落地后，欧盟按另一套理论罚捆绑和互操作。Linux 和 Google 开始从两边挖。",
        "progress": [
            "欧盟罚 4.972 亿欧元：媒体播放器捆绑 + 服务器互操作。",
            "研发跳到 77.8 亿美元（含股权激励重述口径变化）。",
        ],
        "outlook": "SP2 安全加固、长期 Vista，以及把搜索和广告当成必须补的互联网层。",
    },
    2005: {
        "author": "Steve Ballmer",
        "source_kind": "年报+事件综合",
        "source": "FY2005 年报；特别分红；Xbox 360 落在下一财年。",
        "environment": "Google 把搜索和广告做成新利润池。苹果在消费电子重新定义体验。微软账上现金过多。",
        "progress": [
            "每股 3 美元特别分红，约 320 亿美元一次性返还。",
            "营收 397.88 亿美元，营业利润 145.6 亿美元。",
            "Xbox 360 进入量产前夜。",
        ],
        "outlook": "用下一代主机抢客厅；用在线服务补搜索；Vista 被内部写成「安全的 Windows」。",
    },
    2006: {
        "author": "Steve Ballmer",
        "source_kind": "年报+事件综合",
        "source": "FY2006 年报口径 + Xbox 360。",
        "environment": "宽带和数字媒体改变消费软件。Vista 延期已经是公开事实。Google 与苹果同时加压。",
        "progress": [
            "Xbox 360 上市，主机业务进入第二代。",
            "营收 442.82 亿美元。",
        ],
        "outlook": "Vista 必须在下一财年出来；在线广告需要买而不是只自研。",
    },
    2007: {
        "author": "Steve Ballmer",
        "source_kind": "股东信综述",
        "source": "FY2007 年报；Vista / Office 2007 / aQuantive。",
        "environment": "消费 PC 换代周期。广告市场被 Google 拿走大部分增量。欧盟继续罚互操作执行不力。",
        "progress": [
            "Windows Vista 面向消费者发布，口碑与驱动兼容成为包袱。",
            "宣布约 60 亿美元收购 aQuantive，补广告技术。",
            "欧盟再罚约 2.805 亿欧元。",
            "Zune 上市，对抗 iPod，后来没形成平台。",
            "营收 511.22 亿美元。",
        ],
        "outlook": "把广告做成搜索之外的第二条在线腿；Windows 7 被内部当成 Vista 的修正版启动。",
    },
    2008: {
        "author": "Bill Gates / Steve Ballmer",
        "source_kind": "股东信综述",
        "source": "FY2008 年报；Gates 卸任全职；雅虎出价。",
        "environment": "金融危机从信贷市场向 IT 预算传导。Google 在搜索和广告已是默认。雅虎被看成最后可买的规模入口。",
        "progress": [
            "出价约 446 亿美元竞购雅虎，未成。",
            "欧盟确定定期罚金约 8.99 亿欧元（后减至 8.60 亿）。",
            "Gates 卸任首席软件架构师，保留董事长，更多时间给慈善。",
            "营收 604.20 亿美元，是危机前高峰。",
        ],
        "outlook": "搜索要自建品牌（后来的 Bing）；云作为服务开始写进战略，但还不是收入柱。",
    },
    2009: {
        "author": "Steve Ballmer",
        "source_kind": "股东信综述",
        "source": "FY2009 年报；公司上市后首次全年营收下降。",
        "environment": "全球衰退，企业推迟 PC 和服务器采购。Google Chrome 发布，浏览器再成战场。",
        "progress": [
            "营收 584.37 亿美元，同比下降，四十年里第一次全年收缩。",
            "Bing 取代 MSN 搜索品牌。",
            "Chrome 发布，IE 份额进入长期下滑。",
        ],
        "outlook": "用 Windows 7 修复 Vista；用 Bing 保搜索入口；云开始从项目变成产品。",
    },
    2010: {
        "author": "Steve Ballmer",
        "source_kind": "股东信综述",
        "source": "FY2010 年报；Windows 7 / Azure 商用。",
        "environment": "iPhone 已经改写计算入口。PC 还在，但增量在手机。欧盟要求浏览器选择屏。",
        "progress": [
            "Windows 7 发布，修复 Vista，换代周期回来。",
            "欧盟浏览器选择屏承诺落地。",
            "Windows Azure 正式商用。",
            "Kin 手机上市约 48 天后停售。",
            "营收 624.84 亿美元。",
        ],
        "outlook": "手机必须有答案；Azure 要从开发者预览变成企业合同。Kin 失败说明硬件不能再试错式发布。",
    },
    2011: {
        "author": "Steve Ballmer",
        "source_kind": "年报+事件综合",
        "source": "FY2011 年报；Skype / 诺基亚联盟 / Windows Phone。",
        "environment": "iOS 与 Android 把手机操作系统锁死。微软在手机上只剩应用和授权，没有默认入口。",
        "progress": [
            "Windows Phone 取代 Windows Mobile。",
            "与诺基亚结盟，把 WP 押成主要硬件伙伴。",
            "宣布 85 亿美元现金收购 Skype。",
            "营收 699.43 亿美元。",
        ],
        "outlook": "用诺基亚补硬件，用 Skype 补通信，用 Azure 补服务器。三条线是否咬合，要看下一轮 Windows。",
    },
    2012: {
        "author": "Steve Ballmer",
        "source_kind": "年报+事件综合",
        "source": "FY2012 年报；aQuantive 减值；Windows 8 / Surface 落在下一财年。",
        "environment": "平板被 iPad 定义。PC 出货即将见顶。广告收购没有换来搜索份额。",
        "progress": [
            "aQuantive 近全额减值，广告并购被账本否定。",
            "营收 737.23 亿美元；营业利润因减值掉到 217.6 亿美元。",
            "Windows 8 与 Surface 进入发布前夜，「设备与服务」被写成公司战略。",
        ],
        "outlook": "用一块屏幕打通 PC / 平板 / 手机；用自有硬件示范。这是 Ballmer 后期的中心赌注。",
    },
    2013: {
        "author": "Steve Ballmer",
        "source_kind": "股东信综述",
        "source": "FY2013 年报，Ballmer 最后一封致股东信。",
        "environment": "Windows 8 的开始屏幕分裂了 PC 用户。Surface 没打开平板市场。手机份额继续丢。",
        "progress": [
            "Surface 自有硬件与 Windows 8 同日发布。",
            "欧盟罚 5.61 亿欧元：违反 2009 浏览器选择承诺。",
            "营收 778.49 亿美元，营业利润回升到 267.6 亿美元。",
        ],
        "outlook": "公开把公司写成「设备与服务」公司。信里仍坚持这条路；几个月后他自己宣布退休。",
    },
    2014: {
        "author": "Satya Nadella",
        "source_kind": "股东信综述",
        "source": "FY2014 Annual Report，Nadella 第一封股东信；主题是 mobile-first, cloud-first。",
        "environment": "PC 出货下滑。Azure 仍远小于 AWS。诺基亚手机刚交割，文化与亏损一并进来。董事会刚换完董事长和 CEO。",
        "progress": [
            "Ballmer 宣布退休，董事会选出 Nadella。",
            "Gates 卸任董事长，John W. Thompson 任独立董事董事长。",
            "诺基亚设备与服务业务交割。",
            "Office for iPad 发布，办公软件不再绑死 Windows。",
            "Surface RT 存货减记约 9 亿美元。",
            "Xbox One 发布。",
            "宣布约 72 亿美元买诺基亚手机业务（2013-09，本财年）。",
        ],
        "outlook": "云优先、移动优先。Windows 仍重要，但不再是唯一平台。文化要从「知道」改成「学习」。",
    },
    2015: {
        "author": "Satya Nadella",
        "source_kind": "股东信综述",
        "source": "FY2015 年报；诺基亚减记；Windows 10 落在下一财年 7 月。",
        "environment": "手机业务被账本否定。云增速成为投资者唯一愿听的故事。Windows 10 被设计成「最后一个大版本」。",
        "progress": [
            "Ballmer 离开董事会。",
            "诺基亚业务减记约 76 亿美元并裁员约 7800 人。",
            "收购 Mojang（Minecraft）25 亿美元。",
            "营收 935.80 亿美元；营业利润掉到 181.6 亿美元，利润率约 19%。",
        ],
        "outlook": "退出自我安慰的手机份额叙事，把资源转到 Azure、Office 365 和 Windows 10 免费升级获取。",
    },
    2016: {
        "author": "Satya Nadella",
        "source_kind": "股东信综述",
        "source": "FY2016 Annual Report；LinkedIn 宣布；Windows 10。",
        "environment": "订阅制办公软件被企业接受。AWS 仍是云第一，但 Azure 已是可信第二。LinkedIn 被看成职业图谱。",
        "progress": [
            "Windows 10 发布，向 Win7/8.1 免费升级。",
            "宣布 262 亿美元收购 LinkedIn。",
            "营收按 ASC 606 重述后 911.54 亿美元（首次公布口径更低）。",
            "三个分部口径成型：生产力、智能云、更多个人计算。",
        ],
        "outlook": "用 LinkedIn 补职业数据，用 Azure 追 AWS，用 365 把许可改成年费。手机不再是董事会主议程。",
    },
    2017: {
        "author": "Satya Nadella",
        "source_kind": "股东信综述",
        "source": "FY2017 Annual Report；LinkedIn 交割年；Teams 上线。",
        "environment": "Slack 在协作层挖 Office。AWS 继续领先。董事会要看云是否能把利润率带回 30% 以上。",
        "progress": [
            "LinkedIn 并表，当年营收 22.7 亿美元量级。",
            "Teams 作为 Office 365 协作工具上线。",
            "营收 965.71 亿美元，营业利润 290 亿美元。",
        ],
        "outlook": "Teams 要做成默认协作层；Azure 继续用企业协议和混合云差异化。",
    },
    2018: {
        "author": "Satya Nadella",
        "source_kind": "股东信综述",
        "source": "FY2018 Annual Report；GitHub；美国税改打击净利润。",
        "environment": "开源已经成为企业默认。微软要让开发者重新信任「微软」这个词。税改一次性打低净利润。",
        "progress": [
            "75 亿美元收购 GitHub。",
            "营收 1103.60 亿美元，首次重新站上千亿美元。",
            "净利润 165.7 亿美元，被税改一次性拖低。",
        ],
        "outlook": "GitHub 保开发者入口；Azure 与 365 继续当增长双引擎。Windows 变成漏斗而不是税。",
    },
    2019: {
        "author": "Satya Nadella",
        "source_kind": "股东信综述",
        "source": "FY2019 Annual Report。公开开始投资 OpenAI。",
        "environment": "市值重新接近苹果。企业上云从「要不要」变成「上哪家」。AI 还写在研究议程，不是产品定价。",
        "progress": [
            "开始投资 OpenAI。",
            "营收 1258.43 亿美元，营业利润 429.6 亿美元，利润率回到约 34%。",
            "智能云成为能在年报里单独讲故事的增长柱。",
        ],
        "outlook": "把 Azure 做成企业经营系统，而不是虚拟机目录。OpenAI 被当成研究期权。",
    },
    2020: {
        "author": "Satya Nadella",
        "source_kind": "股东信综述",
        "source": "FY2020 Annual Report；疫情；Gates 离任董事。",
        "environment": "疫情把远程协作从试点变成生存条件。实体零售和现场活动失效。创始人离开董事会。",
        "progress": [
            "Gates 于 2020-03-13 离开董事会。",
            "Teams 用量跳升，Office 云变成默认办公。",
            "宣布永久关闭实体微软零售店。",
            "营收 1430.15 亿美元，营业利润 529.6 亿美元。",
        ],
        "outlook": "混合工作被写成长期结构，不是几个月的应急。云与安全开支优先于设备。",
    },
    2021: {
        "author": "Satya Nadella",
        "source_kind": "股东信综述",
        "source": "FY2021 Annual Report；Nadella 兼任董事长。",
        "environment": "疫情红利还在。SolarWinds 与 Exchange 攻击把云安全写成生存问题。游戏内容成为并购主题。",
        "progress": [
            "Nadella 于 2021-06-16 兼任董事长，Thompson 改任首席独立董事。",
            "Xbox Series X/S 上市（2020-11，本财年）。",
            "SolarWinds 与 Hafnium 两起国家级攻击。",
            "宣布约 197 亿美元收购 Nuance。",
            "TikTok 美国业务洽购未成。",
            "营收 1680.88 亿美元，净利润 612.7 亿美元。",
        ],
        "outlook": "董事会认为云转型已站稳，允许 CEO 兼董事长。下一步是游戏内容库和语音/医疗 AI（Nuance）。",
    },
    2022: {
        "author": "Satya Nadella",
        "source_kind": "股东信综述",
        "source": "FY2022 Annual Report；Activision 宣布。",
        "environment": "疫情后的 IT 预算仍强。游戏直播和移动游戏是微软没有的腿。通胀开始，但云合同还在涨。",
        "progress": [
            "收购 ZeniMax / 贝塞斯达交割。",
            "Windows 11 发布。",
            "宣布收购 Activision Blizzard（对价后来落到约 687 亿美元）。",
            "营收 1982.70 亿美元。",
        ],
        "outlook": "用 Activision 补移动和广告级游戏 IP；云继续资本开支。监管审批被写成可管理风险。",
    },
    2023: {
        "author": "Satya Nadella",
        "source_kind": "股东信综述",
        "source": "FY2023 Annual Report；Copilot 与 OpenAI 加注；Activision 被英国暂禁。",
        "environment": "ChatGPT 把生成式 AI 做成公共事件。企业 IT 开支突然减速。董事会要同时裁员、加资本开支、打并购官司。",
        "progress": [
            "开启本轮大规模裁员。",
            "宣布对 OpenAI 多年、数十亿美元投资（媒体口径约 100 亿美元）。",
            "英国 CMA 禁止 Activision 交易（后路径改道完成）。",
            "营收 2119.15 亿美元，增速放缓；营业利润 885 亿美元。",
        ],
        "outlook": "把 Copilot 做成每个产品的加价层。资本开支转向 GPU 与数据中心。游戏并购改为「可接受监管条件也要拿下」。",
    },
    2024: {
        "author": "Satya Nadella",
        "source_kind": "股东信综述",
        "source": "FY2024 Annual Report；Activision 交割；OpenAI 董事会危机。",
        "environment": "AI 资本开支竞赛开始。监管把云、办公套件、游戏并购同时放在聚光灯下。OpenAI 治理被证明不是旁观者风险。",
        "progress": [
            "Activision Blizzard 交割，约 687 亿美元。",
            "OpenAI 董事会罢免奥尔特曼；微软公开承接团队，随后重整伙伴治理。",
            "游戏部门裁约 1900 人。",
            "Windows Recall 被批间谍软件，发布受阻。",
            "Midnight Blizzard 进入微软自身租户。",
            "全球提供不含 Teams 的套件。",
            "营收 2451.22 亿美元，营业利润 1094 亿美元。",
        ],
        "outlook": "AI 要变成 Azure 和 365 的单价，而不是演示。安全被董事会写成与 AI 同级的执行项。",
    },
    2025: {
        "author": "Satya Nadella",
        "source_kind": "股东信综述",
        "source": "https://www.microsoft.com/investor/reports/ar25/index.html ；FY2025 10-K。",
        "environment": "客户要看 AI 是否能进业务流程，而不只是聊天。电力、芯片和资本开支变成云增长的物理上限。欧盟继续管捆绑。",
        "progress": [
            "Skype 停服，并入 Teams。",
            "两轮合计约裁 1.5 万人，边裁员边加 AI 资本开支。",
            "Azure 全年约 750 亿美元，公司后来在产品表单列。",
            "营收 2817.24 亿美元，净利润 1018 亿美元。",
        ],
        "outlook": "继续把 Copilot 席位做上去；数据中心与电网约束被写进展望。治理上要同时应付欧盟承诺和 AI 伙伴风险。",
    },
    2026: {
        "author": "Satya Nadella",
        "source_kind": "业绩稿+10-K MD&A",
        "source": "2026-07-29 业绩稿 / FY2026 10-K MD&A。年度图文股东信通常略晚于 10-K。",
        "environment": "AI 从叙事进入利润表：云资本开支超过 1100 亿美元，客户同时问投资回报。OpenAI 不再是独家 API。Windows 消费 AI 和游戏内容没有跟上云的利润率。",
        "progress": [
            "营收 3318 亿美元；Azure 全年破 1000 亿美元；Copilot 付费席位超 3000 万。",
            "资本开支 1159 亿美元。",
            "欧盟 Teams 捆绑案以承诺决定结案。",
            "重订 OpenAI：API 不再独占，OpenAI 可上 AWS 等。",
            "报道收缩 Windows 11 Copilot 铺量，重估 Recall。",
            "再裁约 4800 人；Xbox 侧约 3200、剥离最多五家工作室（7 月，紧挨财年结束）。",
        ],
        "outlook": "云和 365 被账本证明；Windows 消费 AI、游戏并购和安全事件没有同等证明。展望围绕 AI 单价、资本开支纪律和 OpenAI 关系的非独占现实。",
    },
}


def fy_of(date: str) -> int:
    raw = str(date).split("/")[0]
    year = int(raw[:4])
    if len(raw) == 4:
        return year
    month = int(raw[5:7])
    return year if month <= 6 else year + 1


def _pct(num, den):
    if num is None or den in (None, 0):
        return None
    return round(100.0 * float(num) / float(den), 1)


def _yoy(cur, prev):
    if cur is None or prev in (None, 0):
        return None
    return round(100.0 * (float(cur) - float(prev)) / float(prev), 1)


def _money(value):
    if value is None:
        return None
    n = float(value)
    if abs(n) >= 100:
        yi = n / 100.0
        text = f"{yi:.0f}" if yi >= 10 else f"{yi:.1f}"
        return f"{text} 亿美元"
    return f"{n:.0f} 百万美元"


def leaders_on(iso: str) -> tuple[str, str]:
    if iso < "2000-01-13":
        return "Bill Gates", "Bill Gates"
    if iso < "2014-02-04":
        return "Steve Ballmer", "Bill Gates"
    if iso < "2021-06-16":
        return "Satya Nadella", "John W. Thompson"
    return "Satya Nadella", "Satya Nadella"


def event_fy(row: dict) -> int:
    date = str(row.get("date") or "")
    # Annual earnings sit in late July, after the FY close they report.
    if date.startswith("2026-07-29"):
        return 2026
    if date.startswith("2026-07-06"):
        return 2026
    return fy_of(date)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build() -> dict:
    fy_payload = load_json(FY_PATH)
    events = load_json(EVENTS).get("events") or []
    years_fin = {int(r["fy"]): r for r in fy_payload.get("years") or []}
    prev = None
    by_fy: dict[int, list] = {}
    for ev in events:
        fy = event_fy(ev)
        by_fy.setdefault(fy, []).append(
            {"date": ev.get("date"), "type": ev.get("type"), "event": ev.get("event")}
        )

    gov_by_fy: dict[int, list] = {}
    timeline = []
    for item in GOVERNANCE:
        fy = item.get("fy")
        row = {
            "date": item["date"],
            "fy": fy,
            "title": item["title"],
            "who": item["who"],
            "detail": item["detail"],
        }
        timeline.append(row)
        if fy:
            gov_by_fy.setdefault(int(fy), []).append(row)

    reports = []
    for fy in sorted(years_fin):
        fin = years_fin[fy]
        letter = LETTERS.get(fy) or {}
        ceo, chair = leaders_on(f"{fy}-06-30")
        yoy_rev = _yoy(fin.get("revenue"), (prev or {}).get("revenue") if prev else None)
        op_m = _pct(fin.get("operating_income"), fin.get("revenue"))
        net_m = _pct(fin.get("net_income"), fin.get("revenue"))
        reports.append(
            {
                "fy": fy,
                "period": f"{fy - 1}-07-01 ~ {fy}-06-30",
                "ceo": ceo,
                "chair": chair,
                "letter_author": letter.get("author") or ceo,
                "source_kind": letter.get("source_kind") or "年报+事件综合",
                "source": letter.get("source") or "当年 10-K MD&A 与事件台账。",
                "environment": letter.get("environment") or "",
                "progress": list(letter.get("progress") or []),
                "outlook": letter.get("outlook") or "",
                "board_moves": gov_by_fy.get(fy, []),
                "year_events": by_fy.get(fy, []),
                "financials": {
                    "revenue_usd_m": fin.get("revenue"),
                    "revenue_yoy_pct": yoy_rev,
                    "rd_usd_m": fin.get("rd"),
                    "operating_income_usd_m": fin.get("operating_income"),
                    "op_margin_pct": op_m,
                    "net_income_usd_m": fin.get("net_income"),
                    "net_margin_pct": net_m,
                    "capex_usd_m": fin.get("capex"),
                    "revenue_text": _money(fin.get("revenue")),
                    "operating_income_text": _money(fin.get("operating_income")),
                    "net_income_text": _money(fin.get("net_income")),
                },
            }
        )
        prev = fin

    payload = {
        "issuer": "Microsoft Corporation",
        "ticker": "MSFT",
        "as_of": fy_payload.get("as_of"),
        "fiscal_year_end": fy_payload.get("fiscal_year_end") or "June 30",
        "method": (
            "美国 10-K 没有 A 股「董事会报告」科目。本文件按财年（截止 6 月 30 日）"
            "把股东信 / 年报 MD&A / 物质事件折成同一组标题：当时环境、项目进展、未来展望；"
            "董事会人事与资本回报单独做成执行时间线。股东信综述是压缩，不是原文。"
        ),
        "year_count": len(reports),
        "governance": timeline,
        "years": reports,
    }
    return payload


def write_report_md(payload: dict) -> None:
    reports_dir = ROOT / "reports"
    reports_dir.mkdir(exist_ok=True)
    path = reports_dir / "MSFT_board_reports_2026-09-07.md"
    lines = [
        "# 微软董事会报告（按财年）",
        "",
        payload["method"],
        "",
        f"覆盖 FY{payload['years'][0]['fy']}–FY{payload['years'][-1]['fy']}，共 {payload['year_count']} 年。",
        "页：`docs/company.html`。数据：`data/issuers/MSFT/board_reports.json`，由 `listed_trust/enrich_board_reports.py` 写入。",
        "",
        "## 董事会执行时间线",
        "",
    ]
    for row in payload["governance"]:
        fy = f"FY{row['fy']} · " if row.get("fy") else ""
        lines.append(f"- **{row['date']}** {fy}{row['title']} — {row['who']}")
        lines.append(f"  {row['detail']}")
    lines += ["", "## 各年摘要", ""]
    for y in payload["years"]:
        fin = y["financials"]
        yoy = fin.get("revenue_yoy_pct")
        yoy_s = f"，营收同比 {yoy:+.1f}%" if yoy is not None else ""
        lines.append(f"### FY{y['fy']}（{y['period']}）")
        lines.append("")
        lines.append(
            f"CEO {y['ceo']} · 董事长 {y['chair']} · {y['source_kind']} · "
            f"营收 {fin.get('revenue_text')}{yoy_s} · 营业利润率 {fin.get('op_margin_pct')}%。"
        )
        lines.append("")
        lines.append(f"**环境。** {y['environment']}")
        lines.append("")
        lines.append("**进展。**")
        for b in y["progress"]:
            lines.append(f"- {b}")
        lines.append("")
        lines.append(f"**展望。** {y['outlook']}")
        lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {path}")


def main() -> None:
    payload = build()
    missing = [y["fy"] for y in payload["years"] if not y["environment"]]
    if missing:
        raise SystemExit(f"missing letter overlay for FY {missing}")
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report_md(payload)
    print(f"wrote {OUT} ({payload['year_count']} years, {len(payload['governance'])} governance rows)")


if __name__ == "__main__":
    main()
