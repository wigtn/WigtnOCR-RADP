"""1차 baseline grid: N parsers × 1 retriever × 1 chunker → RCPS table.

Uses v1's pre-computed parser outputs from
  /mnt/data1/work/wigtnOCR-v1/results/kogovdoc/<parser>_val/predictions/

Output:
  output/baselines/grid_v1.json  — machine-readable results
  output/baselines/grid_v1.md    — human-readable markdown table

Usage:
  uv run python scripts/evaluation/baseline_grid.py [--n N] [--chunker parser_native|md_h3|fixed500]
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
from wigtnocr_radp.evaluation.parser_outputs import load_parser_outputs
from wigtnocr_radp.evaluation.rcps import load_qa_pairs


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("baseline_grid")


PARSER_DEFS = [
    # (display_name, v1_dir, role)
    ("WigtnOCR-2B (ours, v1)", "v1_val", "ours"),
    ("Qwen3-VL-30B (teacher)", "30b_val", "teacher"),
    ("Qwen3-VL-2B (base)", "2b_base_val", "baseline"),
    ("MinerU", "mineru_val", "baseline"),
    ("Marker", "marker_val", "baseline"),
    ("PaddleOCR", "paddleocr_val", "baseline"),
]

CHUNKERS = {
    "parser_native": ParserNativeChunker(min_chars=30),
    "md_h3": MarkdownHeaderChunker(max_level=3),
    "fixed500": FixedSizeChunker(size=500),
}

V1_RESULTS_ROOT = Path("/mnt/data1/work/wigtnOCR-v1/results/kogovdoc")
VAL_JSONL = Path("data/KoGovDoc-Bench/val.jsonl")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qa", default="data/KoGovDoc-RAG/qa_pairs_v1.jsonl")
    parser.add_argument("--n", type=int, default=0, help="0 = use all Q-A")
    parser.add_argument(
        "--chunker", choices=tuple(CHUNKERS), default="parser_native"
    )
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--out_dir", default="output/baselines")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    qa_pairs = load_qa_pairs(args.qa)
    if args.n > 0:
        qa_pairs = qa_pairs[: args.n]
    logger.info("loaded %d Q-A pairs", len(qa_pairs))

    chunker = CHUNKERS[args.chunker]
    retriever = BgeM3Retriever(device=args.device, batch_size=32)

    grid: dict[str, Any] = {
        "config": {
            "qa_pairs_path": args.qa,
            "num_qa": len(qa_pairs),
            "chunker": chunker.name,
            "retriever": retriever.name,
            "device": args.device,
        },
        "parsers": [],
    }

    for display_name, dir_name, role in PARSER_DEFS:
        parser_dir = V1_RESULTS_ROOT / dir_name / "predictions"
        if not parser_dir.is_dir():
            logger.warning("%s: parser dir missing, skipping", display_name)
            continue

        pages = load_parser_outputs(parser_dir, VAL_JSONL)
        logger.info("=== %s (%d pages) ===", display_name, len(pages))

        res = compute_rcps(
            qa_pairs=qa_pairs,
            parser_pages=pages,
            retrievers=[retriever],
            chunker=chunker,
            k_values=(1, 5, 10),
        )
        retr_metrics = res["by_retriever"][retriever.name]
        row = {
            "name": display_name,
            "role": role,
            "dir": dir_name,
            "num_pages": len(pages),
            "num_chunks": res["meta"]["num_chunks"],
            "rcps": res["rcps"],
            "hit@1": retr_metrics["hit"][1],
            "hit@5": retr_metrics["hit"][5],
            "hit@10": retr_metrics["hit"][10],
            "mrr@10": retr_metrics["mrr"][10],
            "ndcg@10": retr_metrics["ndcg"][10],
            "by_difficulty": res["by_difficulty"],
        }
        print(
            f"  RCPS={row['rcps']:.4f}  "
            f"Hit@1={row['hit@1']:.4f}  "
            f"MRR@10={row['mrr@10']:.4f}  "
            f"nDCG@10={row['ndcg@10']:.4f}  "
            f"pages={row['num_pages']}  chunks={row['num_chunks']}"
        )
        grid["parsers"].append(row)

    # Sort by RCPS desc
    grid["parsers"].sort(key=lambda r: r["rcps"], reverse=True)

    json_path = out_dir / f"grid_v1_{chunker.name}.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(grid, f, ensure_ascii=False, indent=2)
    logger.info("wrote %s", json_path)

    # Markdown table
    md_path = out_dir / f"grid_v1_{chunker.name}.md"
    lines: list[str] = []
    lines.append(f"# Baseline Grid v1 — chunker={chunker.name}, retriever={retriever.name}")
    lines.append("")
    lines.append(
        f"Q-A: `{args.qa}` ({len(qa_pairs)} pairs). Pages: KoGovDoc-Bench val (294).\n"
    )
    lines.append("| Rank | Parser | role | pages | chunks | **RCPS** | Hit@1 | Hit@5 | Hit@10 | MRR@10 | nDCG@10 |")
    lines.append("|:----:|--------|:----:|:----:|:----:|:----:|:----:|:----:|:----:|:----:|:----:|")
    for i, r in enumerate(grid["parsers"], 1):
        lines.append(
            f"| {i} | {r['name']} | {r['role']} | {r['num_pages']} | {r['num_chunks']} "
            f"| **{r['rcps']:.4f}** | {r['hit@1']:.4f} | {r['hit@5']:.4f} | {r['hit@10']:.4f} "
            f"| {r['mrr@10']:.4f} | {r['ndcg@10']:.4f} |"
        )
    lines.append("")
    lines.append("## Difficulty breakdown — MRR@10")
    lines.append("")
    lines.append("| Parser | easy | medium | hard |")
    lines.append("|--------|:----:|:----:|:----:|")
    for r in grid["parsers"]:
        d = r["by_difficulty"]
        lines.append(
            f"| {r['name']} "
            f"| {d.get('easy', {}).get('mrr@10', 0.0):.4f} "
            f"| {d.get('medium', {}).get('mrr@10', 0.0):.4f} "
            f"| {d.get('hard', {}).get('mrr@10', 0.0):.4f} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("wrote %s", md_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
