"""Figure 3 — Coverage diagnostic (C2): localising the gap to a pipeline layer.

Parser output fixed (WigtnOCR v1); chunker varied. For each chunker we classify
every gold answer as covered, split (cut by a chunk boundary — a *chunker* fault,
recoverable) or absent/parser-fault (missing from parser output — a *parser*
fault, unrecoverable by re-chunking). The parser-fault rate is ~constant across
chunkers while split stays near zero → the gap is a PARSER problem.

Actionable rule: if absent dominates, fix the parser; if split dominates, fix the chunker.

Source: output/diagnostics/coverage_diagnostic_v1.json
Output: paper/figures/fig_coverage.{pdf,png}
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt

SRC = Path("output/diagnostics/coverage_diagnostic_v1.json")
OUT_DIR = Path("paper/figures")

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def main() -> None:
    data = json.loads(SRC.read_text())
    chunkers = data["chunkers"]
    names = [c["chunker"] for c in chunkers]
    split = [c["split_rate"] * 100 for c in chunkers]
    absent = [c["parser_fault_rate"] * 100 for c in chunkers]
    covered = [c["coverage"] * 100 for c in chunkers]

    mean_absent = sum(absent) / len(absent)

    fig, ax = plt.subplots(figsize=(5.4, 3.0))
    x = range(len(names))

    b_cov = ax.bar(x, covered, color="#cfe8cf", label="covered", zorder=3)
    b_split = ax.bar(x, split, bottom=covered, color="#ff7f0e",
                     label="split (chunker fault)", zorder=3)
    bottom2 = [c + s for c, s in zip(covered, split)]
    b_abs = ax.bar(x, absent, bottom=bottom2, color="#d62728",
                   label="absent (parser fault)", zorder=3)

    # constant-absent reference line
    ax.axhline(100 - mean_absent, color="#d62728", ls="--", lw=0.9, zorder=4)
    ax.text(len(names) - 0.5, 100 - mean_absent + 0.6,
            f"absent ≈ {mean_absent:.1f}% (≈constant)", color="#d62728",
            fontsize=7.5, ha="right")

    ax.set_xticks(list(x))
    ax.set_xticklabels(names, rotation=30, ha="right", fontsize=7.5)
    ax.set_ylabel("% of gold answers")
    ax.set_ylim(70, 101)
    ax.set_title("Coverage by chunker (parser fixed = v1):\nabsent is flat → fix the parser, not the chunker",
                 fontsize=8.5)
    ax.legend(fontsize=7, loc="lower left", ncol=3, frameon=False,
              bbox_to_anchor=(0.0, -0.42))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(OUT_DIR / f"fig_coverage.{ext}", bbox_inches="tight", dpi=200)
    print("chunkers:", names)
    print("absent (parser-fault) %:", [f"{a:.1f}" for a in absent])
    print("split %:", [f"{s:.1f}" for s in split])
    print(f"mean absent = {mean_absent:.2f}%")
    print(f"saved -> {OUT_DIR}/fig_coverage.pdf")


if __name__ == "__main__":
    main()
