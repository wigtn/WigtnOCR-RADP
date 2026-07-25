"""Per-source RCPS / macro-Hit@1 from a per-Q-A results file.

Aggregates the raw per-Q-A `<retriever>__mrr@<k>` arrays of a perqa JSON
(e.g. `output/results/FULL_HF_perqa_242p.json`) into the paper's two headline
numbers, decomposed by Q-A source (kogov / arxiv):

    RCPS       = mean over {3 retrievers} x {k in 1,5,10} of MRR@k
    macro Hit@1 = mean over {3 retrievers} of MRR@1  (MRR@1 == Hit@1)

The overall column is recomputed from the same arrays (not copied from any
table), so `overall == (n_kogov*kogov + n_arxiv*arxiv) / n_total` holds by
construction and the check against published values applies to the overall
column. NOTE: perqa files are evaluated on their own fold/corpus (FULL_HF =
242-page corpus); compare against the matching published fold value, not
against a different-corpus grid value.

Usage:
    .venv/bin/python scripts/analysis/perqa_source_rcps.py \
        --perqa output/results/FULL_HF_perqa_242p.json --system 'v1 (ref)'
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def load_sources(qa_path: Path, val_path: Path) -> dict[str, str]:
    """qa_id -> source ('kogov' | 'arxiv'), via page_id -> val.jsonl image path."""
    page_src: dict[str, str] = {}
    with val_path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            doc_id = json.loads(line)["images"][0].rstrip("/").split("/")[-2]
            page_src[f"val_{i:04d}"] = doc_id.split("_")[0]
    out: dict[str, str] = {}
    with qa_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            out[d["qa_id"]] = page_src.get(d["page_id"], "?")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--perqa", type=Path, required=True)
    ap.add_argument("--system", default="v1 (ref)", help="system label prefix (before __chunker)")
    ap.add_argument("--qa", type=Path, default=Path("data/KoGovDoc-RAG/qa_pairs_v1.jsonl"))
    ap.add_argument("--val", type=Path, default=Path("data/KoGovDoc-Bench/val.jsonl"))
    args = ap.parse_args()

    perqa = json.loads(args.perqa.read_text())
    qa_ids: list[str] = perqa["meta"]["qa_ids"]
    src_of = load_sources(args.qa, args.val)

    idx: dict[str, list[int]] = defaultdict(list)
    for i, qid in enumerate(qa_ids):
        idx[src_of.get(qid, "?")].append(i)
    idx["overall"] = list(range(len(qa_ids)))
    groups = [s for s in ("kogov", "arxiv", "overall") if idx.get(s)]

    systems = {
        name: m for name, m in perqa["systems"].items()
        if name.startswith(args.system + "__")
    }
    if not systems:
        raise SystemExit(f"no system matches {args.system!r}; have: {list(perqa['systems'])}")

    print(f"# Per-source RCPS / Hit@1 — {args.system} ({args.perqa.name}, "
          + ", ".join(f"{s}={len(idx[s])}" for s in groups) + ")\n")
    print("| chunker | metric | " + " | ".join(groups) + " |")
    print("|---------|--------|" + "----:|" * len(groups))

    for name, metrics in sorted(systems.items()):
        chunker = name.split("__", 1)[1]
        mrr1 = [v for k, v in metrics.items() if k.endswith("__mrr@1")]
        allk = [v for k, v in metrics.items() if "__mrr@" in k]
        for label, arrays in (("macro Hit@1 (=MRR@1)", mrr1), ("RCPS (9-cell mean)", allk)):
            cells = []
            for s in groups:
                rows = idx[s]
                val = sum(sum(a[i] for i in rows) for a in arrays) / (len(arrays) * len(rows))
                cells.append(f"{val:.6f}")
            print(f"| {chunker} | {label} | " + " | ".join(cells) + " |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
