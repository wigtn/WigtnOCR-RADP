"""Chunking-strategy grid (PRD §1.5 / §5.3): fixed parser, vary the chunker.

Holds the parser fixed (WigtnOCR v1 output) and compares chunking strategies on
RCPS — Fixed-size / Markdown-header / Parser-native / LumberChunker. This is the
chunking-baseline axis complementary to baseline_grid.py (which varies parsers).

Retrievers run on CPU by default (both GPUs are usually busy with vLLM servers).

Usage:
    uv run python scripts/evaluation/chunking_grid.py
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
from wigtnocr_radp.evaluation.llm_chunkers import PrecomputedChunker
from wigtnocr_radp.evaluation.parser_outputs import load_parser_outputs
from wigtnocr_radp.evaluation.rcps import load_qa_pairs
from wigtnocr_radp.evaluation.retrievers import (
    MultilingualE5LargeRetriever,
    Qwen3EmbeddingRetriever,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("chunking_grid")

V1_PARSES = Path("/mnt/data1/work/wigtnOCR-v1/results/kogovdoc/v1_val/predictions")
VAL_JSONL = Path("data/KoGovDoc-Bench/val.jsonl")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--qa", default="data/KoGovDoc-RAG/qa_pairs_v1.jsonl")
    ap.add_argument("--parser_dir", type=Path, default=V1_PARSES)
    ap.add_argument("--device", default="cpu", help="retriever device (GPUs usually busy)")
    ap.add_argument("--out_dir", type=Path, default=Path("output/baselines"))
    args = ap.parse_args()

    qa_pairs = load_qa_pairs(args.qa)
    pages = load_parser_outputs(args.parser_dir, VAL_JSONL)
    logger.info("parser=v1: %d pages, %d Q-A", len(pages), len(qa_pairs))

    chunkers = [
        FixedSizeChunker(size=500),
        MarkdownHeaderChunker(max_level=3),
        ParserNativeChunker(min_chars=30),
        # LumberChunker chunks precomputed (122B vLLM) so GPU 1 can be freed.
        PrecomputedChunker("output/chunks/lumberchunker_v1.jsonl", "lumberchunker"),
    ]
    retrievers = [
        BgeM3Retriever(device=args.device, batch_size=32),
        MultilingualE5LargeRetriever(device=args.device, batch_size=32),
        Qwen3EmbeddingRetriever(device=args.device, batch_size=8),
    ]
    names = [r.name for r in retrievers]

    rows: list[dict[str, Any]] = []
    for chunker in chunkers:
        logger.info("=== chunker=%s ===", chunker.name)
        res = compute_rcps(qa_pairs, pages, retrievers, chunker, k_values=(1, 5, 10))
        br = res["by_retriever"]

        def _avg(metric: str, k: int, br: dict = br) -> float:
            return sum(br[n][metric][k] for n in names) / len(names)

        rows.append({
            "chunker": chunker.name,
            "num_chunks": res["meta"]["num_chunks"],
            "rcps": res["rcps"],
            "hit@1": _avg("hit", 1), "hit@5": _avg("hit", 5),
            "mrr@10": _avg("mrr", 10), "ndcg@10": _avg("ndcg", 10),
            "by_retriever": br,
        })

    rows.sort(key=lambda r: r["rcps"], reverse=True)
    report = {
        "config": {"parser": "WigtnOCR v1", "num_qa": len(qa_pairs),
                   "num_pages": len(pages), "retrievers": names},
        "chunkers": rows,
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "chunking_grid_v1.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))

    md = ["# Chunking-strategy Grid — parser=WigtnOCR v1", "",
          f"Q-A: {len(qa_pairs)}. Retrievers: {', '.join(names)} (RCPS averaged).", "",
          "| Rank | Chunker | chunks | **RCPS** | Hit@1 | Hit@5 | MRR@10 | nDCG@10 |",
          "|:--:|--------|:--:|:--:|:--:|:--:|:--:|:--:|"]
    for i, r in enumerate(rows, 1):
        md.append(f"| {i} | {r['chunker']} | {r['num_chunks']} | **{r['rcps']:.4f}** "
                  f"| {r['hit@1']:.4f} | {r['hit@5']:.4f} | {r['mrr@10']:.4f} | {r['ndcg@10']:.4f} |")
    (args.out_dir / "chunking_grid_v1.md").write_text("\n".join(md))
    print("\n".join(md))
    logger.info("wrote %s", args.out_dir / "chunking_grid_v1.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
