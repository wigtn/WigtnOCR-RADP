"""RADP-B λ-sweep evaluation on the held-out eval fold (PHASE_2 §2.2-2.3).

Auto-discovers every `output/parses/radp_b_lambda*_eval/` directory, scores each
on the eval-fold Q-A (RCPS / Hit@k / MRR / nDCG + parse↔GT similarity), and
reports the λ sweep. v1 (the real 2,667p model) is a reference row only.

Gate (memory: radp-b-scaleup-gate): λ=0 is the control; the contrastive effect
is RCPS(λ>0) − RCPS(λ=0) on md_h3. ≥ +0.05 for some λ → scale-up justified.

Usage:
    uv run python scripts/evaluation/eval_radp_b.py
"""

from __future__ import annotations

import argparse
import difflib
import json
import logging
import re
from pathlib import Path
from typing import Any

from wigtnocr_radp.evaluation import (
    BgeM3Retriever,
    MarkdownHeaderChunker,
    ParserNativeChunker,
    compute_rcps,
)
from wigtnocr_radp.evaluation.parser_outputs import load_parser_outputs
from wigtnocr_radp.evaluation.rcps import load_qa_pairs

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("eval_radp_b")

CHUNKERS = {
    "md_h3": MarkdownHeaderChunker(max_level=3),
    "parser_native": ParserNativeChunker(min_chars=30),
}
V1_PARSES = Path("/mnt/data1/work/wigtnOCR-v1/results/kogovdoc/v1_val/predictions")
GATE_THRESHOLD = 0.05  # 5pp RCPS gain — see memory: radp-b-scaleup-gate
GATE_CHUNKER = "md_h3"


def lambda_from_dirname(name: str) -> float | None:
    """radp_b_lambda03_eval → 0.3, lambda10 → 1.0, lambda00 → 0.0."""
    m = re.search(r"lambda(\d)(\d)", name)
    return int(m.group(1)) + int(m.group(2)) / 10 if m else None


