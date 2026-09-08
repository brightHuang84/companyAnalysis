#!/usr/bin/env python3
"""Assemble fy1996_2007.json from official Chinese extracts + FY1996–97 translations."""
import json
import re
from pathlib import Path

EXTRACT = Path("/home/bright/cryto/data/issuers/MSFT/letters/_extracted_official.json")
OUT = Path("/home/bright/cryto/data/issuers/MSFT/letters/fy1996_2007.json")

official = json.loads(EXTRACT.read_text(encoding="utf-8"))


def tidy(paras):
    out = []
    i = 0
    while i < len(paras):
        p = paras[i]
        p = p.replace("\u0000", "")
        p = p.replace("�٧�٧", "——")
        p = p.replace("\ufffd", "")
        p = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", p)
        p = p.replace("\ufffd", "")
        p = re.sub(r"^[\.．•·]\s*", "", p)
        p = re.sub(r"^[　\s]+", "", p)
        p = re.sub(r"\s+", " ", p).strip()
        p = p.replace("创 新 的 力 量", "创新的力量")
        p = p.replace("关 心 用 户", "关心用户")
        if p in {"•", ".", "．"}:
            i += 1
            continue
        if p in {
            "比尔.盖茨",
            "比尔 盖茨",
            "董事会主席兼首席软件设计师",
            "总裁兼首席执行官",
            "史蒂夫 鲍尔默",
            "Bill Gates",
        }:
            i += 1
            continue
        # merge heading leftover ".NET" / "2001" / "2002" glued to previous
        if p.endswith("2001") and len(p) > 10:
            body, head = p[:-4].rstrip("。"), "2001"
            out.append(body + "。")
            out.append(head)
            i += 1
            continue
        if p.endswith("2002") and "在2002财年" not in p and len(p) > 20:
            body = p[:-4].rstrip()
            out.append(body)
            out.append("2002")
            i += 1
            continue
        if p == "NET和XML Web Service的美好未来":
            p = ".NET和XML Web Service的美好未来"
        # merge "我们一直在努力确保" + next
        if p.endswith("我们一直在努力确保") and i + 1 < len(paras):
            nxt = tidy([paras[i + 1]])
            if nxt:
                p = p + nxt[0]
                i += 2
                out.append(p)
                continue
        if p.endswith("我们正在设法为我们的开发商") and i + 1 < len(paras):
            nxt = paras[i + 1].strip()
            p = p + nxt
            i += 2
            out.append(p)
            continue
        p = p.rstrip("\ufffd")
        if p:
            out.append(p)
        i += 1
    return out


FY1996_PARAS = [
    "我们对互联网产生了巨大影响，互联网也对我们也产生了巨大影响。",
    "在微软21年的历史上，创新的步伐一直很快。过去这一年尤为突出：既有令人振奋的新产品，也有人们普遍认识到计算机将彻底改变通信。Windows 95发布后，4000万人体会到了它的好处：易用、32位应用，以及更高的生产力。Windows NT形成了惊人的销售势头，并作为企业市场的基础、以及新一代企业内联网和Web服务器，获得了广泛接受。",
    "互联网走向成熟，微软拥抱这一机遇，增强了全线产品与服务，为从普通上网者到企业IT经理的每个人创造最佳Web体验。微软押注未来十年互联网使用将大幅增长。明年广义的研发支出将增至20亿美元以上，增速快于销售。我们的研发由客户反馈驱动，也源于我们的信念：只要采取长期视角，软件领域仍有许多突破可以实现。",
    "在与金融界的对话中，我们特意指出维持或提高盈利能力所面临的挑战。这种审慎是我们文化的一部分。尽管如此，我们仍认为未来十年业务前景非常强劲。",
    "我要感谢我们的员工、客户、合作伙伴和股东，感谢他们在建设微软过程中给予的全部支持。",
]

# Fix awkward first sentence
FY1996_PARAS[0] = "我们对互联网产生了巨大影响。互联网也对我们也产生了巨大影响。"
FY1996_PARAS[0] = "我们深刻影响了互联网，互联网也深刻影响了我们。"

