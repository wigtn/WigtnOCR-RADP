"""Re-run MinerU on KoGov pages with TABLE recognition ENABLED (the fair config).

The original MinerU baseline was run with `table-config.enable: false` in
magic-pdf.json, so tables were dumped as image crops and never transcribed
(0 markdown tables over 294 pages). That makes MinerU's KoGov absent rate a
config artifact, not a parser-quality verdict. This script re-parses the same
KoGov page images with tables (and formulas) ON, to a NEW output dir, so the
family-neutral absent diagnostic can be recomputed on a fair MinerU.

It does NOT touch the shared magic-pdf.json: it writes a temp config copy with
`table-config.enable=true` / `formula-config.enable=true` and points MinerU at it
via the MINERU_TOOLS_CONFIG_JSON env var.

Prereqs on the machine that has the data:
  - magic-pdf installed (the same 1.x family that produced the original models),
    e.g. `uv pip install "magic-pdf>=1.0,<2"`; models already on disk.
  - KoGov page images at <images_root>/<doc_id>/<page_stem>.png
    (doc_id/page_stem are read from val.jsonl's image paths).

Usage:
  uv run python scripts/evaluation/run_mineru_tableon.py \
      --images_root /path/to/images/documents \
      --val_jsonl data/KoGovDoc-Bench/val.jsonl \
      --config ~/magic-pdf.json \
      --out /path/to/results/kogovdoc/mineru_val_tableon/predictions \
      --device cpu            # or cuda if a GPU is free

Then recompute the diagnostic against the new dir:
  uv run python scripts/evaluation/absent_robustness.py \
      --override MinerU=mineru_val_tableon/predictions --ref Prod
  uv run python scripts/evaluation/absent_llm_judge.py \
      --parsers Prod MinerU --override MinerU=mineru_val_tableon/predictions
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import subprocess
import tempfile
from pathlib import Path

# MinerU emits tables as HTML (<table><td>...) not markdown pipes. Left raw, the
# `<td>`/`</td>` remnants sit between cell values and make the format-normalised
# matcher HARSHER on HTML than on markdown (a markdown `|` is stripped to nothing,
# but `<td` leaves letters). Replacing every tag with a space makes cell values
# space-separated, so an HTML table normalises the same way a markdown table does
# — a fair comparison with the other parsers. Single-cell answer spans are
# unaffected either way; this only removes the cross-cell HTML penalty.
_HTML_TAG = re.compile(r"<[^>]+>")


def _strip_html(md: str) -> str:
    return _HTML_TAG.sub(" ", md)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("run_mineru_tableon")


def _doc_page(image_path: str) -> tuple[str, str]:
    """<...>/kogov_008/page_0544.png -> ('kogov_008', 'page_0544')."""
    p = Path(image_path)
    return p.parent.name, p.stem


def _kogov_pages(val_jsonl: Path) -> list[tuple[str, str]]:
    """Return unique (doc_id, page_stem) for KoGov records in val.jsonl."""
    seen: dict[tuple[str, str], None] = {}
    for line in val_jsonl.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        imgs = d.get("images") or []
        if not imgs:
            continue
        doc, page = _doc_page(imgs[0])
        if doc.startswith("kogov"):
            seen[(doc, page)] = None
    return list(seen)


def _table_on_config(src_config: Path) -> Path:
    """Write a temp copy of magic-pdf.json with table + formula recognition ON."""
    cfg = json.loads(src_config.read_text(encoding="utf-8"))
    cfg.setdefault("table-config", {})["enable"] = True
    cfg.setdefault("formula-config", {})["enable"] = True
    fd, tmp = tempfile.mkstemp(prefix="magic-pdf-tableon-", suffix=".json")
    os.close(fd)
    Path(tmp).write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    return Path(tmp)


def _find_md(mineru_out: Path, stem: str) -> Path | None:
    """magic-pdf writes <out>/<stem>/auto/<stem>.md (structure varies); search."""
    cand = mineru_out / stem / "auto" / f"{stem}.md"
    if cand.exists():
        return cand
    hits = list(mineru_out.rglob(f"{stem}.md"))
    return hits[0] if hits else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--images_root", type=Path, required=True,
                    help="dir containing <doc_id>/<page_stem>.png")
    ap.add_argument("--val_jsonl", type=Path, default=Path("data/KoGovDoc-Bench/val.jsonl"))
    ap.add_argument("--config", type=Path, default=Path.home() / "magic-pdf.json")
    ap.add_argument("--out", type=Path, required=True, help="predictions output dir")
    ap.add_argument("--device", default="cpu", help="cpu or cuda")
    ap.add_argument("--mode", default="auto", help="magic-pdf parse mode (auto/ocr)")
    ap.add_argument("--limit", type=int, default=0, help="only first N pages (pilot); 0 = all")
    ap.add_argument("--keep_html", action="store_true",
                    help="keep MinerU's raw HTML tables (default: strip tags to spaces "
                         "for a fair comparison with markdown parsers)")
    args = ap.parse_args()

    pages = _kogov_pages(args.val_jsonl)
    if args.limit:
        pages = pages[: args.limit]
    logger.info("%d KoGov pages to parse (tables ON)", len(pages))

    cfg = _table_on_config(args.config)
    env = dict(os.environ, MINERU_TOOLS_CONFIG_JSON=str(cfg))
    # magic-pdf reads device-mode from the config; also export for good measure.
    logger.info("using table-on config: %s (device=%s)", cfg, args.device)

    args.out.mkdir(parents=True, exist_ok=True)
    ok = missing_img = failed = with_table = 0
    with tempfile.TemporaryDirectory(prefix="mineru-work-") as work:
        work = Path(work)
        for i, (doc, page) in enumerate(pages, 1):
            img = args.images_root / doc / f"{page}.png"
            if not img.exists():
                logger.warning("[%d/%d] missing image: %s", i, len(pages), img)
                missing_img += 1
                continue
            outdir = work / f"{doc}_{page}"
            try:
                subprocess.run(
                    ["magic-pdf", "-p", str(img), "-o", str(outdir), "-m", args.mode],
                    env=env, check=True, capture_output=True, timeout=600,
                )
            except Exception as e:  # noqa: BLE001
                logger.warning("[%d/%d] magic-pdf failed on %s_%s: %s", i, len(pages), doc, page, e)
                failed += 1
                continue
            md = _find_md(outdir, page)
            if md is None:
                logger.warning("[%d/%d] no .md produced for %s_%s", i, len(pages), doc, page)
                failed += 1
                continue
            raw = md.read_text(encoding="utf-8", errors="ignore")
            if "<td" in raw or "<table" in raw or raw.count("|") >= 8:
                with_table += 1  # a table was actually parsed (HTML or markdown)
            text = raw if args.keep_html else _strip_html(raw)
            (args.out / f"{doc}_{page}.md").write_text(text, encoding="utf-8")
            ok += 1
            if i % 20 == 0:
                logger.info("[%d/%d] parsed", i, len(pages))

    # sanity: how many parsed pages actually contained a table (HTML or markdown,
    # counted on the RAW MinerU output before tag-stripping)?
    logger.info("done: %d parsed, %d missing-image, %d failed; %d/%d parsed pages had a table "
                "(pre-strip). If this is ~0, tables-on is NOT working — stop and check the version.",
                ok, missing_img, failed, with_table, ok)
    logger.info("output: %s", args.out)
    Path(cfg).unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
