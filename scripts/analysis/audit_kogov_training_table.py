"""Reproduce the camera-ready KoGovDoc-RAG parser-training table on CPU.

The tracked per-Q--A files store MRR arrays rather than explicit Hit arrays.
For each retriever, Hit@5 is therefore reconstructed as ``MRR@5 > 0``.  The
table value is the per-Q--A macro over three retrievers.  RCPS is the per-Q--A
mean over the same retrievers and retrieval depths k={1,5,10}.

The paired percentile bootstrap uses 10,000 Q--A resamples with NumPy seed 42,
matching Table 8 of the camera-ready manuscript.  No model or GPU is required.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
FULL_SOURCE = ROOT / "output/results/FULL_HF_perqa_242p.json"
R3_SOURCE = ROOT / "output/results/v5_kogov_perqa.json"
DEFAULT_OUT = ROOT / "output/results/kogov_training_table_10k_audit.json"

REF = "v1 (ref)"
CHUNKER = "parser_native"
RETRIEVERS = ("bge-m3", "ml-e5-large", "qwen3-emb-8b")
K_VALUES = (1, 5, 10)
N_BOOT = 10_000
SEED = 42

ROWS = (
    ("RADP-DPO-R3", "RADP-DPO-v5", "r3_source"),
    ("RADP-DPO-R1", "RADP-DPO-v1", "full_source"),
    ("RADP-DPO-R2", "RADP-DPO-v4", "full_source"),
    ("RADP-SimPO (ctrl)", "RADP-SimPO", "full_source"),
)

EXPECTED_DISPLAY = {
    "Prod": {"hit_at_5": "0.6757"},
    "RADP-DPO-R3": {
        "hit_at_5": "0.6968",
        "delta_hit_at_5_pp": "+2.11",
        "ci95_pp": ["-0.90", "+5.13"],
        "p_boot": "0.91",
        "delta_rcps_pp": "+1.72",
    },
    "RADP-DPO-R1": {
        "hit_at_5": "0.6963",
        "delta_hit_at_5_pp": "+2.06",
        "ci95_pp": ["-0.96", "+5.13"],
        "p_boot": "0.91",
        "delta_rcps_pp": "+0.57",
    },
    "RADP-DPO-R2": {
        "hit_at_5": "0.6953",
        "delta_hit_at_5_pp": "+1.96",
        "ci95_pp": ["-1.06", "+5.03"],
        "p_boot": "0.90",
        "delta_rcps_pp": "+0.47",
    },
    "RADP-SimPO (ctrl)": {
        "hit_at_5": "0.6687",
        "delta_hit_at_5_pp": "-0.70",
        "ci95_pp": ["-3.77", "+2.31"],
        "p_boot": "0.32",
        "delta_rcps_pp": "-1.56",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_source(path: Path) -> dict[str, Any]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    meta = doc.get("meta", {})
    if tuple(meta.get("retrievers", ())) != RETRIEVERS:
        raise ValueError(f"{path}: unexpected retriever order")
    if tuple(meta.get("k_values", ())) != K_VALUES:
        raise ValueError(f"{path}: unexpected retrieval depths")
    if len(meta.get("qa_ids", ())) != 663:
        raise ValueError(f"{path}: expected 663 Q--A IDs")
    return doc


def mrr_array(doc: dict[str, Any], label: str, retriever: str, k: int) -> np.ndarray:
    key = f"{label}__{CHUNKER}"
    metric = f"{retriever}__mrr@{k}"
    try:
        values = doc["systems"][key][metric]
    except KeyError as exc:
        raise KeyError(f"missing {key}/{metric}") from exc
    result = np.asarray(values, dtype=float)
    if result.shape != (663,):
        raise ValueError(f"{key}/{metric}: expected 663 values, got {result.shape}")
    return result


def hit_at_5_array(doc: dict[str, Any], label: str) -> np.ndarray:
    per_retriever = [
        (mrr_array(doc, label, retriever, 5) > 0).astype(float)
        for retriever in RETRIEVERS
    ]
    return np.stack(per_retriever, axis=0).mean(axis=0)


def rcps_array(doc: dict[str, Any], label: str) -> np.ndarray:
    values = [
        mrr_array(doc, label, retriever, k)
        for retriever in RETRIEVERS
        for k in K_VALUES
    ]
    return np.stack(values, axis=0).mean(axis=0)


def paired_bootstrap(delta: np.ndarray) -> dict[str, float]:
    rng = np.random.default_rng(SEED)
    indices = rng.integers(0, delta.size, size=(N_BOOT, delta.size))
    means = delta[indices].mean(axis=1)
    return {
        "mean_pp": float(delta.mean() * 100),
        "ci95_lo_pp": float(np.percentile(means, 2.5) * 100),
        "ci95_hi_pp": float(np.percentile(means, 97.5) * 100),
        "p_boot_delta_gt_zero": float((means > 0).mean()),
    }


def signed(value: float) -> str:
    return f"{value:+.2f}"


def display_row(row: dict[str, Any]) -> dict[str, Any]:
    delta = row["delta_hit_at_5"]
    return {
        "hit_at_5": f"{row['hit_at_5']:.4f}",
        "delta_hit_at_5_pp": signed(delta["mean_pp"]),
        "ci95_pp": [signed(delta["ci95_lo_pp"]), signed(delta["ci95_hi_pp"])],
        "p_boot": f"{delta['p_boot_delta_gt_zero']:.2f}",
        "delta_rcps_pp": signed(row["delta_rcps_pp"]),
    }


def build_report() -> dict[str, Any]:
    full = load_source(FULL_SOURCE)
    r3 = load_source(R3_SOURCE)
    sources = {"full_source": full, "r3_source": r3}

    if full["meta"]["qa_ids"] != r3["meta"]["qa_ids"]:
        raise ValueError("the two sources do not share identical Q--A order")
    for retriever in RETRIEVERS:
        for k in K_VALUES:
            if not np.array_equal(
                mrr_array(full, REF, retriever, k),
                mrr_array(r3, REF, retriever, k),
            ):
                raise ValueError(f"Prod reference differs between sources at {retriever}/MRR@{k}")

    reference_hit = hit_at_5_array(full, REF)
    reference_rcps = rcps_array(full, REF)
    rows: list[dict[str, Any]] = []
    for paper_label, source_label, source_key in ROWS:
        source = sources[source_key]
        hit = hit_at_5_array(source, source_label)
        source_ref_hit = hit_at_5_array(source, REF)
        rcps = rcps_array(source, source_label)
        source_ref_rcps = rcps_array(source, REF)
        row = {
            "variant": paper_label,
            "source_label": source_label,
            "source": source_key,
            "hit_at_5": float(hit.mean()),
            "delta_hit_at_5": paired_bootstrap(hit - source_ref_hit),
            "delta_rcps_pp": float((rcps - source_ref_rcps).mean() * 100),
        }
        row["camera_ready_display"] = display_row(row)
        if row["camera_ready_display"] != EXPECTED_DISPLAY[paper_label]:
            raise ValueError(f"{paper_label}: recomputation no longer matches Table 8")
        rows.append(row)

    seed_labels = ("RADP-DPO-v1", "DPO-v1-seed123", "DPO-v1-seed999")
    seed_deltas = {
        label: float((hit_at_5_array(full, label) - reference_hit).mean() * 100)
        for label in seed_labels
    }
    seed_std = float(np.std(list(seed_deltas.values()), ddof=1))
    if f"{seed_std:.2f}" != "0.90":
        raise ValueError("three-seed standard deviation no longer rounds to 0.90 pp")

    prod_display = {"hit_at_5": f"{reference_hit.mean():.4f}"}
    if prod_display != EXPECTED_DISPLAY["Prod"]:
        raise ValueError("Prod Hit@5 no longer matches Table 8")

    return {
        "schema_version": 1,
        "scope": {
            "dataset": "KoGovDoc-RAG",
            "num_pages": 242,
            "num_qa": 663,
            "chunker": CHUNKER,
            "retrievers": list(RETRIEVERS),
            "retrieval_depths": list(K_VALUES),
        },
        "method": {
            "hit_at_5": "mean over retrievers of indicator(MRR@5 > 0), then mean over Q--A",
            "rcps": "mean MRR over retrievers and k={1,5,10}, then mean over Q--A",
            "uncertainty": "paired Q--A-level percentile bootstrap",
            "resamples": N_BOOT,
            "seed": SEED,
            "p_boot_definition": (
                "fraction of bootstrap mean deltas strictly greater than zero; not a p-value"
            ),
        },
        "inputs": {
            "full_source": {
                "path": str(FULL_SOURCE.relative_to(ROOT)),
                "sha256": sha256(FULL_SOURCE),
            },
            "r3_source": {
                "path": str(R3_SOURCE.relative_to(ROOT)),
                "sha256": sha256(R3_SOURCE),
            },
            "runner": {
                "path": str(Path(__file__).resolve().relative_to(ROOT)),
                "sha256": sha256(Path(__file__).resolve()),
            },
        },
        "source_validation": {
            "identical_qa_ids_and_order": True,
            "identical_prod_reference_arrays": True,
        },
        "prod_reference": {
            "source_label": REF,
            "hit_at_5": float(reference_hit.mean()),
            "rcps": float(reference_rcps.mean()),
            "camera_ready_display": prod_display,
        },
        "rows": rows,
        "three_seed_r1_recipe": {
            "labels": list(seed_labels),
            "mean_delta_hit_at_5_pp_by_seed": seed_deltas,
            "sample_standard_deviation_pp": seed_std,
            "camera_ready_display": "0.90",
        },
        "verdict": "all camera-ready Table 8 values reproduce from tracked per-Q--A arrays",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--out", type=Path, help="write the deterministic audit JSON")
    group.add_argument("--check", type=Path, help="compare a tracked audit JSON with recomputation")
    args = parser.parse_args()

    report = build_report()
    if args.check is not None:
        tracked = json.loads(args.check.read_text(encoding="utf-8"))
        if tracked != report:
            raise ValueError(f"stale KoGov training-table audit: {args.check}")
        print(f"OK: {args.check} reproduces all camera-ready Table 8 values")
        return 0

    out = args.out or DEFAULT_OUT
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
