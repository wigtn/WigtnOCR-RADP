"""Figure (C4) — parser-side training: the retrieval reward is unnecessary.

Convergence layout (distinct from C2's decision tree): best-of-K candidates are
ranked two ways --- by edit-distance to ground truth (RADP-Distill) or by
page-local RCPS (RADP-DPO) --- and the "≈" shows they give the same gain, so both
feed the same LoRA-toggle DPO and reach +1.22 pp; the retrieval reward adds nothing.
Output: paper/figures/fig_c4_training.{pdf,png}
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT_DIR = Path("paper/figures")
plt.rcParams.update({"font.family": "serif"})

GREY = "#ececec"
GREEN = "#cfe9cf"
TAN = "#fce3c4"
DGREEN = "#1a6b1a"
DAMBER = "#8a5200"
EC = "#444444"


def box(ax, cx, cy, w, h, text, fc, fs=8.0, bold=False, tc="#111111"):
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                                boxstyle="round,pad=0.006,rounding_size=0.02",
                                linewidth=1.0, edgecolor=EC, facecolor=fc, zorder=2))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs,
            fontweight="bold" if bold else "normal", color=tc, zorder=3)


def arrow(ax, x1, y1, x2, y2, color=EC):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=10, lw=1.2, color=color, zorder=1))


def main():
    fig, ax = plt.subplots(figsize=(3.3, 2.95))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    # source
    box(ax, 0.5, 0.905, 0.76, 0.115, "best-of-$K$ parses from Prod", GREY, 8.2)

    # two ranking routes (the comparison), with "≈" between them
    lx, ry, rw, rh = 0.255, 0.66, 0.40, 0.155
    box(ax, lx, ry, rw, rh, "RADP-Distill\nedit-dist → GT", GREEN, 7.8, bold=True, tc=DGREEN)
    box(ax, 0.745, ry, rw, rh, "RADP-DPO\npage-RCPS", TAN, 7.8, bold=True, tc=DAMBER)
    ax.text(0.5, ry, "≈", ha="center", va="center", fontsize=17, color="#333333", zorder=3)

    # converge into shared training
    box(ax, 0.5, 0.405, 0.50, 0.115, "LoRA-toggle DPO", GREY, 8.2)
    box(ax, 0.5, 0.195, 0.66, 0.125, "improved parser\n$+1.22$ pp Hit@5", GREEN, 8.2,
        bold=True, tc=DGREEN)

    arrow(ax, 0.42, 0.848, lx + 0.06, ry + rh / 2)        # source -> Distill
    arrow(ax, 0.58, 0.848, 0.745 - 0.06, ry + rh / 2)     # source -> DPO
    arrow(ax, lx + 0.06, ry - rh / 2, 0.45, 0.405 + 0.06)  # Distill -> DPO-train
    arrow(ax, 0.745 - 0.06, ry - rh / 2, 0.55, 0.405 + 0.06)  # DPO -> DPO-train
    arrow(ax, 0.5, 0.405 - 0.115 / 2, 0.5, 0.195 + 0.125 / 2)

    ax.text(0.5, 0.045, "retrieval reward unnecessary — lever is fidelity distillation",
            ha="center", va="center", fontsize=7.4, fontweight="bold", color=DAMBER)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(OUT_DIR / f"fig_c4_training.{ext}", bbox_inches="tight", dpi=200)
    print(f"saved -> {OUT_DIR}/fig_c4_training.pdf")


if __name__ == "__main__":
    main()
