"""Figure (C2) — the retriever-free coverage diagnostic as a decision tree.

Classifies each gold answer span by where it lands after chunking: ABSENT
(parser fault), SPLIT (chunker fault), or COVERED. The 20.2% absent rate is
constant across eight chunkers -> the gap is a parser problem.

Matches the visual style of make_fig_rcps_protocol.py (serif, rounded boxes).
Output: paper/figures/fig_c2_coverage.{pdf,png}
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT_DIR = Path("paper/figures")
plt.rcParams.update({"font.family": "serif"})

GREY = "#eaeaea"
BLUE = "#dbe9f6"
RED = "#f3d4d4"
TAN = "#fde7c9"
GREEN = "#cfe9cf"
DRED = "#9a1c1c"
DAMBER = "#9a5a00"
DGREEN = "#1a6b1a"


def box(ax, x, y, w, h, text, fc, fs=8.0, bold=False, ec="#333333", tc="#111111"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.008,rounding_size=0.02",
                                linewidth=1.0, edgecolor=ec, facecolor=fc, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            fontweight="bold" if bold else "normal", color=tc, zorder=3)


def arrow(ax, x1, y1, x2, y2, color="#333333"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=9, lw=1.1, color=color, zorder=1))


def label(ax, x, y, text, color="#333333"):
    ax.text(x, y, text, ha="center", va="center", fontsize=7.0, style="italic",
            color=color, zorder=4,
            bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none"))


def main():
    fig, ax = plt.subplots(figsize=(3.3, 3.05))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    # left decision spine
    box(ax, 0.06, 0.86, 0.50, 0.11, "gold answer span", GREY, 8.2)
    box(ax, 0.06, 0.62, 0.50, 0.11, "in parser output?", BLUE, 8.2, bold=True)
    box(ax, 0.06, 0.38, 0.50, 0.11, "in one chunk?", BLUE, 8.2, bold=True)
    box(ax, 0.06, 0.13, 0.50, 0.12, "COVERED", GREEN, 8.6, bold=True, tc=DGREEN)

    # right branches (faults)
    box(ax, 0.62, 0.61, 0.36, 0.13, "ABSENT  20.2%\nparser fault", RED, 7.8, bold=True, tc=DRED)
    box(ax, 0.62, 0.37, 0.36, 0.13, "SPLIT  ≤2.3%\nchunker fault", TAN, 7.8, bold=True, tc=DAMBER)

    # spine arrows (yes path, down)
    arrow(ax, 0.31, 0.86, 0.31, 0.735)
    arrow(ax, 0.31, 0.62, 0.31, 0.495)
    arrow(ax, 0.31, 0.38, 0.31, 0.255)
    label(ax, 0.31, 0.557, "yes", DGREEN)
    label(ax, 0.31, 0.317, "yes", DGREEN)

    # right branches (no path)
    arrow(ax, 0.56, 0.675, 0.62, 0.675, color=DRED)
    arrow(ax, 0.56, 0.435, 0.62, 0.435, color=DAMBER)
    label(ax, 0.59, 0.715, "no", DRED)
    label(ax, 0.59, 0.475, "no", DAMBER)

    ax.text(0.5, 0.025, "absent rate constant across 8 chunkers", ha="center", va="center",
            fontsize=6.8, style="italic", color="#555555")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(OUT_DIR / f"fig_c2_coverage.{ext}", bbox_inches="tight", dpi=200)
    print(f"saved -> {OUT_DIR}/fig_c2_coverage.pdf")


if __name__ == "__main__":
    main()
