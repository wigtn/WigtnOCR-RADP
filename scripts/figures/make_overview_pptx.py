"""Figure 1 (overview) — the document-RAG pipeline and where C1-C4 act.

Editable PowerPoint deliverable: phase band (Document->Generate) + component
boxes (real model brand logos for the Parser / Retriever stages, clean icons
elsewhere) + three colour-coded contribution zones that read on their own:
Diagnose (C1, C2) / Select (C3) / Improve (C4). No badges, no bottom band.

Brand logos: official GitHub org avatars (Qwen, OpenDataLab/MinerU, PaddlePaddle,
Datalab/Marker, FlagOpen/BGE, Microsoft/mE5), trimmed + squared under
icons/logos/norm/.  Generic icons: Bootstrap Icons (MIT) under icons/.
Output: paper/figures/fig1_overview.pptx
"""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR, MSO_AUTO_SIZE
from pptx.oxml.ns import qn

HERE = Path(__file__).resolve().parent
ICON = HERE / "icons"
LOGO = HERE / "icons" / "logos" / "norm"
OUT = HERE.parent.parent / "paper" / "figures" / "fig1_overview.pptx"

SLATE = "37474F"
GREY_LN = "B0BEC5"
GREY_TX = "546E7A"
ARROW = "78909C"
RED = "C62828"
DIAG_H, DIAG_F = "1565C0", "E8F0FE"
SEL_H, SEL_F = "2E7D32", "E7F5EA"
IMP_H, IMP_F = "E65100", "FFF3E0"
FOOT_F = "ECEFF1"
INK = "1F3247"


def C(h):
    return RGBColor.from_string(h)


def rrect(slide, x, y, w, h, fill, line=None, lw=1.0, radius=0.09):
    sp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                Inches(x), Inches(y), Inches(w), Inches(h))
    sp.fill.solid(); sp.fill.fore_color.rgb = C(fill)
    if line:
        sp.line.color.rgb = C(line); sp.line.width = Pt(lw)
    else:
        sp.line.fill.background()
    sp.shadow.inherit = False
    try:
        sp.adjustments[0] = radius
    except Exception:
        pass
    return sp


def set_rich(shape, paras, anchor=MSO_ANCHOR.MIDDLE, wrap=True, m=0.06, space_after=3.0):
    tf = shape.text_frame
    tf.word_wrap = wrap
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(m)
    tf.margin_top = tf.margin_bottom = Inches(min(m, 0.04))
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = para.get("align", PP_ALIGN.CENTER)
        p.space_after = Pt(para.get("space_after", space_after))
        p.space_before = Pt(0)
        for (txt, size, bold, color) in para["runs"]:
            r = p.add_run(); r.text = txt
            r.font.size = Pt(size); r.font.bold = bold
            r.font.name = "Calibri"; r.font.color.rgb = C(color)
    return tf


def textbox(slide, x, y, w, h, paras, anchor=MSO_ANCHOR.TOP, m=0.03, space_after=4.0):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    set_rich(tb, paras, anchor=anchor, m=m, space_after=space_after)
    return tb


def arrow(slide, x1, y1, x2, y2, color=ARROW, w=1.6):
    cn = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,
                                    Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    cn.line.color.rgb = C(color); cn.line.width = Pt(w)
    ln = cn.line._get_or_add_ln()
    ln.append(ln.makeelement(qn("a:tailEnd"), {"type": "triangle", "w": "med", "len": "med"}))
    return cn


def badge(slide, x, y, text, w=0.38, h=0.21, fs=9):
    sp = rrect(slide, x, y, w, h, RED, line="FFFFFF", lw=1.1, radius=0.5)
    set_rich(sp, [{"runs": [(text, fs, True, "FFFFFF")], "align": PP_ALIGN.CENTER}],
             anchor=MSO_ANCHOR.MIDDLE, m=0.0)
    return sp


def logo_tile(slide, path, x, y, w, h, name, name_sz=6.5):
    lsz = min(w * 0.92, h * 0.66)
    slide.shapes.add_picture(str(path), Inches(x + (w - lsz) / 2), Inches(y),
                             Inches(lsz), Inches(lsz))
    textbox(slide, x, y + lsz + 0.01, w, h - lsz - 0.01,
            [{"runs": [(name, name_sz, False, GREY_TX)], "align": PP_ALIGN.CENTER}],
            anchor=MSO_ANCHOR.TOP, m=0.0)


def icon_box(slide, i, xs, bw, cb_y, cb_h, icon, label, detail):
    rrect(slide, xs[i], cb_y, bw, cb_h, "FFFFFF", line=GREY_LN, lw=1.1, radius=0.06)
    isz = 0.56
    slide.shapes.add_picture(str(ICON / icon),
                             Inches(xs[i] + bw / 2 - isz / 2), Inches(cb_y + 0.16),
                             Inches(isz), Inches(isz))
    textbox(slide, xs[i], cb_y + cb_h - 0.50, bw, 0.46, [
        {"runs": [(label, 11, True, INK)], "align": PP_ALIGN.CENTER, "space_after": 1.0},
        {"runs": [(detail, 8.5, False, GREY_TX)], "align": PP_ALIGN.CENTER},
    ], anchor=MSO_ANCHOR.TOP, m=0.05)


