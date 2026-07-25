"""RCPS / Hit@k for ONE parser output dir — no edits to baseline_grid.py.

Purpose: score a parser directory that is not in `baseline_grid.PARSER_DEFS`
(e.g. the MinerU table-ON re-run at
`results/kogovdoc/mineru_val_tableon/predictions/`) on the exact same pipeline:
same chunkers, same 3 retrievers, same `compute_rcps`, same 663-Q-A probe.

Besides the grid-style summary row, it writes a per-Q-A JSON in the same shape
as `output/results/FULL_HF_perqa_242p.json` (`systems.<label>__<chunker>.<retriever>__mrr@<k>`),
so the per-domain decomposition comes free via:

    .venv/bin/python scripts/analysis/perqa_source_rcps.py \
        --perqa output/results/<out>.json --system '<label>'

Needs the 3 embedders (GPU recommended). Typical use (WSL, RTX 5070):

    uv run python scripts/analysis/grid_single_parser.py \
        --parser-dir results/kogovdoc/mineru_val_tableon/predictions \
        --label MinerU-tableON --chunker parser_native --device cuda
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
from wigtnocr_radp.evaluation.retrievers import (
    MultilingualE5LargeRetriever,
    Qwen3EmbeddingRetriever,
)
from wigtnocr_radp.evaluation.parser_outputs import load_parser_outputs
from wigtnocr_radp.evaluation.rcps import load_qa_pairs

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("grid_single_parser")

CHUNKERS = {
    "parser_native": ParserNativeChunker(min_chars=30),
    "md_h3": MarkdownHeaderChunker(max_level=3),
    "fixed500": FixedSizeChunker(size=500),
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parser-dir", type=Path, required=True)
    ap.add_argument("--label", required=True, help="system label, e.g. MinerU-tableON")
    ap.add_argument("--qa", default="data/KoGovDoc-RAG/qa_pairs_v1.jsonl")
    ap.add_argument("--val", default="data/KoGovDoc-Bench/val.jsonl")
    ap.add_argument("--chunker", choices=tuple(CHUNKERS), default="parser_native")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--out_dir", default="output/results")
    args = ap.parse_args()

    qa_pairs = load_qa_pairs(args.qa)
    pages = load_parser_outputs(args.parser_dir, args.val)
    chunker = CHUNKERS[args.chunker]
    retrievers = [
        BgeM3Retriever(device=args.device, batch_size=32),
        MultilingualE5LargeRetriever(device=args.device, batch_size=32),
        Qwen3EmbeddingRetriever(device=args.device, batch_size=8),
    ]

    res = compute_rcps(
        qa_pairs=qa_pairs,
        parser_pages=pages,
        retrievers=retrievers,
        chunker=chunker,
        k_values=(1, 5, 10),
        return_per_qa=True,
    )

    names = [r.name for r in retrievers]
    br = res["by_retriever"]

    def _avg(metric: str, k: int) -> float:
        return sum(br[n][metric][k] for n in names) / len(names)

    summary: dict[str, Any] = {
        "label": args.label,
        "parser_dir": str(args.parser_dir),
        "chunker": chunker.name,
        "num_qa": len(qa_pairs),
        "num_pages": len(pages),
        "num_chunks": res["meta"]["num_chunks"],
        "rcps": res["rcps"],
        "hit@1": _avg("hit", 1),
        "hit@5": _avg("hit", 5),
        "hit@10": _avg("hit", 10),
        "mrr@10": _avg("mrr", 10),
        "ndcg@10": _avg("ndcg", 10),
        "by_retriever": br,
        "by_difficulty": res["by_difficulty"],
    }
    print(
        f"{args.label} ({chunker.name}): RCPS={summary['rcps']:.6f} "
        f"Hit@1={summary['hit@1']:.6f} Hit@5={summary['hit@5']:.6f} "
        f"pages={summary['num_pages']} chunks={summary['num_chunks']}"
    )

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{args.label.replace(' ', '_')}_{chunker.name}"

    (out_dir / f"grid_{stem}.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # perqa-compatible dump: systems.<label>__<chunker>.<retriever>__mrr@<k> = [...]
    perqa = {
        "meta": {
            "qa_ids": [qa.qa_id for qa in qa_pairs],
            "retrievers": names,
            "k_values": [1, 5, 10],
            "chunkers": [chunker.name],
            "labels": [args.label],
        },
        "systems": {
            f"{args.label}__{chunker.name}": {
                f"{retr}__mrr@{k}": vals
                for (retr, k), vals in res["per_qa"].items()
            }
        },
    }
    perqa_path = out_dir / f"perqa_{stem}.json"
    perqa_path.write_text(json.dumps(perqa, ensure_ascii=False), encoding="utf-8")
    logger.info("wrote %s (+ grid_%s.json)", perqa_path, stem)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
