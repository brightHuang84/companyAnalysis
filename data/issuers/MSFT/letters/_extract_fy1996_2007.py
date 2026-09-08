#!/usr/bin/env python3
"""Extract official Chinese letter prose from downloaded Microsoft AR HTML."""
from html.parser import HTMLParser
from pathlib import Path
import re
import json

SRC = Path("/tmp/msft-letters")
OUT = Path("/home/bright/cryto/data/issuers/MSFT/letters/_extracted_official.json")


class ParaExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.paras = []
        self.buf = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "select", "option", "noscript"}:
            self.skip += 1
        if tag in {"p", "br", "h1", "h2", "h3", "h4", "li"} and self.skip == 0:
            self._flush()

    def handle_endtag(self, tag):
        if tag in {"script", "style", "select", "option", "noscript"} and self.skip:
            self.skip -= 1
        if tag in {"p", "h1", "h2", "h3", "h4", "li", "td"} and self.skip == 0:
            self._flush()

    def handle_data(self, data):
        if self.skip:
            return
        self.buf.append(data)

    def _flush(self):
        t = "".join(self.buf)
        t = t.replace("\xa0", " ").replace("\u3000", " ")
        t = re.sub(r"\s+", " ", t).strip()
        self.buf = []
        if t:
            self.paras.append(t)


def decode(path: Path) -> str:
    raw = path.read_bytes()
    head = raw[:5000].decode("latin-1", "ignore").lower()
    if "charset=utf-8" in head or "charset=utf8" in head:
        return raw.decode("utf-8", "replace")
    if "charset=gb2312" in head or "charset=gbk" in head or "charset=gb18030" in head:
        return raw.decode("gb18030", "replace")
    for enc in ("utf-8", "gb18030"):
        try:
            t = raw.decode(enc)
            if "股东" in t or "微软" in t:
                return t
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace")


