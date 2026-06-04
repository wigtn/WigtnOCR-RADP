"""Stage 1c (Arm B) — Build DPO preference pairs ranked by TextNED-vs-GT.

This is the **TextNED-DPO distillation baseline ("Arm B")** for the
retrieval-reward ablation. It is a byte-for-byte mirror of
`build_preference_pairs.py` (the RADP-DPO Arm A pair builder) EXCEPT the
selection signal:

    Arm A (RADP-DPO):  chosen = argmax RCPS,   rejected = argmin RCPS
    Arm B (this file): chosen = argmin TextNED, rejected = argmax TextNED

where TextNED = character-level Levenshtein distance / max(len) of the
candidate markdown against the page's ground-truth markdown — the *same*
metric the paper's §4.5 uses (`rapidfuzz.distance.Levenshtein.normalized_distance`,
see scripts/analysis/ohr_text_ned.py). 0 = identical, 1 = fully disjoint.

The ground-truth markdown is the v1 train target: the **assistant message** in
each row of `train_2667.jsonl` (`messages[role=="assistant"]["content"]`). No
GPU and no recompute are needed — the K candidate parses are already persisted
in the candidate pool, so the whole ranking is a CPU job.

Output schema is drop-in compatible with `train_radp_dpo.py`
(`DPOPreferenceDataset.from_jsonl`). The `chosen_rcps` / `rejected_rcps` /
`rcps_gap` fields are reused as the chosen/rejected *similarity* (1 - NED) and
gap so downstream consumers (dataset loader, mechanism reports) keep working;
the raw NEDs are also emitted under `chosen_ned` / `rejected_ned` / `ned_gap`.

Pairs with `ned_gap < --min_gap` are dropped — they carry no preference signal.

Usage (mirrors the K=16/K=14 RADP-DPO build, target K=14 like R3):
    uv run python scripts/training/build_preference_pairs_textned.py \
        --candidates output/candidates/v1_k14_front.jsonl \
        --out output/preference/arm_b_textned_pairs.jsonl \
        --min_gap 0.05
"""

from __future__ import annotations

import argparse
import json
import logging
from collections import defaultdict
from pathlib import Path

from rapidfuzz.distance import Levenshtein

from wigtnocr_radp.training.data import remap_train_image_path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("build_pairs_textned")

V1_DATASETS = Path("/mnt/data1/work/wigtnOCR-v1/datasets")


def text_ned(a: str, b: str) -> float:
    """Character-level Levenshtein / max(len). Same metric as paper §4.5."""
    return Levenshtein.normalized_distance(a, b)


def gt_markdown(row: dict) -> str | None:
    """Ground-truth markdown = the v1 train assistant target for this page."""
    for m in row["messages"]:
        if m.get("role") == "assistant":
            return m["content"]
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidates", type=Path,
                    default=Path("output/candidates/v1_k14_front.jsonl"),
                    help="candidate pool — SAME file as RADP-DPO (each row has page_id, "
                         "candidate_idx, markdown). Default = K=14 R3 pool.")
    ap.add_argument("--train_jsonl", type=Path, default=Path("data/KoGovDoc-RAG/train_2667.jsonl"),
                    help="v1 train rows — supplies prompts, image paths, and GT markdown.")
    ap.add_argument("--train_images_root", type=Path, default=V1_DATASETS)
    ap.add_argument("--out", type=Path, default=Path("output/preference/arm_b_textned_pairs.jsonl"))
    ap.add_argument("--min_gap", type=float, default=0.05,
                    help="drop pairs whose chosen↔rejected TextNED gap < this (default 0.05 = 5pp), "
                         "matching the RADP-DPO RCPS-gap filter.")
    ap.add_argument("--limit", type=int, default=None, help="restrict to first N candidate rows (smoke).")
    args = ap.parse_args()

    cand_rows = [json.loads(l) for l in args.candidates.read_text().splitlines() if l.strip()]
    if args.limit:
        cand_rows = cand_rows[: args.limit]
    by_page: dict[str, list[dict]] = defaultdict(list)
    for r in cand_rows:
        by_page[r["page_id"]].append(r)
    logger.info("candidates: %d rows across %d pages", len(cand_rows), len(by_page))

    # Load v1 train rows by page_id for prompts + image paths + GT markdown
    train_rows = [json.loads(l) for l in args.train_jsonl.read_text().splitlines() if l.strip()]
    page_to_row = {f"train_{i:04d}": row for i, row in enumerate(train_rows)}

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fout = args.out.open("w", encoding="utf-8")

    n_pairs = n_low_gap = n_no_pair = n_no_gt = 0
    for page_id, cands in by_page.items():
        if len(cands) < 2:
            n_no_pair += 1
            continue
        row = page_to_row.get(page_id)
        if row is None:
            logger.warning("no train row for %s", page_id)
            continue
        gt = gt_markdown(row)
        if not gt:
            n_no_gt += 1
            continue

        # Rank candidates by TextNED to GT: chosen = closest (min NED), rejected = farthest.
        scored = sorted(cands, key=lambda c: text_ned(c["markdown"], gt))
        chosen, rejected = scored[0], scored[-1]
        chosen_ned = text_ned(chosen["markdown"], gt)
        rejected_ned = text_ned(rejected["markdown"], gt)
        gap = rejected_ned - chosen_ned
        if gap < args.min_gap:
            n_low_gap += 1
            continue

        system = row["messages"][0]["content"]
        user = row["messages"][1]["content"].replace("<image>", "", 1).lstrip()
        image_path = remap_train_image_path(row["images"][0], args.train_images_root)

        fout.write(json.dumps({
            "page_id": page_id,
            "image": str(image_path),
            "system_prompt": system,
            "user_prompt": user,
            "chosen_markdown": chosen["markdown"],
            "rejected_markdown": rejected["markdown"],
            # reuse rcps-named fields (= similarity 1-NED) so downstream stays drop-in compatible
            "chosen_rcps": round(1.0 - chosen_ned, 6),
            "rejected_rcps": round(1.0 - rejected_ned, 6),
            "rcps_gap": round(gap, 4),
            # raw TextNED for transparency / audit
            "chosen_ned": round(chosen_ned, 6),
            "rejected_ned": round(rejected_ned, 6),
            "ned_gap": round(gap, 4),
            "selection_signal": "textned",
        }, ensure_ascii=False) + "\n")
        n_pairs += 1

    fout.close()
    logger.info(
        "wrote %d TextNED preference pairs to %s  (skipped: low_gap=%d, no_pair=%d, no_gt=%d)",
        n_pairs, args.out, n_low_gap, n_no_pair, n_no_gt,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