FY1997_PARAS = [
    "1997年是出色的一年。客户要求微软做出能让他们从互联网中获得商业收益的产品，我们做到了。无论是生产力应用、工具、桌面系统还是服务器产品，我们都在全面获得显著动能。如同我们23年历史上的任何时候一样，我们拥有巨大机遇，也面临若干威胁。",
    "我们在1998财年的首要任务是简洁：降低总拥有成本，并降低复杂性。即便我们要推出众多产品、即便竞争对手在多个战线与我们交锋，我们也必须守住这一焦点。",
    "展望前路，我们聚焦四个关键领域：",
    "桌面上的Windows。",
    "几年前，我们提出了“Windows无处不在”的构想：一套架构，让客户拥有一族操作系统和一套兼容应用，覆盖从极小到极大的各类设备。我们已成功把计算桌面推进到32位系统——Microsoft Windows 95和Windows NT Workstation——并推出了Windows CE，这是最初面向移动专业人士手持设备的新版Windows操作系统。Microsoft Internet Explorer 4.0将是我们把PC与互联网结合的又一次重大进展。Windows的一项核心优势是其开发工具集合，让开发者能够发掘我们平台的丰富能力，并从他们的应用中获得出色性能。",
    "生产力应用。",
    "Microsoft Office 97是一次重大发布，在功能、特性和集成上设立了新标杆。我们为此投入了多年研发，并纳入了研究部门的一些发现。Office 97具备自然语言系统和复杂的语法检查。但这只是开始。我们的目标是让人们以尽可能轻松的方式完成工作，而不必去想他们正在使用哪些工具。",
    "企业解决方案。",
    "Windows NT Server和Microsoft BackOffice系列服务器应用正以惊人速度增长。随着芯片越来越快，我们已能向客户交付以往只有大型机才能实现的性能。除了性能，我们现在还聚焦简洁与可管理性。但要把高端计算做得更轻松、成本更低，我们还有很多工作要做。",
    "交互媒体与服务。",
    "我们的交互媒体集团（IMG）有三个重点：套装软件、硬件和在线服务。它们都是为了增强围绕PC和Web生活方式的消费体验。套装软件的努力集中在游戏、学习、个人理财和地图等品类交付出色作品。在硬件上，我们的目标是增强软件体验。",
    "在在线服务上，重点是做出软件与内容的激动人心组合，帮助客户借助互联网过上更知情、更有趣、更有生产力的生活。你们会越来越多地看到我们强调那些软件卓越能带来差异的产品与服务。我们在这一新领域的部分投资会有回报——有些则不会。我们还有很多要学。和网上其他所有人一样，我们并不知道收入组合会是什么——订阅、广告，还是促销。",
    "数字神经系统",
    "我用“数字神经系统”来指公司用来解决业务和客户问题的电子系统。出色的数字神经系统始于强大的操作系统和网络，但任何企业若要自动化，还必须拥有出色的数据库系统和消息系统。多年来，微软在Microsoft SQL Server和Microsoft Exchange以及BackOffice其他组件的技术开发上投入巨大，聘请最优秀的人才，打造性能与互操作性出色的产品。",
    "今年我们还将大力投资对垂直市场软件开发者和解决方案提供商的技术与营销支持。我们希望确保几乎任何客户都能在高性能的Windows系统上找到自己的具体业务应用。你们也会看到我们对全球企业客户覆盖的扩大。这些都是在销售增长温和时期的重大投资。",
    "5月20日，我们与客户举行了“可伸缩性日”，这是一个重要里程碑，因为我们证明了任何规模的公司都可以用我们的软件、在PC硬件上构建的解决方案来运营业务。硬件厂商一直在以大型机价格的一小部分生产世界级机器。我非常乐观：企业客户会像他们在桌面上已经认识到的那样，认识到性能提升、质量上升、价格下降，使个人电脑服务器成为最佳选择。",
    "简洁",
    "在1998财年，我们预计广义研发支出将接近26亿美元。看到微软引进世界级专家从事网络、安全、图形和语言学等工作，我非常振奋。",
    "我们的行业制造出令人难以置信的生产力设备，正在影响世界各地的人们。但技术的复杂性阻碍了用户和系统管理员从其投资中获得最大价值。在应用、工具、桌面与服务器系统以及交互内容上，我们都必须为用户和系统管理员把事情做得更简单。三大领域是：总拥有成本（TCO）与可管理性、降低复杂性，以及低端的新型、更简单设备。",
    "总拥有成本。",
    "应对TCO对各种规模的公司都很重要。问题不只是降低成本——而是在不增加复杂性的前提下提高可用性与功能。我们的零管理计划就是这里的焦点。",
    "我们相信每位知识工作者都应当拥有一台个人电脑。我们相信员工不只是机器上的齿轮。我们相信企业成功是因为员工的智慧与创造力。我们相信，企业要在这个快节奏世界中保持竞争力，就需要数字化做法。但要让客户真正收获建设数字神经系统的回报，我们必须帮助他们摆脱不得不把大量资源只用于维持系统运转的跑步机。",
    "Windows NT Server 5.0是应对TCO问题的重大突破。它将让组织轻松控制用户配置，智能地把客户端机器状态镜像到服务器上，并允许用户在机器之间漫游。我们还将使移动用户在旅途中充分受益于自己的机器，并在返回时能够与服务器完全同步，从而保护本地数据和系统状态。我们将把PC的力量与灵活性，与集中管理的好处结合起来。",
    "降低复杂性。",
    "尽管我们坚信个人电脑的力量，但并非一种规格适合所有人。有些客户拥有较旧的PC硬件，出于各种原因还不准备升级。有些需要为许多员工提供更简单的标准配置。有些客户已在终端上有既有投资。",
    "我们已与其他公司合作推出NetPC和基于Windows的终端。NetPC是一种更简单、更易管理的企业桌面PC配置，PC厂商现已开始推出。基于Windows的终端背后的技术，通过在服务器上运行有限数量的较新应用来延长较旧、性能较弱PC的寿命，从而帮助客户，也为我们打开了一个新的客户细分。",
    "新设备。",
    "“Windows无处不在”意味着我们既向上扩展，也向下扩展。我们的Windows CE操作系统最初聚焦手持设备。用户将从监控库存的零售店员，到为病人做记录的医护人员，再到安装电线的公用事业工人。",
    "Windows CE也将适用于更小的“钱包”PC、数字信息寻呼机和蜂窝智能手机等无线通信设备、下一代娱乐与多媒体控制台（包括游戏机和更智能的DVD播放器），以及WebTV、有线与卫星数字机顶盒、互联网“网络电话”等专用互联网接入设备。",
    "互联的PC，互联的电视",
    "我们长期以来认为，PC正从独立PC走向互联PC。今天，这一进程已全面展开。PC网络在企业中已广泛存在，互联网正在创造一张全球PC之网。Windows NT 5.0和Windows 98将进一步使PC互联。我们的愿景现已演进为“互联的PC与互联的电视”——把PC的智能与交互，与电视的影像和声音结合起来。随着电视走向数字格式，这将加速。实现这一愿景依赖于物理基础设施——把这些设备连接起来的高速连接。今年早些时候，我们投资了美国第四大有线公司Comcast，主要是为了推动有线和电话行业建设双向高速网络。我们收购WebTV，是为了加快电视和PC使用Windows技术、在家中提供互补的信息与娱乐来源的那一天到来。Windows CE作为我们Windows家族的兼容子集，让消费电子厂商更容易做出定制电视节目指南，或让你在电视上浏览网页、查看简单电子邮件、控制家中供暖和照明，甚至接上数码相机、通过互联网发布或电邮照片。",
    "这些发展，加上我们在IMG的工作，将帮助使“Web生活方式”成为现实。这是一种人们利用互联网过上更知情、更有生产力、也更有乐趣的生活的方式。有了Web生活方式，人们会自然而然地首先转向互联网去获取信息、管理财务、做出更好的购买和旅行决策，并与朋友以及有共同兴趣的人交流。",
    "我们的业务充满风险与挑战，也有巨大的潜在回报。我感谢股东们对公司长期愿景与潜力持续的信任与支持。我有信心，通过员工的奉献与努力，我们能够交付既成就微软、也成就客户的产品与服务。",
]


