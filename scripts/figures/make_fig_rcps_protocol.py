"""Generate the compact, camera-ready RCPS protocol schematic.

The figure presents RCPS as a training-free evaluation protocol around standard
MRR.  It deliberately avoids dataset-specific performance claims and keeps the
retriever policy conditional: use the deployment retriever when it is fixed;
otherwise average a declared set.

Output: paper/figures/fig_rcps_protocol.{pdf,png}
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT_DIR = Path("paper/figures")

INK = "#263238"
BLUE = "#dceaf5"
AMBER = "#faead2"
GREEN = "#dcebdc"
GRAY = "#eeeeee"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 8.2,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)


def rounded_box(
    ax,
    x: float,
    y: float,
    width: float,
    height: float,
    text: str,
    facecolor: str,
    *,
    fontsize: float = 8.0,
    bold: bool = False,
) -> None:
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            width,
            height,
            boxstyle="round,pad=0.009,rounding_size=0.025",
            linewidth=0.9,
            edgecolor=INK,
            facecolor=facecolor,
            zorder=2,
        )
    )
    ax.text(
        x + width / 2,
        y + height / 2,
        text,
        ha="center",
        va="center",
        fontsize=fontsize,
        fontweight="bold" if bold else "normal",
        color=INK,
        linespacing=1.15,
        zorder=3,
    )


def arrow(ax, start: tuple[float, float], end: tuple[float, float]) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=10,
            linewidth=1.0,
            color=INK,
            zorder=1,
        )
    )


def main() -> None:
    # Sized close to one ACL/EMNLP column so text remains near its authored size.
    fig, ax = plt.subplots(figsize=(3.35, 2.96))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    rounded_box(
        ax,
        0.04,
        0.885,
        0.92,
        0.085,
        "Evaluation pages + candidate (P,C)",
        GRAY,
        fontsize=7.8,
        bold=True,
    )
    arrow(ax, (0.5, 0.885), (0.5, 0.825))

    rounded_box(
        ax,
        0.08,
        0.715,
        0.84,
        0.10,
        "Parse with P, chunk with C,\nand index",
        BLUE,
        fontsize=7.7,
    )
    arrow(ax, (0.5, 0.715), (0.5, 0.655))

    rounded_box(
        ax,
        0.08,
        0.545,
        0.84,
        0.10,
        "Retrieve fixed probe D\nwith declared R and K",
        BLUE,
        fontsize=7.7,
    )
    arrow(ax, (0.5, 0.545), (0.5, 0.485))

    rounded_box(
        ax,
        0.08,
        0.375,
        0.84,
        0.10,
        "Relevant = reference page\n+ normalised answer span",
        AMBER,
        fontsize=7.8,
    )
    arrow(ax, (0.5, 0.375), (0.5, 0.315))

    rounded_box(
        ax,
        0.08,
        0.205,
        0.84,
        0.10,
        "RCPS(P,C) = mean MRR@k\nover r in R and k in K = {1, 5, 10}",
        BLUE,
        fontsize=7.35,
    )
    arrow(ax, (0.5, 0.205), (0.5, 0.145))

    rounded_box(
        ax,
        0.05,
        0.045,
        0.90,
        0.09,
        "Rank candidates - no training",
        GREEN,
        fontsize=8.0,
        bold=True,
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_DIR / "fig_rcps_protocol.pdf", bbox_inches="tight", pad_inches=0.03)
    fig.savefig(
        OUT_DIR / "fig_rcps_protocol.png",
        bbox_inches="tight",
        pad_inches=0.03,
        dpi=240,
    )
    plt.close(fig)
    print(f"saved -> {OUT_DIR}/fig_rcps_protocol.pdf")


if __name__ == "__main__":
    main()
