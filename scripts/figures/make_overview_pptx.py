"""Figure 1 (overview) — the RADP story as a four-move arc (C1->C4).

Editable PowerPoint deliverable.
  Top: a thin, grey RAG-pipeline context ribbon (Document -> Parse -> Chunk ->
       Retrieve -> Generate) carrying the real model logos at the Parser and
       Retriever stages — this is the system we study.
  Below: four self-titled contribution cards forming the paper's arc
       PROBLEM (C1) -> DIAGNOSE (C2) -> SELECT (C3) -> IMPROVE (C4),
       each with a name, a one-line description, and the headline number,
       so each Cn reads on its own (no cryptic badges).

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

FONT = "Calibri"
INK = "1F3247"
GREY_TX = "546E7A"
ARROW = "90A4AE"
RIB_F, RIB_LN = "F4F6F7", "CFD8DC"

# arc colours: problem -> diagnose -> select -> improve
CARDS_COLOR = {
    "C1": ("C62828", "FDEBEC"),   # PROBLEM  (red)
    "C2": ("1565C0", "E8F0FE"),   # DIAGNOSE (blue)
    "C3": ("2E7D32", "E7F5EA"),   # SELECT   (green)
    "C4": ("E65100", "FFF3E0"),   # IMPROVE  (amber)
}


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
        ls = para.get("line_spacing")
        if ls:
            p.line_spacing = ls
        for (txt, size, bold, color) in para["runs"]:
            r = p.add_run(); r.text = txt
            r.font.size = Pt(size); r.font.bold = bold
            r.font.name = FONT; r.font.color.rgb = C(color)
    return tf


def textbox(slide, x, y, w, h, paras, anchor=MSO_ANCHOR.TOP, m=0.03, space_after=3.0):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    set_rich(tb, paras, anchor=anchor, m=m, space_after=space_after)
    return tb


def arrow(slide, x1, y1, x2, y2, color=ARROW, w=2.0):
    cn = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,
                                    Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    cn.line.color.rgb = C(color); cn.line.width = Pt(w)
    ln = cn.line._get_or_add_ln()
    ln.append(ln.makeelement(qn("a:tailEnd"), {"type": "triangle", "w": "med", "len": "med"}))
    return cn


def picture(slide, path, x, y, w, h):
    slide.shapes.add_picture(str(path), Inches(x), Inches(y), Inches(w), Inches(h))


def logo_row(slide, logos, x, y, w, h, sz, gap=0.07):
    n = len(logos)
    total = n * sz + (n - 1) * gap
    sx = x + (w - total) / 2
    yy = y + (h - sz) / 2
    for i, lg in enumerate(logos):
        picture(slide, LOGO / lg, sx + i * (sz + gap), yy, sz, sz)


def main():
    prs = Presentation()
    prs.slide_width = Inches(11.3)
    prs.slide_height = Inches(3.62)
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    # ============================ context ribbon ============================
    rb_y, rb_h = 0.14, 0.74
    rxs = [0.2 + 2.24 * i for i in range(5)]
    rbw = 1.94
    stages = ["Document", "Parse", "Chunk", "Retrieve", "Generate"]
    for i, name in enumerate(stages):
        rrect(slide, rxs[i], rb_y, rbw, rb_h, RIB_F, line=RIB_LN, lw=0.9, radius=0.10)
        textbox(slide, rxs[i], rb_y + 0.04, rbw, 0.18,
                [{"runs": [(name, 9, True, GREY_TX)], "align": PP_ALIGN.CENTER}],
                anchor=MSO_ANCHOR.MIDDLE, m=0.02)
    cy = rb_y + 0.24
    ch = rb_h - 0.28
    picture(slide, ICON / "document.png", rxs[0] + rbw / 2 - 0.16, cy + 0.02, 0.32, 0.32)
    logo_row(slide, ["qwen.png", "mineru.png", "paddle.png", "marker.png"],
             rxs[1], cy, rbw, ch, 0.30)
    picture(slide, ICON / "chunk.png", rxs[2] + rbw / 2 - 0.16, cy + 0.02, 0.32, 0.32)
    logo_row(slide, ["bge.png", "me5.png", "qwen.png"], rxs[3], cy, rbw, ch, 0.32)
    picture(slide, ICON / "answer.png", rxs[4] + rbw / 2 - 0.16, cy + 0.02, 0.32, 0.32)
    ry = rb_y + rb_h / 2
    for i in range(4):
        arrow(slide, rxs[i] + rbw + 0.02, ry, rxs[i + 1] - 0.02, ry, color="B0BEC5", w=1.4)
    textbox(slide, 0.2, rb_y + rb_h + 0.005, rbw, 0.16,
            [{"runs": [("the document-RAG pipeline we study", 7.5, False, "90A4AE")],
              "align": PP_ALIGN.LEFT}], anchor=MSO_ANCHOR.TOP, m=0.02)

    # ============================ contribution arc ============================
    cxs = [0.2 + 2.81 * i for i in range(4)]
    cw = 2.46
    cd_y, cd_h = 1.18, 2.30
    hh = 0.56
    cards = [
        ("C1", "PROBLEM", "C1 · The disconnect",
         "Parsers that look clean don’t retrieve. Boundary Clarity "
         "anti-correlates with retrieval (r = −0.81).",
         "Parser choice → Hit@1 2.8×  (0.197 → 0.549)"),
        ("C2", "DIAGNOSE", "C2 · Coverage diagnostic",
         "A retriever-free check labels every answer covered / split / "
         "absent. Absent means a parser fault.",
         "20.2% absent — constant across 8 chunkers"),
        ("C3", "SELECT", "C3 · RCPS protocol",
         "Rank parsers & chunkers by what retrieval does, on a held-out "
         "Q–A probe. Retriever-averaged & format-invariant. No training.",
         "Picks what BC / edit-distance rank wrong"),
        ("C4", "IMPROVE", "C4 · Bounded training",
         "Best-of-K fidelity distillation improves the parser; a matched "
         "control shows the retrieval reward is unnecessary.",
         "+1.22 pp Hit@5  (OHR-Bench)"),
    ]
    for i, (key, verb, title, desc, stat) in enumerate(cards):
        hcol, fcol = CARDS_COLOR[key]
        x = cxs[i]
        rrect(slide, x, cd_y, cw, cd_h, "FFFFFF", line=hcol, lw=1.3, radius=0.05)
        hd = rrect(slide, x, cd_y, cw, hh, hcol, radius=0.09)
        set_rich(hd, [
            {"runs": [(verb, 8, True, "FFFFFF")], "align": PP_ALIGN.CENTER, "space_after": 1.0},
            {"runs": [(title, 12, True, "FFFFFF")], "align": PP_ALIGN.CENTER},
        ], anchor=MSO_ANCHOR.MIDDLE, m=0.04)
        # description
        textbox(slide, x + 0.10, cd_y + hh + 0.07, cw - 0.20, cd_h - hh - 0.55,
                [{"runs": [(desc, 9.5, False, INK)], "align": PP_ALIGN.LEFT,
                  "line_spacing": 1.04}], anchor=MSO_ANCHOR.TOP, m=0.03)
        # headline stat strip
        st = rrect(slide, x + 0.10, cd_y + cd_h - 0.46, cw - 0.20, 0.36, fcol, radius=0.12)
        set_rich(st, [{"runs": [(stat, 9.5, True, hcol)], "align": PP_ALIGN.CENTER}],
                 anchor=MSO_ANCHOR.MIDDLE, m=0.03)

    ay = cd_y + cd_h / 2
    for i in range(3):
        arrow(slide, cxs[i] + cw + 0.02, ay, cxs[i + 1] - 0.02, ay)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUT))
    print("saved ->", OUT)


if __name__ == "__main__":
    main()