def year_entry(fy, author, role, source_kind, source, source_url, greeting, paragraphs):
    return {
        "fy": fy,
        "author": author,
        "role": role,
        "date": "",
        "source_kind": source_kind,
        "source": source,
        "source_url": source_url,
        "greeting": greeting,
        "paragraphs": paragraphs,
    }


years = [
    year_entry(
        1996,
        "Bill Gates",
        "董事长兼首席执行官",
        "年报股东信原文翻译",
        "Microsoft 1996 Annual Report, Letter from Bill Gates",
        "https://www.microsoft.com/investor/reports/ar96/lb.htm",
        "",
        FY1996_PARAS,
    ),
    year_entry(
        1997,
        "Bill Gates",
        "董事长兼首席执行官",
        "年报股东信原文翻译",
        "Microsoft 1997 Annual Report, Letter to Shareholders",
        "https://www.microsoft.com/investor/reports/ar97/bill_letter/bill_letter.htm",
        "",
        FY1997_PARAS,
    ),
    year_entry(
        1998,
        "Bill Gates",
        "董事长兼首席执行官",
        "年报股东信官方中文",
        "Microsoft 1998 Annual Report, 致股票持有人的公开信",
        "https://www.microsoft.com/investor/reports/ar98/lts-chinese.htm",
        "",
        tidy(official["1998"]),
    ),
    year_entry(
        1999,
        "Bill Gates",
        "董事长兼首席执行官",
        "年报股东信官方中文",
        "Microsoft 1999 Annual Report, 致股东的一封信",
        "https://www.microsoft.com/investor/reports/ar99/lts-chinese.htm",
        "股票持有者全体同仁",
        tidy(official["1999"]),
    ),
    year_entry(
        2000,
        "Bill Gates / Steve Ballmer",
        "董事会主席兼首席软件设计师 / 总裁兼首席执行官",
        "年报股东信官方中文",
        "Microsoft 2000 Annual Report, 致股东的一封信",
        "https://www.microsoft.com/investor/reports/ar00/lts-chinese.htm",
        "",
        tidy(official["2000"]),
    ),
    year_entry(
        2001,
        "Bill Gates / Steve Ballmer",
        "董事会主席兼首席软件设计师 / 首席执行官",
        "年报股东信官方中文",
        "Microsoft 2001 Annual Report, 致股东的一封信",
        "https://www.microsoft.com/investor/reports/ar01/low/shareholderltr_chi.htm",
        "致股东、客户、合作伙伴和全体员工",
        tidy(official["2001"]),
    ),
    year_entry(
        2002,
        "Bill Gates / Steve Ballmer",
        "董事会主席兼首席软件设计师 / 首席执行官",
        "年报股东信官方中文",
        "Microsoft 2002 Annual Report, 致股东的一封信",
        "https://www.microsoft.com/investor/reports/ar02/shareholder_letter/letter_chi.htm",
        "",
        tidy(official["2002"]),
    ),
    year_entry(
        2003,
        "Bill Gates / Steve Ballmer",
        "董事长兼首席软件设计师 / 首席执行官",
        "年报股东信官方中文",
        "Microsoft 2003 Annual Report, 致股东的一封信",
        "https://www.microsoft.com/investor/reports/ar03/chinese.htm",
        "尊敬的股东、客户、合作伙伴和雇员们：",
        tidy(official["2003"]),
    ),
    year_entry(
        2004,
        "Bill Gates / Steve Ballmer",
        "董事长兼首席软件设计师 / 首席执行官",
        "年报股东信官方中文",
        "Microsoft 2004 Annual Report, 致股东的一封信",
        "https://www.microsoft.com/investor/reports/ar04/nonflash/10k_sl_chi.html",
        "致股东、客户、合作伙伴和员工：",
        tidy(official["2004"]),
    ),
    year_entry(
        2005,
        "Bill Gates / Steve Ballmer",
        "主席及首席软件设计师 / 首席执行官",
        "年报股东信官方中文",
        "Microsoft 2005 Annual Report, 致股东的一封信",
        "https://www.microsoft.com/investor/reports/ar05/staticversion/10k_sl_chi.html",
        "致股东、客户、合作伙伴及员工：",
        tidy(official["2005"]),
    ),
    year_entry(
        2006,
        "Bill Gates / Steve Ballmer",
        "董事长 / 首席执行官",
        "年报股东信官方中文",
        "Microsoft 2006 Annual Report, 致股东的一封信",
        "https://www.microsoft.com/investor/reports/ar06/staticversion/10k_sl_chi.html",
        "致尊敬的股东、客户、合作伙伴及员工：",
        tidy(official["2006"]),
    ),
    year_entry(
        2007,
        "Bill Gates / Steve Ballmer",
        "董事长 / 首席执行官",
        "年报股东信官方中文",
        "Microsoft 2007 Annual Report, 致股东的一封信",
        "https://www.microsoft.com/investor/reports/ar07/staticversion/10k_sl_chi.html",
        "尊敬的股东、客户、合作伙伴及员工：",
        tidy(official["2007"]),
    ),
]

payload = {"years": years, "missing": []}
OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print("Wrote", OUT)
for y in years:
    print(
        f"FY{y['fy']}: {y['source_kind']}  paras={len(y['paragraphs'])}  "
        f"chars={sum(len(p) for p in y['paragraphs'])}"
    )
