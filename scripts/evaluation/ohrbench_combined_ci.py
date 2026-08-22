"""Exploratory combined KoGov + corrected legacy OHR compatibility CI.

Union per-Q-A arrays from:
  - KoGov: output/results/FULL_HF_perqa_242p.json (RADP-DPO-v1, v1 ref)
  - OHR-Bench: output/results/ohrbench_v1dpo_perqa.json (dpo_v1, v1),
    filtered by output/results/ohrbench_alignment_audit.json

For each metric (hit, mrr, ndcg, recall) × k ∈ {1,5,10} × retriever:
  - Cross-retriever mean per Q-A
  - Concat KoGov + OHR per-Q-A → combined N
  - Paired bootstrap CI for DPO - v1

This cross-dataset union is not a camera-ready endpoint.  The alignment audit is
mandatory so the legacy 223-row notes failure and five missing-page Q-A cannot
silently enter the result.

Usage:
  uv run python scripts/evaluation/ohrbench_combined_ci.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
from pathlib import Path

import numpy as np

from wigtnocr_radp.evaluation.bootstrap import bootstrap_paired_delta

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("combined_ci")

ROOT = Path(__file__).resolve().parents[2]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _require_audited_source(path: Path, audit: dict) -> None:
    """Bind an OHR per-QA input to the exact artifact audited for alignment."""

    source_artifacts = audit.get("source_artifacts")
    if not isinstance(source_artifacts, dict):
        raise ValueError("OHR alignment audit lacks source_artifacts")

    try:
        repo_key = path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        repo_key = ""

    expected = source_artifacts.get(repo_key)
    if expected is None:
        basename_matches = [
            digest
            for source_path, digest in source_artifacts.items()
            if Path(source_path).name == path.name
        ]
        if len(basename_matches) != 1:
            raise ValueError(
                f"{path}: not uniquely identified by alignment-audit source_artifacts"
            )
        expected = basename_matches[0]

    actual = _sha256(path)
    if actual != expected:
        raise ValueError(
            f"{path}: SHA-256 does not match alignment audit "
            f"(expected {expected}, got {actual})"
        )


def _compatibility_mask(artifact: dict, audit: dict) -> np.ndarray:
    """Validate legacy Q-A identity/order, then derive the audited strict mask."""

    strict = audit.get("c4_strict_compatibility_subset")
    if not isinstance(strict, dict):
        raise ValueError("OHR alignment audit lacks c4_strict_compatibility_subset")
    excluded = strict.get("excluded")
    if not isinstance(excluded, dict):
        raise ValueError("OHR alignment audit lacks exclusion metadata")

    qa_ids = artifact.get("qa_ids")
    domains = artifact.get("domains")
    if not isinstance(qa_ids, list) or not isinstance(domains, list) or len(qa_ids) != len(domains):
        raise ValueError("OHR per-QA artifact lacks aligned qa_ids/domains arrays")
    if len(set(qa_ids)) != len(qa_ids):
        raise ValueError("OHR per-QA artifact contains duplicate qa_ids")

    source_n = int(strict["source_num_qa"])
    meta_n = artifact.get("meta", {}).get("n_qa")
    if len(qa_ids) != source_n or meta_n != source_n:
        raise ValueError(
            f"OHR source identity mismatch: qa_ids={len(qa_ids)}, meta.n_qa={meta_n}, "
            f"audit source_num_qa={source_n}"
        )

    expected_notes = int(excluded["legacy_notes_zero_rows"])
    notes_count = sum(domain == "notes" for domain in domains)
    if notes_count != expected_notes:
        raise ValueError(f"OHR notes identity mismatch: got {notes_count}, expected {expected_notes}")

    missing_ids = set(excluded["missing_v2_page_qa_ids"])
    expected_missing = int(excluded["missing_v2_page_num_qa"])
    found_missing = missing_ids.intersection(qa_ids)
    if len(missing_ids) != expected_missing or found_missing != missing_ids:
        raise ValueError(
            "OHR missing-page identity mismatch: "
            f"audit lists {len(missing_ids)}, artifact contains {len(found_missing)}, "
            f"expected {expected_missing}"
        )

    for model, values in artifact.get("models", {}).items():
        if not isinstance(values, dict):
            raise ValueError(f"OHR model {model!r} has invalid metric mapping")
        for key, values_per_qa in values.items():
            if len(values_per_qa) != source_n:
                raise ValueError(
                    f"OHR model {model!r} metric {key!r} has {len(values_per_qa)} values; "
                    f"expected {source_n} in qa_ids order"
                )

    mask = np.asarray(
        [domain != "notes" and qa_id not in missing_ids for qa_id, domain in zip(qa_ids, domains)],
        dtype=bool,
    )
    expected_n = int(strict["num_qa"])
    if int(mask.sum()) != expected_n:
        raise ValueError(f"OHR compatibility mask produced {int(mask.sum())}, expected {expected_n}")

    actual_domains: dict[str, int] = {}
    for domain, keep in zip(domains, mask):
        if keep:
            actual_domains[domain] = actual_domains.get(domain, 0) + 1
    expected_domains = {str(k): int(v) for k, v in strict["domain_counts"].items()}
    if actual_domains != expected_domains:
        raise ValueError(
            f"OHR strict-domain identity mismatch: got {actual_domains}, expected {expected_domains}"
        )
    return mask


def load_kogov_perqa(path: Path, chunker: str = "parser_native"):
    """Load KoGov FULL_HF_perqa: returns {system_short: {(metric, retriever, k): np.ndarray}}.

    KoGov perqa file stores MRR only. Hit@k and nDCG@k cannot be reconstructed from MRR alone
    (Hit needs binary relevance per chunk; nDCG needs rank). So combined CI only supports MRR.
    """
    d = json.loads(path.read_text())
    meta = d["meta"]
    retrievers = meta["retrievers"]
    k_values = meta["k_values"]
    n = len(meta["qa_ids"])
    logger.info("KoGov perqa: n=%d Q-A, retrievers=%s, k=%s", n, retrievers, k_values)

    # We need: v1 (ref) and RADP-DPO-v1, both at parser_native
    wanted_labels = {
        "v1 (ref)": "v1",
        "RADP-DPO-v1": "dpo_v1",
        "RADP-DPO-v4": "dpo_v4",
    }
    out: dict[str, dict] = {}
    for label, short in wanted_labels.items():
        sys_key = f"{label}__{chunker}"
        if sys_key not in d["systems"]:
            logger.warning("missing KoGov system: %s", sys_key)
            continue
        sysd = d["systems"][sys_key]
        per_qa: dict[tuple[str, str, int], np.ndarray] = {}
        for retr in retrievers:
            for k in k_values:
                key = f"{retr}__mrr@{k}"
                if key in sysd:
                    per_qa[("mrr", retr, int(k))] = np.array(sysd[key], dtype=float)
        out[short] = per_qa
        logger.info("  loaded KoGov [%s]: %d metric entries", short, len(per_qa))
    return out, retrievers, k_values


def load_ohr_perqa(path: Path, alignment_audit: Path):
    """Load OHR per-QA arrays after applying the tracked compatibility mask."""
    d = json.loads(path.read_text())
    audit = json.loads(alignment_audit.read_text())
    if audit.get("status") != "corrected_legacy_compatibility_subset_not_full_v2":
        raise ValueError(f"unsupported OHR alignment audit status: {alignment_audit}")
    _require_audited_source(path, audit)
    mask = _compatibility_mask(d, audit)
    expected_n = int(audit["c4_strict_compatibility_subset"]["num_qa"])
    meta = d["meta"]
    logger.info(
        "OHR perqa: legacy n=%d, aligned n=%d, retrievers=%s, k=%s",
        meta["n_qa"], expected_n, meta["retrievers"], meta["k_values"],
    )
    out: dict[str, dict] = {}
    for model, vals in d["models"].items():
        per_qa: dict[tuple[str, str, int], np.ndarray] = {}
        for full_key, arr in vals.items():
            # full_key format: "hit@5__bge-m3"
            metric_part, retr = full_key.split("__")
            metric, kpart = metric_part.split("@")
            per_qa[(metric, retr, int(kpart))] = np.array(arr, dtype=float)[mask]
        out[model] = per_qa
        logger.info("  loaded OHR [%s]: %d metric entries", model, len(per_qa))
    return out


def cross_retriever_mean(per_qa, metric, retr_names, k):
    arrs = [per_qa[(metric, n, k)] for n in retr_names if (metric, n, k) in per_qa]
    if not arrs:
        return None
    return np.mean(np.stack(arrs, axis=0), axis=0)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kogov_perqa", type=Path,
                    default=Path("output/results/FULL_HF_perqa_242p.json"))
    ap.add_argument("--ohr_perqa", type=Path,
                    default=Path("output/results/ohrbench_v1dpo_perqa.json"))
    ap.add_argument("--ohr_alignment_audit", type=Path,
                    default=Path("output/results/ohrbench_alignment_audit.json"))
    ap.add_argument("--out", type=Path,
                    default=Path("output/results/combined_kogov_ohr_compat_ci.json"))
    ap.add_argument("--n_boot", type=int, default=1000)
    args = ap.parse_args()

    kogov, kogov_retrs, kogov_ks = load_kogov_perqa(args.kogov_perqa)
    ohr = load_ohr_perqa(args.ohr_perqa, args.ohr_alignment_audit)

    # KoGov has 3 retrievers; OHR also 3. Use retriever names from KoGov for cross-mean.
    # (OHR retriever names should match if same Python wigtnocr_radp.evaluation.retrievers).
    out: dict = {
        "meta": {
            "kogov_n": int(np.array(list(kogov["v1"].values())[0]).shape[0]) if "v1" in kogov else 0,
            "ohr_n": int(np.array(list(ohr["v1"].values())[0]).shape[0]) if "v1" in ohr else 0,
            "kogov_retrievers": kogov_retrs,
            "n_boot": args.n_boot,
        },
        "paired_vs_v1": {},
    }
    out["meta"]["combined_n"] = out["meta"]["kogov_n"] + out["meta"]["ohr_n"]

    if "v1" not in kogov or "v1" not in ohr:
        logger.error("missing v1 in one of the perqa files; abort")
        return 1

    for dpo_model in ("dpo_v1", "dpo_v4"):
        if dpo_model not in kogov or dpo_model not in ohr:
            logger.warning("skip %s: missing in kogov(%s) or ohr(%s)",
                           dpo_model, dpo_model in kogov, dpo_model in ohr)
            continue
        rows = {}
        # MRR only — common across both datasets (hit/ndcg/recall require per-chunk re-scoring)
        for k in (1, 5, 10):
            for dataset_name, kogov_data, ohr_data, retr_list in [
                ("kogov", kogov, ohr, kogov_retrs),
                ("ohr_only", ohr, ohr, kogov_retrs),
                ("combined", kogov, ohr, kogov_retrs),
            ]:
                if dataset_name == "kogov":
                    a = cross_retriever_mean(kogov[dpo_model], "mrr", kogov_retrs, k)
                    b = cross_retriever_mean(kogov["v1"], "mrr", kogov_retrs, k)
                elif dataset_name == "ohr_only":
                    a = cross_retriever_mean(ohr[dpo_model], "mrr", kogov_retrs, k)
                    b = cross_retriever_mean(ohr["v1"], "mrr", kogov_retrs, k)
                else:  # combined
                    a_k = cross_retriever_mean(kogov[dpo_model], "mrr", kogov_retrs, k)
                    b_k = cross_retriever_mean(kogov["v1"], "mrr", kogov_retrs, k)
                    a_o = cross_retriever_mean(ohr[dpo_model], "mrr", kogov_retrs, k)
                    b_o = cross_retriever_mean(ohr["v1"], "mrr", kogov_retrs, k)
                    if any(x is None for x in [a_k, b_k, a_o, b_o]):
                        continue
                    a = np.concatenate([a_k, a_o])
                    b = np.concatenate([b_k, b_o])
                if a is None or b is None:
                    continue
                delta = bootstrap_paired_delta(a, b, n_boot=args.n_boot, alpha=0.05, seed=42)
                rows[f"mrr@{k}__{dataset_name}"] = {
                    "n": int(a.shape[0]),
                    "delta_pp": round(delta.mean * 100, 3),
                    "ci_lo_pp": round(delta.lo * 100, 3),
                    "ci_hi_pp": round(delta.hi * 100, 3),
                    "two_sided_sig": bool(delta.lo > 0 or delta.hi < 0),
                }
        # OHR-only Hit/nDCG/Recall (kogov has only MRR)
        for metric in ("hit", "ndcg", "recall"):
            for k in (1, 5, 10):
                a = cross_retriever_mean(ohr[dpo_model], metric, kogov_retrs, k)
                b = cross_retriever_mean(ohr["v1"], metric, kogov_retrs, k)
                if a is None or b is None:
                    continue
                delta = bootstrap_paired_delta(a, b, n_boot=args.n_boot, alpha=0.05, seed=42)
                rows[f"{metric}@{k}__ohr_only"] = {
                    "n": int(a.shape[0]),
                    "delta_pp": round(delta.mean * 100, 3),
                    "ci_lo_pp": round(delta.lo * 100, 3),
                    "ci_hi_pp": round(delta.hi * 100, 3),
                    "two_sided_sig": bool(delta.lo > 0 or delta.hi < 0),
                }
        out["paired_vs_v1"][dpo_model] = rows

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    logger.info("wrote %s", args.out)

    # Print summary
    print(f"\n{'='*84}")
    print(f"Combined KoGov + OHR-Bench paired CI (n_boot={args.n_boot})")
    print(f"KoGov n={out['meta']['kogov_n']}, OHR n={out['meta']['ohr_n']}, combined n={out['meta']['combined_n']}")
    print(f"{'='*84}")
    for dpo_model, rows in out["paired_vs_v1"].items():
        print(f"\n[{dpo_model} vs v1]")
        print(f"  {'key':<30}{'n':>6}{'Δpp':>10}{'95% CI':>22}{'sig':>6}")
        for key in sorted(rows.keys()):
            v = rows[key]
            sig = "**" if v["two_sided_sig"] else "  "
            ci_str = f"[{v['ci_lo_pp']:+.2f}, {v['ci_hi_pp']:+.2f}]"
            print(f"  {key:<30}{v['n']:>6}{v['delta_pp']:>+10.2f}{ci_str:>22}{sig:>6}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
