"""OHRBench Boundary Clarity — C1 cross-domain check.

For each OHRBench parser output (gt, MinerU, Qwen2.5-VL) over Law+Manual,
compute mean MoC Boundary Clarity, then put it next to the per-parser RCPS
(from ohrbench_crossdomain.json). Tests whether the intrinsic-metric vs
retrieval disconnect (C1) — strong in Korean gov docs (BC↔RCPS −0.81) — also
appears in the English enterprise domain.

n=3 parsers: the correlation is illustrative, not inferential — the readable
signal is the *ordering* (does the cleanest-boundary parser retrieve worst?).

Usage:
    CUDA_VISIBLE_DEVICES=1 uv run python scripts/evaluation/eval_ohrbench_bc.py
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np

from eval_ohrbench import load_parser_pages  # same dir (scripts/evaluation)
from wigtnocr_radp.evaluation.boundary_clarity import PerplexityLM
from wigtnocr_radp.evaluation.chunkers import ParserNativeChunker

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("eval_ohrbench_bc")

DEFAULT_DOMAINS = ["law", "manual"]
DEFAULT_RCPS_JSON = Path("output/results/ohrbench_noise.json")
DEFAULT_OUT = Path("output/results/ohrbench_bc_noise.json")


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--domains", default=",".join(DEFAULT_DOMAINS))
    ap.add_argument("--rcps-json", type=Path, default=DEFAULT_RCPS_JSON)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    DOMAINS = args.domains.split(",")
    RCPS_JSON = args.rcps_json
    OUT = args.out

    chunker = ParserNativeChunker(min_chars=30)
    ppl = PerplexityLM()

    rcps = json.loads(RCPS_JSON.read_text())["results"]["parser_native"]

    rows = []
    for parser in sorted(rcps):
        pages = load_parser_pages(parser, DOMAINS)
        bcs: list[float] = []
        n_boundaries = 0
        for pid, md in pages.items():
            chunks = chunker.chunk(pid, md)
            for i in range(len(chunks) - 1):
                bc = ppl.boundary_clarity(chunks[i].text, chunks[i + 1].text)
                if bc is not None:
                    bcs.append(bc)
                    n_boundaries += 1
        mean_bc = float(np.mean(bcs)) if bcs else float("nan")
        rows.append({
            "parser": parser,
            "boundary_clarity": mean_bc,
            "n_boundaries": n_boundaries,
            "rcps": rcps[parser]["rcps"],
            "hit@1": rcps[parser]["hit@1"],
        })
        logger.info("%s: BC=%.4f (n=%d boundaries), RCPS=%.4f",
                    parser, mean_bc, n_boundaries, rcps[parser]["rcps"])

    bc_vals = np.array([r["boundary_clarity"] for r in rows])
    rcps_vals = np.array([r["rcps"] for r in rows])
    pearson = float(np.corrcoef(bc_vals, rcps_vals)[0, 1])

    out = {"domains": DOMAINS, "rows": rows, "pearson_BC_vs_RCPS": pearson, "n": len(rows)}
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))

    print("\n" + "=" * 64)
    print(f"OHRBench Boundary Clarity vs RCPS — {DOMAINS}, n={len(rows)} parsers")
    print("=" * 64)
    print(f"  {'parser':<14}{'BC':>10}{'RCPS':>10}{'Hit@1':>10}")
    for r in sorted(rows, key=lambda x: -x["boundary_clarity"]):
        print(f"  {r['parser']:<14}{r['boundary_clarity']:>10.4f}"
              f"{r['rcps']:>10.4f}{r['hit@1']:>10.4f}")
    print(f"\n  Pearson BC vs RCPS = {pearson:+.3f} (n={len(rows)}, illustrative)")
    print(f"  wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
