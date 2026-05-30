"""OHR-Bench full eval for v1 / DPO-v1 / DPO-v4 — Hit/MRR/nDCG/Recall per Q-A.

Pipeline:
  1. Load OHR-Bench parquet across all 7 domains, verbatim filter via gt_text
  2. Load our parses from output/parses_ohrbench/{v1,dpo_v1,dpo_v4}/<dom>/*.md
  3. Chunker: parser_native (matches §4.4 setup)
  4. 3 retrievers: BGE-M3, mE5-large, Qwen3-Emb-8B
  5. Per-Q-A: hit@{1,5,10}, mrr@{5,10}, ndcg@{5,10}, recall@{5,10}
  6. Paired bootstrap CI: DPO-v1 - v1, DPO-v4 - v1 (per metric per retriever)
  7. Cross-retriever mean per-Q-A for combined Hit@k two-sided sig attempt
  8. Optional: union with KoGov perqa for n boost (combined paired CI)

Outputs:
  output/results/ohrbench_v1dpo_perqa.json    (per-Q-A arrays for all metrics)
  output/results/ohrbench_v1dpo_ci.json       (paired CI summary)

Usage:
  CUDA_VISIBLE_DEVICES=0 uv run python scripts/evaluation/ohrbench_v1dpo_full.py
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from wigtnocr_radp.evaluation.bootstrap import bootstrap_paired_delta
from wigtnocr_radp.evaluation.chunkers import ParserNativeChunker
from wigtnocr_radp.evaluation.metrics import hit_at_k, mrr_at_k, ndcg_at_k
from wigtnocr_radp.evaluation.retrievers import (
    BgeM3Retriever,
    MultilingualE5LargeRetriever,
    Qwen3EmbeddingRetriever,
)
from wigtnocr_radp.evaluation.types import QAPair, normalize_for_match

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ohrbench_v1dpo")

ROOT = Path("/mnt/data1/work/WigtnOCR-RADP")
OHR = ROOT / "data/OHR-Bench"
PARSE_ROOT = ROOT / "output/parses_ohrbench"

# parquet domain -> our parse subdir naming (we used pdf_to_parquet mapping during PNG gen,
# so our subdirs follow the *pdf* domain names: administration vs notes, academic vs paper)
PARQUET_TO_PDF = {
    "law": "law", "manual": "manual", "finance": "finance",
    "textbook": "textbook", "news": "news",
    "paper": "academic", "notes": "administration",
}

_BAD_ANSWERS = {"yes", "no", "true", "false", "n/a", "none", "not specified"}


def page_id(doc_name: str, page_idx: int) -> str:
    base = doc_name.rsplit("/", 1)[-1]
    return f"{base}__p{int(page_idx)}"


def load_qa() -> list[QAPair]:
    """Build QAPair list from OHR-Bench.parquet (all 7 domains, verbatim-answerable only)."""
    df = pd.read_parquet(OHR / "OHR-Bench.parquet")
    gt_text = {page_id(r["doc_name"], r["page_idx"]): (r["gt_text"] or "") for _, r in df.iterrows()}

    pairs: list[QAPair] = []
    n_raw = n_short = n_unanswerable = 0
    for _, row in df.iterrows():
        qas = row["qas"]
        if qas is None or "questions" not in qas:
            continue
        cols = {k: list(qas[k]) for k in qas}
        n = len(cols["questions"])
        for i in range(n):
            n_raw += 1
            ans = str(cols["answers"][i]).strip()
            if len(normalize_for_match(ans)) < 2 or ans.lower() in _BAD_ANSWERS:
                n_short += 1
                continue
            pid = page_id(str(cols["doc_name"][i]), cols["evidence_page_no"][i])
            if normalize_for_match(ans) not in normalize_for_match(gt_text.get(pid, "")):
                n_unanswerable += 1
                continue
            pairs.append(QAPair(
                qa_id=str(cols["ID"][i]),
                page_id=pid,
                doc_id=str(cols["doc_name"][i]),
                language="en",
                domain=str(cols["doc_type"][i]),
                question=str(cols["questions"][i]),
                answer_span=ans,
                answer_chunk=str(cols.get("evidence_context", [""] * n)[i]),
                question_type=str(cols.get("evidence_source", ["text"] * n)[i]),
                difficulty="medium",
            ))
    logger.info("Q-A: %d kept / %d raw (short=%d, not-in-GT=%d)",
                len(pairs), n_raw, n_short, n_unanswerable)
    return pairs


def load_our_parses(model_subdir: str) -> dict[str, str]:
    """Load our parses from output/parses_ohrbench/<model_subdir>/<pdf_dom>/<page_id>.md."""
    pages: dict[str, str] = {}
    base = PARSE_ROOT / model_subdir
    if not base.is_dir():
        logger.warning("missing parse dir: %s", base)
        return pages
    for md_path in base.glob("*/*.md"):
        # filename: <page_id>.md, key by the same page_id (basename)
        pid = md_path.stem
        try:
            text = md_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning("read fail %s: %s", md_path, e)
            continue
        if text.strip():
            pages[pid] = text
    logger.info("[%s] loaded %d page parses", model_subdir, len(pages))
    return pages


def compute_per_qa_metrics(qa_list, pages, retrievers, chunker, k_values):
    """Returns per_qa[(metric, retriever, k)] = np.ndarray(N,) for each Q-A."""
    chunks = []
    for pid, text in pages.items():
        chunks.extend(chunker.chunk(pid, text))
    logger.info("  chunks: %d (from %d pages)", len(chunks), len(pages))

    per_qa: dict[tuple[str, str, int], np.ndarray] = {}
    max_k = max(k_values)
    for retr in retrievers:
        retr.index(chunks)
        results = retr.search(qa_list, top_k=max_k)
        for k in k_values:
            per_qa[("hit", retr.name, k)] = np.array(
                [hit_at_k(r, qa, k) for r, qa in zip(results, qa_list)], dtype=float)
            per_qa[("mrr", retr.name, k)] = np.array(
                [mrr_at_k(r, qa, k) for r, qa in zip(results, qa_list)], dtype=float)
            per_qa[("ndcg", retr.name, k)] = np.array(
                [ndcg_at_k(r, qa, k) for r, qa in zip(results, qa_list)], dtype=float)
        # Recall@k: single-relevant per QA in this setup -> identical to Hit@k, but
        # report explicitly so downstream framing can use "Recall" wording per user's
        # 13:48 hypothesis ("Recall 성능 끌어올릴 수 있다").
        for k in k_values:
            per_qa[("recall", retr.name, k)] = per_qa[("hit", retr.name, k)].copy()
    return per_qa


def cross_retriever_mean(per_qa, metric, k, retr_names):
    """Average per-Q-A across retrievers for one (metric, k)."""
    arrs = [per_qa[(metric, n, k)] for n in retr_names if (metric, n, k) in per_qa]
    return np.mean(np.stack(arrs, axis=0), axis=0)  # shape (N,)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--out_perqa", type=Path, default=Path("output/results/ohrbench_v1dpo_perqa.json"))
    ap.add_argument("--out_ci", type=Path, default=Path("output/results/ohrbench_v1dpo_ci.json"))
    ap.add_argument("--n_boot", type=int, default=1000)
    ap.add_argument("--models", default="v1,dpo_v1,dpo_v4",
                    help="parse subdirs under output/parses_ohrbench/")
    args = ap.parse_args()

    qa_list = load_qa()

    retrievers = [
        BgeM3Retriever(device=args.device, batch_size=32),
        MultilingualE5LargeRetriever(device=args.device, batch_size=32),
        Qwen3EmbeddingRetriever(device=args.device, batch_size=8),
    ]
    retr_names = [r.name for r in retrievers]
    chunker = ParserNativeChunker(min_chars=30)
    k_values = (1, 5, 10)

    models = args.models.split(",")
    per_model: dict[str, dict] = {}
    for m in models:
        logger.info("=== model: %s ===", m)
        pages = load_our_parses(m)
        if not pages:
            logger.warning("skip %s: no parses", m)
            continue
        per_qa = compute_per_qa_metrics(qa_list, pages, retrievers, chunker, k_values)
        per_model[m] = per_qa

    # Save per-Q-A
    args.out_perqa.parent.mkdir(parents=True, exist_ok=True)
    perqa_serial = {
        "qa_ids": [qa.qa_id for qa in qa_list],
        "domains": [qa.domain for qa in qa_list],
        "models": {},
        "meta": {"retrievers": retr_names, "k_values": list(k_values), "n_qa": len(qa_list)},
    }
    for m, pq in per_model.items():
        perqa_serial["models"][m] = {
            f"{metric}@{k}__{rn}": vals.tolist()
            for (metric, rn, k), vals in pq.items()
        }
    args.out_perqa.write_text(json.dumps(perqa_serial, indent=2))
    logger.info("wrote %s", args.out_perqa)

    # Paired CI: DPO models vs v1
    ci_out: dict = {"meta": perqa_serial["meta"], "paired_vs_v1": {}}
    if "v1" in per_model:
        for m in [x for x in models if x != "v1" and x in per_model]:
            row = {}
            for metric in ("hit", "mrr", "ndcg", "recall"):
                for k in k_values:
                    # cross-retriever mean per-QA, then paired delta
                    a = cross_retriever_mean(per_model[m], metric, k, retr_names)
                    b = cross_retriever_mean(per_model["v1"], metric, k, retr_names)
                    delta = bootstrap_paired_delta(a, b, n_boot=args.n_boot, alpha=0.05, seed=42)
                    row[f"{metric}@{k}"] = {
                        "delta_pp": round(delta.mean * 100, 3),
                        "ci_lo_pp": round(delta.lo * 100, 3),
                        "ci_hi_pp": round(delta.hi * 100, 3),
                        "two_sided_sig": bool(delta.lo > 0 or delta.hi < 0),
                    }
            ci_out["paired_vs_v1"][m] = row
    args.out_ci.write_text(json.dumps(ci_out, indent=2, ensure_ascii=False))
    logger.info("wrote %s", args.out_ci)

    # Console summary
    print("\n" + "=" * 84)
    print(f"OHR-Bench v1+DPO paired CI — N={len(qa_list)} Q-A across 7 domains")
    print("=" * 84)
    for m, row in ci_out["paired_vs_v1"].items():
        print(f"\n[{m} vs v1]  (cross-retriever mean, paired bootstrap N={args.n_boot})")
        print(f"  {'metric':<14}{'Δpp':>10}{'95% CI':>22}{'two-sided':>12}")
        for key, val in row.items():
            sig = "**" if val["two_sided_sig"] else "  "
            ci_str = f"[{val['ci_lo_pp']:+.2f}, {val['ci_hi_pp']:+.2f}]"
            print(f"  {key:<14}{val['delta_pp']:>+10.2f}{ci_str:>22}{sig:>12}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
