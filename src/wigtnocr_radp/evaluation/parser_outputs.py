"""Load parser markdown outputs and map them to KoGovDoc-Bench page IDs.

The benchmark's val.jsonl has image paths like
    .../images/documents/kogov_008/page_0544.png
    .../images/papers/arxiv_009/page_0012.png
We derive a stable file stem `<doc_id>_<page_stem>` from these paths
(e.g. `kogov_008_page_0544`) and use it to look up `<stem>.md` in a parser
output directory.

This is the bridge between
    (a) Q-A page IDs `val_NNNN` produced by `qa_generation.generator`,
    (b) parser output filenames (e.g. v1's `results/kogovdoc/*_val/predictions/`).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path


logger = logging.getLogger("wigtnocr_radp.evaluation.parser_outputs")


def _doc_page_from_image_path(image_path: str) -> str:
    """Extract `<doc_id>_<page_stem>` from a benchmark image path."""
    p = Path(image_path)
    return f"{p.parent.name}_{p.stem}"


def build_page_id_index(val_jsonl_path: str | Path) -> dict[str, str]:
    """Return {`val_NNNN`: `<doc_id>_<page_stem>`} for every record in val.jsonl."""
    p = Path(val_jsonl_path)
    index: dict[str, str] = {}
    with p.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            images = d.get("images", [])
            if not images:
                logger.warning("val_%04d: no images field", i)
                continue
            page_id = f"val_{i:04d}"
            index[page_id] = _doc_page_from_image_path(images[0])
    return index


def load_parser_outputs(
    parser_dir: str | Path,
    val_jsonl_path: str | Path,
    *,
    strict: bool = False,
) -> dict[str, str]:
    """Load a parser's per-page markdown outputs keyed by `val_NNNN`.

    Args:
        parser_dir: directory containing `<doc_id>_<page_stem>.md` files
            (e.g. `wigtnOCR-v1/results/kogovdoc/v1_val/predictions/`).
        val_jsonl_path: KoGovDoc-Bench validation jsonl.
        strict: if True, raise on missing files; otherwise log a warning.

    Returns:
        {page_id: markdown}. Pages whose file is missing are omitted.
    """
    parser_dir = Path(parser_dir)
    if not parser_dir.is_dir():
        raise FileNotFoundError(f"parser_dir not found: {parser_dir}")
    index = build_page_id_index(val_jsonl_path)

    out: dict[str, str] = {}
    missing: list[str] = []
    for page_id, stem in index.items():
        f = parser_dir / f"{stem}.md"
        if not f.exists():
            missing.append(stem)
            continue
        out[page_id] = f.read_text(encoding="utf-8")

    if missing:
        msg = (
            f"{parser_dir.name}: {len(missing)} pages missing"
            f" (e.g. {missing[:3]})"
        )
        if strict:
            raise FileNotFoundError(msg)
        logger.warning(msg)

    logger.info(
        "loaded %d/%d pages from %s",
        len(out),
        len(index),
        parser_dir,
    )
    return out
