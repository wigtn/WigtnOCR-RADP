"""Boundary Clarity on the OHR-Bench Law--Manual compatibility slice.

For each OHRBench parser output (gt, MinerU, Qwen2.5-VL) over Law+Manual,
compute mean MoC Boundary Clarity, then put it next to the per-parser RCPS
(from the source-aligned compatibility RCPS output).  This script does not
produce a full-v2 or seven-domain result.

n=3 parsers: the correlation is illustrative, not inferential — the readable
signal is the *ordering* (does the cleanest-boundary parser retrieve worst?).

Usage:
    CUDA_VISIBLE_DEVICES=1 uv run python scripts/evaluation/eval_ohrbench_bc.py
"""

from __future__ import annotations

import json
import hashlib
import logging
from pathlib import Path

import numpy as np

from eval_ohrbench import (  # same dir (scripts/evaluation)
    LAW_MANUAL_COMPAT_DOMAINS,
    LAW_MANUAL_COMPAT_NUM_QA,
    LAW_MANUAL_COMPAT_STATUS,
    load_parser_pages,
    load_qa,
)
from wigtnocr_radp.evaluation.boundary_clarity import PerplexityLM
from wigtnocr_radp.evaluation.chunkers import ParserNativeChunker
from wigtnocr_radp.ohrbench_paths import (
    require_compatibility_output_path,
    require_evidence_page_coverage,
    require_supported_ohr_alignment_audit,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("eval_ohrbench_bc")

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DOMAINS = list(LAW_MANUAL_COMPAT_DOMAINS)
DEFAULT_RCPS_JSON = Path("output/results/ohrbench_law_manual_compat_rcps.json")
DEFAULT_ALIGNMENT_AUDIT = Path("output/results/ohrbench_alignment_audit.json")
DEFAULT_OUT = Path("output/results/ohrbench_law_manual_compat_bc.json")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _validate_rcps_input(path: Path, artifact: dict, audit_path: Path) -> None:
    """Accept either a freshly tagged compat result or an exact audited source."""

    if artifact.get("domains") != DEFAULT_DOMAINS:
        raise ValueError(f"RCPS input is not the Law--Manual slice: {path}")
    if artifact.get("num_qa") != LAW_MANUAL_COMPAT_NUM_QA:
        raise ValueError(
            f"RCPS input has {artifact.get('num_qa')} Q-A; "
            f"expected {LAW_MANUAL_COMPAT_NUM_QA}: {path}"
        )

    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    require_supported_ohr_alignment_audit(audit, path=audit_path)
    sources = audit.get("source_artifacts", {})
    try:
        repo_key = path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        repo_key = ""
    expected_hash = sources.get(repo_key)
    if expected_hash is None:
        basename_matches = [
            digest for source, digest in sources.items() if Path(source).name == path.name
        ]
        if len(basename_matches) == 1:
            expected_hash = basename_matches[0]

    if expected_hash is not None:
        actual_hash = _sha256(path)
        if actual_hash != expected_hash:
            raise ValueError(
                f"audited RCPS input hash mismatch for {path}: "
                f"expected {expected_hash}, got {actual_hash}"
            )
    elif artifact.get("meta", {}).get("status") != LAW_MANUAL_COMPAT_STATUS:
        raise ValueError(
            f"RCPS input is neither an exact audit source nor a tagged compatibility result: {path}"
        )


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--domains", default=",".join(DEFAULT_DOMAINS))
    ap.add_argument("--rcps-json", type=Path, default=DEFAULT_RCPS_JSON)
    ap.add_argument("--alignment-audit", type=Path, default=DEFAULT_ALIGNMENT_AUDIT)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    DOMAINS = [domain.strip() for domain in args.domains.split(",") if domain.strip()]
    RCPS_JSON = args.rcps_json
    OUT = args.out

    if DOMAINS != DEFAULT_DOMAINS:
        raise ValueError(
            f"Boundary Clarity compatibility evaluation requires {DEFAULT_DOMAINS}; got {DOMAINS}"
        )
    require_compatibility_output_path(OUT)
    if OUT.resolve() == RCPS_JSON.resolve() or OUT.resolve() == args.alignment_audit.resolve():
        raise ValueError("output path must differ from RCPS and alignment-audit inputs")

    chunker = ParserNativeChunker(min_chars=30)
    ppl = PerplexityLM()

    rcps_artifact = json.loads(RCPS_JSON.read_text(encoding="utf-8"))
    _validate_rcps_input(RCPS_JSON, rcps_artifact, args.alignment_audit)
    rcps = rcps_artifact["results"]["parser_native"]

    rows = []
    qa_pairs = load_qa(DOMAINS)
    if len(qa_pairs) != LAW_MANUAL_COMPAT_NUM_QA:
        raise ValueError(
            f"Law--Manual compatibility identity changed: got {len(qa_pairs)} Q-A"
        )
    for parser in sorted(rcps):
        pages = load_parser_pages(parser, DOMAINS)
        require_evidence_page_coverage(
            qa_pairs,
            pages,
            label=f"OHR-Bench BC domains={','.join(DOMAINS)} parser={parser}",
        )
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
        if not np.isfinite(mean_bc):
            raise ValueError(f"no finite Boundary Clarity observations for parser={parser}")
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
    if len(rows) < 2 or not np.all(np.isfinite(rcps_vals)):
        raise ValueError("Boundary Clarity correlation needs at least two finite parser rows")
    pearson = float(np.corrcoef(bc_vals, rcps_vals)[0, 1])
    if not np.isfinite(pearson):
        raise ValueError("Boundary Clarity correlation is not finite")

    out = {
        "domains": DOMAINS,
        "rows": rows,
        "pearson_BC_vs_RCPS": pearson,
        "n": len(rows),
        "meta": {"status": LAW_MANUAL_COMPAT_STATUS, "full_v2": False},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

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
