"""Stage 1c — Build DPO preference pairs from scored candidates.

Reads `output/candidates/v1_train_candidate_scores.jsonl` + the candidate
markdowns and emits one preference example per page where two candidates exist
and have a non-trivial RCPS gap (≥ `--min_gap`).

Each output line:
    {
      "page_id": "train_0042",
      "image": "<repo-local image path>",
      "system_prompt": "<v1 system prompt>",
      "user_prompt": "<v1 user prompt minus <image> tag>",
      "chosen_markdown": "<higher-RCPS candidate>",
      "rejected_markdown": "<lower-RCPS candidate>",
      "chosen_rcps": 0.83,
      "rejected_rcps": 0.42,
      "rcps_gap": 0.41,
      "n_qa": 2,
    }

Pairs with `rcps_gap < min_gap` are dropped — they carry no preference signal
(the model can't reliably rank them, and DPO would just inject noise).

Usage:
    uv run python scripts/training/build_preference_pairs.py --min_gap 0.05
"""

from __future__ import annotations

import argparse
import json
import logging
from collections import defaultdict
from pathlib import Path

from wigtnocr_radp.training.data import remap_train_image_path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("build_preference_pairs")

V1_DATASETS = Path("/mnt/data1/work/wigtnOCR-v1/datasets")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidates", type=Path, default=Path("output/candidates/v1_train_candidates.jsonl"))
    ap.add_argument("--scores", type=Path, default=Path("output/candidates/v1_train_candidate_scores.jsonl"))
    ap.add_argument("--train_jsonl", type=Path, default=Path("data/KoGovDoc-RAG/train_2667.jsonl"))
    ap.add_argument("--train_images_root", type=Path, default=V1_DATASETS)
    ap.add_argument("--out", type=Path, default=Path("output/preference/v1_pairs.jsonl"))
    ap.add_argument("--min_gap", type=float, default=0.05,
                    help="drop pairs with RCPS gap below this (default 0.05 = 5pp)")
    args = ap.parse_args()

    # Index candidate markdowns + scores by (page_id, candidate_idx)
    cands = {(r["page_id"], r["candidate_idx"]): r
             for r in (json.loads(l) for l in args.candidates.read_text().splitlines() if l.strip())}
    scores = {(r["page_id"], r["candidate_idx"]): r
              for r in (json.loads(l) for l in args.scores.read_text().splitlines() if l.strip())}
    logger.info("candidates: %d rows, scores: %d rows", len(cands), len(scores))

    # Group scored candidates by page
    by_page: dict[str, list[dict]] = defaultdict(list)
    for (page_id, _), s in scores.items():
        by_page[page_id].append(s)

    # Load v1 train rows by page_id for prompts + image paths
    train_rows = [json.loads(l) for l in args.train_jsonl.read_text().splitlines() if l.strip()]
    page_to_row = {f"train_{i:04d}": row for i, row in enumerate(train_rows)}

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fout = args.out.open("w", encoding="utf-8")

    n_pairs = n_low_gap = n_no_pair = 0
    for page_id, scored_cands in by_page.items():
        if len(scored_cands) < 2:
            n_no_pair += 1
            continue
        scored_cands.sort(key=lambda s: s["rcps"], reverse=True)
        chosen = scored_cands[0]
        rejected = scored_cands[-1]
        gap = chosen["rcps"] - rejected["rcps"]
        if gap < args.min_gap:
            n_low_gap += 1
            continue

        ch_md = cands[(page_id, chosen["candidate_idx"])]["markdown"]
        rj_md = cands[(page_id, rejected["candidate_idx"])]["markdown"]
        row = page_to_row.get(page_id)
        if row is None:
            logger.warning("no train row for %s", page_id); continue
        system = row["messages"][0]["content"]
        user = row["messages"][1]["content"].replace("<image>", "", 1).lstrip()
        image_path = remap_train_image_path(row["images"][0], args.train_images_root)

        fout.write(json.dumps({
            "page_id": page_id,
            "image": str(image_path),
            "system_prompt": system,
            "user_prompt": user,
            "chosen_markdown": ch_md,
            "rejected_markdown": rj_md,
            "chosen_rcps": chosen["rcps"],
            "rejected_rcps": rejected["rcps"],
            "rcps_gap": round(gap, 4),
            "n_qa": chosen["n_qa"],
        }, ensure_ascii=False) + "\n")
        n_pairs += 1

    fout.close()
    logger.info(
        "wrote %d preference pairs to %s  (skipped: low_gap=%d, no_pair=%d)",
        n_pairs, args.out, n_low_gap, n_no_pair,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
