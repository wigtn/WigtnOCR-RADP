"""Figure 1 — The parsing-retrieval disconnect (the headline).

Two panels on Korean government documents (KoGov, Table 1):
  (a) BC vs RCPS scatter: the cleanest-boundary parsers (MinerU, Marker; highest
      BC) retrieve worst. Pearson r = -0.81 (n=5; PaddleOCR excluded — MoC
      detects zero boundaries so its Boundary Clarity is undefined).
  (b) Parser choice swings retrieval Hit@1 by 2.8x: picking by appearance
      (MinerU, 0.197) vs by RCPS (v1, 0.549).

Single source of truth (reproducible):
  - BC   : output/baselines/moc_bc_correlation.json   (Qwen3-VL-2B ppl)
  - RCPS / Hit@1 : output/baselines/grid_v1_parser_native.json
                   (3-retriever averaged: BGE-M3, mE5-large, Qwen3-Emb-8B; n=663)

Output: paper/figures/fig_disconnect.{pdf,png}
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
from scipy.stats import pearsonr

OUT_DIR = Path("paper/figures")

_BC = json.load(open("output/baselines/moc_bc_correlation.json"))["parsers"]
_GRID = {p["name"]: p for p in
         json.load(open("output/baselines/grid_v1_parser_native.json"))["parsers"]}
_SHORT = {
    "Qwen3-VL-30B (teacher)": "Qwen3-VL-30B\n(teacher)",
    "WigtnOCR-2B (ours, v1)": "Prod (ours)",
    "Qwen3-VL-2B (base)": "Qwen3-VL-2B\n(base)",
    "MinerU": "MinerU", "PaddleOCR": "PaddleOCR", "Marker": "Marker (38p)",
}

# (name, BC, RCPS, Hit@1).  BC may be NaN (PaddleOCR -> undefined).
PARSERS = []
for p in _BC:
    g = _GRID.get(p["parser"], {})
    PARSERS.append((_SHORT.get(p["parser"], p["parser"]),
                    p["mean_bc"], g.get("rcps"), g.get("hit@1")))

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def main() -> None:
    fig, (ax_s, ax_b) = plt.subplots(
        1, 2, figsize=(7.0, 2.9), gridspec_kw={"width_ratios": [1.45, 1.0], "wspace": 0.32}
    )

    # ---- (a) scatter: BC vs RCPS (valid BC only -> n=5) ----
    valid = [(bc, rc, name) for name, bc, rc, _ in PARSERS
             if bc is not None and not math.isnan(bc)]
    bcs = [p[0] for p in valid]
    rcps = [p[1] for p in valid]
    r, _ = pearsonr(bcs, rcps)

    ax_s.scatter(bcs, rcps, s=55, color="#1f77b4", zorder=3,
                 edgecolor="white", linewidth=0.6)

    # offsets tuned so the three clustered VLM labels fan out without overlap
    label_off = {
        "MinerU": (9, -1), "Marker (38p)": (9, -1),
        "Prod (ours)": (-9, 11),                  # above-left of the cluster
        "Qwen3-VL-30B\n(teacher)": (11, 5),       # above-right, clear of Prod
        "Qwen3-VL-2B\n(base)": (-2, -27),         # below
    }
    for bc, rc, name in valid:
        dx, dy = label_off.get(name, (6, 4))
        weight = "bold" if name in ("MinerU", "Marker (38p)") else "normal"
        ha = "center" if -10 <= dx <= 8 else ("right" if dx < 0 else "left")
        ax_s.annotate(name, (bc, rc), textcoords="offset points", xytext=(dx, dy),
                      fontsize=7.0, fontweight=weight, ha=ha)

    ax_s.set_xlabel("Boundary Clarity (intrinsic, MoC)")
    ax_s.set_ylabel("RCPS (retrieval)")
    ax_s.set_title(f"(a) Cleaner boundaries → worse retrieval\nPearson r = {r:.2f}  "
                   f"(n=5; PaddleOCR excl., BC undefined)", fontsize=8.5)
    ax_s.set_ylim(0, 0.68)
    ax_s.set_xlim(0.48, 0.76)
    # callout on the clean-but-worst cluster
    ax_s.annotate("highest BC,\nworst retrieval", xy=(0.716, 0.212), xytext=(0.66, 0.40),
                  fontsize=7, color="#d62728", ha="center",
                  arrowprops=dict(arrowstyle="->", color="#d62728", lw=1.1))

    # ---- (b) Hit@1 swing bar ----
    g = _GRID
    mineru_h1 = g["MinerU"]["hit@1"]
    v1_h1 = g["WigtnOCR-2B (ours, v1)"]["hit@1"]
    labels = ["Pick by\nappearance\n(MinerU)", "Pick by\nRCPS\n(Prod)"]
    vals = [mineru_h1, v1_h1]
    colors = ["#d62728", "#2ca02c"]
    bars = ax_b.bar(labels, vals, color=colors, width=0.6, zorder=3)
    for b, v in zip(bars, vals):
        ax_b.text(b.get_x() + b.get_width() / 2, v + 0.012, f"{v:.3f}",
                  ha="center", fontsize=8.5, fontweight="bold")
    ax_b.set_ylabel("Retrieval Hit@1")
    ax_b.set_ylim(0, 0.66)
    ax_b.set_title(f"(b) Parser choice swings\nHit@1 by {v1_h1/mineru_h1:.1f}×", fontsize=8.5)
    ax_b.annotate("", xy=(1, v1_h1), xytext=(0, v1_h1),
                  arrowprops=dict(arrowstyle="<->", color="#333333", lw=1.0))
    ax_b.text(0.5, v1_h1 + 0.026, f"{v1_h1/mineru_h1:.1f}×", ha="center",
              fontsize=9, fontweight="bold")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(OUT_DIR / f"fig_disconnect.{ext}", bbox_inches="tight", dpi=200)
    print(f"n={len(valid)}  Pearson r = {r:.4f}")
    print(f"Hit@1 swing: {v1_h1/mineru_h1:.2f}x  ({mineru_h1:.3f} -> {v1_h1:.3f})")
    print(f"saved -> {OUT_DIR}/fig_disconnect.pdf")


if __name__ == "__main__":
    main()
