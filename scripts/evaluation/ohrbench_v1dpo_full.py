"""Strict legacy-compatibility OHR eval for v1 / DPO-v1 / DPO-v4.

Pipeline:
  1. Load the legacy OHR parquet and the tracked source-alignment audit
  2. Exclude 223 invalid legacy ``notes`` Q-A and five missing-page Q-A
  3. Require the exact audited 2,036-Q-A / six-domain identity
  4. Load parses only for the same six-domain compatibility corpus
  5. Score parser-native chunks with three retrievers and paired bootstrap CIs

Outputs:
  output/results/ohrbench_v1dpo_strict2036_perqa.json
  output/results/ohrbench_v1dpo_strict2036_ci.json

This remains a corrected legacy compatibility rerun, not a full OHR-Bench v2
evaluation.  The historical 2,264-Q-A source artifacts are immutable audit
inputs and this script refuses to overwrite them.

Usage:
  CUDA_VISIBLE_DEVICES=0 uv run python scripts/evaluation/ohrbench_v1dpo_full.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
from collections import Counter
from pathlib import Path
from typing import Any

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
from wigtnocr_radp.ohrbench_paths import (
    ohr_page_id,
    require_compatibility_cache_path,
    require_compatibility_output_path,
    require_evidence_page_coverage,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ohrbench_v1dpo")

ROOT = Path(__file__).resolve().parents[2]
OHR = ROOT / "data/OHR-Bench"
DEFAULT_PARSE_ROOT = ROOT / "output/parses_ohrbench_compat2036"

_BAD_ANSWERS = {"yes", "no", "true", "false", "n/a", "none", "not specified"}

AUDIT_STATUS = "corrected_legacy_compatibility_subset_not_full_v2"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_alignment_audit(path: Path) -> dict[str, Any]:
    audit = json.loads(path.read_text(encoding="utf-8"))
    if audit.get("status") != AUDIT_STATUS:
        raise ValueError(f"unsupported OHR alignment audit status: {path}")
    if not isinstance(audit.get("c4_strict_compatibility_subset"), dict):
        raise ValueError(f"OHR alignment audit lacks strict-subset metadata: {path}")
    return audit


def apply_strict_compatibility_mask(
    pairs: list[QAPair],
    audit: dict[str, Any],
) -> list[QAPair]:
    """Fail closed unless ``pairs`` has the audited legacy identity and order."""

    strict = audit["c4_strict_compatibility_subset"]
    excluded = strict["excluded"]
    source_n = int(strict["source_num_qa"])
    if len(pairs) != source_n:
        raise ValueError(f"expected {source_n} legacy Q-A before masking, got {len(pairs)}")

    qa_ids = [qa.qa_id for qa in pairs]
    if len(set(qa_ids)) != len(qa_ids):
        raise ValueError("legacy OHR Q-A contain duplicate qa_ids")

    expected_notes = int(excluded["legacy_notes_zero_rows"])
    notes_count = sum(qa.domain == "notes" for qa in pairs)
    if notes_count != expected_notes:
        raise ValueError(f"expected {expected_notes} legacy notes Q-A, got {notes_count}")

    missing_ids = set(excluded["missing_v2_page_qa_ids"])
    expected_missing = int(excluded["missing_v2_page_num_qa"])
    found_missing = missing_ids.intersection(qa_ids)
    if len(missing_ids) != expected_missing or found_missing != missing_ids:
        raise ValueError(
            "missing-page Q-A identity mismatch: "
            f"audit lists {len(missing_ids)}, source contains {len(found_missing)}, "
            f"expected {expected_missing}"
        )

    filtered = [
        qa for qa in pairs if qa.domain != "notes" and qa.qa_id not in missing_ids
    ]
    expected_n = int(strict["num_qa"])
    if len(filtered) != expected_n:
        raise ValueError(f"strict compatibility mask produced {len(filtered)}, expected {expected_n}")

    actual_domains = dict(sorted(Counter(qa.domain for qa in filtered).items()))
    expected_domains = {
        str(domain): int(count) for domain, count in sorted(strict["domain_counts"].items())
    }
    if actual_domains != expected_domains:
        raise ValueError(
            f"strict-domain identity mismatch: got {actual_domains}, expected {expected_domains}"
        )
    return filtered


def load_qa(alignment_audit: dict[str, Any]) -> list[QAPair]:
    """Load and validate the audited 2,036-Q-A legacy compatibility subset."""
    df = pd.read_parquet(OHR / "OHR-Bench.parquet")
    gt_text = {
        ohr_page_id(r["doc_name"], r["page_idx"]): (r["gt_text"] or "")
        for _, r in df.iterrows()
    }

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
            pid = ohr_page_id(str(cols["doc_name"][i]), cols["evidence_page_no"][i])
            if normalize_for_match(ans) not in normalize_for_match(gt_text.get(pid, "")):
                n_unanswerable += 1
                continue
            pairs.append(QAPair(
                qa_id=str(cols["ID"][i]),
                page_id=pid,
                doc_id=str(cols["doc_name"][i]),
                language="en",
                # The compatibility mask is defined on the legacy parquet
                # domains, not on v2 physical folder names or nested labels.
                domain=str(row["domain"]),
                question=str(cols["questions"][i]),
                answer_span=ans,
                answer_chunk=str(cols.get("evidence_context", [""] * n)[i]),
                question_type=str(cols.get("evidence_source", ["text"] * n)[i]),
                difficulty="medium",
            ))
    logger.info("legacy Q-A: %d kept / %d raw (short=%d, not-in-GT=%d)",
                len(pairs), n_raw, n_short, n_unanswerable)
    strict_pairs = apply_strict_compatibility_mask(pairs, alignment_audit)
    logger.info("strict compatibility Q-A: %d across six domains", len(strict_pairs))
    return strict_pairs


def load_corpus_page_ids(alignment_audit: dict[str, Any]) -> set[str]:
    """Page IDs in the same audited six-domain legacy compatibility corpus."""

    strict = alignment_audit["c4_strict_compatibility_subset"]
    allowed_domains = set(strict["domain_counts"])
    missing_page = str(strict["excluded"]["missing_v2_page"])
    df = pd.read_parquet(OHR / "OHR-Bench.parquet", columns=["domain", "doc_name", "page_idx"])
    all_page_ids = {
        ohr_page_id(row["doc_name"], row["page_idx"])
        for _, row in df.iterrows()
        if str(row["domain"]) in allowed_domains
    }
    if missing_page not in all_page_ids:
        raise ValueError(f"audited missing page is absent from the legacy corpus identity: {missing_page}")
    all_page_ids.remove(missing_page)
    return all_page_ids


def load_our_parses(
    model_subdir: str,
    *,
    parse_root: Path = DEFAULT_PARSE_ROOT,
    allowed_page_ids: set[str] | None = None,
) -> dict[str, str]:
    """Load parses from a compatibility-only cache below ``parse_root``."""
    pages: dict[str, str] = {}
    base = parse_root / model_subdir
    if not base.is_dir():
        logger.warning("missing parse dir: %s", base)
        return pages
    for md_path in base.glob("*/*.md"):
        # filename: <page_id>.md, key by the same page_id (basename)
        pid = md_path.stem
        if allowed_page_ids is not None and pid not in allowed_page_ids:
            continue
        if pid in pages:
            raise ValueError(
                f"duplicate OHR page ID {pid!r} under {base}; "
                "remove the stale release-specific cache copy"
            )
        try:
            text = md_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning("read fail %s: %s", md_path, e)
            continue
        # Keep an empty-but-present parse in the page map.  The coverage gate
        # checks missing files, while empty parser content remains a legitimate
        # model error that retrieval should score as zero.
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
        # Recall@k: with exactly one relevant chunk per Q-A in this setup, Recall@k
        # equals Hit@k by definition. Computed explicitly only so both names are
        # available; Hit and Recall here are the same measurement, not independent.
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
    ap.add_argument(
        "--ohr_alignment_audit",
        type=Path,
        default=Path("output/results/ohrbench_alignment_audit.json"),
    )
    ap.add_argument(
        "--out_perqa",
        type=Path,
        default=Path("output/results/ohrbench_v1dpo_strict2036_perqa.json"),
    )
    ap.add_argument(
        "--out_ci",
        type=Path,
        default=Path("output/results/ohrbench_v1dpo_strict2036_ci.json"),
    )
    ap.add_argument(
        "--parse_root",
        type=Path,
        default=DEFAULT_PARSE_ROOT,
        help="compatibility-only parse cache produced by ohrbench_v1_dpo_eval.py",
    )
    ap.add_argument("--n_boot", type=int, default=1000)
    ap.add_argument("--models", default="v1,dpo_v1,dpo_v4",
                    help="parse subdirs under output/parses_ohrbench/")
    args = ap.parse_args()

    alignment_audit = load_alignment_audit(args.ohr_alignment_audit)
    require_compatibility_cache_path(args.parse_root)
    require_compatibility_output_path(args.out_perqa)
    require_compatibility_output_path(args.out_ci)
    resolved_outputs = {args.out_perqa.resolve(), args.out_ci.resolve()}
    if len(resolved_outputs) != 2:
        raise ValueError("per-QA and CI outputs must use distinct paths")
    if args.ohr_alignment_audit.resolve() in resolved_outputs:
        raise ValueError("result output must not overwrite the alignment-audit input")
    qa_list = load_qa(alignment_audit)
    corpus_page_ids = load_corpus_page_ids(alignment_audit)
    missing_corpus_pages = {qa.page_id for qa in qa_list} - corpus_page_ids
    if missing_corpus_pages:
        raise ValueError(
            "strict Q-A evidence pages fall outside the six-domain corpus: "
            f"{sorted(missing_corpus_pages)[:5]}"
        )

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
        pages = load_our_parses(
            m,
            parse_root=args.parse_root,
            allowed_page_ids=corpus_page_ids,
        )
        require_evidence_page_coverage(qa_list, pages, label=f"OHR-Bench model={m}")
        per_qa = compute_per_qa_metrics(qa_list, pages, retrievers, chunker, k_values)
        per_model[m] = per_qa

    # Save per-Q-A
    args.out_perqa.parent.mkdir(parents=True, exist_ok=True)
    perqa_serial = {
        "qa_ids": [qa.qa_id for qa in qa_list],
        "domains": [qa.domain for qa in qa_list],
        "models": {},
        "meta": {
            "status": "strict_legacy_compatibility_subset_not_full_v2",
            "retrievers": retr_names,
            "k_values": list(k_values),
            "n_qa": len(qa_list),
            "domains": sorted({qa.domain for qa in qa_list}),
            "source_num_qa": int(
                alignment_audit["c4_strict_compatibility_subset"]["source_num_qa"]
            ),
            "alignment_audit": str(args.ohr_alignment_audit),
            "alignment_audit_sha256": _sha256(args.ohr_alignment_audit),
        },
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
    print(
        "OHR-Bench strict legacy compatibility CI — "
        f"N={len(qa_list)} Q-A across {len(perqa_serial['meta']['domains'])} domains"
    )
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
