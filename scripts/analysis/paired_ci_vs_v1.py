"""Paired bootstrap CI of every variant vs v1 (production parser).

The existing FULL_HF_ci_242p.json computes Δ vs λ=0 (RADP-B aux control).
The central check needs Δ vs **v1** (the production fine-tuned parser):
the question is "does parser-side preference learning improve over v1?".

Outputs (per chunker × {RCPS aggregate, per-retriever MRR@k, standard Hit@k}):
  - paired CI 95% on (variant − v1) per Q-A
  - mean delta in pp
  - sign (positive = improvement)

Hit@k is derived as 1{MRR@k > 0} per Q-A.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np

from wigtnocr_radp.evaluation.bootstrap import bootstrap_mean, bootstrap_paired_delta

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] PAIRED: %(message)s")
log = logging.getLogger("paired")

ROOT = Path("/mnt/data1/work/WigtnOCR-RADP")
PERQA = ROOT / "output/results/FULL_HF_perqa_242p.json"
OUT_JSON = ROOT / "output/results/dpo_paired_ci_vs_v1_242p.json"
OUT_MD = ROOT / "output/results/dpo_paired_ci_vs_v1_242p.md"

N_BOOT = 1000
ALPHA = 0.05
REF_LABEL = "v1 (ref)"
RETRIEVERS = ("bge-m3", "ml-e5-large", "qwen3-emb-8b")
K_VALUES = (1, 5, 10)
CHUNKERS = ("md_h3", "parser_native")


def mrr_array(systems: dict, label: str, ck: str, retr: str, k: int) -> np.ndarray:
    return np.asarray(systems[f"{label}__{ck}"][f"{retr}__mrr@{k}"], dtype=float)


def hit_array(systems: dict, label: str, ck: str, retr: str, k: int) -> np.ndarray:
    return (mrr_array(systems, label, ck, retr, k) > 0).astype(float)


def rcps_array(systems: dict, label: str, ck: str) -> np.ndarray:
    """RCPS aggregate per Q-A: mean over (retriever, k) of MRR@k."""
    stacks = []
    for r in RETRIEVERS:
        for k in K_VALUES:
            stacks.append(mrr_array(systems, label, ck, r, k))
    return np.stack(stacks).mean(axis=0)


def hit_macro_array(systems: dict, label: str, ck: str, k: int) -> np.ndarray:
    """Mean Hit@k across the 3 retrievers, per Q-A."""
    stacks = [hit_array(systems, label, ck, r, k) for r in RETRIEVERS]
    return np.stack(stacks).mean(axis=0)


def main() -> int:
    raw = json.loads(PERQA.read_text())
    systems = raw["systems"]
    labels = sorted({k.rsplit("__", 1)[0] for k in systems})
    variants = [l for l in labels if l != REF_LABEL]
    log.info("ref=%s, variants=%d", REF_LABEL, len(variants))

    out: dict = {
        "meta": {
            "ref": REF_LABEL,
            "n_boot": N_BOOT,
            "alpha": ALPHA,
            "chunkers": list(CHUNKERS),
            "retrievers": list(RETRIEVERS),
            "k_values": list(K_VALUES),
            "source": str(PERQA.relative_to(ROOT)),
        },
        "by_chunker": {},
    }

    md_lines: list[str] = []
    md_lines.append("# Paired bootstrap CI vs v1 — 12-variant on 242p (n=663 Q-A)")
    md_lines.append("")
    md_lines.append(f"Source: `{PERQA.relative_to(ROOT)}`. CI: 95% percentile, N={N_BOOT} bootstrap, paired by Q-A.")
    md_lines.append("Hit@k derived as 1{MRR@k > 0}. RCPS = mean MRR across 3 retrievers × {k=1,5,10}.")
    md_lines.append("")

    for ck in CHUNKERS:
        out["by_chunker"][ck] = {}
        ref_rcps = rcps_array(systems, REF_LABEL, ck)
        ref_rcps_ci = bootstrap_mean(ref_rcps, n_boot=N_BOOT, alpha=ALPHA, seed=42).to_dict()
        ref_hit1 = hit_macro_array(systems, REF_LABEL, ck, 1)
        ref_hit5 = hit_macro_array(systems, REF_LABEL, ck, 5)
        ref_mrr10 = np.stack([mrr_array(systems, REF_LABEL, ck, r, 10) for r in RETRIEVERS]).mean(0)
        log.info("[%s] v1 RCPS=%.4f, Hit@1=%.4f, Hit@5=%.4f, MRR@10=%.4f", ck, ref_rcps.mean(),
                 ref_hit1.mean(), ref_hit5.mean(), ref_mrr10.mean())

        md_lines.append(f"## chunker = `{ck}`")
        md_lines.append("")
        md_lines.append("**v1 (ref) anchors**: "
                        f"RCPS={ref_rcps.mean():.4f} "
                        f"[{ref_rcps_ci['lo']:.4f}, {ref_rcps_ci['hi']:.4f}], "
                        f"Hit@1={ref_hit1.mean():.4f}, "
                        f"Hit@5={ref_hit5.mean():.4f}, "
                        f"MRR@10={ref_mrr10.mean():.4f}")
        md_lines.append("")
        md_lines.append("### Δ (variant − v1) bootstrap CI 95% — in pp")
        md_lines.append("")
        md_lines.append("| Variant | ΔRCPS pp [CI] | ΔHit@1 pp [CI] | ΔHit@5 pp [CI] | ΔMRR@10 pp [CI] | sig? |")
        md_lines.append("|---|---|---|---|---|---|")

        for label in variants:
            row: dict = {}

            # RCPS aggregate
            var_rcps = rcps_array(systems, label, ck)
            d_rcps = bootstrap_paired_delta(var_rcps, ref_rcps, n_boot=N_BOOT, alpha=ALPHA, seed=42).to_dict()
            row["rcps"] = {
                "var_mean": float(var_rcps.mean()),
                "ref_mean": float(ref_rcps.mean()),
                "delta_pp": d_rcps["mean"] * 100,
                "ci_lo_pp": d_rcps["lo"] * 100,
                "ci_hi_pp": d_rcps["hi"] * 100,
            }

            # Hit@1
            var_h1 = hit_macro_array(systems, label, ck, 1)
            d_h1 = bootstrap_paired_delta(var_h1, ref_hit1, n_boot=N_BOOT, alpha=ALPHA, seed=42).to_dict()
            row["hit@1"] = {"delta_pp": d_h1["mean"]*100, "ci_lo_pp": d_h1["lo"]*100, "ci_hi_pp": d_h1["hi"]*100}

            # Hit@5
            var_h5 = hit_macro_array(systems, label, ck, 5)
            d_h5 = bootstrap_paired_delta(var_h5, ref_hit5, n_boot=N_BOOT, alpha=ALPHA, seed=42).to_dict()
            row["hit@5"] = {"delta_pp": d_h5["mean"]*100, "ci_lo_pp": d_h5["lo"]*100, "ci_hi_pp": d_h5["hi"]*100}

            # MRR@10
            var_mrr10 = np.stack([mrr_array(systems, label, ck, r, 10) for r in RETRIEVERS]).mean(0)
            d_mrr10 = bootstrap_paired_delta(var_mrr10, ref_mrr10, n_boot=N_BOOT, alpha=ALPHA, seed=42).to_dict()
            row["mrr@10"] = {"delta_pp": d_mrr10["mean"]*100, "ci_lo_pp": d_mrr10["lo"]*100, "ci_hi_pp": d_mrr10["hi"]*100}

            # Per-retriever Hit@5 (so user can see which embedder benefits)
            row["per_retriever_hit@5"] = {}
            for r in RETRIEVERS:
                vh = hit_array(systems, label, ck, r, 5)
                rh = hit_array(systems, REF_LABEL, ck, r, 5)
                dr = bootstrap_paired_delta(vh, rh, n_boot=N_BOOT, alpha=ALPHA, seed=42).to_dict()
                row["per_retriever_hit@5"][r] = {"delta_pp": dr["mean"]*100,
                                                   "ci_lo_pp": dr["lo"]*100,
                                                   "ci_hi_pp": dr["hi"]*100}

            # Sig: 0 outside CI
            sig_rcps = "+" if d_rcps["lo"] > 0 else ("-" if d_rcps["hi"] < 0 else "0")
            out["by_chunker"][ck][label] = row

            def fmt(d):
                return f"{d['mean']*100:+.2f} [{d['lo']*100:+.2f}, {d['hi']*100:+.2f}]"
            md_lines.append(
                f"| {label} | {fmt(d_rcps)} | {fmt(d_h1)} | {fmt(d_h5)} | {fmt(d_mrr10)} | "
                f"**{sig_rcps}** |"
            )
            log.info("  %s  ΔRCPS=%+.2fpp [%+.2f, %+.2f]  ΔHit@1=%+.2fpp  ΔHit@5=%+.2fpp",
                     label,
                     d_rcps["mean"]*100, d_rcps["lo"]*100, d_rcps["hi"]*100,
                     d_h1["mean"]*100, d_h5["mean"]*100)

        md_lines.append("")
        md_lines.append("**Per-retriever Hit@5 Δ vs v1** (which embedder, if any, sees DPO benefit)")
        md_lines.append("")
        md_lines.append("| Variant | BGE-M3 Hit@5 Δpp [CI] | mE5-large Hit@5 Δpp [CI] | Qwen3-Emb-8B Hit@5 Δpp [CI] |")
        md_lines.append("|---|---|---|---|")
        for label in variants:
            row = out["by_chunker"][ck][label]["per_retriever_hit@5"]
            cells = []
            for r in RETRIEVERS:
                d = row[r]
                cells.append(f"{d['delta_pp']:+.2f} [{d['ci_lo_pp']:+.2f}, {d['ci_hi_pp']:+.2f}]")
            md_lines.append(f"| {label} | {cells[0]} | {cells[1]} | {cells[2]} |")
        md_lines.append("")

    md_lines.append("## Reading guide")
    md_lines.append("")
    md_lines.append("- **sig = `+`** → CI lower bound > 0, statistically positive (Δ > 0)")
    md_lines.append("- **sig = `-`** → CI upper bound < 0, statistically negative")
    md_lines.append("- **sig = `0`** → CI straddles 0, no significant effect")
    md_lines.append("")
    md_lines.append("Industry-track relevance: even **+1pp with CI excluding 0** would be a")
    md_lines.append("publishable contribution. If all `sig = 0`, the parser-side preference learning thesis")
    md_lines.append("is genuinely null on 242p — supports comprehensive-negative framing.")

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    OUT_MD.write_text("\n".join(md_lines))
    log.info("wrote %s", OUT_JSON)
    log.info("wrote %s", OUT_MD)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
