"""Decompose the frozen 663 Q-A set by source (kogov / arxiv) and language.

Why: the paper describes KoGovDoc-RAG as "663 Q-A pairs over 294 pages of
Korean government documents", but KoGovDoc-Bench val mixes 9 KoGov documents
(229 pages) with 29 arXiv papers (65 pages). Before the rebuttal we need the
exact Q-A-level composition and, if per-case verdicts are available, the
absent-rate / retrieval groupbys by source.

Inputs:
    --qa        data/KoGovDoc-RAG/qa_pairs_v1.jsonl  (frozen 663 Q-A; required)
    --val       data/KoGovDoc-Bench/val.jsonl        (294 pages; default path)
    --perqa     output/results/FULL_HF_perqa_242p.json (optional; local in repo)
    --verdicts  per-case coverage verdicts JSON, {qa_id: "absent"|"covered"|"split"}
                per parser (optional; lives with the coverage diagnostic runs)

Outputs (stdout, markdown-ish):
    1. Composition: pages and Q-A by source x language, per-doc Q-A counts,
       identity of the Q-A-free pages (the 52 distractors).
    2. Retrieval groupby: mean per-Q-A metric by source for every
       system x chunker x retriever x k in --perqa.
    3. Absent-rate groupby by source for each --verdicts file given.

Usage (on the machine that has qa_pairs_v1.jsonl):
    uv run python scripts/analysis/source_groupby.py \
        --qa data/KoGovDoc-RAG/qa_pairs_v1.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional

HANGUL = re.compile(r"[가-힣]")


def load_val_pages(val_path: Path) -> dict[str, dict[str, str]]:
    """Map page_id (val_XXXX) -> {doc_id, source} from val.jsonl order."""
    pages: dict[str, dict[str, str]] = {}
    with val_path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            d = json.loads(line)
            doc_id = d["images"][0].rstrip("/").split("/")[-2]
            pages[f"val_{i:04d}"] = {
                "doc_id": doc_id,
                "source": doc_id.split("_")[0],
            }
    return pages


def question_language(question: str) -> str:
    return "ko" if HANGUL.search(question) else "en"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--qa", type=Path, required=True)
    ap.add_argument(
        "--val", type=Path, default=Path("data/KoGovDoc-Bench/val.jsonl")
    )
    ap.add_argument(
        "--perqa",
        type=Path,
        default=Path("output/results/FULL_HF_perqa_242p.json"),
    )
    ap.add_argument(
        "--verdicts",
        type=Path,
        nargs="*",
        default=[],
        help="per-case coverage verdict JSONs, one per parser",
    )
    args = ap.parse_args()

    pages = load_val_pages(args.val)

    qa_rows: list[dict[str, str]] = []
    with args.qa.open("r", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            src = pages.get(d["page_id"], {}).get("source", d.get("domain", "?"))
            qa_rows.append(
                {
                    "qa_id": d["qa_id"],
                    "page_id": d["page_id"],
                    "doc_id": d["doc_id"],
                    "source": src,
                    "domain_field": d.get("domain", "?"),
                    "language_field": d.get("language", "?"),
                    "language_detected": question_language(d["question"]),
                }
            )

    n = len(qa_rows)
    print(f"# Source groupby — {n} Q-A, {len(pages)} val pages\n")

    # -- 1. Composition ------------------------------------------------------
    by_source = Counter(r["source"] for r in qa_rows)
    by_src_lang = Counter(
        (r["source"], r["language_detected"]) for r in qa_rows
    )
    print("## 1. Composition\n")
    print("| source | Q-A | share | ko | en |")
    print("|--------|----:|------:|---:|---:|")
    for src in sorted(by_source):
        c = by_source[src]
        ko = by_src_lang.get((src, "ko"), 0)
        en = by_src_lang.get((src, "en"), 0)
        print(f"| {src} | {c} | {c / n:.1%} | {ko} | {en} |")
    print()

    mismatches = [
        r for r in qa_rows if r["domain_field"] not in ("?", r["source"])
    ]
    if mismatches:
        print(
            f"WARNING: {len(mismatches)} Q-A where the jsonl `domain` field "
            "disagrees with the val.jsonl image path — inspect before release."
        )

    qa_pages = {r["page_id"] for r in qa_rows}
    free = [p for p in pages if p not in qa_pages]
    free_src = Counter(pages[p]["source"] for p in free)
    print(
        f"Q-A-bearing pages: {len(qa_pages)} | Q-A-free pages: {len(free)} "
        f"({dict(free_src)})"
    )
    per_doc = Counter(r["doc_id"] for r in qa_rows)
    print("\nPer-doc Q-A counts:")
    for doc in sorted(per_doc):
        print(f"  {doc}: {per_doc[doc]}")
    print()

    # -- 2. Retrieval groupby ------------------------------------------------
    if args.perqa.exists():
        perqa = json.loads(args.perqa.read_text())
        order = perqa["meta"]["qa_ids"]
        src_of = {r["qa_id"]: r["source"] for r in qa_rows}
        idx = defaultdict(list)
        for i, qid in enumerate(order):
            idx[src_of.get(qid, "?")].append(i)
        print("## 2. Retrieval groupby (mean per-Q-A metric by source)\n")
        print("| system | metric | " + " | ".join(sorted(idx)) + " |")
        print("|--------|--------|" + "---:|" * len(idx))
        for sys_name, metrics in perqa["systems"].items():
            for m_name, values in metrics.items():
                cells = [
                    f"{sum(values[i] for i in idx[s]) / len(idx[s]):.4f}"
                    for s in sorted(idx)
                ]
                print(f"| {sys_name} | {m_name} | " + " | ".join(cells) + " |")
        print()
    else:
        print(f"(skip retrieval groupby — {args.perqa} not found)\n")

    # -- 3. Absent-rate groupby ---------------------------------------------
    for vpath in args.verdicts:
        verdicts: dict[str, str] = json.loads(vpath.read_text())
        agg: dict[str, Counter[str]] = defaultdict(Counter)
        for r in qa_rows:
            v: Optional[str] = verdicts.get(r["qa_id"])
            if v is not None:
                agg[r["source"]][v] += 1
        print(f"## 3. Absent rate by source — {vpath.name}\n")
        print("| source | absent | covered | split | absent rate |")
        print("|--------|-------:|--------:|------:|------------:|")
        for src in sorted(agg):
            c = agg[src]
            total = sum(c.values())
            print(
                f"| {src} | {c['absent']} | {c['covered']} | {c['split']} | "
                f"{c['absent'] / total:.1%} |"
            )
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
