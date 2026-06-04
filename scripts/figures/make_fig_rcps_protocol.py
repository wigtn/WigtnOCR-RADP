"""Figure (C3) — RCPS protocol flow.

RCPS is not a new scoring function; it is a *protocol* wrapping ordinary MRR in
three choices (§3.1): (i) extrinsic — score on a held-out Q-A probe over the
parsed corpus; (ii) retriever-agnostic — average MRR over several embedders;
(iii) format-invariant relevance — a chunk is relevant iff it contains the gold
answer span under markdown/whitespace-insensitive matching. Output: a parser/
chunker ranking that intrinsic metrics (TEDS, BC) get wrong.

A simple, information-bearing schematic (single column). No external data.
Output: paper/figures/fig_rcps_protocol.{pdf,png}
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT_DIR = Path("paper/figures")

plt.rcParams.update({"font.family": "serif", "font.size": 8.5})


def box(ax, x, y, w, h, text, fc, ec="#333333", fs=8.0, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.02",
                                linewidth=1.0, edgecolor=ec, facecolor=fc, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            fontweight="bold" if bold else "normal", zorder=3)


def arrow(ax, x1, y1, x2, y2):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=11, lw=1.1, color="#333333", zorder=1))


def main() -> None:
    fig, ax = plt.subplots(figsize=(3.3, 4.4))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Inputs
    box(ax, 0.04, 0.88, 0.42, 0.085, "Parser / chunker\ncandidates", "#eaeaea", fs=7.8)
    box(ax, 0.54, 0.88, 0.42, 0.085, "Held-out Q–A probe\n(~few hundred, no training)", "#eaeaea", fs=7.2)

    # Parse + chunk
    box(ax, 0.18, 0.72, 0.64, 0.075, "chunk the parsed corpus", "#dbe9f6", fs=8)
    arrow(ax, 0.25, 0.88, 0.35, 0.795)
    arrow(ax, 0.75, 0.88, 0.62, 0.795)

    # The three protocol choices (the contribution)
    box(ax, 0.06, 0.60, 0.88, 0.066,
        "(iii) format-invariant relevance:\nchunk relevant iff it contains the gold answer span", "#fde7c9", fs=7.0)
    box(ax, 0.06, 0.495, 0.88, 0.066,
        "(i) extrinsic: score retrieval on the probe, not the text", "#fde7c9", fs=7.4)
    box(ax, 0.06, 0.39, 0.88, 0.066,
        "(ii) retriever-agnostic: average MRR@{1,5,10}\nover R = {BGE-M3, mE5-large, Qwen3-Emb-8B}", "#fde7c9", fs=7.0)
    arrow(ax, 0.5, 0.72, 0.5, 0.668)
    arrow(ax, 0.5, 0.60, 0.5, 0.562)
    arrow(ax, 0.5, 0.495, 0.5, 0.457)

    # bracket label for the 3 choices
    ax.text(0.5, 0.665, "the protocol (not a new metric)", ha="center", va="bottom",
            fontsize=6.6, style="italic", color="#a0610a")

    # RCPS score
    box(ax, 0.22, 0.265, 0.56, 0.072, "RCPS(P)  =  retriever-averaged MRR", "#cfe9cf", fs=8.2, bold=True)
    arrow(ax, 0.5, 0.39, 0.5, 0.337)

    # Output: ranking / selection
    box(ax, 0.13, 0.13, 0.74, 0.075, "rank & select parser / chunker\n(picks what TEDS / BC rank wrong)", "#cfe9cf", fs=7.6, bold=True)
    arrow(ax, 0.5, 0.265, 0.5, 0.205)

    # payoff
    ax.text(0.5, 0.055, "0.20 → 0.55 Hit@1 on our data", ha="center", va="center",
            fontsize=8, color="#1a6b1a", fontweight="bold")
    arrow(ax, 0.5, 0.13, 0.5, 0.085)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(OUT_DIR / f"fig_rcps_protocol.{ext}", bbox_inches="tight", dpi=200)
    print(f"saved -> {OUT_DIR}/fig_rcps_protocol.pdf")


if __name__ == "__main__":
    main()
