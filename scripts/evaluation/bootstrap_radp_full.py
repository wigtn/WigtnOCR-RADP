"""Bootstrap CIs for the full-scale RADP λ sweep (Table 3 in paper §4.4).

Re-runs the held-out eval (73p / ~202 Q-A) for each full-scale λ checkpoint,
*capturing per-Q-A MRR scores* so we can compute bootstrap CIs and paired
deltas against the λ=0 control. Same retrievers, chunkers, and parses as the
original `eval_radp_b.py` for `output/parses_full/` — only the per-Q-A capture
and the bootstrap step are new.

Output:
    output/results/radp_b_full_eval_ci.json
        {meta, by_chunker: {<chunker>: {<label>: {rcps_ci, vs_lambda0_ci}}}}
    output/results/radp_b_full_eval_perqa.json
        raw per-(retriever, k) per-Q-A MRR arrays for downstream analysis.

Usage:
    uv run python scripts/evaluation/bootstrap_radp_full.py --device cuda:0
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from pathlib import Path
from typing import Any

import numpy as np

from wigtnocr_radp.evaluation import (
    BgeM3Retriever,
    MarkdownHeaderChunker,
    ParserNativeChunker,
    compute_rcps,
)
from wigtnocr_radp.evaluation.bootstrap import (
    bootstrap_mean,
    bootstrap_paired_delta,
    per_qa_rcps,
    save_per_qa_arrays,
)
from wigtnocr_radp.evaluation.parser_outputs import load_parser_outputs
from wigtnocr_radp.evaluation.rcps import load_qa_pairs
from wigtnocr_radp.evaluation.retrievers import (
    MultilingualE5LargeRetriever,
    Qwen3EmbeddingRetriever,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("bootstrap_radp_full")

CHUNKERS = {
    "md_h3": MarkdownHeaderChunker(max_level=3),
    "parser_native": ParserNativeChunker(min_chars=30),
}
V1_PARSES = Path("/mnt/data1/work/wigtnOCR-v1/results/kogovdoc/v1_val/predictions")
N_BOOT = 1000
ALPHA = 0.05


def lambda_from_dirname(name: str) -> float | None:
    m = re.search(r"lambda(\d)(\d)", name)
    return int(m.group(1)) + int(m.group(2)) / 10 if m else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--parses_root", type=Path, default=Path("output/parses_full"))
    ap.add_argument("--v1_parses", type=Path, default=V1_PARSES)
    ap.add_argument("--qa", type=Path, default=Path("data/KoGovDoc-RAG/qa_pairs_v1.jsonl"))
    ap.add_argument("--split", type=Path, default=Path("data/KoGovDoc-RAG/page_split_v1.json"))
    ap.add_argument("--val_jsonl", type=Path, default=Path("data/KoGovDoc-Bench/val.jsonl"))
    ap.add_argument("--chunkers", nargs="+", default=["md_h3", "parser_native"], choices=tuple(CHUNKERS))
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--out_ci", type=Path, default=Path("output/results/radp_b_full_eval_ci.json"))
    ap.add_argument("--out_perqa", type=Path, default=Path("output/results/radp_b_full_eval_perqa.json"))
    ap.add_argument("--n_boot", type=int, default=N_BOOT)
    ap.add_argument("--extra_system", action="append", default=[],
                    help="extra <label>=<parses_dir>, e.g. RADP-DPO=output/parses_full/radp_dpo_eval. "
                         "Repeatable.")
    ap.add_argument("--fold", default="eval", choices=("eval", "all"),
                    help="'eval' uses 73-page held-out; 'all' uses train ∪ eval from the split (242p)")
    args = ap.parse_args()

    split_data = json.loads(args.split.read_text())
    if args.fold == "all":
        eval_pages = set(split_data["train_pages"]) | set(split_data["eval_pages"])
    else:
        eval_pages = set(split_data["eval_pages"])
    eval_qa = [qa for qa in load_qa_pairs(args.qa) if qa.page_id in eval_pages]
    logger.info("eval fold=%s: %d pages, %d Q-A", args.fold, len(eval_pages), len(eval_qa))

    def load_parses(d: Path) -> dict[str, str]:
        return {p: m for p, m in load_parser_outputs(d, args.val_jsonl).items() if p in eval_pages}

    sweep: list[tuple[str, float | None, dict[str, str]]] = []
    for d in sorted(args.parses_root.glob("radp_b_lambda*_eval")):
        lam = lambda_from_dirname(d.name)
        if lam is None:
            continue
        sweep.append((f"λ={lam:.1f}", lam, load_parses(d)))
    sweep.sort(key=lambda r: (r[1] is None, r[1] or 0.0))
    if args.v1_parses.is_dir():
        sweep.append(("v1 (ref)", None, load_parses(args.v1_parses)))
    # extra systems (e.g., RADP-DPO checkpoint) appended after the canonical sweep
    for spec in args.extra_system:
        if "=" not in spec:
            raise SystemExit(f"--extra_system must be LABEL=DIR, got: {spec!r}")
        label, raw_dir = spec.split("=", 1)
        path = Path(raw_dir)
        if not path.is_dir():
            raise SystemExit(f"extra system dir does not exist: {path}")
        sweep.append((label.strip(), None, load_parses(path)))
    for label, _lam, pages in sweep:
        logger.info("%s: %d/%d eval pages", label, len(pages), len(eval_pages))

    retrievers = [
        BgeM3Retriever(device=args.device, batch_size=32),
        MultilingualE5LargeRetriever(device=args.device, batch_size=32),
        Qwen3EmbeddingRetriever(device=args.device, batch_size=8),
    ]

    # systems[label][chunker] = {(retr, k): np.ndarray(N,)}
    systems: dict[str, dict[str, dict[tuple[str, int], np.ndarray]]] = {}
    rcps_scalar: dict[str, dict[str, float]] = {}

    for label, _lam, pages in sweep:
        systems[label] = {}
        rcps_scalar[label] = {}
        for ck_name in args.chunkers:
            res = compute_rcps(
                eval_qa,
                pages,
                retrievers,
                CHUNKERS[ck_name],
                k_values=(1, 5, 10),
                return_per_qa=True,
            )
            per_rk = {key: np.asarray(v, dtype=float) for key, v in res["per_qa"].items()}
            systems[label][ck_name] = per_rk
            rcps_scalar[label][ck_name] = res["rcps"]
            logger.info(
                "%s [%s]  rcps=%.4f  (n_qa=%d, n_chunks=%d)",
                label, ck_name, res["rcps"], res["meta"]["num_queries"], res["meta"]["num_chunks"],
            )

    # Bootstrap: per chunker, per system.
    control_label = next((l for l, lam, _ in sweep if lam == 0.0), None)
    if control_label is None:
        logger.warning("no λ=0 control found — paired deltas will be skipped")

    by_chunker_ci: dict[str, dict[str, dict[str, Any]]] = {ck: {} for ck in args.chunkers}
    for ck_name in args.chunkers:
        ctrl_per_qa = (
            per_qa_rcps(systems[control_label][ck_name]) if control_label else None
        )
        for label in (l for l, _, _ in sweep):
            per_qa = per_qa_rcps(systems[label][ck_name])
            row: dict[str, Any] = {
                "rcps": rcps_scalar[label][ck_name],
                "rcps_ci": bootstrap_mean(per_qa, n_boot=args.n_boot, alpha=ALPHA, seed=42).to_dict(),
                "n_qa": int(per_qa.shape[0]),
            }
            if ctrl_per_qa is not None and label != control_label:
                delta_ci = bootstrap_paired_delta(
                    per_qa, ctrl_per_qa, n_boot=args.n_boot, alpha=ALPHA, seed=42
                )
                row["vs_lambda0_ci"] = delta_ci.to_dict()
                row["vs_lambda0_pp"] = round(delta_ci.mean * 100, 3)
            by_chunker_ci[ck_name][label] = row

    args.out_ci.parent.mkdir(parents=True, exist_ok=True)
    args.out_ci.write_text(
        json.dumps(
            {
                "meta": {
                    "eval_fold": {"num_pages": len(eval_pages), "num_qa": len(eval_qa)},
                    "retrievers": [r.name for r in retrievers],
                    "k_values": [1, 5, 10],
                    "n_boot": args.n_boot,
                    "ci_alpha": ALPHA,
                    "control": control_label,
                },
                "by_chunker": by_chunker_ci,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    logger.info("wrote %s", args.out_ci)

    # Save per-Q-A arrays for downstream re-analysis.
    flat_per_qa: dict[str, dict[tuple[str, int], np.ndarray]] = {}
    for label, by_ck in systems.items():
        for ck_name, per_rk in by_ck.items():
            flat_per_qa[f"{label}__{ck_name}"] = per_rk
    save_per_qa_arrays(
        args.out_perqa,
        flat_per_qa,
        extra_meta={
            "qa_ids": [qa.qa_id for qa in eval_qa],
            "retrievers": [r.name for r in retrievers],
            "k_values": [1, 5, 10],
            "chunkers": list(args.chunkers),
            "labels": [l for l, _, _ in sweep],
        },
    )
    logger.info("wrote %s", args.out_perqa)

    # Console summary
    print(f"\n{'='*88}\nRADP full λ sweep — bootstrap 95% CI (N={args.n_boot})\n{'='*88}")
    for ck_name in args.chunkers:
        print(f"\n[chunker = {ck_name}]")
        print(f"  {'system':12s} {'RCPS':>8} {'95% CI':>22} {'Δ vs λ=0 (pp)':>22}")
        for label, _lam, _pages in sweep:
            r = by_chunker_ci[ck_name][label]
            ci = r["rcps_ci"]
            ci_str = f"[{ci['lo']:.4f}, {ci['hi']:.4f}]"
            delta_str = "—"
            if "vs_lambda0_ci" in r:
                d = r["vs_lambda0_ci"]
                delta_str = f"{d['mean']*100:+.2f} [{d['lo']*100:+.2f}, {d['hi']*100:+.2f}]"
            print(f"  {label:12s} {r['rcps']:8.4f} {ci_str:>22} {delta_str:>22}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
