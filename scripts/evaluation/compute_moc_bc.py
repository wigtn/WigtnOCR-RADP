"""MoC Boundary Clarity vs RCPS — intrinsic-vs-extrinsic correlation (PHASE_3 §3.2).

For each of the 6 baseline-grid parsers: chunk its markdown (parser_native),
compute mean MoC Boundary Clarity over adjacent chunk pairs, then correlate the
per-parser BC against the per-parser RCPS / Hit@1 from the baseline grid.

The paper claim (C2 defence): if BC (MoC's *intrinsic* metric) correlates weakly
with RCPS (our *extrinsic* metric), the two measure different things — RCPS is
complementary to intrinsic chunking metrics, not redundant.

Output: output/baselines/moc_bc_correlation.json + .md

Usage:
    CUDA_VISIBLE_DEVICES=1 uv run python scripts/evaluation/compute_moc_bc.py
"""

from __future__ import annotations

import os

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

import argparse  # noqa: E402
import json  # noqa: E402
import logging  # noqa: E402
import math  # noqa: E402
from pathlib import Path  # noqa: E402

from scipy import stats  # noqa: E402

from wigtnocr_radp.evaluation.boundary_clarity import PerplexityLM  # noqa: E402
from wigtnocr_radp.evaluation.chunkers import ParserNativeChunker  # noqa: E402
from wigtnocr_radp.evaluation.parser_outputs import load_parser_outputs  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("compute_moc_bc")

# (display name, v1 results dir, role) — same parser set as baseline_grid.py
PARSER_DEFS = [
    ("WigtnOCR-2B (ours, v1)", "v1_val", "ours"),
    ("Qwen3-VL-30B (teacher)", "30b_val", "teacher"),
    ("Qwen3-VL-2B (base)", "2b_base_val", "baseline"),
    ("MinerU", "mineru_val", "baseline"),
    ("Marker", "marker_val", "baseline"),
    ("PaddleOCR", "paddleocr_val", "baseline"),
]
V1_RESULTS_ROOT = Path("/mnt/data1/work/wigtnOCR-v1/results/kogovdoc")
VAL_JSONL = Path("data/KoGovDoc-Bench/val.jsonl")
GRID = Path("output/baselines/grid_v1_parser_native.json")


def corr_block(label: str, bc: list[float], metric: list[float]) -> dict:
    pr, pp = stats.pearsonr(bc, metric)
    sr, sp = stats.spearmanr(bc, metric)
    return {"label": label, "n": len(bc),
            "pearson_r": round(float(pr), 4), "pearson_p": round(float(pp), 4),
            "spearman_r": round(float(sr), 4), "spearman_p": round(float(sp), 4)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ppl_model", default="Qwen/Qwen3-VL-2B-Instruct")
    ap.add_argument("--out_dir", type=Path, default=Path("output/baselines"))
    args = ap.parse_args()

    rcps_by_parser = {
        p["name"]: {"rcps": p["rcps"], "hit@1": p["hit@1"]}
        for p in json.loads(GRID.read_text())["parsers"]
    }
    chunker = ParserNativeChunker(min_chars=30)
    ppl = PerplexityLM(model_id=args.ppl_model)

    rows: list[dict] = []
    for name, dir_name, role in PARSER_DEFS:
        pred_dir = V1_RESULTS_ROOT / dir_name / "predictions"
        if not pred_dir.is_dir():
            logger.warning("%s: predictions dir missing, skipping", name)
            continue
        pages = load_parser_outputs(pred_dir, VAL_JSONL)

        bc_vals: list[float] = []
        for page_id, md in pages.items():
            chunks = chunker.chunk(page_id, md)
            for i in range(len(chunks) - 1):
                bc = ppl.boundary_clarity(chunks[i].text, chunks[i + 1].text)
                if bc is not None:
                    bc_vals.append(bc)
        mean_bc = sum(bc_vals) / len(bc_vals) if bc_vals else float("nan")
        r = rcps_by_parser.get(name, {})
        row = {"parser": name, "role": role, "num_pages": len(pages),
               "num_boundaries": len(bc_vals), "mean_bc": round(mean_bc, 4),
               "rcps": r.get("rcps"), "hit@1": r.get("hit@1")}
        rows.append(row)
        logger.info("%s: BC=%.4f over %d boundaries (RCPS=%.4f)",
                    name, mean_bc, len(bc_vals), row["rcps"] or float("nan"))

    # Correlations — exclude parsers with no measurable boundaries (e.g. PaddleOCR:
    # flat OCR output yields 1 chunk/page), and the small-sample Marker (38p).
    valid = [r for r in rows if r["num_boundaries"] > 0 and math.isfinite(r["mean_bc"])]
    excluded = [r["parser"] for r in rows if not (r["num_boundaries"] > 0
                                                  and math.isfinite(r["mean_bc"]))]
    correlations = []
    for label, subset in [("all_valid", valid),
                          ("excluding_marker", [r for r in valid if r["parser"] != "Marker"])]:
        bc = [r["mean_bc"] for r in subset]
        correlations.append({
            "BC_vs_RCPS": corr_block(label, bc, [r["rcps"] for r in subset]),
            "BC_vs_Hit1": corr_block(label, bc, [r["hit@1"] for r in subset]),
        })

    report = {"ppl_model": args.ppl_model, "chunker": "parser_native",
              "excluded_from_correlation": excluded,
              "parsers": rows, "correlations": correlations}
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "moc_bc_correlation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))

    # Markdown report
    md = ["# MoC Boundary Clarity vs RCPS (intrinsic vs extrinsic)", "",
          f"Boundary Clarity per MoC (arXiv:2503.09600), ppl model `{args.ppl_model}`, "
          "chunker `parser_native`. Higher BC = cleaner boundaries (intrinsic).", "",
          "| Parser | role | pages | boundaries | **BC** | RCPS | Hit@1 |",
          "|--------|:----:|:----:|:----:|:----:|:----:|:----:|"]
    for r in rows:
        md.append(f"| {r['parser']} | {r['role']} | {r['num_pages']} | {r['num_boundaries']} "
                  f"| **{r['mean_bc']:.4f}** | {r['rcps']:.4f} | {r['hit@1']:.4f} |")
    md += ["", "## Correlation — Boundary Clarity (intrinsic) vs RCPS (extrinsic)", ""]
    for block in correlations:
        b = block["BC_vs_RCPS"]
        md += [f"### {b['label']} (n={b['n']})", "",
               "| Pair | Pearson r | Spearman r |", "|------|:---:|:---:|",
               f"| BC vs RCPS | {b['pearson_r']:+.3f} (p={b['pearson_p']:.2f}) "
               f"| {b['spearman_r']:+.3f} |",
               f"| BC vs Hit@1 | {block['BC_vs_Hit1']['pearson_r']:+.3f} "
               f"(p={block['BC_vs_Hit1']['pearson_p']:.2f}) "
               f"| {block['BC_vs_Hit1']['spearman_r']:+.3f} |", ""]
    (args.out_dir / "moc_bc_correlation.md").write_text("\n".join(md))

    print("\n".join(md))
    logger.info("wrote %s", args.out_dir / "moc_bc_correlation.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
