"""Mechanism analysis for user's C1 dual-proof hypothesis (Hyeongseob 13:35-13:40).

Hypothesis:
  Human-friendly BC/CS ≠ AI-friendly. DPO learns AI-friendly chunking →
  BC/CS DIFFER from v1, but RCPS ≈ v1. This proves C1 from the constructive
  side: there's >1 way to be retrieval-good; DPO finds one that humans
  wouldn't pick.

Measures, per variant on 242p eval fold:
  1. MoC Boundary Clarity (BC) — adjacent-chunk perplexity ratio (Qwen3-VL-2B LM).
  2. Text Normalized Edit Distance (Text NED) — vs GT markdown.
  3. Mean parse length — coarse sanity.
  4. Mean chunk count + chunk size — chunking shape.

Variants: v1, λ=0/0.1/0.3/0.5, DPO-v1/v2/v3/v4, SimPO, seed123/seed999.
"""

from __future__ import annotations

import argparse
import difflib
import json
import logging
import os
from pathlib import Path

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

import numpy as np  # noqa: E402

from wigtnocr_radp.evaluation import ParserNativeChunker  # noqa: E402
from wigtnocr_radp.evaluation.boundary_clarity import PerplexityLM  # noqa: E402
from wigtnocr_radp.evaluation.parser_outputs import build_page_id_index, load_parser_outputs  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] MECH: %(message)s")
log = logging.getLogger("mech")

ROOT = Path("/mnt/data1/work/WigtnOCR-RADP")
V1_PARSES = Path("/mnt/data1/work/wigtnOCR-v1/results/kogovdoc/v1_val/predictions")

VARIANTS = [
    # (label, parses_dir)
    ("v1 (ref)", V1_PARSES),
    ("λ=0.0", ROOT / "output/parses_full/radp_b_lambda00_eval"),
    ("λ=0.1", ROOT / "output/parses_full/radp_b_lambda01_eval"),
    ("λ=0.3", ROOT / "output/parses_full/radp_b_lambda03_eval"),
    ("λ=0.5", ROOT / "output/parses_full/radp_b_lambda05_eval"),
    ("RADP-DPO-v1", ROOT / "output/parses_full/radp_dpo_eval"),
    ("RADP-DPO-v2", ROOT / "output/parses_full/radp_dpo_v2_eval"),
    ("RADP-DPO-v3", ROOT / "output/parses_full/radp_dpo_v3_eval"),
    ("RADP-DPO-v4", ROOT / "output/parses_full/radp_dpo_v4_eval"),
    ("RADP-SimPO", ROOT / "output/parses_full/radp_simpo_eval"),
    ("DPO-v1-seed123", ROOT / "output/parses_full/radp_dpo_seed123_eval"),
    ("DPO-v1-seed999", ROOT / "output/parses_full/radp_dpo_seed999_eval"),
]


def gt_markdown(val_jsonl: Path, page_ids: set[str]) -> dict[str, str]:
    """Read GT markdown (assistant message) from val.jsonl for given page_ids."""
    out: dict[str, str] = {}
    for i, line in enumerate(val_jsonl.read_text().splitlines()):
        pid = f"val_{i:04d}"
        if pid in page_ids and line.strip():
            row = json.loads(line)
            out[pid] = row["messages"][2]["content"]
    return out


def text_ned(a: str, b: str) -> float:
    """Normalized edit distance via difflib (1 - similarity ratio)."""
    return 1.0 - difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


