"""CLI: screen issuers, score titles/financials, and verify original filings."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from listed_trust.report import write_report
from listed_trust.score import analyze_company
from listed_trust.universe import lookup_company, save_universe


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="上市十年以上公司：财报原文、承诺与解释核验"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    uni = sub.add_parser("universe", help="筛选上市满 N 年的公司名单")
    uni.add_argument("--years", type=int, default=10)
    uni.add_argument("--out", type=Path, default=None)

    ana = sub.add_parser("analyze", help="对单家公司生成七维报告（财务指标+公告标题）")
    ana.add_argument("code", help="股票代码，如 600519")
    ana.add_argument("--years", type=int, default=10)
    ana.add_argument("--no-esg", action="store_true")
    ana.add_argument("--out", type=Path, default=None)

    batch = sub.add_parser("batch", help="批量分析，逗号分隔代码")
    batch.add_argument("codes", help="例如 600519,000002")
    batch.add_argument("--years", type=int, default=10)
    batch.add_argument("--no-esg", action="store_true")
    batch.add_argument("--out", type=Path, default=None)

    corpus = sub.add_parser("corpus", help="下载巨潮原文 PDF，抽取承诺/解释并逐条核验")
    corpus.add_argument("code", help="股票代码，如 600519")
    corpus.add_argument("--years", type=int, default=10)
    corpus.add_argument("--skip-download", action="store_true")

    args = parser.parse_args(argv)
    if args.cmd == "corpus":
        from listed_trust.claims import extract_claims
        from listed_trust.cninfo import download_corpus
        from listed_trust.pdftext import extract_corpus
        from listed_trust.verify_claims import verify_claims

        code = str(args.code).zfill(6)
        if not args.skip_download:
            dl = download_corpus(code, years=args.years)
            print(
                json.dumps(
                    {"download": {k: dl[k] for k in ("code", "folder", "count", "downloaded")}},
                    ensure_ascii=False,
                )
            )
        texts = extract_corpus(code)
        print(json.dumps({"extract": {k: texts[k] for k in ("code", "count", "ocr_needed")}}, ensure_ascii=False))
        claims = extract_claims(code)
        print(json.dumps({"claims": {"count": claims["count"]}}, ensure_ascii=False))
        verified = verify_claims(code, years=args.years)
        print(
            json.dumps(
                {
                    "verify": {
                        "count": verified["count"],
                        "counts": verified["counts"],
                        "path": f"data/filings/{code}/verified_claims.json",
                    }
                },
                ensure_ascii=False,
            )
        )
        return 0

    if args.cmd == "universe":
        frame = save_universe(path=args.out, min_years=args.years)
        print(f"eligible={len(frame)} years>={args.years}")
        print(frame.head(8).to_string(index=False))
        return 0

    codes = [args.code] if args.cmd == "analyze" else [c.strip() for c in args.codes.split(",") if c.strip()]
    for code in codes:
        listing = lookup_company(code)
        report = analyze_company(
            code,
            years=args.years,
            with_esg=not args.no_esg,
            listing=listing or None,
        )
        json_path, md_path = write_report(report, out_dir=args.out)
        print(
            json.dumps(
                {
                    "code": report["code"],
                    "name": report["name"],
                    "credibility": report["credibility"]["score"],
                    "sustainability": report["sustainability"]["score"],
                    "json": str(json_path),
                    "markdown": str(md_path),
                },
                ensure_ascii=False,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
