"""Figure (C4) — parser-side training: the retrieval reward is unnecessary (data).

Both ways of ranking the best-of-K candidates give a real, significant, and
statistically indistinguishable OHR-Bench Hit@5 gain over the untuned parser:
  RADP-Distill  edit-distance to reference   +1.22 pp  CI[0.35, 2.15]
  RADP-DPO      page-local RCPS       +0.85 pp  CI[0.35, 1.43]
The overlapping CIs are the evidence for "≈": the cheap fidelity signal matches
the retrieval reward, so the retrieval reward adds nothing.
Source: output/results/arm_b_ohr_ci.json (n_qa=2264, 3-retriever avg).
Output: paper/figures/fig_c4_training.{pdf,png}
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

OUT_DIR = Path("paper/figures")
plt.rcParams.update({"font.family": "serif"})

GREEN = "#4a9a4a"
TAN = "#d98a2b"
DGREEN = "#1a6b1a"
DAMBER = "#8a5200"

# (label, sublabel, delta_pp, ci_lo, ci_hi, color)
ROWS = [
    ("RADP-Distill", "edit-dist → ref", 1.22, 0.35, 2.15, GREEN),
    ("RADP-DPO", "page-RCPS", 0.85, 0.35, 1.43, TAN),
]


def main():
    fig, ax = plt.subplots(figsize=(3.3, 2.05))

    ys = [1.0, 0.0]
    for y, (_, _, d, lo, hi, c) in zip(ys, ROWS):
        ax.barh(y, d, height=0.46, color=c, edgecolor="#333333", linewidth=0.8, zorder=2)
        ax.errorbar(d, y, xerr=[[d - lo], [hi - d]], fmt="none", ecolor="#333333",
                    elinewidth=1.1, capsize=4, capthick=1.1, zorder=3)
        ax.text(d + 0.07, y + 0.20, f"+{d:.2f} pp", va="center", ha="left",
                fontsize=8.0, fontweight="bold", color="#222222")

    ax.axvline(0, color="#888888", lw=1.0, ls="--", zorder=1)

    # two-line y tick labels (name + ranking signal)
    ax.set_yticks(ys)
    ax.set_yticklabels(
        [f"{ROWS[0][0]}\n{ROWS[0][1]}", f"{ROWS[1][0]}\n{ROWS[1][1]}"],
        fontsize=8.0)
    for tick, c in zip(ax.get_yticklabels(), (DGREEN, DAMBER)):
        tick.set_color(c)
        tick.set_fontweight("bold")

    ax.set_xlim(0, 2.5)
    ax.set_ylim(-0.6, 1.4)
    ax.set_xlabel("$\\Delta$ Hit@5 (pp) vs untuned  —  OHR-Bench, $n{=}2264$",
                  fontsize=7.8)
    ax.set_xticks([0, 1, 2])
    ax.tick_params(axis="x", labelsize=7.5)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)

    # the takeaway: overlapping CIs => equal gain => reward unnecessary
    ax.annotate("CIs overlap → equal gain:\nretrieval reward unnecessary",
                xy=(1.43, 0.0), xytext=(1.62, 0.66),
                fontsize=7.2, color=DAMBER, fontweight="bold", va="center",
                ha="left")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(OUT_DIR / f"fig_c4_training.{ext}", bbox_inches="tight", dpi=200)
    print(f"saved -> {OUT_DIR}/fig_c4_training.pdf")


if __name__ == "__main__":
    main()
