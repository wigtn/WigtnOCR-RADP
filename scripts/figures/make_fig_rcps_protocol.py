"""Figure (C3) — the RCPS protocol, with the failure each choice fixes.

RCPS is not a new scoring function; it is a protocol that wraps ordinary MRR in
three choices (§3.1). This figure shows each choice together with the failure
mode it removes — the information that distinguishes RCPS from plain MRR:
  (i)  extrinsic            — intrinsic text scores (TEDS, BC) mispredict retrieval
  (ii) retriever-averaged   — a single embedder flips the top-1 parser (Table 3b)
  (iii) format-invariant    — credit content the parser kept, not its formatting

Single information-bearing schematic. No external data.
Output: paper/figures/fig_rcps_protocol.{pdf,png}
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT_DIR = Path("paper/figures")
plt.rcParams.update({"font.family": "serif"})

BROWN = "#9a5a00"


def box(ax, x, y, w, h, text, fc, fs, bold=False, ec="#333333"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.008,rounding_size=0.018",
                                linewidth=1.0, edgecolor=ec, facecolor=fc, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            fontweight="bold" if bold else "normal", zorder=3)


def choice(ax, x, y, w, h, main, fix, fc="#fde7c9"):
    """A protocol-choice box: the choice (top) + the failure it fixes (italic, below)."""
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.008,rounding_size=0.018",
                                linewidth=1.0, edgecolor="#333333", facecolor=fc, zorder=2))
    ax.text(x + w / 2, y + h * 0.68, main, ha="center", va="center", fontsize=7.3, zorder=3)
    ax.text(x + w / 2, y + h * 0.26, fix, ha="center", va="center", fontsize=6.4,
            style="italic", color=BROWN, zorder=3)


def arrow(ax, x1, y1, x2, y2):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=10, lw=1.1, color="#333333", zorder=1))


def main() -> None:
    fig, ax = plt.subplots(figsize=(5.0, 5.9))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Inputs
    box(ax, 0.03, 0.900, 0.44, 0.075, "Parser / chunker\ncandidates", "#eaeaea", 7.8)
    box(ax, 0.53, 0.900, 0.44, 0.075, "Held-out Q–A probe\n(few hundred, no training)", "#eaeaea", 7.2)

    # Chunk
    box(ax, 0.22, 0.792, 0.56, 0.060, "chunk the parsed corpus", "#dbe9f6", 8.2)
    arrow(ax, 0.25, 0.900, 0.37, 0.856)
    arrow(ax, 0.75, 0.900, 0.63, 0.856)
    arrow(ax, 0.5, 0.792, 0.5, 0.766)

    # The three protocol choices, each with the failure it fixes (a *set*, not a sequence)
    choice(ax, 0.02, 0.672, 0.96, 0.082,
           "(i) extrinsic — score retrieval on the probe, not the text",
           "fixes: intrinsic text scores (TEDS, BC) mispredict retrieval")
    choice(ax, 0.02, 0.566, 0.96, 0.082,
           "(ii) retriever-averaged MRR over {BGE-M3, mE5, Qwen3-Emb}",
           "fixes: a single embedder flips the top-1 parser (Table 3b)")
    choice(ax, 0.02, 0.460, 0.96, 0.082,
           "(iii) format-invariant relevance — chunk holds the answer span",
           "fixes: credits content the parser kept, not its formatting")

    # RCPS score
    box(ax, 0.08, 0.338, 0.84, 0.064, "RCPS(P) = retriever-averaged MRR", "#cfe9cf", 8.6, bold=True)
    arrow(ax, 0.5, 0.460, 0.5, 0.404)

    # Select
    box(ax, 0.10, 0.205, 0.80, 0.072,
        "rank & select parser / chunker\n(picks what TEDS / BC rank wrong)", "#cfe9cf", 7.8, bold=True)
    arrow(ax, 0.5, 0.338, 0.5, 0.279)

    # Payoff
    ax.text(0.5, 0.082, "Hit@1   0.20 → 0.55   on our data", ha="center", va="center",
            fontsize=8.6, color="#1a6b1a", fontweight="bold")
    arrow(ax, 0.5, 0.205, 0.5, 0.108)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(OUT_DIR / f"fig_rcps_protocol.{ext}", bbox_inches="tight", dpi=200)
    print(f"saved -> {OUT_DIR}/fig_rcps_protocol.pdf")


if __name__ == "__main__":
    main()
