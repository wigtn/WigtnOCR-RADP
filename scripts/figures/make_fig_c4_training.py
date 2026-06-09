"""Figure (C4) — parser-side training pipeline (best-of-K), reward-agnostic.

Prod -> sample K parses -> rank candidates -> LoRA-toggle DPO -> improved parser.
Ranking by edit-distance to GT (RADP-Distill) reproduces ranking by page-local
RCPS (RADP-DPO): the retrieval reward is unnecessary; the lever is fidelity
distillation (+1.22 pp Hit@5 on OHR-Bench).

Matches the visual style of make_fig_rcps_protocol.py (serif, rounded boxes).
Output: paper/figures/fig_c4_training.{pdf,png}
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT_DIR = Path("paper/figures")
plt.rcParams.update({"font.family": "serif"})

GREY = "#eaeaea"
BLUE = "#dbe9f6"
GREEN = "#cfe9cf"
TAN = "#fde7c9"
DGREEN = "#1a6b1a"
BROWN = "#9a5a00"


def box(ax, x, y, w, h, text, fc, fs=8.0, bold=False, ec="#333333", tc="#111111"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.008,rounding_size=0.02",
                                linewidth=1.0, edgecolor=ec, facecolor=fc, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            fontweight="bold" if bold else "normal", color=tc, zorder=3)


def arrow(ax, x1, y1, x2, y2, color="#333333"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=9, lw=1.1, color=color, zorder=1))


def main():
    fig, ax = plt.subplots(figsize=(3.3, 3.35))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    cx, w = 0.08, 0.50          # left flow column
    box(ax, cx, 0.875, w, 0.085, "Prod parser", GREY, 8.2)
    box(ax, cx, 0.745, w, 0.085, "sample $K$ parses", GREY, 8.2)
    box(ax, cx, 0.560, w, 0.115, "rank candidates", BLUE, 8.2, bold=True)
    box(ax, cx, 0.405, w, 0.085, "LoRA-toggle DPO", GREY, 8.2)
    box(ax, cx, 0.255, w, 0.095, "improved parser", GREEN, 8.4, bold=True, tc=DGREEN)
    for y1, y2 in [(0.875, 0.835), (0.745, 0.680), (0.560, 0.495), (0.405, 0.355)]:
        arrow(ax, cx + w / 2, y1, cx + w / 2, y2)

    # ranking-route annotation (right of "rank candidates")
    box(ax, 0.62, 0.625, 0.36, 0.095, "edit-dist → GT\nRADP-Distill ✓", GREEN, 7.2, tc=DGREEN)
    box(ax, 0.62, 0.510, 0.36, 0.090, "page-RCPS\nRADP-DPO", TAN, 7.2, tc=BROWN)
    arrow(ax, 0.62, 0.672, 0.58, 0.640, color=DGREEN)
    arrow(ax, 0.62, 0.555, 0.58, 0.595, color=BROWN)
    ax.text(0.80, 0.445, "same result", ha="center", va="center", fontsize=6.6,
            style="italic", color="#555555")

    # payoff
    ax.text(0.5, 0.135, "retrieval reward unnecessary", ha="center", va="center",
            fontsize=7.8, fontweight="bold", color=BROWN)
    ax.text(0.5, 0.055, "lever = fidelity distillation · $+1.22$ pp Hit@5", ha="center",
            va="center", fontsize=7.8, fontweight="bold", color=DGREEN)
    arrow(ax, cx + w / 2, 0.255, cx + w / 2, 0.180)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(OUT_DIR / f"fig_c4_training.{ext}", bbox_inches="tight", dpi=200)
    print(f"saved -> {OUT_DIR}/fig_c4_training.pdf")


if __name__ == "__main__":
    main()
