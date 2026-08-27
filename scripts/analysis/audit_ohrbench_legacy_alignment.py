"""Reproduce the camera-ready OHR-Bench compatibility-subset audit.

This is a CPU-only audit of already stored per-QA arrays.  It does *not*
convert the legacy OHR-Bench Q-A release into the current v2 benchmark.  The
script removes observations known to be invalid in the stored arrays:

* 223 legacy ``notes`` Q-A whose documents were looked up in the unrelated v2
  ``administration`` directory; and
* five Q-A for a legacy textbook page absent from the v2 parser bundle.

The resulting 2,036-Q-A set is suitable only as a corrected compatibility
subset.  The audit also aligns the RADP-Distill per-QA artifact to this exact
mask and verifies that its shared Prod and R2 arrays are byte-for-byte equal to
the corresponding arrays in the R2 artifact.  A full v2 evaluation would still
require ``OHR-Bench_v2.parquet`` and ``qas_v2.json`` plus fresh parser and
retrieval runs; the camera-ready paper makes no full-v2 claim.

Usage:
    python scripts/analysis/audit_ohrbench_legacy_alignment.py
    python scripts/analysis/audit_ohrbench_legacy_alignment.py \
        --check output/results/ohrbench_alignment_audit.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
R2_PATH = ROOT / "output/results/ohrbench_v1dpo_perqa.json"
R3_PATH = ROOT / "output/results/ohr_v5_perqa.json"
DISTILL_PATH = ROOT / "output/results/arm_b_ohr_perqa.json"
C1_RCPS_PATH = ROOT / "output/results/ohrbench_noise.json"
C1_BC_PATH = ROOT / "output/results/ohrbench_bc_noise.json"

RETRIEVERS = ("bge-m3", "ml-e5-large", "qwen3-emb-8b")
MISSING_PAGE = (
    "Triangulated_Categories_of_Mixed_Motives_"
    "(Denis-Charles_Cisinski_,_Frédéric_Déglise)_(Z-Library).pdf_145__p0"
)
MISSING_PAGE_QA_IDS = {
    "74ea8681-238b-45f0-abf7-f77bb50fd1ab",
    "74ee5979-663b-435d-96c9-9850fef666b1",
    "74f15f46-c9e7-48ba-9a05-00d0a29d94c0",
    "74f8c57b-24c5-42ca-aab3-c4d8d4e4004b",
    "74fa03af-423a-472c-8582-2158e1ab84a5",
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _cross_retriever(
    artifact: dict[str, Any],
    model: str,
    metric: str,
    cutoff: int,
    mask: np.ndarray,
) -> np.ndarray:
    arrays = [
        np.asarray(artifact["models"][model][f"{metric}@{cutoff}__{retriever}"], dtype=float)
        for retriever in RETRIEVERS
    ]
    return np.mean(np.stack(arrays, axis=0), axis=0)[mask]


def _paired_delta(
    candidate: np.ndarray,
    baseline: np.ndarray,
    *,
    n_boot: int = 1000,
    seed: int = 42,
) -> dict[str, float]:
    delta = candidate - baseline
    rng = np.random.default_rng(seed)
    boot = np.empty(n_boot, dtype=float)
    for index in range(n_boot):
        sample = rng.integers(0, len(delta), len(delta))
        boot[index] = delta[sample].mean()
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return {
        "delta_pp": round(float(delta.mean() * 100), 6),
        "ci95_lo_pp": round(float(lo * 100), 6),
        "ci95_hi_pp": round(float(hi * 100), 6),
    }


def _model_metrics(
    artifact: dict[str, Any],
    model: str,
    mask: np.ndarray,
) -> dict[str, dict[str, float]]:
    metrics: dict[str, dict[str, float]] = {}
    for label, metric, cutoff in (
        ("hit_at_1", "hit", 1),
        ("hit_at_5", "hit", 5),
        ("hit_at_10", "hit", 10),
        ("mrr_at_10", "mrr", 10),
        ("ndcg_at_5", "ndcg", 5),
    ):
        candidate = _cross_retriever(artifact, model, metric, cutoff, mask)
        baseline = _cross_retriever(artifact, "v1", metric, cutoff, mask)
        metrics[label] = _paired_delta(candidate, baseline)

    candidate_rcps = np.mean(
        np.stack(
            [_cross_retriever(artifact, model, "mrr", cutoff, mask) for cutoff in (1, 5, 10)],
            axis=0,
        ),
        axis=0,
    )
    baseline_rcps = np.mean(
        np.stack(
            [_cross_retriever(artifact, "v1", "mrr", cutoff, mask) for cutoff in (1, 5, 10)],
            axis=0,
        ),
        axis=0,
    )
    metrics["rcps"] = _paired_delta(candidate_rcps, baseline_rcps)
    return metrics


def _assert_same_observations(reference: dict[str, Any], candidate: dict[str, Any], label: str) -> None:
    if reference["qa_ids"] != candidate["qa_ids"] or reference["domains"] != candidate["domains"]:
        raise ValueError(f"{label} does not share the R2 observation order")


def _assert_same_model_arrays(
    reference: dict[str, Any],
    candidate: dict[str, Any],
    *,
    reference_model: str,
    candidate_model: str,
    label: str,
) -> None:
    reference_arrays = reference["models"][reference_model]
    candidate_arrays = candidate["models"][candidate_model]
    if reference_arrays.keys() != candidate_arrays.keys():
        raise ValueError(f"{label} metric cells differ")
    for key in reference_arrays:
        if reference_arrays[key] != candidate_arrays[key]:
            raise ValueError(f"{label} differs at {key}")


def _hit_at_5(artifact: dict[str, Any], model: str, mask: np.ndarray) -> np.ndarray:
    return _cross_retriever(artifact, model, "hit", 5, mask)


def build_report() -> dict[str, Any]:
    r2 = _read_json(R2_PATH)
    r3 = _read_json(R3_PATH)
    distill = _read_json(DISTILL_PATH)
    _assert_same_observations(r2, r3, "R3")
    _assert_same_observations(r2, distill, "RADP-Distill")
    _assert_same_model_arrays(
        r2,
        distill,
        reference_model="v1",
        candidate_model="v1",
        label="RADP-Distill Prod control",
    )
    _assert_same_model_arrays(
        r2,
        distill,
        reference_model="dpo_v4",
        candidate_model="dpo_v4",
        label="RADP-Distill R2 control",
    )

    qa_ids = list(r2["qa_ids"])
    domains = list(r2["domains"])
    if len(qa_ids) != 2264 or len(domains) != 2264:
        raise ValueError(f"expected 2,264 legacy observations, got {len(qa_ids)}")

    notes_count = sum(domain == "notes" for domain in domains)
    missing_ids_found = MISSING_PAGE_QA_IDS.intersection(qa_ids)
    if notes_count != 223 or missing_ids_found != MISSING_PAGE_QA_IDS:
        raise ValueError(
            "the stored arrays no longer match the audited exclusions: "
            f"notes={notes_count}, missing-page-QA={len(missing_ids_found)}"
        )

    mask = np.asarray(
        [domain != "notes" and qa_id not in MISSING_PAGE_QA_IDS for qa_id, domain in zip(qa_ids, domains)],
        dtype=bool,
    )
    if int(mask.sum()) != 2036:
        raise ValueError(f"expected strict n=2,036, got {int(mask.sum())}")

    strict_domains = Counter(domain for domain, keep in zip(domains, mask) if keep)
    c1_rcps = _read_json(C1_RCPS_PATH)
    c1_bc = _read_json(C1_BC_PATH)
    if c1_rcps.get("domains") != ["law", "manual"] or c1_rcps.get("num_qa") != 1043:
        raise ValueError("C1 artifact is not the audited 1,043-Q-A Law--Manual subset")
    if c1_bc.get("domains") != ["law", "manual"] or c1_bc.get("n") != 15:
        raise ValueError("C1 BC artifact is not the audited 15-variant Law--Manual grid")

    return {
        "schema_version": 2,
        "status": "audited_legacy_compatibility_subset_with_aligned_distill_not_full_v2",
        "generated_by": "scripts/analysis/audit_ohrbench_legacy_alignment.py",
        "source_artifacts": {
            str(R2_PATH.relative_to(ROOT)): _sha256(R2_PATH),
            str(R3_PATH.relative_to(ROOT)): _sha256(R3_PATH),
            str(DISTILL_PATH.relative_to(ROOT)): _sha256(DISTILL_PATH),
            str(C1_RCPS_PATH.relative_to(ROOT)): _sha256(C1_RCPS_PATH),
            str(C1_BC_PATH.relative_to(ROOT)): _sha256(C1_BC_PATH),
        },
        "c1_aligned_perturbation_subset": {
            "domains": ["law", "manual"],
            "num_qa": 1043,
            "num_variants": 15,
            "pearson_bc_vs_rcps": round(float(c1_bc["pearson_BC_vs_RCPS"]), 6),
            "interpretation": "descriptive; variants within a noise family are not independent parsers",
        },
        "c4_strict_compatibility_subset": {
            "source_num_qa": 2264,
            "excluded": {
                "legacy_notes_zero_rows": 223,
                "reason": (
                    "stored arrays resolved legacy notes documents against unrelated v2 administration files"
                ),
                "missing_v2_page": MISSING_PAGE,
                "missing_v2_page_num_qa": 5,
                "missing_v2_page_qa_ids": sorted(MISSING_PAGE_QA_IDS),
            },
            "num_qa": 2036,
            "domain_counts": dict(sorted(strict_domains.items())),
            "retrievers": list(RETRIEVERS),
            "cutoffs": [1, 5, 10],
            "bootstrap": {"kind": "paired_percentile", "resamples": 1000, "seed": 42},
            "delta_vs_prod_pp": {
                "RADP-DPO-R2": _model_metrics(r2, "dpo_v4", mask),
                "RADP-DPO-R3": _model_metrics(r3, "v5", mask),
                "RADP-Distill": _model_metrics(distill, "arm_b", mask),
            },
            "paired_hit_at_5_contrasts_pp": {
                "RADP-Distill_minus_RADP-DPO-R2": _paired_delta(
                    _hit_at_5(distill, "arm_b", mask),
                    _hit_at_5(r2, "dpo_v4", mask),
                ),
                "RADP-Distill_minus_RADP-DPO-R3": _paired_delta(
                    _hit_at_5(distill, "arm_b", mask),
                    _hit_at_5(r3, "v5", mask),
                ),
            },
        },
        "submission_gate": {
            "full_v2_rerun_completed": False,
            "full_v2_inputs": ["OHR-Bench_v2.parquet", "data/qas_v2.json"],
            "camera_ready_scope_decision": (
                "retain the source-aligned 2,036-Q-A compatibility subset and make no full-v2 claim"
            ),
            "radp_distill_comparison_available": True,
            "warning": (
                "Do not cite unfiltered seven-domain, 2,264-Q-A, or OHR TextNED results. "
                "RADP-Distill is valid only after applying this strict 2,036-Q-A mask."
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", type=Path, help="compare the reproduced report with a tracked JSON file")
    args = parser.parse_args()

    report = build_report()
    if args.check:
        expected = _read_json(args.check)
        if report != expected:
            raise SystemExit(f"audit mismatch: {args.check}")
        print(f"OK: {args.check} matches the deterministic OHR alignment audit")
        return 0

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
