"""Figure (C3) — RCPS protocol flow.

RCPS is not a new scoring function; it is a *protocol* wrapping ordinary MRR in
three choices (§3.1): (i) extrinsic — score on a held-out Q-A probe over the
parsed corpus; (ii) retriever-agnostic — average MRR over several embedders;
(iii) format-invariant relevance — a chunk is relevant iff it contains the gold
answer span. Output: a parser/chunker ranking that intrinsic metrics get wrong.

A simple, information-bearing schematic (single column). No external data.
Output: paper/figures/fig_rcps_protocol.{pdf,png}
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT_DIR = Path("paper/figures")

plt.rcParams.update({"font.family": "serif"})


def box(ax, x, y, w, h, text, fc, fs, ec="#333333", bold=False):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.008,rounding_size=0.018",
        linewidth=1.0, edgecolor=ec, facecolor=fc, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            fontweight="bold" if bold else "normal", zorder=3)


def arrow(ax, x1, y1, x2, y2):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=10, lw=1.1, color="#333333", zorder=1))


def main() -> None:
    fig, ax = plt.subplots(figsize=(4.7, 5.3))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Inputs
    box(ax, 0.03, 0.885, 0.44, 0.085, "Parser / chunker\ncandidates", "#eaeaea", 8.0)
    box(ax, 0.53, 0.885, 0.44, 0.085, "Held-out Q–A probe\n(few hundred, no training)", "#eaeaea", 7.6)

    # Parse + chunk
    box(ax, 0.22, 0.755, 0.56, 0.072, "chunk the parsed corpus", "#dbe9f6", 8.5)
    arrow(ax, 0.24, 0.885, 0.36, 0.83)
    arrow(ax, 0.76, 0.885, 0.64, 0.83)

    # The three protocol choices (the contribution) — grouped by shared colour + (i)(ii)(iii)
    box(ax, 0.02, 0.625, 0.96, 0.068,
        "(iii) format-invariant relevance:\nchunk relevant iff it contains the gold answer span",
        "#fde7c9", 7.6)
    box(ax, 0.02, 0.527, 0.96, 0.062,
        "(i) extrinsic: score retrieval on the probe, not the text",
        "#fde7c9", 7.6)
    box(ax, 0.02, 0.429, 0.96, 0.068,
        "(ii) retriever-agnostic: average MRR@{1,5,10}\nover R = {BGE-M3, mE5, Qwen3-Emb}",
        "#fde7c9", 7.6)
    arrow(ax, 0.5, 0.755, 0.5, 0.695)
    arrow(ax, 0.5, 0.625, 0.5, 0.591)
    arrow(ax, 0.5, 0.527, 0.5, 0.499)

    # RCPS score
    box(ax, 0.08, 0.300, 0.84, 0.070, "RCPS(P) = retriever-averaged MRR",
        "#cfe9cf", 8.6, bold=True)
    arrow(ax, 0.5, 0.429, 0.5, 0.372)

    # Output: ranking / selection
    box(ax, 0.10, 0.160, 0.80, 0.072,
        "rank & select parser / chunker\n(picks what TEDS / BC rank wrong)",
        "#cfe9cf", 7.8, bold=True)
    arrow(ax, 0.5, 0.300, 0.5, 0.234)

    # payoff
    ax.text(0.5, 0.065, "0.20 → 0.55 Hit@1 on our data", ha="center", va="center",
            fontsize=8.5, color="#1a6b1a", fontweight="bold")
    arrow(ax, 0.5, 0.160, 0.5, 0.092)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(OUT_DIR / f"fig_rcps_protocol.{ext}", bbox_inches="tight", dpi=200)
    print(f"saved -> {OUT_DIR}/fig_rcps_protocol.pdf")


if __name__ == "__main__":
    main()
