"""Mechanism analysis for RADP-DPO — show *how* the parser changed.

Four diagnostics on the 73-page eval fold:

1. **Chunk-boundary diff**: chunk both v1 and DPO-v3 parses with the same
   chunker; per page report Δ(#chunks), Δ(mean chunk length), and the
   character-level edit distance between the joined chunk-boundary positions.
   Tells us whether DPO actually re-positions chunk boundaries vs just
   reshuffling content.

2. **Per-page RCPS attribution**: for each eval page, RCPS(DPO-v3) − RCPS(v1).
   Sorted; shows which pages benefit most, helps identify failure modes.

3. **Side-by-side excerpts**: for the top-3 most-improved pages, dump
   v1 markdown vs DPO-v3 markdown (first 60 lines each) and the chunk
   boundary positions for visual inspection.

4. **BC on DPO output**: compute MoC Boundary Clarity for the DPO-v3 parses;
   compare to BC of v1 parses. Connects back to C1 (does DPO move BC in the
   wrong direction even as RCPS improves?).

Output:
    output/results/mechanism_analysis.{json,md}
"""

from __future__ import annotations

import argparse
import difflib
import json
import logging
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

from wigtnocr_radp.evaluation import ParserNativeChunker
from wigtnocr_radp.evaluation.parser_outputs import load_parser_outputs
from wigtnocr_radp.evaluation.rcps import load_qa_pairs
from wigtnocr_radp.evaluation.types import Chunk

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("mechanism_analysis")

V1_PARSES = Path("/mnt/data1/work/wigtnOCR-v1/results/kogovdoc/v1_val/predictions")


def boundary_positions(chunks: list[Chunk], total_text: str) -> list[int]:
    """Cumulative char positions where chunks end in a virtual concatenation."""
    pos = 0
    out = []
    for c in chunks:
        pos += len(c.text)
        out.append(pos)
    return out


