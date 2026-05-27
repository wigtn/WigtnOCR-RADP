"""Sanity check for RCPS — run on KoGovDoc-Bench ground-truth markdown as parser output.

This is the "perfect parser" ceiling: every answer_span is by construction inside its
source page, so a competent retriever should achieve high Hit@1 (~0.85+). A score
much lower than that indicates either a chunker bug, retriever issue, or a misaligned
answer_span (e.g. whitespace normalization mismatch between markdown and chunks).

Usage:
    uv run python scripts/evaluation/rcps_sanity.py [--n N]
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

from wigtnocr_radp.evaluation import (
    BgeM3Retriever,
    FixedSizeChunker,
    MarkdownHeaderChunker,
    ParserNativeChunker,
    compute_rcps,
)
from wigtnocr_radp.evaluation.rcps import load_qa_pairs


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("rcps_sanity")


def load_gt_pages(jsonl_path: Path) -> dict[str, str]:
    """Read KoGovDoc-Bench val.jsonl and return {page_id: gt_markdown}."""
    pages: dict[str, str] = {}
    with jsonl_path.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            d = json.loads(line)
            page_id = f"val_{idx:04d}"
            # generator.py uses messages[2].content as GT
            pages[page_id] = d["messages"][2]["content"]
    return pages


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qa", default="data/KoGovDoc-RAG/qa_pairs_v1.jsonl")
    parser.add_argument("--gt", default="data/KoGovDoc-Bench/val.jsonl")
    parser.add_argument("--n", type=int, default=0, help="0 = use all Q-A")
    parser.add_argument("--out", default="output/rcps/sanity_results.json")
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()

    qa_pairs = load_qa_pairs(args.qa)
    if args.n > 0:
        qa_pairs = qa_pairs[: args.n]
    logger.info("loaded %d Q-A pairs", len(qa_pairs))

    pages = load_gt_pages(Path(args.gt))
    # restrict pages to those referenced by selected Q-A (saves embedding time)
    needed = {qa.page_id for qa in qa_pairs}
    pages = {pid: md for pid, md in pages.items() if pid in needed}
    logger.info("loaded %d source pages (referenced by selected Q-A)", len(pages))

    retriever = BgeM3Retriever(device=args.device, batch_size=32)

    summary: dict[str, Any] = {}
    for chunker in (
        ParserNativeChunker(min_chars=30),
        MarkdownHeaderChunker(max_level=3),
        FixedSizeChunker(size=500),
    ):
        logger.info("=== chunker=%s ===", chunker.name)
        res = compute_rcps(
            qa_pairs=qa_pairs,
            parser_pages=pages,
            retrievers=[retriever],
            chunker=chunker,
            k_values=(1, 5, 10),
        )
        summary[chunker.name] = res
        print(
            f"  RCPS={res['rcps']:.4f}  "
            f"Hit@1={res['by_retriever'][retriever.name]['hit'][1]:.4f}  "
            f"MRR@10={res['by_retriever'][retriever.name]['mrr'][10]:.4f}  "
            f"nDCG@10={res['by_retriever'][retriever.name]['ndcg'][10]:.4f}  "
            f"chunks={res['meta']['num_chunks']}"
        )
        diff = res["by_difficulty"]
        for d in ("easy", "medium", "hard"):
            if d in diff:
                print(f"    {d}: mrr@10={diff[d].get('mrr@10', 0.0):.4f}")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    logger.info("results written to %s", out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