def compute_bc_for_variant(ppl: PerplexityLM, chunker: ParserNativeChunker,
                            parses: dict[str, str]) -> tuple[float, int]:
    """Mean MoC Boundary Clarity over all adjacent chunk pairs."""
    bc_vals: list[float] = []
    for page_id, md in parses.items():
        chunks = chunker.chunk(page_id, md)
        for i in range(len(chunks) - 1):
            bc = ppl.boundary_clarity(chunks[i].text, chunks[i + 1].text)
            if bc is not None and np.isfinite(bc):
                bc_vals.append(bc)
    return (float(np.mean(bc_vals)) if bc_vals else float("nan")), len(bc_vals)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--val_jsonl", type=Path, default=ROOT / "data/KoGovDoc-Bench/val.jsonl")
    ap.add_argument("--split", type=Path, default=ROOT / "data/KoGovDoc-RAG/page_split_v1.json")
    ap.add_argument("--out", type=Path, default=ROOT / "output/results/mechanism_242p.json")
    ap.add_argument("--bc_model", default="Qwen/Qwen3-VL-2B-Instruct")
    ap.add_argument("--skip_bc", action="store_true")
    args = ap.parse_args()

    split = json.loads(args.split.read_text())
    all_pages = set(split["train_pages"]) | set(split["eval_pages"])
    page_stems = build_page_id_index(args.val_jsonl)
    gt = gt_markdown(args.val_jsonl, all_pages)
    log.info("eval pages: %d, GT markdown loaded: %d", len(all_pages), len(gt))

    chunker = ParserNativeChunker(min_chars=30)
    ppl = None if args.skip_bc else PerplexityLM(model_id=args.bc_model)

    report: dict[str, dict] = {}
    for label, parses_dir in VARIANTS:
        log.info("=" * 60)
        log.info("variant: %s  ←  %s", label, parses_dir)
        log.info("=" * 60)
        parses = {p: m for p, m in load_parser_outputs(parses_dir, args.val_jsonl).items()
                  if p in all_pages}
        log.info("  loaded %d parses", len(parses))
        if not parses:
            continue

        # 1. Parse length stats
        lens = [len(m) for m in parses.values()]
        # 2. Chunk shape
        chunk_counts = []
        chunk_lens = []
        for pid, md in parses.items():
            chunks = chunker.chunk(pid, md)
            chunk_counts.append(len(chunks))
            for c in chunks:
                chunk_lens.append(len(c.text))
        # 3. Text NED vs GT (per-page mean)
        neds = []
        for pid, md in parses.items():
            if pid in gt:
                neds.append(text_ned(md, gt[pid]))
        # 4. BC (slow — Qwen3-VL-2B perplexity on each pair)
        bc_mean = None
        bc_n = 0
        if ppl is not None:
            bc_mean, bc_n = compute_bc_for_variant(ppl, chunker, parses)
            log.info("  BC mean=%.4f over %d boundaries", bc_mean, bc_n)

        report[label] = {
            "n_pages": len(parses),
            "parse_len_mean": round(float(np.mean(lens)), 1),
            "parse_len_median": int(np.median(lens)),
            "chunks_per_page_mean": round(float(np.mean(chunk_counts)), 2),
            "chunk_len_mean": round(float(np.mean(chunk_lens)), 1),
            "text_ned_vs_gt_mean": round(float(np.mean(neds)), 4) if neds else None,
            "n_ned_pages": len(neds),
            "bc_mean": round(bc_mean, 4) if bc_mean is not None and np.isfinite(bc_mean) else None,
            "n_bc_boundaries": bc_n,
        }
        log.info("  %s", report[label])

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    log.info("wrote %s", args.out)

    # Markdown comparison table
    md_lines = [
        "# Mechanism Analysis — DPO/SimPO vs v1 (standard metrics)", "",
        "Eval fold: 242 KoGov pages.",
        "",
        "| Variant | n | parse_len (mean) | chunks/page | chunk_len | TextNED ↓ vs GT | BC (MoC) |",
        "|---------|:-:|:---:|:---:|:---:|:---:|:---:|",
    ]
    for label, r in report.items():
        md_lines.append(
            f"| {label} | {r['n_pages']} | {r['parse_len_mean']:.0f} | {r['chunks_per_page_mean']:.2f} "
            f"| {r['chunk_len_mean']:.0f} | {r['text_ned_vs_gt_mean'] if r['text_ned_vs_gt_mean'] else '—'} "
            f"| {r['bc_mean'] if r['bc_mean'] is not None else '—'} |"
        )
    md_lines += ["",
        "**Hypothesis check**: if DPO/SimPO variants show **different BC / TextNED / chunk shape** ",
        "vs v1, while RCPS ≈ v1 (separate eval), this proves C1 dual: there's >1 way to be ",
        "retrieval-good, and DPO finds a non-human-friendly style.",
        ""]
    (args.out.with_suffix(".md")).write_text("\n".join(md_lines))
    log.info("wrote %s", args.out.with_suffix(".md"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
