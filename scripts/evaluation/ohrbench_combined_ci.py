"""Combined KoGov + OHR-Bench paired CI — n boost for two-sided sig.

Union per-Q-A arrays from:
  - KoGov: output/results/FULL_HF_perqa_242p_7seeds.json (RADP-DPO-v1, v1 ref)
  - OHR-Bench: output/results/ohrbench_v1dpo_perqa.json (dpo_v1, v1)

For each metric (hit, mrr, ndcg, recall) × k ∈ {1,5,10} × retriever:
  - Cross-retriever mean per Q-A
  - Concat KoGov + OHR per-Q-A → combined N
  - Paired bootstrap CI for DPO - v1

Goal: n=663 + ~2000 → tighter CI, push Hit@1/5 two-sided sig.

Usage:
  uv run python scripts/evaluation/ohrbench_combined_ci.py
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import numpy as np

from wigtnocr_radp.evaluation.bootstrap import bootstrap_paired_delta

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("combined_ci")


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


def load_ohr_perqa(path: Path):
    """Load OHR perqa: returns {model: {(metric, retriever, k): np.ndarray}}."""
    d = json.loads(path.read_text())
    meta = d["meta"]
    n = meta["n_qa"]
    logger.info("OHR perqa: n=%d Q-A, retrievers=%s, k=%s",
                n, meta["retrievers"], meta["k_values"])
    out: dict[str, dict] = {}
    for model, vals in d["models"].items():
        per_qa: dict[tuple[str, str, int], np.ndarray] = {}
        for full_key, arr in vals.items():
            # full_key format: "hit@5__bge-m3"
            metric_part, retr = full_key.split("__")
            metric, kpart = metric_part.split("@")
            per_qa[(metric, retr, int(kpart))] = np.array(arr, dtype=float)
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
                    default=Path("output/results/FULL_HF_perqa_242p_7seeds.json"))
    ap.add_argument("--ohr_perqa", type=Path,
                    default=Path("output/results/ohrbench_v1dpo_perqa.json"))
    ap.add_argument("--out", type=Path,
                    default=Path("output/results/combined_kogov_ohr_ci.json"))
    ap.add_argument("--n_boot", type=int, default=1000)
    args = ap.parse_args()

    kogov, kogov_retrs, kogov_ks = load_kogov_perqa(args.kogov_perqa)
    ohr = load_ohr_perqa(args.ohr_perqa)

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
