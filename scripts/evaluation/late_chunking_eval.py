"""Late Chunking vs naive chunk embedding (PRD §1.5 / §5.3).

Holds parser (WigtnOCR v1) and chunker (md_h3, the best from chunking_grid)
fixed, and compares the BGE-M3 embedding strategy:
  - naive          : each chunk embedded independently (mean pooling)
  - late-chunking  : whole page embedded once, chunk = mean of its token vectors

Same model and pooling — the only difference is document context. Shows whether
Late Chunking (Günther et al., 2024) helps on Korean government-document RAG.

Usage:
    CUDA_VISIBLE_DEVICES=1 uv run python scripts/evaluation/late_chunking_eval.py
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from wigtnocr_radp.evaluation import MarkdownHeaderChunker, compute_rcps
from wigtnocr_radp.evaluation.parser_outputs import load_parser_outputs
from wigtnocr_radp.evaluation.rcps import load_qa_pairs
from wigtnocr_radp.evaluation.retrievers import LateChunkingRetriever

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("late_chunking_eval")

V1_PARSES = Path("/mnt/data1/work/wigtnOCR-v1/results/kogovdoc/v1_val/predictions")
VAL_JSONL = Path("data/KoGovDoc-Bench/val.jsonl")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--qa", default="data/KoGovDoc-RAG/qa_pairs_v1.jsonl")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--out", type=Path, default=Path("output/baselines/late_chunking_v1.json"))
    args = ap.parse_args()

    qa_pairs = load_qa_pairs(args.qa)
    pages = load_parser_outputs(V1_PARSES, VAL_JSONL)
    chunker = MarkdownHeaderChunker(max_level=3)
    logger.info("parser=v1, chunker=md_h3: %d pages, %d Q-A", len(pages), len(qa_pairs))

    rows = {}
    for late in (False, True):
        retr = LateChunkingRetriever(device=args.device, late=late)
        logger.info("=== %s ===", retr.name)
        res = compute_rcps(qa_pairs, pages, [retr], chunker, k_values=(1, 5, 10))
        m = res["by_retriever"][retr.name]
        rows[retr.name] = {
            "rcps": res["rcps"], "hit@1": m["hit"][1], "hit@5": m["hit"][5],
            "mrr@10": m["mrr"][10], "ndcg@10": m["ndcg"][10],
        }

    report = {"config": {"parser": "WigtnOCR v1", "chunker": "md_h3",
                          "num_qa": len(qa_pairs)}, "results": rows}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2))

    naive, late = rows["naive-bge-meanpool"], rows["late-chunk-bge"]
    print(f"\n{'='*60}\nLate Chunking vs naive — parser=v1, chunker=md_h3\n{'='*60}")
    print(f"  {'strategy':22s} {'RCPS':>8} {'Hit@1':>8} {'MRR@10':>8}")
    for label, r in [("naive (independent)", naive), ("late-chunking", late)]:
        print(f"  {label:22s} {r['rcps']:8.4f} {r['hit@1']:8.4f} {r['mrr@10']:8.4f}")
    print(f"  {'Δ (late − naive)':22s} {late['rcps']-naive['rcps']:+8.4f} "
          f"{late['hit@1']-naive['hit@1']:+8.4f} {late['mrr@10']-naive['mrr@10']:+8.4f}")
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