def gt_markdown(val_jsonl: Path, page_ids: set[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for i, line in enumerate(val_jsonl.read_text().splitlines()):
        pid = f"val_{i:04d}"
        if pid in page_ids and line.strip():
            out[pid] = json.loads(line)["messages"][2]["content"]
    return out


def mean_parse_similarity(parses: dict[str, str], gt: dict[str, str]) -> float:
    """Mean char-level parse↔GT similarity (difflib ratio) — regression proxy."""
    sims = [
        difflib.SequenceMatcher(None, parses[pid], gt[pid], autojunk=False).ratio()
        for pid in gt if pid in parses
    ]
    return sum(sims) / len(sims) if sims else 0.0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--parses_root", type=Path, default=Path("output/parses"))
    ap.add_argument("--v1_parses", type=Path, default=V1_PARSES)
    ap.add_argument("--qa", type=Path, default=Path("data/KoGovDoc-RAG/qa_pairs_v1.jsonl"))
    ap.add_argument("--split", type=Path, default=Path("data/KoGovDoc-RAG/page_split_v1.json"))
    ap.add_argument("--val_jsonl", type=Path, default=Path("data/KoGovDoc-Bench/val.jsonl"))
    ap.add_argument("--chunkers", nargs="+", default=["md_h3", "parser_native"], choices=tuple(CHUNKERS))
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--out", type=Path, default=Path("output/results/week2_lambda_sweep.json"))
    args = ap.parse_args()

    eval_pages = set(json.loads(args.split.read_text())["eval_pages"])
    eval_qa = [qa for qa in load_qa_pairs(args.qa) if qa.page_id in eval_pages]
    logger.info("eval fold: %d pages, %d Q-A", len(eval_pages), len(eval_qa))

    def load(d: Path) -> dict[str, str]:
        return {p: m for p, m in load_parser_outputs(d, args.val_jsonl).items() if p in eval_pages}

    # Discover λ-sweep parse dirs, ordered by λ; v1 appended as reference.
    sweep: list[tuple[str, float | None, dict[str, str]]] = []
    for d in sorted(args.parses_root.glob("radp_b_lambda*_eval")):
        lam = lambda_from_dirname(d.name)
        if lam is None:
            continue
        sweep.append((f"λ={lam:.1f}", lam, load(d)))
    sweep.sort(key=lambda r: r[1])
    if args.v1_parses.is_dir():
        sweep.append(("v1 (ref)", None, load(args.v1_parses)))
    for label, _lam, pages in sweep:
        logger.info("%s: %d/%d eval pages", label, len(pages), len(eval_pages))

    gt = gt_markdown(args.val_jsonl, eval_pages)
    retriever = BgeM3Retriever(device=args.device, batch_size=32)

    report: dict[str, Any] = {
        "eval_fold": {"num_pages": len(eval_pages), "num_qa": len(eval_qa)},
        "rows": [],
        "by_chunker": {ck: {} for ck in args.chunkers},
    }
    for label, lam, pages in sweep:
        row: dict[str, Any] = {
            "label": label, "lambda": lam,
            "parse_similarity": round(mean_parse_similarity(pages, gt), 4),
        }
        for ck_name in args.chunkers:
            res = compute_rcps(eval_qa, pages, [retriever], CHUNKERS[ck_name], k_values=(1, 5, 10))
            m = res["by_retriever"][retriever.name]
            cell = {"rcps": res["rcps"], "hit@1": m["hit"][1], "hit@5": m["hit"][5],
                    "mrr@10": m["mrr"][10], "ndcg@10": m["ndcg"][10]}
            report["by_chunker"][ck_name][label] = cell
            if ck_name == GATE_CHUNKER:
                row["rcps_md_h3"] = res["rcps"]
        report["rows"].append(row)

    # Gate: best λ>0 vs λ=0 on the gate chunker.
    gck = report["by_chunker"].get(GATE_CHUNKER, {})
    lam0 = next((label for label, lam, _ in sweep if lam == 0.0), None)
    treated = [(label, lam) for label, lam, _ in sweep if lam and lam > 0]
    gate: dict[str, Any] = {"metric": "RCPS", "chunker": GATE_CHUNKER, "threshold_pp": GATE_THRESHOLD}
    if lam0 and treated:
        base = gck[lam0]["rcps"]
        best_label, _ = max(treated, key=lambda t: gck[t[0]]["rcps"])
        delta = gck[best_label]["rcps"] - base
        gate.update({"control": lam0, "best": best_label,
                     "rcps_delta": round(delta, 4), "passed": delta >= GATE_THRESHOLD})
    report["gate"] = gate

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2))

    # Console summary
    print(f"\n{'='*78}\nRADP-B λ sweep — eval fold ({len(eval_pages)} pages, {len(eval_qa)} Q-A)\n{'='*78}")
    for ck_name in args.chunkers:
        rows = report["by_chunker"][ck_name]
        print(f"\n[chunker = {ck_name}]")
        print(f"  {'model':12s} {'RCPS':>8} {'Hit@1':>8} {'Hit@5':>8} {'MRR@10':>8} {'nDCG@10':>8} {'parseSim':>9}")
        for label, _lam, _pages in sweep:
            r = rows[label]
            sim = next(x["parse_similarity"] for x in report["rows"] if x["label"] == label)
            print(f"  {label:12s} {r['rcps']:8.4f} {r['hit@1']:8.4f} {r['hit@5']:8.4f} "
                  f"{r['mrr@10']:8.4f} {r['ndcg@10']:8.4f} {sim:9.4f}")
    g = report["gate"]
    if "passed" in g:
        verdict = "PASS → scale-up justified" if g["passed"] else "FAIL → PHASE_2 fallback"
        print(f"\n{'─'*78}")
        print(f"GATE [{GATE_CHUNKER}]: best {g['best']} vs {g['control']} → "
              f"RCPS Δ = {g['rcps_delta']:+.4f} vs {GATE_THRESHOLD:+.2f}  →  {verdict}")
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
