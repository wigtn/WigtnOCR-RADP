"""Answer-coverage diagnostic — attribute the parsing-retrieval gap to parser vs chunker.

Holds the parser output fixed (WigtnOCR v1) and varies the chunker, measuring for
each Q-A whether the gold answer lands inside a single chunk (covered), is cut by a
chunk boundary (split — a *chunker* problem), or is missing from the page markdown
(absent / no_parse — a *parser* problem). No retriever / GPU needed: pure text
matching, so this runs on CPU in seconds.

Coverage is the *ceiling* on RCPS — a split or absent Q-A scores zero for any
retriever. Read the output like this:

    * `split` high, and shrinks under overlap / larger windows  → the disconnect is
      a CHUNKING problem; a parser-side fix (best-of-N / DPO) is the wrong lever.
    * `absent` dominates and is flat across chunkers            → a PARSER problem;
      the parser-side fix is justified.

`parser-fault` (absent + no_parse) should be ~constant across chunkers (it does not
depend on where boundaries fall) — a useful sanity check.

Usage:
    uv run python scripts/evaluation/coverage_diagnostic.py
    uv run python scripts/evaluation/coverage_diagnostic.py --qa data/KoGovDoc-RAG/qa_pairs_v1.jsonl
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

from wigtnocr_radp.evaluation.chunkers import (
    FixedSizeChunker,
    MarkdownHeaderChunker,
    ParserNativeChunker,
)
from wigtnocr_radp.evaluation.coverage import CoverageReport, diagnose_coverage
from wigtnocr_radp.evaluation.parser_outputs import load_parser_outputs
from wigtnocr_radp.evaluation.rcps import load_qa_pairs

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("coverage_diagnostic")

V1_PARSES = Path("/mnt/data1/work/wigtnOCR-v1/results/kogovdoc/v1_val/predictions")
VAL_JSONL = Path("data/KoGovDoc-Bench/val.jsonl")

# Fixed parser, varied chunker. Ordered fine→coarse so `split` should trend down.
CHUNKERS = [
    MarkdownHeaderChunker(max_level=3),  # current production chunker (md_h3)
    MarkdownHeaderChunker(max_level=2),
    MarkdownHeaderChunker(max_level=1),  # coarsest header chunking
    ParserNativeChunker(min_chars=30),
    FixedSizeChunker(size=500),
    FixedSizeChunker(size=500, overlap=200),  # overlap rescues boundary-cut answers
    FixedSizeChunker(size=1000),
    FixedSizeChunker(size=1000, overlap=200),
]


def _report_row(rep: CoverageReport) -> dict[str, Any]:
    return {
        "chunker": rep.chunker,
        "num_chunks": rep.num_chunks,
        "coverage": rep.coverage,
        "split_rate": rep.split_rate,
        "parser_fault_rate": rep.parser_fault_rate,
        "counts": rep.counts,
        "by_question_type": rep.by_question_type,
        "by_difficulty": rep.by_difficulty,
        "split_examples": rep.split_examples,
        "absent_examples": rep.absent_examples,
    }


def _markdown_table(reports: list[CoverageReport], total: int) -> list[str]:
    md = [
        "# Answer-Coverage Diagnostic — parser=WigtnOCR v1",
        "",
        f"Q-A: {total}. Pure text matching (no retriever). Coverage = retrieval ceiling.",
        "",
        "- **covered**: answer in a single chunk (retrievable)",
        "- **split**: answer in page but cut by chunk boundary — *chunker fault* (recoverable)",
        "- **parser-fault**: answer absent from parser output — *parser fault* (unrecoverable by re-chunking)",
        "",
        "| Chunker | chunks | covered | split (chunker) | parser-fault |",
        "|---------|:------:|:-------:|:--------------:|:------------:|",
    ]
    for rep in reports:
        md.append(
            f"| {rep.chunker} | {rep.num_chunks} | {rep.coverage:.1%} "
            f"| {rep.split_rate:.1%} | {rep.parser_fault_rate:.1%} |"
        )
    md += [
        "",
        "> `parser-fault` should be ~constant across chunkers (it is boundary-independent). "
        "If `split` falls sharply from md_h3 to overlapped/large windows, the gap is a "
        "chunking problem and a parser-side fix is the wrong lever.",
    ]
    return md


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--qa", default="data/KoGovDoc-RAG/qa_pairs_v1.jsonl")
    ap.add_argument("--parser_dir", type=Path, default=V1_PARSES)
    ap.add_argument("--val_jsonl", type=Path, default=VAL_JSONL)
    ap.add_argument("--out_dir", type=Path, default=Path("output/diagnostics"))
    ap.add_argument("--max_examples", type=int, default=8)
    args = ap.parse_args()

    qa_pairs = load_qa_pairs(args.qa)
    pages = load_parser_outputs(args.parser_dir, args.val_jsonl)
    logger.info("parser=v1: %d pages, %d Q-A", len(pages), len(qa_pairs))

    reports = [
        diagnose_coverage(qa_pairs, pages, chunker, max_examples=args.max_examples)
        for chunker in CHUNKERS
    ]

    args.out_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "config": {
            "parser": "WigtnOCR v1",
            "num_qa": len(qa_pairs),
            "num_pages": len(pages),
            "parser_dir": str(args.parser_dir),
        },
        "chunkers": [_report_row(r) for r in reports],
    }
    (args.out_dir / "coverage_diagnostic_v1.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2)
    )

    table = _markdown_table(reports, len(qa_pairs))
    (args.out_dir / "coverage_diagnostic_v1.md").write_text("\n".join(table))
    print("\n".join(table))
    logger.info("wrote %s", args.out_dir / "coverage_diagnostic_v1.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
