"""Generate the camera-ready exact-span coverage diagnostic.

With Prod output fixed, the diagnostic separates a pre-chunking normalised
exact-span no-match from a span split by chunk boundaries.  These are
operational labels; a no-match does not by itself establish semantic omission.

Source: output/diagnostics/coverage_diagnostic_v1.json
Output: paper/figures/fig_coverage.{pdf,png}
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

SRC = Path("output/diagnostics/coverage_diagnostic_v1.json")
OUT_DIR = Path("paper/figures")

INK = "#263238"
BLUE = "#245a7a"
PALE_BLUE = "#e3edf3"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 8.0,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)

DISPLAY_NAMES = {
    "md_h3": "md-h3",
    "md_h2": "md-h2",
    "md_h1": "md-h1",
    "parser_native": "parser-native",
    "fixed500": "fixed-500",
    "fixed500_ov200": "fixed-500 (ov200)",
    "fixed1000": "fixed-1000",
    "fixed1000_ov200": "fixed-1000 (ov200)",
}


def main() -> None:
    data = json.loads(SRC.read_text())
    chunkers = data["chunkers"]
    names = [DISPLAY_NAMES.get(c["chunker"], c["chunker"]) for c in chunkers]
    split = np.array([c["split_rate"] * 100 for c in chunkers])
    absent = np.array([c["parser_fault_rate"] * 100 for c in chunkers])

    absent_rate = float(absent.mean())
    absent_count = round(absent_rate / 100 * 663)

    # Sized close to one ACL/EMNLP column to preserve 8 pt labels after inclusion.
    # Keep the plot's physical size while removing the former top callout.
    fig = plt.figure(figsize=(3.35, 2.15))
    ax = fig.add_axes([0.31, 0.17, 0.65, 0.70])
    y = np.arange(len(names))
    # Extend each guide a little behind its marker so the visual direction
    # reaches the endpoint instead of appearing detached by the white outline.
    guide_end = np.where(split > 0, split + 0.035, 0.045)
    ax.hlines(
        y,
        0,
        guide_end,
        color=PALE_BLUE,
        linewidth=3.2,
        zorder=1,
    )
    ax.scatter(
        split,
        y,
        s=27,
        marker="o",
        color=BLUE,
        edgecolor="white",
        linewidth=0.35,
        zorder=3,
    )

    for yi, value in zip(y, split):
        if value > 0:
            ax.text(
                value + 0.08,
                yi,
                f"{value:.1f}",
                va="center",
                ha="left",
                fontsize=7.0,
                color=INK,
            )

    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=7.2)
    ax.invert_yaxis()
    # Leave a narrow margin before zero so exact-zero markers are not clipped
    # by the axes boundary in the two-column paper rendering.
    ax.set_xlim(-0.06, 2.65)
    ax.set_xticks(np.arange(0, 2.6, 0.5))
    ax.set_xlabel("Reference spans split across chunks (%)", fontsize=7.7)
    ax.set_title(
        rf"Chunk-boundary split: $0.0$-${split.max():.1f}\%$ across eight chunkers",
        fontsize=8.0,
        fontweight="bold",
        pad=4,
    )
    ax.grid(axis="x", color="#d6d6d6", linewidth=0.55, zorder=0)
    ax.tick_params(axis="x", labelsize=7.0, length=2.5)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color("#777777")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_DIR / "fig_coverage.pdf", bbox_inches="tight", pad_inches=0.03)
    fig.savefig(
        OUT_DIR / "fig_coverage.png",
        bbox_inches="tight",
        pad_inches=0.03,
        dpi=240,
    )
    plt.close(fig)

    print("chunkers:", names)
    print("split %:", [f"{value:.1f}" for value in split])
    print(f"pre-chunking no-match = {absent_count}/663 ({absent_rate:.2f}%)")
    print(f"saved -> {OUT_DIR}/fig_coverage.pdf")


if __name__ == "__main__":
    main()
