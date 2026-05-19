"""Split KoGovDoc-RAG pages into train (contrastive) / eval (hold-out RCPS).

Why split: in our option-2 setup (no train-fold Q-A), contrastive supervision
comes from the same 242 pages we want to evaluate on. Without a split, eval
leaks into training.

Strategy:
    - Random page-level split with fixed seed.
    - All Q-A from the same page go to the same fold.
    - Stratified-ish: try to balance domain (kogov / arxiv) and language.

Output: `data/KoGovDoc-RAG/page_split_v1.json`
    {
      "seed": 42,
      "train_pages": [...],   # 169 page_ids
      "eval_pages": [...],    # 73 page_ids
      "stats": {...}
    }
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path

QA_PATH = Path("data/KoGovDoc-RAG/qa_pairs_v1.jsonl")
OUT_PATH = Path("data/KoGovDoc-RAG/page_split_v1.json")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train_ratio", type=float, default=0.70)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--qa", type=Path, default=QA_PATH)
    ap.add_argument("--out", type=Path, default=OUT_PATH)
    args = ap.parse_args()

    # Load Q-A, collect per-page metadata
    page_to_meta: dict[str, dict[str, str | int]] = {}
    qa_per_page: Counter[str] = Counter()
    with args.qa.open("r", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            pid = d["page_id"]
            qa_per_page[pid] += 1
            if pid not in page_to_meta:
                page_to_meta[pid] = {
                    "doc_id": d["doc_id"],
                    "language": d["language"],
                    "domain": d["domain"],
                }

    pages = sorted(page_to_meta)
    print(f"loaded {len(pages)} unique pages, {sum(qa_per_page.values())} Q-A")

    # Stratify by (domain, language) to keep distribution balanced
    buckets: dict[tuple[str, str], list[str]] = {}
    for pid in pages:
        key = (page_to_meta[pid]["domain"], page_to_meta[pid]["language"])
        buckets.setdefault(key, []).append(pid)

    rng = random.Random(args.seed)
    train: list[str] = []
    eval_: list[str] = []
    for key, page_list in buckets.items():
        page_list = list(page_list)
        rng.shuffle(page_list)
        n_train = round(len(page_list) * args.train_ratio)
        train.extend(page_list[:n_train])
        eval_.extend(page_list[n_train:])

    train.sort()
    eval_.sort()

    def fold_stats(fold: list[str]) -> dict[str, object]:
        return {
            "num_pages": len(fold),
            "num_qa": int(sum(qa_per_page[p] for p in fold)),
            "domain": dict(Counter(page_to_meta[p]["domain"] for p in fold)),
            "language": dict(Counter(page_to_meta[p]["language"] for p in fold)),
        }

    summary = {
        "seed": args.seed,
        "train_ratio": args.train_ratio,
        "train_pages": train,
        "eval_pages": eval_,
        "stats": {
            "train": fold_stats(train),
            "eval": fold_stats(eval_),
        },
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"wrote {args.out}")
    print(json.dumps(summary["stats"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
