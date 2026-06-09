"""Figure (C2) — the retriever-free coverage diagnostic as a decision tree.

Each gold answer span is classified covered / split (chunker fault) / absent
(parser fault). yes-path goes straight down (green); no-path branches right to a
fault (red = parser, amber = chunker). Labels sit in the empty gaps, never over
a box or arrow.
Output: paper/figures/fig_c2_coverage.{pdf,png}
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT_DIR = Path("paper/figures")
plt.rcParams.update({"font.family": "serif"})

GREY = "#ececec"
BLUE = "#dbe9f6"
RED = "#f3d2d2"
TAN = "#fce3c4"
GREEN = "#cfe9cf"
DRED = "#8f1b1b"
DAMBER = "#8a5200"
DGREEN = "#1a6b1a"
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


def tag(ax, x, y, t, color):
    ax.text(x, y, t, ha="center", va="center", fontsize=7.0, color=color,
            fontstyle="italic", zorder=4)


def main():
    fig, ax = plt.subplots(figsize=(3.25, 2.55))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    sx = 0.30          # spine centre x
    rx = 0.80          # right-branch centre x
    bw, bh = 0.46, 0.135
    rw, rh = 0.38, 0.165

    y_span, y_q1, y_q2, y_cov = 0.90, 0.65, 0.37, 0.11
    box(ax, sx, y_span, bw, bh, "gold answer span", GREY, 8.2)
    box(ax, sx, y_q1, bw, bh, "in parser\noutput?", BLUE, 8.0, bold=True)
    box(ax, sx, y_q2, bw, bh, "in one\nchunk?", BLUE, 8.0, bold=True)
    box(ax, sx, y_cov, bw, 0.15, "COVERED", GREEN, 8.6, bold=True, tc=DGREEN)
    box(ax, rx, y_q1, rw, rh, "ABSENT  20.2%\nparser fault", RED, 7.8, bold=True, tc=DRED)
    box(ax, rx, y_q2, rw, rh, "SPLIT  ≤2.3%\nchunker fault", TAN, 7.8, bold=True, tc=DAMBER)

    # yes-path (down the spine) — arrows in the gaps between boxes
    arrow(ax, sx, y_span - bh / 2, sx, y_q1 + bh / 2)
    arrow(ax, sx, y_q1 - bh / 2, sx, y_q2 + bh / 2, color=DGREEN)
    arrow(ax, sx, y_q2 - bh / 2, sx, y_cov + 0.075, color=DGREEN)
    tag(ax, sx + 0.055, (y_q1 - bh / 2 + y_q2 + bh / 2) / 2, "yes", DGREEN)
    tag(ax, sx + 0.055, (y_q2 - bh / 2 + y_cov + 0.075) / 2, "yes", DGREEN)

    # no-path (branch right) — arrows in the gap between spine and right boxes
    arrow(ax, sx + bw / 2, y_q1, rx - rw / 2, y_q1, color=DRED)
    arrow(ax, sx + bw / 2, y_q2, rx - rw / 2, y_q2, color=DAMBER)
    tag(ax, (sx + bw / 2 + rx - rw / 2) / 2, y_q1 + 0.052, "no", DRED)
    tag(ax, (sx + bw / 2 + rx - rw / 2) / 2, y_q2 + 0.052, "no", DAMBER)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(OUT_DIR / f"fig_c2_coverage.{ext}", bbox_inches="tight", dpi=200)
    print(f"saved -> {OUT_DIR}/fig_c2_coverage.pdf")


if __name__ == "__main__":
    main()
