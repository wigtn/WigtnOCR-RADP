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
        "font.size": 7.2,
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
    fontsize: float = 7.0,
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
            shrinkA=0.0,
            shrinkB=0.0,
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
        0.06,
        0.875,
        0.88,
        0.095,
        r"Evaluation pages + candidate $(P,C)$",
        GRAY,
        fontsize=6.6,
        bold=True,
    )
    arrow(ax, (0.5, 0.875), (0.5, 0.815))

    rounded_box(
        ax,
        0.06,
        0.715,
        0.88,
        0.10,
        r"Parse with $P$, chunk with $C$," "\n" r"and index $C(P)$",
        BLUE,
        fontsize=6.7,
    )
    arrow(ax, (0.5, 0.715), (0.5, 0.645))

    rounded_box(
        ax,
        0.06,
        0.545,
        0.88,
        0.10,
        r"Retrieve fixed probe $D$" "\n" r"with declared $R$ and $K$",
        BLUE,
        fontsize=6.7,
    )
    arrow(ax, (0.5, 0.545), (0.5, 0.475))

    rounded_box(
        ax,
        0.06,
        0.375,
        0.88,
        0.10,
        "Relevant = reference page\n+ normalised answer span",
        AMBER,
        fontsize=6.8,
    )
    arrow(ax, (0.5, 0.375), (0.5, 0.305))

    rounded_box(
        ax,
        0.06,
        0.205,
        0.88,
        0.10,
        r"$\mathrm{RCPS}(P,C)=\mathrm{mean}_{r\in R,\,k\in K}\,\mathrm{MRR}@k$"
        "\n"
        r"$\left(r,C(P),D\right),\quad K=\{1,5,10\}$",
        BLUE,
        fontsize=5.65,
    )
    arrow(ax, (0.5, 0.205), (0.5, 0.135))

    rounded_box(
        ax,
        0.06,
        0.035,
        0.88,
        0.09,
        "Rank candidates - no training",
        GREEN,
        fontsize=7.0,
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
