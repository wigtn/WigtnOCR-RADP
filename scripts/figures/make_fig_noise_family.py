"""Figure 2 — OHRBench noise-family curves: BC stays flat while RCPS plummets.

The mechanism behind C1: intrinsic boundary-clarity metrics do not perceive
semantic content quality. As semantic noise is added (clean → mild → moderate
→ severe), Boundary Clarity barely moves while RCPS collapses.

Source: output/results/ohrbench_bc_noise.json (15 parser-output variants on
OHR-Bench Law+Manual). We group the 3 base parsers (gt, MinerU, Qwen2.5-VL) +
their semantic_noise variants into 3 families. GOT has no clean baseline so
only its noise variants are plotted. Formatting-noise variants are not
parser-specific and are omitted from this figure.

Output: paper/figures/fig_noise_family.{pdf,png}
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt

SRC = Path("output/results/ohrbench_bc_noise.json")
OUT_DIR = Path("paper/figures")
SEVERITIES = ["clean", "mild", "moderate", "severe"]
FAMILIES = {
    "MinerU":     {"clean": "MinerU",     "noise": "semantic_noise_MinerU_{}"},
    "Qwen2.5-VL": {"clean": "Qwen2.5-VL", "noise": "semantic_noise_Qwen2.5-VL_{}"},
    "GOT":        {"clean": None,         "noise": "semantic_noise_GOT_{}"},
}
COLORS = {"MinerU": "#d62728", "Qwen2.5-VL": "#1f77b4", "GOT": "#2ca02c"}
MARKERS = {"MinerU": "o", "Qwen2.5-VL": "s", "GOT": "^"}


def collect(rows: list[dict]) -> dict[str, dict[str, tuple[float, float]]]:
    by_name = {r["parser"]: (r["boundary_clarity"], r["rcps"]) for r in rows}
    out: dict[str, dict[str, tuple[float, float]]] = {}
    for family, names in FAMILIES.items():
        series: dict[str, tuple[float, float]] = {}
        if names["clean"] and names["clean"] in by_name:
            series["clean"] = by_name[names["clean"]]
        for sev in ("mild", "moderate", "severe"):
            n = names["noise"].format(sev)
            if n in by_name:
                series[sev] = by_name[n]
        out[family] = series
    return out


def main() -> None:
    data = json.loads(SRC.read_text())
    series = collect(data["rows"])

    fig, (ax_bc, ax_rcps) = plt.subplots(
        2, 1, figsize=(5.2, 4.4), sharex=True, gridspec_kw={"hspace": 0.12}
    )

    for family, pts in series.items():
        sevs = [s for s in SEVERITIES if s in pts]
        bcs = [pts[s][0] for s in sevs]
        rcpss = [pts[s][1] for s in sevs]
        ax_bc.plot(sevs, bcs, marker=MARKERS[family], color=COLORS[family],
                   label=family, linewidth=1.6, markersize=6)
        ax_rcps.plot(sevs, rcpss, marker=MARKERS[family], color=COLORS[family],
                     label=family, linewidth=1.6, markersize=6)

    ax_bc.set_ylabel("Boundary Clarity")
    ax_bc.set_ylim(0.50, 0.70)
    ax_bc.grid(True, alpha=0.3, linestyle="--")
    ax_bc.legend(loc="lower right", fontsize=9, frameon=True)
    ax_bc.set_title("Intrinsic boundary metric is blind to content noise",
                    fontsize=10.5, pad=6)

    ax_rcps.set_ylabel("RCPS (3-retriever avg)")
    ax_rcps.set_xlabel("Semantic noise severity (OHR-Bench Law+Manual)")
    ax_rcps.set_ylim(0.20, 0.65)
    ax_rcps.grid(True, alpha=0.3, linestyle="--")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        out = OUT_DIR / f"fig_noise_family.{ext}"
        fig.savefig(out, bbox_inches="tight", dpi=200)
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
