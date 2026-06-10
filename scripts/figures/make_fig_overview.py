"""Figure 1 (overview) --- the document-RAG pipeline and where C1--C4 act.

A first-time reader should see in one glance: the parser is the under-examined
lever. Horizontal pipeline (Document -> Parse -> Chunk -> Embed+Retrieve ->
Answer) with the real candidate-parser and retriever logos, and four numbered
badges placing each contribution at the stage it acts on. No result numbers
(those live in the C1--C4 figures); badges never sit over a logo.
Output: paper/figures/fig_overview.{pdf,png}
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT_DIR = Path("paper/figures")
LOGO = Path("scripts/figures/icons/logos")
plt.rcParams.update({"font.family": "serif"})

GREY = "#ececec"
HILITE = "#dce9f7"      # parser stage (the star)
GREENH = "#d9efd9"      # answer stage
C1C, C2C, C3C, C4C = "#1f5fa8", "#8f1b1b", "#155b15", "#8a5200"


def tab(ax, cx, w, text, fc, y=0.905, h=0.085, fs=8.4):
    ax.add_patch(FancyBboxPatch((cx - w / 2, y - h / 2), w, h,
                 boxstyle="round,pad=0.004,rounding_size=0.015",
                 lw=1.0, edgecolor="#555555", facecolor=fc, zorder=3))
    ax.text(cx, y, text, ha="center", va="center", fontsize=fs,
            fontweight="bold", color="#222222", zorder=4)


def zone(ax, cx, w, y, h, fc="#ffffff"):
    ax.add_patch(FancyBboxPatch((cx - w / 2, y - h / 2), w, h,
                 boxstyle="round,pad=0.004,rounding_size=0.02",
                 lw=1.0, edgecolor="#999999", facecolor=fc, zorder=1))


def logo(ax, path, x, y, zoom):
    img = np.asarray(Image.open(LOGO / path).convert("RGBA"))
    ax.add_artist(AnnotationBbox(OffsetImage(img, zoom=zoom), (x, y),
                                 frameon=False, zorder=5))


def arrow(ax, x1, x2, y):
    ax.add_patch(FancyArrowPatch((x1, y), (x2, y), arrowstyle="-|>",
                 mutation_scale=12, lw=1.5, color="#444444", zorder=2))


def badge(ax, x, y, tag, text, color):
    """Left-anchored [tag][label]; x is the badge's left edge."""
    ax.add_patch(FancyBboxPatch((x, y - 0.026), 0.034, 0.052,
                 boxstyle="round,pad=0.002,rounding_size=0.008",
                 lw=0, facecolor=color, zorder=6))
    ax.text(x + 0.017, y, tag, ha="center", va="center", fontsize=7.4,
            fontweight="bold", color="white", zorder=7)
    ax.text(x + 0.045, y, text, ha="left", va="center", fontsize=7.6,
            color=color, fontweight="bold", zorder=7)


def main():
    fig, ax = plt.subplots(figsize=(7.3, 2.95))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    xd, xp, xc, xr, xa = 0.072, 0.295, 0.505, 0.715, 0.905
    wd, wp, wc, wr, wa = 0.12, 0.185, 0.15, 0.205, 0.105
    ymid = 0.60

    # stage header tabs
    tab(ax, xd, wd, "Document", GREY)
    tab(ax, xp, wp, "Parse", HILITE)
    tab(ax, xc, wc, "Chunk", GREY)
    tab(ax, xr, wr, "Embed + Retrieve", GREY)
    tab(ax, xa, wa, "Answer", GREENH)

    # content zones
    zh = 0.32
    zone(ax, xd, wd, ymid, zh)
    zone(ax, xp, wp, ymid, zh, "#fbfdff")
    zone(ax, xc, wc, ymid, zh)
    zone(ax, xr, wr, ymid, zh, "#fbfdff")
    zone(ax, xa, wa, ymid, zh, "#f6fbf6")

    # Document: page glyph
    ax.text(xd, ymid + 0.11, "scanned\nPDF page", ha="center", va="center",
            fontsize=7.4, color="#333333")
    ax.add_patch(FancyBboxPatch((xd - 0.026, ymid - 0.12), 0.052, 0.10,
                 boxstyle="round,pad=0.002", lw=1.0, edgecolor="#999999",
                 facecolor="#fafafa", zorder=4))
    for dy in (0.0, -0.028, -0.056):
        ax.plot([xd - 0.016, xd + 0.016], [ymid - 0.035 + dy] * 2,
                color="#bbbbbb", lw=0.8, zorder=5)

    # Parse: 2x2 candidate-parser logos, label above
    ax.text(xp, ymid + 0.14, "candidate parsers", ha="center", va="center",
            fontsize=7.2, fontstyle="italic", color="#444444")
    for path, gx, gy in [("qwen.png", xp - 0.045, ymid + 0.055),
                         ("mineru.png", xp + 0.045, ymid + 0.055),
                         ("marker_datalab.png", xp - 0.045, ymid - 0.06),
                         ("paddle.png", xp + 0.045, ymid - 0.06)]:
        logo(ax, path, gx, gy, 0.046)

    # Chunk: stacked chunk glyphs
    ax.text(xc, ymid + 0.10, "split into\nchunks", ha="center", va="center",
            fontsize=7.4, color="#333333")
    for dy in (-0.035, -0.072, -0.109):
        ax.add_patch(FancyBboxPatch((xc - 0.046, ymid + dy), 0.092, 0.026,
                     boxstyle="round,pad=0.001", lw=0.8, edgecolor="#aaaaaa",
                     facecolor="#f2f2f2", zorder=4))

    # Retrieve: row of 3 retriever logos, label above
    ax.text(xr, ymid + 0.115, "3 retrievers (averaged)", ha="center",
            va="center", fontsize=7.2, fontstyle="italic", color="#444444")
    for path, gx in [("bge_baai.png", xr - 0.07), ("me5_ms.png", xr),
                     ("qwen.png", xr + 0.07)]:
        logo(ax, path, gx, ymid - 0.03, 0.052)

    # Answer
    ax.text(xa, ymid, "retrieved\nanswer", ha="center", va="center",
            fontsize=7.8, color="#1a5b1a", fontweight="bold")

    # flow arrows
    arrow(ax, xd + wd / 2, xp - wp / 2 - 0.004, ymid)
    arrow(ax, xp + wp / 2, xc - wc / 2 - 0.004, ymid)
    arrow(ax, xc + wc / 2, xr - wr / 2 - 0.004, ymid)
    arrow(ax, xr + wr / 2, xa - wa / 2 - 0.004, ymid)

    # contribution badges: short, conceptual; grouped under their stage
    badge(ax, xp - 0.088, 0.275, "C1", "select by retrieval", C1C)
    badge(ax, xp - 0.088, 0.160, "C4", "bounded training", C4C)
    badge(ax, xc - 0.072, 0.215, "C2", "locate the fault", C2C)
    badge(ax, xr - 0.066, 0.215, "C3", "RCPS protocol", C3C)

    # one-line thesis, no result numbers
    ax.text(0.5, 0.045, "The parser is the under-examined lever in document-RAG.",
            ha="center", va="center", fontsize=8.8, color="#222222",
            fontweight="bold")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(OUT_DIR / f"fig_overview.{ext}", bbox_inches="tight", dpi=200)
    print(f"saved -> {OUT_DIR}/fig_overview.pdf")


if __name__ == "__main__":
    main()