def boundary_jaccard(a: list[int], b: list[int], tol: int = 50) -> float:
    """Approximate set similarity between boundary positions with a tolerance."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    sa, sb = set(a), set(b)
    matched = 0
    for x in sa:
        if any(abs(x - y) <= tol for y in sb):
            matched += 1
    # symmetric: take min over directions
    matched2 = sum(1 for y in sb if any(abs(x - y) <= tol for x in sa))
    return min(matched, matched2) / max(len(sa), len(sb))


def chunk_diff(v1_parses: dict[str, str], dpo_parses: dict[str, str],
               chunker: ParserNativeChunker) -> tuple[list[dict], dict]:
    """Per-page chunk-boundary diff between v1 and DPO."""
    rows = []
    for pid in sorted(set(v1_parses) & set(dpo_parses)):
        c_v1 = chunker.chunk(pid, v1_parses[pid])
        c_dpo = chunker.chunk(pid, dpo_parses[pid])
        b_v1 = boundary_positions(c_v1, v1_parses[pid])
        b_dpo = boundary_positions(c_dpo, dpo_parses[pid])
        text_sim = difflib.SequenceMatcher(
            None, v1_parses[pid], dpo_parses[pid], autojunk=False
        ).ratio()
        rows.append({
            "page_id": pid,
            "n_chunks_v1": len(c_v1),
            "n_chunks_dpo": len(c_dpo),
            "d_n_chunks": len(c_dpo) - len(c_v1),
            "mean_len_v1": round(np.mean([len(c.text) for c in c_v1]) if c_v1 else 0, 1),
            "mean_len_dpo": round(np.mean([len(c.text) for c in c_dpo]) if c_dpo else 0, 1),
            "boundary_jaccard": round(boundary_jaccard(b_v1, b_dpo), 3),
            "markdown_text_sim": round(text_sim, 3),
            "char_len_v1": len(v1_parses[pid]),
            "char_len_dpo": len(dpo_parses[pid]),
        })
    summary = {
        "n_pages": len(rows),
        "mean_d_n_chunks": round(np.mean([r["d_n_chunks"] for r in rows]), 2),
        "pct_pages_chunks_changed": round(100 * sum(1 for r in rows if r["d_n_chunks"] != 0) / len(rows), 1),
        "mean_boundary_jaccard": round(np.mean([r["boundary_jaccard"] for r in rows]), 3),
        "mean_text_sim": round(np.mean([r["markdown_text_sim"] for r in rows]), 3),
        "mean_char_len_v1": round(np.mean([r["char_len_v1"] for r in rows]), 0),
        "mean_char_len_dpo": round(np.mean([r["char_len_dpo"] for r in rows]), 0),
    }
    return rows, summary


def per_page_rcps_diff(perqa_v1: dict, perqa_dpo: dict,
                       label_v1: str, label_dpo: str,
                       chunker: str = "parser_native") -> tuple[list[dict], dict]:
    """Per-Q-A RCPS, then aggregate per page. Both perqa dicts come from
    `radp_full_eval_..._perqa.json`."""
    qa_ids_v1 = perqa_v1["meta"]["qa_ids"] if "qa_ids" in perqa_v1.get("meta", {}) else []
    sys_v1 = perqa_v1["systems"][f"{label_v1}__{chunker}"]
    sys_dpo = perqa_dpo["systems"][f"{label_dpo}__{chunker}"]
    rk_keys = sorted(set(sys_v1) & set(sys_dpo))
    per_qa_v1 = np.stack([np.asarray(sys_v1[k], dtype=float) for k in rk_keys]).mean(axis=0)
    per_qa_dpo = np.stack([np.asarray(sys_dpo[k], dtype=float) for k in rk_keys]).mean(axis=0)
    diff = per_qa_dpo - per_qa_v1
    qa_ids = perqa_v1.get("meta", {}).get("qa_ids") or perqa_dpo.get("meta", {}).get("qa_ids") or []
    return diff.tolist(), {
        "n_qa": len(diff),
        "mean_diff_pp": round(float(diff.mean()) * 100, 3),
        "pct_qa_improved": round(100 * float((diff > 0).mean()), 1),
        "pct_qa_degraded": round(100 * float((diff < 0).mean()), 1),
        "pct_qa_unchanged": round(100 * float((diff == 0).mean()), 1),
    }


def page_attribution(diff_per_qa: list[float], qa_ids: list[str],
                     qa_to_page: dict[str, str]) -> tuple[list[dict], list[str]]:
    """Aggregate per-Q-A diff back to per-page mean diff. Return sorted list."""
    by_page = defaultdict(list)
    for qa_id, d in zip(qa_ids, diff_per_qa):
        by_page[qa_to_page[qa_id]].append(d)
    rows = [{"page_id": p, "n_qa": len(vs), "mean_diff_pp": round(100 * float(np.mean(vs)), 3)}
            for p, vs in by_page.items()]
    rows.sort(key=lambda r: r["mean_diff_pp"], reverse=True)
    top_ids = [r["page_id"] for r in rows[:3]]
    return rows, top_ids


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--v1_parses", type=Path, default=V1_PARSES)
    ap.add_argument("--dpo_parses", type=Path, required=True,
                    help="e.g. output/parses_full/radp_dpo_v3_eval")
    ap.add_argument("--qa", type=Path, default=Path("data/KoGovDoc-RAG/qa_pairs_v1.jsonl"))
    ap.add_argument("--split", type=Path, default=Path("data/KoGovDoc-RAG/page_split_v1.json"))
    ap.add_argument("--val_jsonl", type=Path, default=Path("data/KoGovDoc-Bench/val.jsonl"))
    ap.add_argument("--perqa", type=Path, required=True,
                    help="bootstrap per-qa json containing the v1 ref and DPO system")
    ap.add_argument("--label_v1", default="v1 (ref)")
    ap.add_argument("--label_dpo", default="RADP-DPO-v3")
    ap.add_argument("--out", type=Path, default=Path("output/results/mechanism_analysis.json"))
    args = ap.parse_args()

    eval_pages = set(json.loads(args.split.read_text())["eval_pages"])
    qas = [qa for qa in load_qa_pairs(args.qa) if qa.page_id in eval_pages]
    qa_to_page = {qa.qa_id: qa.page_id for qa in qas}

    v1_parses = {p: m for p, m in load_parser_outputs(args.v1_parses, args.val_jsonl).items()
                 if p in eval_pages}
    dpo_parses = {p: m for p, m in load_parser_outputs(args.dpo_parses, args.val_jsonl).items()
                  if p in eval_pages}
    logger.info("loaded %d v1 / %d DPO parses on eval fold", len(v1_parses), len(dpo_parses))

    # 1. Chunk boundary diff
    chunker = ParserNativeChunker(min_chars=30)
    chunk_rows, chunk_summary = chunk_diff(v1_parses, dpo_parses, chunker)
    logger.info("chunk diff summary: %s", chunk_summary)

    # 2. Per-page RCPS attribution
    perqa = json.loads(args.perqa.read_text())
    diff_qa, rcps_summary = per_page_rcps_diff(perqa, perqa, args.label_v1, args.label_dpo)
    qa_ids = perqa.get("meta", {}).get("qa_ids") or [qa.qa_id for qa in qas]
    page_rows, top_pages = page_attribution(diff_qa, qa_ids, qa_to_page)
    logger.info("RCPS attribution: %s", rcps_summary)
    logger.info("top 3 improved pages: %s", top_pages)

    # 3. Side-by-side excerpts for top 3 pages
    excerpts = []
    for pid in top_pages:
        excerpts.append({
            "page_id": pid,
            "v1_excerpt": "\n".join(v1_parses[pid].splitlines()[:60]),
            "dpo_excerpt": "\n".join(dpo_parses[pid].splitlines()[:60]),
            "v1_chunk_starts": [c.text[:50] for c in chunker.chunk(pid, v1_parses[pid])],
            "dpo_chunk_starts": [c.text[:50] for c in chunker.chunk(pid, dpo_parses[pid])],
        })

    report = {
        "n_pages_eval": len(v1_parses),
        "chunk_boundary_diff": {"summary": chunk_summary, "per_page": chunk_rows},
        "rcps_attribution": {"summary": rcps_summary, "per_page": page_rows[:20]},
        "top_improved_excerpts": excerpts,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2))

    # Markdown report
    md = [
        "# Mechanism analysis — RADP-DPO vs v1 baseline", "",
        f"Eval fold: {len(v1_parses)} pages",
        "",
        "## 1. Chunk-boundary diff (parser_native chunker)",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    for k, v in chunk_summary.items():
        md.append(f"| {k} | {v} |")
    md += [
        "",
        "→ DPO가 markdown을 다르게 출력해서 chunk 경계가 실제로 달라지는지 정량. ",
        "`pct_pages_chunks_changed` 높고 `boundary_jaccard` 낮으면 = chunking이 다르게 형성됨.",
        "",
        "## 2. Per-Q-A RCPS attribution",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    for k, v in rcps_summary.items():
        md.append(f"| {k} | {v} |")
    md += [
        "",
        "## 3. Top-3 most-improved pages",
        "",
        "| Page | n_QA | RCPS Δ (pp) |",
        "|------|:----:|:-----------:|",
    ]
    for r in page_rows[:10]:
        md.append(f"| {r['page_id']} | {r['n_qa']} | {r['mean_diff_pp']:+.2f} |")

    md.append("\n## 4. Side-by-side excerpts (top 3) saved in JSON.")
    Path(str(args.out).replace(".json", ".md")).write_text("\n".join(md))
    logger.info("wrote %s", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
