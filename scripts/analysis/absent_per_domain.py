"""Per-domain (KoGov / arXiv) absent-rate decomposition for one parser.

Rebuttal follow-up to `scripts/evaluation/absent_robustness.py`, which reports
corpus-level ladder absent rates: this decomposes the same rates by Q-A source
(kogov vs arxiv) so the per-domain MinerU table-ON rows in
`docs/FINDINGS_mineru_tableon_rerun.md` get a like-for-like Prod counterpart.

It reuses the exact matching ladder (`evaluation.absent_matchers.LADDER`), page
loader (`evaluation.parser_outputs.load_parser_outputs`), and Q-A loader
(`evaluation.rcps.load_qa_pairs`) — no new matching logic, so every number is
directly comparable with the paper's `absent_robustness` output. A missing page
file counts as absent at every rung, as in `absent_robustness.py`.

Verification contract printed with the table: the source-weighted average of the
per-domain rates equals the corpus rate by construction (same 663 Q-A, same
matcher); the corpus rate itself must land within ±0.2 pp of the paper's fixed
numbers for the parser (Prod: L1 20.2 / L4 16.9).

Usage:
    uv run python scripts/analysis/absent_per_domain.py \
        --parser-dir <...>/results/kogovdoc/v1_val/predictions \
        --label Prod
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from wigtnocr_radp.evaluation.absent_matchers import LADDER
from wigtnocr_radp.evaluation.parser_outputs import load_parser_outputs
from wigtnocr_radp.evaluation.rcps import load_qa_pairs


def load_page_sources(val_jsonl: Path) -> dict[str, str]:
    """Map page_id (val_XXXX) -> source ('kogov' | 'arxiv') from val.jsonl order."""
    sources: dict[str, str] = {}
    with val_jsonl.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            doc_id = json.loads(line)["images"][0].rstrip("/").split("/")[-2]
            sources[f"val_{i:04d}"] = doc_id.split("_")[0]
    return sources


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parser-dir", type=Path, required=True)
    ap.add_argument("--label", default=None, help="display name for the parser")
    ap.add_argument("--qa", type=Path, default=Path("data/KoGovDoc-RAG/qa_pairs_v1.jsonl"))
    ap.add_argument("--val", type=Path, default=Path("data/KoGovDoc-Bench/val.jsonl"))
    args = ap.parse_args()

    label = args.label or args.parser_dir.parent.name
    qa_pairs = load_qa_pairs(args.qa)
    pages = load_parser_outputs(args.parser_dir, args.val)
    sources = load_page_sources(args.val)

    # absent[rung][source] = count; totals[source] = n Q-A
    absent: dict[str, dict[str, int]] = {name: defaultdict(int) for name in LADDER}
    totals: dict[str, int] = defaultdict(int)

    for qa in qa_pairs:
        src = sources.get(qa.page_id, "?")
        totals[src] += 1
        page = pages.get(qa.page_id)
        for name, matcher in LADDER.items():
            present = page is not None and matcher(qa.answer_span, page)
            if not present:
                absent[name][src] += 1

    srcs = sorted(totals)
    n = sum(totals.values())
    print(f"# Per-domain absent — {label} ({n} Q-A: "
          + ", ".join(f"{s}={totals[s]}" for s in srcs) + ")\n")
    print("| rung | " + " | ".join(srcs) + " | overall (weighted) |")
    print("|------|" + "----:|" * (len(srcs) + 1))
    for name in LADDER:
        cells = []
        for s in srcs:
            a, t = absent[name][s], totals[s]
            cells.append(f"{a}/{t} = {a / t:.6f} ({a / t:.1%})")
        a_all = sum(absent[name][s] for s in srcs)
        cells.append(f"{a_all}/{n} = {a_all / n:.6f} ({a_all / n:.1%})")
        print(f"| {name} | " + " | ".join(cells) + " |")
    print(
        "\nThe overall column IS the source-weighted average "
        "(identical Q-A set and matcher), so the ±0.2 pp check applies to it "
        "directly against the paper's fixed corpus numbers."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
