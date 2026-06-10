"""Figure 1 (overview) as an EDITABLE PowerPoint, OHR-Bench-Fig2 density.

Full-width, three phase columns, each packed with REAL artifacts (page image,
the garbled-vs-clean parse contrast, the actual result charts, brand logos) so
it reads as densely as OHR-Bench Fig.2 while staying organised:

  C1 Parsing-Retrieval Disconnect  ->  C2/C3 Diagnose + Select  ->  C4 Bounded Training

No heavy bottom bar -- a thin rule + one bold takeaway line.
Korean is set as latin+EA font (Noto Sans CJK KR here; swap in PowerPoint).
Output: paper/figures/fig_overview.pptx
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.oxml.ns import qn

OUT = Path("paper/figures/fig_overview.pptx")
FIG = Path("paper/figures")
LOGO = Path("scripts/figures/icons/logos")
PAGE = Path("data/KoGovDoc-Bench/images/documents/kogov_003/page_0533.png")

KFONT, CF = "Noto Sans CJK KR", "Calibri"
WHITE = RGBColor(0xFF, 0xFF, 0xFF); DARK = RGBColor(0x20, 0x20, 0x20)
GREY = RGBColor(0x55, 0x55, 0x55); LINE = RGBColor(0x90, 0x90, 0x90)
BLUE = RGBColor(0x1F, 0x5F, 0xA8); BLUEF = RGBColor(0xEC, 0xF2, 0xFB)
AMBER = RGBColor(0x9A, 0x5A, 0x00); AMBERF = RGBColor(0xFC, 0xF3, 0xE6)
GREEN = RGBColor(0x1A, 0x6B, 0x1A); GREENF = RGBColor(0xEC, 0xF6, 0xEC)
RED = RGBColor(0x8F, 0x1B, 0x1B); REDF = RGBColor(0xF9, 0xEC, 0xEC)


def _ea(run, name):
    rPr = run._r.get_or_add_rPr()
    for t in ("a:latin", "a:ea", "a:cs"):
        el = rPr.find(qn(t))
        if el is None:
            el = rPr.makeelement(qn(t), {}); rPr.append(el)
        el.set("typeface", name)


def R(txt, size, color, bold=False, italic=False, font=CF):
    return (txt, size, color, bold, italic, font)


def tbox(s, x, y, w, h, paras, *, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
         lead=1.1):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Pt(3); tf.margin_top = tf.margin_bottom = Pt(2)
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align; p.line_spacing = lead
        for (txt, size, color, bold, italic, font) in para:
            r = p.add_run(); r.text = txt
            r.font.size = Pt(size); r.font.bold = bold; r.font.italic = italic
            r.font.color.rgb = color; _ea(r, font)
    return tb


def rrect(s, x, y, w, h, fill, line, lw=1.25, radius=0.04):
    sp = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y),
                            Inches(w), Inches(h))
    sp.adjustments[0] = radius
    sp.fill.background() if fill is None else (sp.fill.solid(),
                                               setattr(sp.fill.fore_color, "rgb", fill))
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = line; sp.line.width = Pt(lw)
    sp.shadow.inherit = False
    return sp


def chevron(s, x, y, w, h, color):
    sp = s.shapes.add_shape(MSO_SHAPE.CHEVRON, Inches(x), Inches(y),
                            Inches(w), Inches(h))
    sp.fill.solid(); sp.fill.fore_color.rgb = color
    sp.line.fill.background(); sp.shadow.inherit = False
    return sp


def pic_fit(s, path, x, y, w, h):
    """Place an image scaled to fit (w,h), centred in that box."""
    iw, ih = Image.open(path).size
    sc = min(w / iw, h / ih)
    dw, dh = iw * sc, ih * sc
    return s.shapes.add_picture(str(path), Inches(x + (w - dw) / 2),
                                Inches(y + (h - dh) / 2), height=Inches(dh))


def logo(s, name, x, y, h):
    return s.shapes.add_picture(str(LOGO / name), Inches(x), Inches(y),
                                height=Inches(h))


def subzone(s, x, y, w, h, title, color, fill):
    rrect(s, x, y, w, h, WHITE, color, lw=1.25)
    rrect(s, x, y, w, 0.34, fill, None, radius=0.10)
    tbox(s, x + 0.05, y, w - 0.1, 0.34, [[R(title, 10.5, color, bold=True)]],
         anchor=MSO_ANCHOR.MIDDLE)


def main():
    prs = Presentation()
    prs.slide_width = Inches(13.3); prs.slide_height = Inches(6.3)
    s = prs.slides.add_slide(prs.slide_layouts[6])

    M, GAP = 0.22, 0.26
    cw = (13.3 - 2 * M - 2 * GAP) / 3
    x1 = M; x2 = M + cw + GAP; x3 = M + 2 * (cw + GAP)

    # ---- column header bars ----
    for x, txt, c in [(x1, "C1 · Parsing–Retrieval Disconnect", BLUE),
                      (x2, "C2 / C3 · Diagnose + Select", AMBER),
                      (x3, "C4 · Bounded Parser Training", GREEN)]:
        rrect(s, x, 0.2, cw, 0.46, c, None, radius=0.12)
        tbox(s, x, 0.2, cw, 0.46, [[R(txt, 12.5, WHITE, bold=True)]],
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

    top = 0.82
    # ================= COLUMN 1 =================
    # 1a candidate parsers (logos in one row + "+GOT"; no overlapping caption)
    h1a = 0.95
    subzone(s, x1, top, cw, h1a, "Candidate parsers", BLUE, BLUEF)
    for nm, dx in [("qwen.png", 0.28), ("mineru.png", 1.02),
                   ("marker_datalab.png", 1.76), ("paddle.png", 2.5)]:
        logo(s, nm, x1 + dx, top + 0.42, 0.46)
    tbox(s, x1 + 3.05, top + 0.42, cw - 3.15, 0.46,
         [[R("+ GOT", 10, GREY, italic=True)]], anchor=MSO_ANCHOR.MIDDLE)

    # 1b same page -> two parses (the concrete disconnect, given real room)
    y1b = top + h1a + 0.16; h1b = 3.55
    subzone(s, x1, y1b, cw, h1b, "Same page → two parses (appearance lies)",
            BLUE, BLUEF)
    pic_fit(s, PAGE, x1 + 0.12, y1b + 0.48, 1.45, h1b - 1.15)
    pcx = x1 + 1.72; pcw = cw - 1.86
    rrect(s, pcx, y1b + 0.52, pcw, 1.06, REDF, RED, 1.1)
    tbox(s, pcx + 0.09, y1b + 0.52, pcw - 0.18, 1.06,
         [[R("MinerU — BC 0.72 (cleanest)", 9.5, RED, bold=True)],
          [R("(2) 即个张号 Sand Mat音斗个张叶", 9, DARK, font=KFONT)],
          [R("clean structure, garbled text", 8.5, GREY, italic=True),
           R("   MISS", 9.5, RED, bold=True)]],
         anchor=MSO_ANCHOR.MIDDLE, lead=1.18)
    rrect(s, pcx, y1b + 1.72, pcw, 1.06, GREENF, GREEN, 1.1)
    tbox(s, pcx + 0.09, y1b + 1.72, pcw - 0.18, 1.06,
         [[R("Prod (Qwen3-VL-2B) — lower BC", 9.5, GREEN, bold=True)],
          [R("모래수량은 Sand Mat층을 제외한 수량", 9, DARK, font=KFONT)],
          [R("messier metric, answer kept", 8.5, GREY, italic=True),
           R("   HIT", 9.5, GREEN, bold=True)]],
         anchor=MSO_ANCHOR.MIDDLE, lead=1.18)
    tbox(s, x1 + 0.12, y1b + h1b - 0.5, cw - 0.24, 0.44,
         [[R("cleanest-looking parse retrieves worst — ", 9.5, DARK),
           R("r = −0.81", 10.5, RED, bold=True)]],
         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

    # ================= COLUMN 2 (C2/C3) =================
    h2a = 2.55
    subzone(s, x2, top, cw, h2a, "C2 · Coverage diagnostic (no retriever)", AMBER, AMBERF)
    pic_fit(s, FIG / "fig_coverage.png", x2 + 0.1, top + 0.4, cw - 0.2, h2a - 1.0)
    tbox(s, x2 + 0.12, top + h2a - 0.6, cw - 0.24, 0.55,
         [[R("20.2% of answers absent = parser fault", 10.5, RED, bold=True)],
          [R("flat across 8 chunkers → fix the parser, not the chunker", 8.8,
             GREY, italic=True)]], align=PP_ALIGN.CENTER, lead=1.1)

    y2b = top + h2a + 0.16; h2b = 1.85
    subzone(s, x2, y2b, cw, h2b, "C3 · RCPS selection protocol (no training)", AMBER, AMBERF)
    tbox(s, x2 + 0.12, y2b + 0.42, cw - 0.24, 0.4,
         [[R("held-out Q–A probe, scored over 3 retrievers:", 9.5, DARK)]])
    for nm, dx in [("bge_baai.png", 0.7), ("me5_ms.png", 1.85), ("qwen.png", 2.85)]:
        logo(s, nm, x2 + dx, y2b + 0.82, 0.5)
    tbox(s, x2 + 0.1, y2b + 1.34, cw - 0.2, 0.24,
         [[R("BGE-M3 · mE5 · Qwen3-Emb", 8.5, GREY, italic=True)]],
         align=PP_ALIGN.CENTER)
    tbox(s, x2 + 0.12, y2b + h2b - 0.4, cw - 0.24, 0.34,
         [[R("→ rank parsers & chunkers by retrieval", 10.5, AMBER, bold=True)]],
         align=PP_ALIGN.CENTER)

    # ================= COLUMN 3 (C4) =================
    h3a = 1.95
    subzone(s, x3, top, cw, h3a, "C4 · Parser-side training", GREEN, GREENF)
    tbox(s, x3 + 0.14, top + 0.44, cw - 0.28, 0.4,
         [[R("best-of-K parses from Prod, ranked two ways:", 9.5, DARK)]])
    rrect(s, x3 + 0.2, top + 0.86, cw - 0.4, 0.46, GREENF, GREEN, 1.0)
    tbox(s, x3 + 0.22, top + 0.86, cw - 0.44, 0.46,
         [[R("RADP-Distill — edit-distance → GT", 9.5, GREEN, bold=True)]],
         anchor=MSO_ANCHOR.MIDDLE)
    tbox(s, x3, top + 1.34, cw, 0.22, [[R("≈", 13, DARK, bold=True)]],
         align=PP_ALIGN.CENTER)
    rrect(s, x3 + 0.2, top + 1.42, cw - 0.4, 0.42, AMBERF, AMBER, 1.0)
    tbox(s, x3 + 0.22, top + 1.42, cw - 0.44, 0.42,
         [[R("RADP-DPO — page-local RCPS", 9.5, AMBER, bold=True)]],
         anchor=MSO_ANCHOR.MIDDLE)

    y3b = top + h3a + 0.16; h3b = 2.45
    subzone(s, x3, y3b, cw, h3b, "Result", GREEN, GREENF)
    pic_fit(s, FIG / "fig_c4_training.png", x3 + 0.1, y3b + 0.4, cw - 0.2, h3b - 1.0)
    tbox(s, x3 + 0.12, y3b + h3b - 0.6, cw - 0.24, 0.55,
         [[R("the two signals tie → retrieval reward unnecessary", 9.5, GREEN,
             bold=True)],
          [R("the deployable lever is fidelity distillation", 8.8, GREY,
             italic=True)]], align=PP_ALIGN.CENTER, lead=1.1)

    # ---- flow chevrons between columns ----
    chevron(s, x1 + cw + 0.01, 3.0, GAP - 0.02, 0.62, AMBER)
    chevron(s, x2 + cw + 0.01, 3.0, GAP - 0.02, 0.62, GREEN)

    # ---- bottom takeaway: thin rule + one bold line (no heavy bar) ----
    ln = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(M), Inches(5.78),
                                Inches(13.3 - M), Inches(5.78))
    ln.line.color.rgb = RGBColor(0xCC, 0xCC, 0xCC); ln.line.width = Pt(1.0)
    tbox(s, M, 5.84, 13.3 - 2 * M, 0.4,
         [[R("The parser — not the chunker — is the under-examined lever:  "
             "choose it by retrieval, not by appearance   ", 13, DARK, bold=True),
           R("(Hit@1 0.20 → 0.55, 2.8×)", 13, BLUE, bold=True)]],
         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUT))
    print(f"saved -> {OUT}")


if __name__ == "__main__":
    main()