def main():
    prs = Presentation()
    prs.slide_width = Inches(11.3)
    prs.slide_height = Inches(4.3)
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    xs = [0.2 + 2.25 * i for i in range(5)]
    bw = 1.85
    ph_y, ph_h = 0.16, 0.34
    cb_y, cb_h = 0.60, 1.46

    phases = ["Document", "Parse", "Chunk", "Retrieve", "Generate"]
    for i, name in enumerate(phases):
        hp = rrect(slide, xs[i], ph_y, bw, ph_h, SLATE, radius=0.18)
        set_rich(hp, [{"runs": [(name, 12.5, True, "FFFFFF")], "align": PP_ALIGN.CENTER}],
                 anchor=MSO_ANCHOR.MIDDLE, m=0.02)

    # generic-icon stages
    icon_box(slide, 0, xs, bw, cb_y, cb_h, "document.png", "Korean gov doc", "PDF / scanned page")
    icon_box(slide, 2, xs, bw, cb_y, cb_h, "chunk.png", "Chunker", "md-header · native · fixed")
    icon_box(slide, 4, xs, bw, cb_y, cb_h, "answer.png", "RAG answer", "grounded generation")

    # ---- Parse stage: real parser logos (2x2) -> Prod 2B ----
    px = xs[1]
    rrect(slide, px, cb_y, bw, cb_h, "FFFFFF", line=GREY_LN, lw=1.1, radius=0.06)
    textbox(slide, px, cb_y + 0.05, bw, 0.22,
            [{"runs": [("Parsers", 10, True, INK)], "align": PP_ALIGN.CENTER}],
            anchor=MSO_ANCHOR.MIDDLE, m=0.02)
    plogos = [("qwen.png", "Qwen-VL"), ("mineru.png", "MinerU"),
              ("paddle.png", "PaddleOCR"), ("marker.png", "Marker")]
    gx, gy, gw, gh = px + 0.06, cb_y + 0.30, (bw - 0.12) / 2, 0.46
    for k, (lg, nm) in enumerate(plogos):
        r, c = divmod(k, 2)
        logo_tile(slide, LOGO / lg, gx + c * gw, gy + r * gh, gw, gh, nm)
    textbox(slide, px, cb_y + cb_h - 0.31, bw, 0.24,
            [{"runs": [("fine-tune → Prod (2B)", 9, True, "00695C")], "align": PP_ALIGN.CENTER}],
            anchor=MSO_ANCHOR.MIDDLE, m=0.02)

    # ---- Retrieve stage: real retriever logos (row of 3) ----
    rx = xs[3]
    rrect(slide, rx, cb_y, bw, cb_h, "FFFFFF", line=GREY_LN, lw=1.1, radius=0.06)
    textbox(slide, rx, cb_y + 0.05, bw, 0.22,
            [{"runs": [("Retrievers ×3", 10, True, INK)], "align": PP_ALIGN.CENTER}],
            anchor=MSO_ANCHOR.MIDDLE, m=0.02)
    rlogos = [("bge.png", "BGE-M3"), ("me5.png", "mE5"), ("qwen.png", "Qwen3-Emb")]
    rw = (bw - 0.10) / 3
    for k, (lg, nm) in enumerate(rlogos):
        logo_tile(slide, LOGO / lg, rx + 0.05 + k * rw, cb_y + 0.34, rw, 0.62, nm)
    textbox(slide, rx, cb_y + cb_h - 0.30, bw, 0.26,
            [{"runs": [("k ∈ {1, 5, 10}", 8.5, False, GREY_TX)], "align": PP_ALIGN.CENTER}],
            anchor=MSO_ANCHOR.MIDDLE, m=0.02)

    # pipeline arrows
    ay = cb_y + cb_h / 2
    for i in range(4):
        arrow(slide, xs[i] + bw + 0.02, ay, xs[i + 1] - 0.02, ay)

    # ---- zones (the contributions read here; no badges on the pipeline) ----
    zy, zh, zhh = 2.18, 1.96, 0.34

    def zone(x, w, hcol, fcol, title, body):
        rrect(slide, x, zy, w, zh, fcol, line=hcol, lw=1.1, radius=0.05)
        hd = rrect(slide, x, zy, w, zhh, hcol, radius=0.10)
        set_rich(hd, [{"runs": [(title, 10.5, True, "FFFFFF")], "align": PP_ALIGN.CENTER}],
                 anchor=MSO_ANCHOR.MIDDLE, m=0.03)
        textbox(slide, x + 0.08, zy + zhh + 0.05, w - 0.16, zh - zhh - 0.12,
                body, anchor=MSO_ANCHOR.TOP, m=0.04, space_after=5.0)

    def cline(tag, tagcol, text):
        return {"align": PP_ALIGN.LEFT,
                "runs": [(tag + "  ", 9.5, True, tagcol), (text, 9.5, False, INK)]}

    zone(0.2, 4.9, DIAG_H, DIAG_F, "DIAGNOSE  —  locate the real fault", [
        cline("C1", DIAG_H,
              "Disconnect — parsers that look clean don’t retrieve. Boundary Clarity "
              "anti-correlates with retrieval (r = −0.81); parser choice alone swings "
              "Hit@1 2.8× (0.197 → 0.549)."),
        cline("C2", DIAG_H,
              "Coverage (no retriever) — 20.2% of answers are absent from the parser "
              "output, constant across 8 chunkers → fix the parser before the retriever."),
    ])
    zone(5.25, 2.90, SEL_H, SEL_F, "SELECT", [
        cline("C3", SEL_H,
              "RCPS — rank parsers & chunkers by what retrieval does, on a held-out "
              "Q–A probe. Retriever-averaged & format-invariant. No training."),
    ])
    zone(8.30, 2.75, IMP_H, IMP_F, "IMPROVE  (bounded)", [
        cline("C4", IMP_H,
              "Best-of-K fidelity distillation: +1.22 pp Hit@5 (OHR-Bench). A matched "
              "control shows the retrieval reward is unnecessary."),
    ])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUT))
    print("saved ->", OUT)


if __name__ == "__main__":
    main()
