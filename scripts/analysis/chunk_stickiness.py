"""MoC Chunk Stickiness (CS) — within-chunk cohesion, paired with BC.

While Boundary Clarity (BC) measures *between*-chunk discontinuity:

    BC(prev, next) = ppl(next | prev) / ppl(next)   (high = clean boundary)

Chunk Stickiness (CS) measures *within*-chunk continuity. We split each chunk
into a head and tail, and ask whether the tail is easier to predict given the
head than given no context:

    CS(c) = ppl(c_tail | c_head) / ppl(c_tail)      (low = cohesive chunk)

  - CS << 1 : strong within-chunk dependency → high stickiness (good cohesion)
  - CS ≈ 1  : no within-chunk dependency → bad cohesion

Together BC (high = good) + CS (low = good) form the MoC framework. The user's
13:35-13:40 hypothesis requires BOTH to change in DPO variants compared to v1
to claim "AI-friendly chunking" — currently BC ≈ v1 for all DPO; we measure CS
here to complete the half.

Variants: same 12 systems as mechanism_full.py.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

import numpy as np  # noqa: E402

from wigtnocr_radp.evaluation import ParserNativeChunker  # noqa: E402
from wigtnocr_radp.evaluation.boundary_clarity import PerplexityLM  # noqa: E402
from wigtnocr_radp.evaluation.parser_outputs import load_parser_outputs  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] CS: %(message)s")
log = logging.getLogger("cs")

ROOT = Path("/mnt/data1/work/WigtnOCR-RADP")
V1_PARSES = Path("/mnt/data1/work/wigtnOCR-v1/results/kogovdoc/v1_val/predictions")

VARIANTS = [
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


def split_chunk(text: str, min_each: int = 20) -> tuple[str, str] | None:
    """Split chunk text into (head, tail) by character midpoint, snap to whitespace.
    Returns None if either half too small to be informative.
    """
    n = len(text)
    if n < 2 * min_each:
        return None
    mid = n // 2
    # snap to nearest whitespace within [mid - n//8, mid + n//8]
    span = max(1, n // 8)
    left = mid
    while left > mid - span and text[left] not in " \t\n":
        left -= 1
    right = mid
    while right < mid + span and text[right] not in " \t\n":
        right += 1
    cut = right if (mid - left) > (right - mid) else left
    head, tail = text[:cut].strip(), text[cut:].strip()
    if len(head) < min_each or len(tail) < min_each:
        return None
    return head, tail


def chunk_stickiness(ppl: PerplexityLM, head: str, tail: str) -> float | None:
    """CS = ppl(tail | head) / ppl(tail).  Lower = better cohesion."""
    l_uncond = ppl._mean_nll(tail, context=None)
    l_cond = ppl._mean_nll(tail, context=head)
    if l_uncond is None or l_cond is None:
        return None
    import math
    return math.exp(l_cond - l_uncond)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--val_jsonl", type=Path, default=ROOT / "data/KoGovDoc-Bench/val.jsonl")
    ap.add_argument("--split", type=Path, default=ROOT / "data/KoGovDoc-RAG/page_split_v1.json")
    ap.add_argument("--out", type=Path, default=ROOT / "output/results/cs_242p.json")
    ap.add_argument("--bc_model", default="Qwen/Qwen3-VL-2B-Instruct")
    args = ap.parse_args()

    split = json.loads(args.split.read_text())
    all_pages = set(split["train_pages"]) | set(split["eval_pages"])
    log.info("eval pages: %d", len(all_pages))

    chunker = ParserNativeChunker(min_chars=30)
    ppl = PerplexityLM(model_id=args.bc_model)

    report: dict[str, dict] = {}
    for label, parses_dir in VARIANTS:
        log.info("=" * 60)
        log.info("variant: %s", label)
        log.info("=" * 60)
        parses = {p: m for p, m in load_parser_outputs(parses_dir, args.val_jsonl).items()
                  if p in all_pages}
        log.info("  loaded %d parses", len(parses))
        if not parses:
            continue

        cs_vals: list[float] = []
        n_skipped = 0
        for pid, md in parses.items():
            chunks = chunker.chunk(pid, md)
            for c in chunks:
                pair = split_chunk(c.text)
                if pair is None:
                    n_skipped += 1
                    continue
                head, tail = pair
                v = chunk_stickiness(ppl, head, tail)
                if v is not None and np.isfinite(v):
                    cs_vals.append(v)

        cs_mean = float(np.mean(cs_vals)) if cs_vals else float("nan")
        cs_median = float(np.median(cs_vals)) if cs_vals else float("nan")
        log.info("  CS mean=%.4f median=%.4f  (n=%d chunks scored, %d skipped)",
                 cs_mean, cs_median, len(cs_vals), n_skipped)
        report[label] = {
            "cs_mean": round(cs_mean, 4),
            "cs_median": round(cs_median, 4),
            "n_chunks_scored": len(cs_vals),
            "n_chunks_skipped_too_short": n_skipped,
        }
        # Save incrementally so we don't lose progress on interrupt
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2))

    # Markdown table
    md_lines = [
        "# MoC Chunk Stickiness (CS) — 12 variants × 242p",
        "",
        f"LM: {args.bc_model}. Split chunk → head/tail at character midpoint (snap to whitespace),",
        "score CS = ppl(tail | head) / ppl(tail). **Lower = better cohesion (high stickiness).**",
        "",
        "| Variant | CS mean ↓ | CS median ↓ | n chunks |",
        "|---|---|---|---|",
    ]
    for label, r in report.items():
        md_lines.append(f"| {label} | {r['cs_mean']:.4f} | {r['cs_median']:.4f} | {r['n_chunks_scored']} |")
    md_lines += [
        "",
        "**Hypothesis (user 13:35-13:40)**: DPO/SimPO should produce **different BC AND different CS**",
        "vs v1 to claim 'AI-friendly chunking style'. BC was ≈ v1 for all DPO (mechanism_242p.md).",
        "If CS is also ≈ v1, the AI-friendly-chunking hypothesis is fully reject: parsing differs",
        "in **content** (TextNED, GT-imitation) but not in **chunkability** signature.",
        "",
    ]
    (args.out.with_suffix(".md")).write_text("\n".join(md_lines))
    log.info("wrote %s and %s", args.out, args.out.with_suffix(".md"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