def clean_text(s: str) -> str:
    s = s.replace("<?/FONT>", "").replace("?/FONT>", "")
    s = s.replace("<FONT>", "").replace("</FONT>", "")
    s = re.sub(r"</?/?FONT>", "", s, flags=re.I)
    s = s.replace("\u6a24\u0e5c\u8bd8", "——")  # mojibake emdash
    s = s.replace("椯侑", "——")
    s = s.replace("—Ù§—Ù§", "——")
    s = s.replace("比尔×盖茨", "比尔·盖茨")
    s = s.replace("史蒂夫×鲍尔默", "史蒂夫·鲍尔默")
    s = s.replace("史蒂夫A.鲍尔默", "史蒂夫·A.鲍尔默")
    s = s.replace("", "“").replace("", "”")
    s = s.replace("牋", "")
    s = re.sub(r"^[\.．]\s*", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def extract_file(name: str) -> list[str]:
    html = decode(SRC / name)
    p = ParaExtractor()
    p.feed(html)
    out = []
    for para in p.paras:
        para = clean_text(para)
        if not para:
            continue
        low = para.lower()
        if any(
            x in low
            for x in (
                "last updated",
                "all rights reserved",
                "terms of use",
                "privacy policy",
                "javascript",
                "choose:",
                "alternative languages",
                "return to top",
                "click here",
                "downloads",
                "we see potential",
                "investor relations",
                "financial highlights",
                "form 10-k",
            )
        ):
            continue
        if para in {
            "msft",
            "ENGLISH",
            "English",
            "Canadien",
            "Français",
            "Deutsch",
            "Español",
            "Italiano",
            "Nederlands",
            "Português (Brasil)",
            "Português (Portugal)",
            "CANADIEN FRANÇAIS",
            "PORTUGUESE-BRASIL",
            "PORTUGUESE-PORTUGAL",
            "TÜRKÇE",
            "FINANCIALS",
            "FINANCIAL CHARTS",
            "MD&A",
            "FINANCIAL STATEMENTS",
            "INCOME",
            "BALANCE SHEETS",
            "CASH FLOWS",
            "STOCKHOLDERS’ EQUITY",
            "NOTES",
            "LETTER TO SHAREHOLDERS",
        }:
            continue
        if re.fullmatch(r"[A-ZÉÇÃÕÍÓÚÂÊÁ /’'\-]+", para) and len(para) < 40:
            continue
        out.append(para)
    return out


def slice_letter(paras, start_pred, end_pred, drop_after=None):
    start = 0
    for i, p in enumerate(paras):
        if start_pred(p):
            start = i
            break
    end = len(paras)
    for i, p in enumerate(paras[start + 1 :], start + 1):
        if end_pred(p):
            end = i + 1
            break
    sliced = paras[start:end]
    if drop_after:
        for i, p in enumerate(sliced):
            if drop_after(p) and i > 3:
                sliced = sliced[:i]
                break
    return sliced


FILES = {
    1998: "fy1998_zh.htm",
    1999: "fy1999_zh.htm",
    2000: "fy2000_zh.htm",
    2001: "fy2001_zh.htm",
    2002: "fy2002_zh.htm",
    2003: "fy2003_zh.htm",
    2004: "fy2004_zh.htm",
    2005: "fy2005_zh.htm",
    2006: "fy2006_zh.htm",
    2007: "fy2007_zh.htm",
}

raw = {fy: extract_file(name) for fy, name in FILES.items()}

# Year-specific letter bounds
letters = {}
letters[1998] = slice_letter(
    raw[1998],
    lambda p: "对于微软公司来说，1998年是不平凡" in p,
    lambda p: p.startswith("比尔") or p == "Bill Gates",
)
letters[1999] = slice_letter(
    raw[1999],
    lambda p: "微软公司在 99 财年度" in p or "微软公司在99财年度" in p,
    lambda p: "一如既往的鼎力支持" in p,
    drop_after=lambda p: p.startswith("微软以客户为中心") and "再创辉煌" not in p,
)
letters[2000] = slice_letter(
    raw[2000],
    lambda p: p.startswith("1975年"),
    lambda p: "史蒂夫" in p and "鲍尔默" in p,
)
letters[2001] = slice_letter(
    raw[2001],
    lambda p: p.startswith("20年前"),
    lambda p: "通过任何设备进行沟通和创造" in p,
)
letters[2002] = slice_letter(
    raw[2002],
    lambda p: "2002财年是微软公司收入稳固增长" in p,
    lambda p: "谢谢你们的支持" in p,
)
letters[2003] = slice_letter(
    raw[2003],
    lambda p: "2003 财政年度充满了激动人心" in p or "2003财政年度充满了激动人心" in p,
    lambda p: "深深地感谢您对我们工作的大力支持" in p,
)
letters[2004] = slice_letter(
    raw[2004],
    lambda p: "2004 财政年度的业绩非常好" in p or "2004财政年度的业绩非常好" in p,
    lambda p: "感谢您一直以来的支持" in p,
)
letters[2005] = slice_letter(
    raw[2005],
    lambda p: "2005 财年是 Microsoft 又一个丰收" in p or "2005财年是 Microsoft 又一个丰收" in p,
    lambda p: "谢谢大家" in p,
)
letters[2006] = slice_letter(
    raw[2006],
    lambda p: "2006 财政年是微软取得重大成就" in p or "2006财政年是微软取得重大成就" in p,
    lambda p: "谢谢大家" in p,
)
letters[2007] = slice_letter(
    raw[2007],
    lambda p: "对于微软而言，2007 财年是硕果累累" in p or "对于微软而言，2007财年是硕果累累" in p,
    lambda p: "谢谢大家" in p,
)

# Merge accidental line-splits that start with a year/product fragment
def merge_splits(paras):
    merged = []
    for p in paras:
        if merged and (
            (len(p) < 40 and re.match(r"^[\d.]+", p))
            or p.startswith(".NET")
            or p.startswith("2000")
            and merged[-1].endswith(("Windows", "Office", "Microsoft", "Xbox", "Windows®"))
        ):
            merged[-1] = merged[-1] + p
        else:
            merged.append(p)
    return merged


letters = {k: merge_splits(v) for k, v in letters.items()}
OUT.write_text(json.dumps(letters, ensure_ascii=False, indent=2), encoding="utf-8")
for fy, paras in letters.items():
    print(f"FY{fy}: {len(paras)} paras; first={paras[0][:60] if paras else 'EMPTY'}... last={paras[-1][:60] if paras else ''}")
