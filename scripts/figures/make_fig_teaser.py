"""Figure 1 (teaser) --- the parsing--retrieval disconnect on one real page.

ColPali-style concrete teaser. Same Korean government page, parsed two ways:
MinerU keeps clean markdown structure (headers, numbered items -> highest
Boundary Clarity 0.72) but garbles the Korean text into CJK noise, so the gold
answer is unrecoverable; our Prod parser looks messier on intrinsic metrics yet
preserves the answer span. The cleaner-looking parse retrieves worse.

Real example: KoGov page kogov_003_page_0533, gold answer "모래수량".
Output: paper/figures/fig_teaser.{pdf,png}
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from matplotlib.font_manager import FontProperties
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT_DIR = Path("paper/figures")
PAGE = Path("data/KoGovDoc-Bench/images/documents/kogov_003/page_0533.png")

_REG = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
_BLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
KO = FontProperties(fname=_REG, size=7.0)
KOQ = FontProperties(fname=_REG, size=7.8)
KOQB = FontProperties(fname=_BLD, size=7.6)
plt.rcParams.update({"font.family": "serif"})

RED, GREEN, GREY = "#8f1b1b", "#1a6b1a", "#555555"
REDF, GREENF = "#fbeaea", "#eaf6ea"

MINERU = ("5) 俳三三动2(φ400m/m)(m)\n"
          "(1) 召Sand Mat音叶.( )\n"
          "(2) 即个张号 Sand Mat音斗个张叶.")
PROD = ("## 5. 샌드 드레인(Φ400m/m)(m)\n"
        " 1. 심도는 Sand Mat층을 포함한다.\n"
        " 2. 모래수량은 Sand Mat층을 제외한 수량이다.")


def card(ax, cx, w, ytop, h, header, hc, hfc, body, note):
    ax.add_patch(FancyBboxPatch((cx - w / 2, ytop - h), w, h,
                 boxstyle="round,pad=0.004,rounding_size=0.012",
                 lw=1.1, edgecolor=hc, facecolor="white", zorder=2))
    ax.add_patch(FancyBboxPatch((cx - w / 2, ytop - 0.062), w, 0.062,
                 boxstyle="round,pad=0.004,rounding_size=0.012",
                 lw=0, facecolor=hfc, zorder=3))
    ax.text(cx, ytop - 0.032, header, ha="center", va="center",
            fontsize=7.4, fontweight="bold", color=hc, zorder=4)
    ax.text(cx - w / 2 + 0.014, ytop - 0.085, body, ha="left", va="top",
            fontproperties=KO, color="#1a1a1a", zorder=4, linespacing=1.55)
    ax.text(cx, ytop - h + 0.03, note, ha="center", va="center",
            fontsize=6.9, fontstyle="italic", color=hc, fontweight="bold",
            zorder=4)


def main():
    fig, ax = plt.subplots(figsize=(7.4, 4.15))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    # --- query band ---
    ax.add_patch(FancyBboxPatch((0.02, 0.915), 0.96, 0.072,
                 boxstyle="round,pad=0.004,rounding_size=0.008",
                 lw=1.0, edgecolor="#bbbbbb", facecolor="#f3f3f3", zorder=1))
    ax.text(0.038, 0.951, "Q", ha="center", va="center", fontsize=7.5,
            fontweight="bold", color="white", zorder=3,
            bbox=dict(boxstyle="circle,pad=0.22", fc="#444444", ec="none"))
    ax.text(0.075, 0.951, "공통으로 Sand Mat층을 제외한다고 한 것은 "
            "무엇의 수량인가?", ha="left", va="center", fontproperties=KOQ,
            color="#222222", zorder=3)
    ax.text(0.962, 0.951, "gold:  모래수량", ha="right", va="center",
            fontproperties=KOQB, color=GREEN, zorder=3)

    # --- page image (left) ---
    img = np.asarray(Image.open(PAGE).convert("RGB"))
    ax.add_artist(AnnotationBbox(OffsetImage(img, zoom=0.083), (0.15, 0.585),
                  frameon=True, pad=0.15,
                  bboxprops=dict(edgecolor="#888888", lw=1.0), zorder=2))
    ax.text(0.15, 0.30, "one real\nKorean gov. page", ha="center",
            va="center", fontsize=7.6, color="#333333")

    # --- split arrows page -> two parses ---
    ax.add_patch(FancyArrowPatch((0.255, 0.64), (0.36, 0.80), arrowstyle="-|>",
                 mutation_scale=12, lw=1.4, color="#888888", zorder=1))
    ax.add_patch(FancyArrowPatch((0.255, 0.55), (0.685, 0.80), arrowstyle="-|>",
                 mutation_scale=12, lw=1.4, color="#888888", zorder=1))

    # --- two parse cards ---
    ct, ch, cw = 0.875, 0.40, 0.31
    card(ax, 0.515, cw, ct, ch, "MinerU — BC $0.72$ (highest)", RED, REDF,
         MINERU, "clean structure, garbled text")
    card(ax, 0.840, cw, ct, ch, "Prod (Qwen3-VL-2B) — lower BC", GREEN, GREENF,
         PROD, "messier metric, answer kept")

    # --- outcome row (CJK bold font carries the ✗/✓ glyphs) ---
    ax.text(0.515, 0.41, "retrieval:  MISS", ha="center", va="center",
            fontsize=9.6, fontweight="bold", color=RED)
    ax.text(0.840, 0.41, "retrieval:  HIT", ha="center", va="center",
            fontsize=9.6, fontweight="bold", color=GREEN)

    # --- thesis ---
    ax.text(0.60, 0.215, "The cleaner-looking parse — higher Boundary "
            "Clarity — retrieves worse.", ha="center", va="center",
            fontsize=9.4, fontweight="bold", color="#111111")
    ax.text(0.60, 0.10, "Across the six-parser grid, selecting by appearance "
            "gives Hit@1 $0.20$ vs. $0.55$ by retrieval ($2.8\\times$).",
            ha="center", va="center", fontsize=7.8, color="#444444")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(OUT_DIR / f"fig_teaser.{ext}", bbox_inches="tight", dpi=200)
    print(f"saved -> {OUT_DIR}/fig_teaser.pdf")


if __name__ == "__main__":
    main()
