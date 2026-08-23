"""Generate the camera-ready parsing-retrieval disconnect figure.

Panel (a) uses the submitted MinerU-off output for the Boundary Clarity (BC)
diagnostic.  The complete 294-page parsers are the primary correlation; Marker
is shown separately because it covers only 38 pages.  Panel (b) is a distinct
deployment audit using the table-enabled MinerU-on output.

Sources:
  - output/baselines/moc_bc_correlation.json
  - output/baselines/grid_v1_parser_native.json
  - output/results/grid_MinerU-tableON_parser_native.json
Output: paper/figures/fig_disconnect.{pdf,png}
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

OUT_DIR = Path("paper/figures")
BC_SRC = Path("output/baselines/moc_bc_correlation.json")
GRID_SRC = Path("output/baselines/grid_v1_parser_native.json")
MINERU_ON_SRC = Path("output/results/grid_MinerU-tableON_parser_native.json")

INK = "#263238"
BLUE = "#245a7a"
PALE_BLUE = "#d9e8f0"
GRAY = "#b8b8b8"
MINERU_ORANGE = "#e6a04b"
DARK_ORANGE = "#974900"

_BC = json.loads(BC_SRC.read_text())["parsers"]
_GRID = {
    parser["name"]: parser
    for parser in json.loads(GRID_SRC.read_text())["parsers"]
}
_MINERU_ON = json.loads(MINERU_ON_SRC.read_text())

_SHORT = {
    "Qwen3-VL-30B (teacher)": "Qwen3-VL-30B\n(teacher)",
    "WigtnOCR-2B (ours, v1)": "Prod",
    "Qwen3-VL-2B (base)": "Qwen3-VL-2B\n(base)",
    "MinerU": "MinerU-off",
    "PaddleOCR": "PaddleOCR",
    "Marker": "Marker (38p)",
}

# (display name, BC, RCPS).  PaddleOCR has undefined BC and is omitted below.
PARSERS = []
for parser in _BC:
    grid_row = _GRID.get(parser["parser"], {})
    PARSERS.append(
        (
            _SHORT.get(parser["parser"], parser["parser"]),
            parser["mean_bc"],
            grid_row.get("rcps"),
        )
    )

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 8.5,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)


def main() -> None:
    fig, (ax_s, ax_b) = plt.subplots(
        1,
        2,
        figsize=(6.45, 2.78),
        gridspec_kw={"width_ratios": [1.55, 1.0], "wspace": 0.33},
    )

    # ---- (a) MinerU-off diagnostic: complete outputs first, Marker as sensitivity ----
    valid = [
        (bc, rcps, name)
        for name, bc, rcps in PARSERS
        if bc is not None and not math.isnan(bc)
    ]
    complete = [row for row in valid if row[2] != "Marker (38p)"]
    marker = next(row for row in valid if row[2] == "Marker (38p)")

    r_complete = float(
        np.corrcoef(
            [row[0] for row in complete], [row[1] for row in complete]
        )[0, 1]
    )
    r_with_marker = float(
        np.corrcoef([row[0] for row in valid], [row[1] for row in valid])[0, 1]
    )

    ax_s.scatter(
        [row[0] for row in complete],
        [row[1] for row in complete],
        s=48,
        marker="o",
        color=BLUE,
        edgecolor="white",
        linewidth=0.7,
        zorder=3,
    )
    ax_s.scatter(
        [marker[0]],
        [marker[1]],
        s=60,
        marker="D",
        facecolor="white",
        edgecolor=INK,
        linewidth=1.1,
        zorder=3,
    )

    label_offsets = {
        "MinerU-off": (8, 0),
        "Marker (38p)": (8, -1),
        "Prod": (0, 10),
        "Qwen3-VL-30B\n(teacher)": (9, 4),
        "Qwen3-VL-2B\n(base)": (0, 12),
    }
    for bc, rcps, name in valid:
        dx, dy = label_offsets[name]
        horizontal = "right" if dx < -3 else ("left" if dx > 3 else "center")
        ax_s.annotate(
            name,
            (bc, rcps),
            textcoords="offset points",
            xytext=(dx, dy),
            fontsize=7.0,
            ha=horizontal,
            va="center",
            color=INK,
            linespacing=1.0,
        )

    ax_s.text(
        0.03,
        0.05,
        f"294-page parsers: r = {r_complete:.2f} (n = 4)\n"
        f"+ Marker (38p): r = {r_with_marker:.2f} (n = 5)",
        transform=ax_s.transAxes,
        fontsize=7.2,
        ha="left",
        va="bottom",
        color=INK,
        bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="#aaaaaa"),
        zorder=4,
    )
    ax_s.set_xlabel("Boundary Clarity (intrinsic)", fontsize=8.0)
    ax_s.set_ylabel("RCPS (retrieval)", fontsize=8.0)
    ax_s.set_title("(a) MinerU-off diagnostic: BC can misrank", fontsize=8.6, pad=6)
    ax_s.set_ylim(0, 0.68)
    ax_s.set_xlim(0.48, 0.76)
    ax_s.grid(color="#dddddd", linewidth=0.55, zorder=0)
    ax_s.tick_params(labelsize=7.4)
    # ---- (b) Separate deployment audit: MinerU-on versus Prod ----
    mineru_on_hit1 = float(_MINERU_ON["hit@1"])
    prod_hit1 = float(_GRID["WigtnOCR-2B (ours, v1)"]["hit@1"])
    values = [mineru_on_hit1, prod_hit1]
    labels = ["MinerU-on", "Prod"]
    bars = ax_b.bar(
        labels,
        values,
        color=[MINERU_ORANGE, PALE_BLUE],
        edgecolor=[DARK_ORANGE, BLUE],
        linewidth=1.0,
        width=0.62,
        zorder=3,
    )
    for bar, value in zip(bars, values):
        ax_b.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.018,
            f"{value:.3f}",
            ha="center",
            va="bottom",
            fontsize=8.5,
            fontweight="bold",
            color=INK,
        )

    delta_points = (prod_hit1 - mineru_on_hit1) * 100
    ratio = prod_hit1 / mineru_on_hit1
    ax_b.set_ylabel("Retrieval Hit@1", fontsize=8.0)
    ax_b.set_ylim(0, 0.68)
    ax_b.set_title("(b) MinerU-on deployment audit", fontsize=8.6, pad=6)
    ax_b.grid(axis="y", color="#dddddd", linewidth=0.55, zorder=0)
    ax_b.tick_params(labelsize=7.4)

    fig.subplots_adjust(left=0.085, right=0.985, top=0.86, bottom=0.20)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_DIR / "fig_disconnect.pdf", bbox_inches="tight", pad_inches=0.03)
    fig.savefig(
        OUT_DIR / "fig_disconnect.png",
        bbox_inches="tight",
        pad_inches=0.03,
        dpi=240,
    )
    plt.close(fig)

    print(f"complete n={len(complete)} Pearson r = {r_complete:.4f}")
    print(f"with Marker n={len(valid)} Pearson r = {r_with_marker:.4f}")
    print(
        f"MinerU-on audit: {mineru_on_hit1:.3f} -> {prod_hit1:.3f}; "
        f"+{delta_points:.1f} points; {ratio:.2f}x"
    )
    print(f"saved -> {OUT_DIR}/fig_disconnect.pdf")


if __name__ == "__main__":
    main()
