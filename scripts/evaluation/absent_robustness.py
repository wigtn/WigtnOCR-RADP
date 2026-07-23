"""Family-neutral absent-rate diagnostic — is the parser absent gap a real
content loss or a same-family matching artifact? (Reviewer rebuttal, C2.)

For every parser we recompute the *absent* rate of the coverage diagnostic under
a ladder of presence matchers of increasing permissiveness (see
`evaluation.absent_matchers`). A gold answer is *present* for a parser iff the
matcher recovers it from that parser's page output; otherwise it is *absent*
(missing page output counts as absent, a parser fault, as in the paper).

Read the output like this:

    * If the MinerU/PaddleOCR-minus-Prod absent gap *collapses* as the matcher
      loosens (L1 -> L4)  → the gap was a surface-form / same-family artifact.
    * If the gap *persists* to L4                                → the content is
      genuinely missing from the OCR-style output; the parser fault is real, and
      the same-family objection does not explain it.

No retriever, no GPU, no API — pure text matching, seconds on CPU. The LLM-judge
semantic ceiling (L5) lives in `absent_llm_judge.py`.

Usage:
    uv run python scripts/evaluation/absent_robustness.py
    uv run python scripts/evaluation/absent_robustness.py --ref Prod --qa data/KoGovDoc-RAG/qa_pairs_v1.jsonl
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

from wigtnocr_radp.evaluation.absent_matchers import LADDER
from wigtnocr_radp.evaluation.parser_outputs import load_parser_outputs
from wigtnocr_radp.evaluation.rcps import load_qa_pairs

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("absent_robustness")

# Parser output roots on the training machine. Same layout as baseline_grid.py:
# <root>/<dir>/predictions/<doc_id>_<page_stem>.md
KOGOV_ROOT = Path("/mnt/data1/work/wigtnOCR-v1/results/kogovdoc")
VAL_JSONL = Path("data/KoGovDoc-Bench/val.jsonl")

# name -> parser output dir (relative to KOGOV_ROOT unless absolute).
PARSERS: dict[str, str] = {
    "Prod": "v1_val/predictions",              # Qwen3-VL-2B fine-tune (same family as ref)
    "Qwen3-VL-30B": "30b_val/predictions",     # teacher = reference source (near-perfect by construction)
    "Qwen3-VL-2B-base": "2b_base_val/predictions",
    "MinerU": "mineru_val/predictions",         # OCR-style, different family
    "PaddleOCR": "paddleocr_val/predictions",   # OCR-style, different family
    "Marker": "marker_val/predictions",         # 38-page subset only
}


def _absent_rates(qa_pairs, pages) -> dict[str, Any]:
    """Absent rate for one parser under every matcher, with per-type breakdown."""
    total = len(qa_pairs)
    absent = {name: 0 for name in LADDER}
    by_type: dict[str, dict[str, int]] = {}
    by_type_total: dict[str, int] = {}
    no_parse = 0

    for qa in qa_pairs:
        page = pages.get(qa.page_id)
        qtype = qa.question_type
        by_type.setdefault(qtype, {name: 0 for name in LADDER})
        by_type_total[qtype] = by_type_total.get(qtype, 0) + 1
        if page is None:
            no_parse += 1
            for name in LADDER:  # no output -> absent under every matcher
                absent[name] += 1
                by_type[qtype][name] += 1
            continue
        for name, match in LADDER.items():
            if not match(qa.answer_span, page):
                absent[name] += 1
                by_type[qtype][name] += 1

    return {
        "total": total,
        "no_parse": no_parse,
        "absent_rate": {name: absent[name] / total if total else 0.0 for name in LADDER},
        "absent_count": absent,
        "by_question_type": {
            qt: {name: by_type[qt][name] / by_type_total[qt] for name in LADDER}
            for qt in by_type
        },
    }


def _table(rows: dict[str, dict[str, Any]], ref: str) -> list[str]:
    names = list(LADDER)
    md = [
        "# Family-neutral absent rate — matching-strictness ladder",
        "",
        "Absent = the gold answer is *not* recoverable from the parser's page output "
        "under the given matcher. If the OCR-parser gap were a same-family surface "
        "artifact it would vanish as the matcher loosens (L0 -> L4).",
        "",
        "| Parser | " + " | ".join(names) + " |",
        "|--------|" + "|".join([":---:"] * len(names)) + "|",
    ]
    for parser, r in rows.items():
        ar = r["absent_rate"]
        md.append(f"| {parser} | " + " | ".join(f"{ar[n]:.1%}" for n in names) + " |")

    if ref in rows:
        md += ["", f"## Absent gap vs {ref} (percentage points)", "",
               "| Parser | " + " | ".join(names) + " |",
               "|--------|" + "|".join([":---:"] * len(names)) + "|"]
        base = rows[ref]["absent_rate"]
        for parser, r in rows.items():
            if parser == ref:
                continue
            ar = r["absent_rate"]
            md.append(f"| {parser} | "
                      + " | ".join(f"{(ar[n]-base[n])*100:+.1f}" for n in names) + " |")
        md += ["",
               f"> If the gap in the rightmost column (L4_fuzzy_lcs) is still large and "
               f"positive for MinerU/PaddleOCR, their absent answers are genuinely missing "
               f"content, not a surface-form mismatch with the {ref} (same-family) reference."]
    return md


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--qa", default="data/KoGovDoc-RAG/qa_pairs_v1.jsonl")
    ap.add_argument("--root", type=Path, default=KOGOV_ROOT)
    ap.add_argument("--val_jsonl", type=Path, default=VAL_JSONL)
    ap.add_argument("--ref", default="Prod", help="baseline parser for the gap table")
    ap.add_argument("--out_dir", type=Path, default=Path("output/diagnostics"))
    args = ap.parse_args()

    qa_pairs = load_qa_pairs(args.qa)
    rows: dict[str, dict[str, Any]] = {}
    for name, subdir in PARSERS.items():
        pdir = Path(subdir) if Path(subdir).is_absolute() else args.root / subdir
        if not pdir.is_dir():
            logger.warning("skip %s: %s not found", name, pdir)
            continue
        pages = load_parser_outputs(pdir, args.val_jsonl)
        rows[name] = _absent_rates(qa_pairs, pages)
        rows[name]["parser_dir"] = str(pdir)
        logger.info("%s: absent L1=%.1f%% L4=%.1f%%", name,
                    rows[name]["absent_rate"]["L1_normalized"] * 100,
                    rows[name]["absent_rate"]["L4_fuzzy_lcs"] * 100)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "absent_robustness.json").write_text(
        json.dumps({"config": {"qa": args.qa, "num_qa": len(qa_pairs), "ref": args.ref,
                               "ladder": list(LADDER)}, "parsers": rows},
                   ensure_ascii=False, indent=2))
    table = _table(rows, args.ref)
    (args.out_dir / "absent_robustness.md").write_text("\n".join(table))
    print("\n".join(table))
    logger.info("wrote %s", args.out_dir / "absent_robustness.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
