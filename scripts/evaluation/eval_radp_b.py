"""RADP-B vs v1 — retrieval comparison on the held-out eval fold (PHASE_2 §2.2).

Computes RCPS / Hit@k / MRR@10 / nDCG@10 for the RADP-B and v1 parsers over the
eval-fold Q-A, plus a char-level parse↔GT similarity as a parsing-regression
proxy ("회귀 여부"). v1 outputs are reused from the v1 project's pre-computed
`v1_val/predictions/`; RADP-B outputs come from `generate_parses.py`.

Both parsers are scored on the SAME held-out pages and Q-A — RADP-B trained on
the train fold of page_split_v1.json, so only the eval fold is a fair test.

Usage:
    uv run python scripts/evaluation/eval_radp_b.py \
        --radp_parses output/parses/radp_b_base_eval
"""

from __future__ import annotations

import argparse
import difflib
import json
import logging
from pathlib import Path
from typing import Any

from wigtnocr_radp.evaluation import (
    BgeM3Retriever,
    MarkdownHeaderChunker,
    ParserNativeChunker,
    compute_rcps,
)
from wigtnocr_radp.evaluation.parser_outputs import load_parser_outputs
from wigtnocr_radp.evaluation.rcps import load_qa_pairs

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("eval_radp_b")

CHUNKERS = {
    "md_h3": MarkdownHeaderChunker(max_level=3),
    "parser_native": ParserNativeChunker(min_chars=30),
}
V1_PARSES = Path("/mnt/data1/work/wigtnOCR-v1/results/kogovdoc/v1_val/predictions")


def gt_markdown(val_jsonl: Path, page_ids: set[str]) -> dict[str, str]:
    """{page_id: ground-truth markdown} from val.jsonl, for the given pages."""
    out: dict[str, str] = {}
    for i, line in enumerate(val_jsonl.read_text().splitlines()):
        pid = f"val_{i:04d}"
        if pid in page_ids and line.strip():
            out[pid] = json.loads(line)["messages"][2]["content"]
    return out


def mean_parse_similarity(parses: dict[str, str], gt: dict[str, str]) -> float:
    """Mean char-level similarity (difflib ratio) between parse and GT markdown.

    A regression proxy, not OmniDocBench element-level NED. Higher = closer to GT.
    """
    sims = [
        difflib.SequenceMatcher(None, parses[pid], gt[pid], autojunk=False).ratio()
        for pid in gt
        if pid in parses
    ]
    return sum(sims) / len(sims) if sims else 0.0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--radp_parses", type=Path, default=Path("output/parses/radp_b_base_eval"))
    ap.add_argument("--v1_parses", type=Path, default=V1_PARSES)
    ap.add_argument("--qa", type=Path, default=Path("data/KoGovDoc-RAG/qa_pairs_v1.jsonl"))
    ap.add_argument("--split", type=Path, default=Path("data/KoGovDoc-RAG/page_split_v1.json"))
    ap.add_argument("--val_jsonl", type=Path, default=Path("data/KoGovDoc-Bench/val.jsonl"))
    ap.add_argument("--chunkers", nargs="+", default=["md_h3", "parser_native"], choices=tuple(CHUNKERS))
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--out", type=Path, default=Path("output/results/week2_radp_b_vs_v1.json"))
    args = ap.parse_args()

    eval_pages = set(json.loads(args.split.read_text())["eval_pages"])
    eval_qa = [qa for qa in load_qa_pairs(args.qa) if qa.page_id in eval_pages]
    logger.info("eval fold: %d pages, %d Q-A", len(eval_pages), len(eval_qa))

    # Parser outputs, restricted to the eval fold.
    radp = {p: m for p, m in load_parser_outputs(args.radp_parses, args.val_jsonl).items()
            if p in eval_pages}
    v1 = {p: m for p, m in load_parser_outputs(args.v1_parses, args.val_jsonl).items()
          if p in eval_pages}
    logger.info("parses on eval fold — RADP-B: %d, v1: %d", len(radp), len(v1))
    if len(radp) != len(eval_pages):
        logger.warning("RADP-B missing %d eval pages", len(eval_pages) - len(radp))

    gt = gt_markdown(args.val_jsonl, eval_pages)
    retriever = BgeM3Retriever(device=args.device, batch_size=32)

    models = {"v1 (baseline)": v1, "RADP-B (λ=0.3)": radp}
    report: dict[str, Any] = {
        "eval_fold": {"num_pages": len(eval_pages), "num_qa": len(eval_qa)},
        "parse_similarity_vs_gt": {
            name: round(mean_parse_similarity(pages, gt), 4) for name, pages in models.items()
        },
        "by_chunker": {},
    }

    for ck_name in args.chunkers:
        chunker = CHUNKERS[ck_name]
        rows = {}
        for name, pages in models.items():
            res = compute_rcps(eval_qa, pages, [retriever], chunker, k_values=(1, 5, 10))
            m = res["by_retriever"][retriever.name]
            rows[name] = {
                "rcps": res["rcps"], "hit@1": m["hit"][1], "hit@5": m["hit"][5],
                "mrr@10": m["mrr"][10], "ndcg@10": m["ndcg"][10],
                "num_chunks": res["meta"]["num_chunks"],
            }
        report["by_chunker"][ck_name] = rows

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2))

    # Console summary
    print(f"\n{'='*72}\nRADP-B vs v1 — eval fold ({len(eval_pages)} pages, {len(eval_qa)} Q-A)\n{'='*72}")
    sim = report["parse_similarity_vs_gt"]
    print(f"\nParse↔GT char similarity (regression proxy, higher=better):")
    for name in models:
        print(f"  {name:22s} {sim[name]:.4f}")
    for ck_name, rows in report["by_chunker"].items():
        print(f"\n[chunker = {ck_name}]")
        print(f"  {'model':22s} {'RCPS':>8} {'Hit@1':>8} {'Hit@5':>8} {'MRR@10':>8} {'nDCG@10':>8}")
        for name in models:
            r = rows[name]
            print(f"  {name:22s} {r['rcps']:8.4f} {r['hit@1']:8.4f} {r['hit@5']:8.4f} "
                  f"{r['mrr@10']:8.4f} {r['ndcg@10']:8.4f}")
        v1r, rr = rows["v1 (baseline)"], rows["RADP-B (λ=0.3)"]
        print(f"  {'Δ (RADP-B − v1)':22s} {rr['rcps']-v1r['rcps']:+8.4f} "
              f"{rr['hit@1']-v1r['hit@1']:+8.4f} {rr['hit@5']-v1r['hit@5']:+8.4f} "
              f"{rr['mrr@10']-v1r['mrr@10']:+8.4f} {rr['ndcg@10']-v1r['ndcg@10']:+8.4f}")
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
