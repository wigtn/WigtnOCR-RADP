"""RCPS protocol-ablation table — "RCPS != naive MRR" (paper §3.1).

Proves the paper's *asserted* claim that "plain single-embedder, format-sensitive
MRR yields a different, unstable parser ranking" vs full RCPS (3-retriever-averaged
+ format-invariant matching), by ablating the two protocol choices over the KoGov
6-parser grid of Table 1.

The 2x2 ablation (axis 1: retrievers {bge-m3 only | 3-retriever avg};
                   axis 2: relevance {format-SENSITIVE | format-INVARIANT}):

    Row A  "Naive MRR"             bge-m3 only   + format-SENSITIVE
    Row B  "+retriever-averaging"  3-retr avg    + format-SENSITIVE
    Row C  "+format-invariant"     bge-m3 only   + format-INVARIANT
    Row D  "Full RCPS" (== Table1) 3-retr avg    + format-INVARIANT  <- reference

For each row we report the induced parser ranking (best->worst by RCPS-style score)
and the number of pairwise inversions + Kendall-tau vs Row D.

------------------------------------------------------------------------------
WHAT IS STORED vs WHAT MUST BE RE-COMPUTED (see AC#1 in the module docstring):

  * output/baselines/grid_v1_parser_native.json  persists, per parser, the
    PER-RETRIEVER MRR@{1,5,10} SCALARS for all 3 retrievers under the
    format-INVARIANT relevance (normalize_for_match). This is exactly Row D, and
    restricting to bge-m3 yields Row C. -> Rows C & D are pure RE-AGGREGATION
    (no GPU, no model load).

  * Ranked chunk lists per (parser, retriever, query) are NOT persisted anywhere.
    The metric scalars were already collapsed under format-INVARIANT matching.
    Format-SENSITIVE matching (raw `answer_span in chunk.text`) changes which
    ranked chunk is the *first relevant* one, so it cannot be recovered from the
    stored scalars. -> Rows A & B require a RE-INDEX of the parser corpora with
    the embedders (the embeddings/ranking are identical to the invariant run;
    only the relevance judgement differs, so one re-index yields all 4 rows).

The script therefore:
  * ALWAYS computes Rows C & D from the stored grid (re-aggregation).
  * With --reindex, re-indexes the parser corpora and computes ALL FOUR rows
    freshly (format-sensitive A/B AND format-invariant C'/D' for cross-check).
    Row A needs only bge-m3; Row B additionally needs ml-e5-large + Qwen3-Emb-8B.

Usage:
    uv run python scripts/evaluation/rcps_protocol_ablation.py            # C & D only
    uv run python scripts/evaluation/rcps_protocol_ablation.py --reindex  # all 4 rows
    uv run python scripts/evaluation/rcps_protocol_ablation.py --reindex --device cuda
"""

from __future__ import annotations

import argparse
import itertools
import json
import logging
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("rcps_protocol_ablation")

REPO = Path(__file__).resolve().parents[2]
STORED_GRID = REPO / "output/baselines/grid_v1_parser_native.json"
OUT_JSON = REPO / "output/results/rcps_protocol_ablation.json"

# Canonical parser display order/identity (Table 1).
PARSER_ORDER = [
    "Qwen3-VL-30B (teacher)",
    "WigtnOCR-2B (ours, v1)",
    "Qwen3-VL-2B (base)",
    "MinerU",
    "PaddleOCR",
    "Marker",
]
BGE = "bge-m3"
K_VALUES = (1, 5, 10)


# --------------------------------------------------------------------------- #
# Ranking utilities                                                           #
# --------------------------------------------------------------------------- #
def ranking_from_scores(scores: dict[str, float]) -> list[str]:
    """Parsers sorted best->worst by score (stable on ties by PARSER_ORDER)."""
    order_idx = {p: i for i, p in enumerate(PARSER_ORDER)}
    return sorted(scores, key=lambda p: (-scores[p], order_idx.get(p, 99)))


def pairwise_inversions(ref: list[str], other: list[str]) -> tuple[int, list[tuple[str, str]]]:
    """Count discordant pairs (Kendall) between two rankings over the same items."""
    common = [p for p in ref if p in other]
    rank_other = {p: i for i, p in enumerate(other)}
    inv = 0
    pairs: list[tuple[str, str]] = []
    for a, b in itertools.combinations(common, 2):  # a before b in ref
        if rank_other[a] > rank_other[b]:  # order flipped in `other`
            inv += 1
            pairs.append((a, b))
    return inv, pairs


def kendall_tau(ref: list[str], other: list[str]) -> float:
    common = [p for p in ref if p in other]
    n = len(common)
    if n < 2:
        return 1.0
    total = n * (n - 1) // 2
    inv, _ = pairwise_inversions(ref, other)
    concordant = total - inv
    return (concordant - inv) / total


# --------------------------------------------------------------------------- #
# Re-aggregation path (Rows C & D) — from stored per-retriever MRR scalars     #
# --------------------------------------------------------------------------- #
def reaggregate_from_stored() -> dict[str, dict[str, float]]:
    """Return {row: {parser: rcps_score}} for Rows C and D (format-invariant)."""
    if not STORED_GRID.exists():
        raise FileNotFoundError(
            f"stored grid not found: {STORED_GRID} — run baseline_grid.py first"
        )
    grid = json.loads(STORED_GRID.read_text(encoding="utf-8"))
    retrs = grid["config"]["retrievers"]
    assert BGE in retrs, f"bge-m3 missing from stored retrievers {retrs}"

    row_d: dict[str, float] = {}  # 3-retriever avg, format-invariant
    row_c: dict[str, float] = {}  # bge-m3 only,    format-invariant
    for p in grid["parsers"]:
        name = p["name"]
        br = p["by_retriever"]
        # RCPS = mean over (retriever, k) of MRR@k
        terms_all = [br[r]["mrr"][str(k)] for r in retrs for k in K_VALUES]
        terms_bge = [br[BGE]["mrr"][str(k)] for k in K_VALUES]
        row_d[name] = sum(terms_all) / len(terms_all)
        row_c[name] = sum(terms_bge) / len(terms_bge)
        # Sanity: reconstructed Row D must equal the stored scalar RCPS.
        if abs(row_d[name] - p["rcps"]) > 1e-9:
            logger.warning(
                "%s: reconstructed RCPS %.6f != stored %.6f",
                name, row_d[name], p["rcps"],
            )
    return {"C": row_c, "D": row_d}


# --------------------------------------------------------------------------- #
# Re-index path (Rows A & B, and cross-check C/D) — needs embedder models      #
# --------------------------------------------------------------------------- #
def reindex_all_rows(device: str, three_retriever: bool) -> dict[str, dict[str, float]]:
    """Re-index parser corpora and compute all available rows freshly.

    Returns {row: {parser: rcps_score}}. Row B/D need 3 retrievers; if
    three_retriever is False only bge-m3 is loaded and B/D are omitted.

    Format-sensitive vs invariant share the *same* embeddings/ranking — only the
    relevance test differs — so we compute both from one set of ranked results.
    """
    from wigtnocr_radp.evaluation.chunkers import ParserNativeChunker
    from wigtnocr_radp.evaluation.parser_outputs import load_parser_outputs
    from wigtnocr_radp.evaluation.rcps import load_qa_pairs
    from wigtnocr_radp.evaluation.retrievers import (
        BgeM3Retriever,
        MultilingualE5LargeRetriever,
        Qwen3EmbeddingRetriever,
    )
    from wigtnocr_radp.evaluation.types import normalize_for_match

    grid = json.loads(STORED_GRID.read_text(encoding="utf-8"))
    qa_path = REPO / grid["config"]["qa_pairs_path"]
    qa_pairs = load_qa_pairs(qa_path)

    v1_root = Path("/mnt/data1/work/wigtnOCR-v1/results/kogovdoc")
    val_jsonl = REPO / "data/KoGovDoc-Bench/val.jsonl"
    parser_dirs = {
        "Qwen3-VL-30B (teacher)": "30b_val",
        "WigtnOCR-2B (ours, v1)": "v1_val",
        "Qwen3-VL-2B (base)": "2b_base_val",
        "MinerU": "mineru_val",
        "PaddleOCR": "paddleocr_val",
        "Marker": "marker_val",
    }
    chunker = ParserNativeChunker(min_chars=30)

    logger.info("loading retrievers on device=%s (3-retriever=%s)", device, three_retriever)
    retrievers = [BgeM3Retriever(device=device, batch_size=32)]
    if three_retriever:
        retrievers.append(MultilingualE5LargeRetriever(device=device, batch_size=32))
        retrievers.append(Qwen3EmbeddingRetriever(device=device, batch_size=8))

    def relevant(chunk, qa, *, invariant: bool) -> bool:
        if chunk.page_id != qa.page_id:  # page gate (both variants)
            return False
        if invariant:
            return normalize_for_match(qa.answer_span) in normalize_for_match(chunk.text)
        return qa.answer_span in chunk.text  # format-SENSITIVE: raw substring

    def first_rel_rank(ranked, qa, *, invariant: bool) -> int | None:
        for i, (chunk, _) in enumerate(ranked, start=1):
            if relevant(chunk, qa, invariant=invariant):
                return i
        return None

    # row -> parser -> list of MRR@k terms (across retrievers/k)
    acc: dict[str, dict[str, list[float]]] = {r: {} for r in ("A", "B", "C", "D")}

    for name, dname in parser_dirs.items():
        pdir = v1_root / dname / "predictions"
        if not pdir.is_dir():
            logger.warning("%s: parser dir missing (%s), skipping", name, pdir)
            continue
        pages = load_parser_outputs(pdir, val_jsonl)
        chunks = chunker.chunk_corpus(dict(pages))
        logger.info("=== %s: %d pages -> %d chunks ===", name, len(pages), len(chunks))

        sens_terms: dict[str, list[float]] = {}  # retriever -> mrr terms (format-sensitive)
        inv_terms: dict[str, list[float]] = {}
        for retr in retrievers:
            retr.index(chunks)
            results = retr.search(qa_pairs, top_k=max(K_VALUES))
            for invariant, store in ((False, sens_terms), (True, inv_terms)):
                terms: list[float] = []
                for k in K_VALUES:
                    mrrs = []
                    for res, qa in zip(results, qa_pairs, strict=True):
                        pos = first_rel_rank(res.ranked, qa, invariant=invariant)
                        mrrs.append(0.0 if (pos is None or pos > k) else 1.0 / pos)
                    terms.append(sum(mrrs) / len(mrrs))
                store[retr.name] = terms

        # Row A: bge-m3 + sensitive ; Row C: bge-m3 + invariant
        acc["A"][name] = list(sens_terms[BGE])
        acc["C"][name] = list(inv_terms[BGE])
        if three_retriever:
            acc["B"][name] = [t for r in sens_terms for t in sens_terms[r]]
            acc["D"][name] = [t for r in inv_terms for t in inv_terms[r]]

    rows: dict[str, dict[str, float]] = {}
    for row, per_parser in acc.items():
        if not per_parser:
            continue
        rows[row] = {p: sum(ts) / len(ts) for p, ts in per_parser.items()}
    return rows


# --------------------------------------------------------------------------- #
# Reporting                                                                    #
# --------------------------------------------------------------------------- #
ROW_LABELS = {
    "A": "Naive MRR (bge-m3, format-SENSITIVE)",
    "B": "+retriever-averaging (3-retr, format-SENSITIVE)",
    "C": "+format-invariant only (bge-m3, format-INVARIANT)",
    "D": "Full RCPS (3-retr, format-INVARIANT) [reference]",
}
ROW_SOURCE = {
    "A": "re-index (format-sensitive; needs embedder)",
    "B": "re-index (format-sensitive; needs 3 embedders)",
    "C": "re-aggregation of stored MRR scalars (no GPU)",
    "D": "re-aggregation of stored MRR scalars (no GPU)",
}
SHORT = {
    "Qwen3-VL-30B (teacher)": "Qwen3-VL-30B",
    "WigtnOCR-2B (ours, v1)": "WigtnOCR-2B",
    "Qwen3-VL-2B (base)": "Qwen3-VL-2B",
    "MinerU": "MinerU",
    "PaddleOCR": "PaddleOCR",
    "Marker": "Marker",
}


def build_report(rows: dict[str, dict[str, float]]) -> dict[str, Any]:
    assert "D" in rows, "Row D (reference) must be present"
    ref_rank = ranking_from_scores(rows["D"])
    out_rows = []
    any_inversion = False
    for r in ("A", "B", "C", "D"):
        if r not in rows:
            out_rows.append({"row": r, "label": ROW_LABELS[r], "status": "BLOCKED",
                             "source": ROW_SOURCE[r], "reason": "requires re-index (run --reindex)"})
            continue
        rank = ranking_from_scores(rows[r])
        inv, pairs = pairwise_inversions(ref_rank, rank)
        tau = kendall_tau(ref_rank, rank)
        if r != "D" and inv > 0:
            any_inversion = True
        out_rows.append({
            "row": r, "label": ROW_LABELS[r], "status": "computed", "source": ROW_SOURCE[r],
            "scores": {SHORT[p]: round(rows[r][p], 4) for p in rows[r]},
            "ranking": [SHORT[p] for p in rank],
            "inversions_vs_D": inv,
            "inverted_pairs": [[SHORT[a], SHORT[b]] for a, b in pairs],
            "kendall_tau_vs_D": round(tau, 4),
        })
    return {
        "reference_ranking_D": [SHORT[p] for p in ref_rank],
        "rows": out_rows,
        "success_criterion_met": any_inversion,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = ["## RCPS Protocol-Ablation — KoGov 6-parser grid (Table 1)", ""]
    lines.append("| Row | Protocol | Source | Ranking (best->worst) | Inv vs D | tau vs D |")
    lines.append("|:---:|----------|--------|-----------------------|:--------:|:--------:|")
    for r in report["rows"]:
        if r["status"] == "BLOCKED":
            lines.append(f"| {r['row']} | {r['label']} | {r['source']} | _BLOCKED — {r['reason']}_ | — | — |")
            continue
        ranking = " > ".join(r["ranking"])
        lines.append(
            f"| {r['row']} | {r['label']} | {r['source']} | {ranking} "
            f"| {r['inversions_vs_D']} | {r['kendall_tau_vs_D']} |"
        )
    lines.append("")
    verdict = "MET" if report["success_criterion_met"] else "NOT met"
    lines.append(f"**Success criterion (>=1 inversion when a protocol choice is stripped): {verdict}**")
    # detail inverted pairs
    for r in report["rows"]:
        if r.get("inverted_pairs"):
            pairs = ", ".join(f"{a}<->{b}" for a, b in r["inverted_pairs"])
            lines.append(f"- Row {r['row']} inversions vs D: {pairs}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reindex", action="store_true",
                    help="re-index parser corpora to compute format-sensitive rows A & B")
    ap.add_argument("--device", default="cpu", help="cpu | cuda | cuda:N (re-index only)")
    ap.add_argument("--single-retriever", action="store_true",
                    help="re-index with bge-m3 only (computes A & C; B & D from stored)")
    args = ap.parse_args()

    rows = reaggregate_from_stored()  # C & D always
    notes: list[str] = [
        "Rows C & D from re-aggregation of stored per-retriever MRR scalars "
        f"({STORED_GRID.relative_to(REPO)}); no GPU.",
    ]

    if args.reindex:
        three = not args.single_retriever
        logger.info("re-indexing for format-sensitive rows (device=%s, 3-retriever=%s)",
                    args.device, three)
        fresh = reindex_all_rows(args.device, three_retriever=three)
        # Prefer freshly re-indexed rows where available; keep stored C/D as fallback.
        for r, scores in fresh.items():
            rows[r] = scores
        notes.append(
            f"Rows A{'/B' if three else ''} (and re-indexed C{'/D' if three else ''}) "
            f"computed by re-index on device={args.device}."
        )
    else:
        notes.append(
            "Rows A & B BLOCKED without --reindex: format-SENSITIVE relevance needs "
            "ranked chunk lists, which are not persisted (only MRR scalars are). "
            "Run with --reindex (needs the embedder models; bge-m3 for A, "
            "+ml-e5-large +Qwen3-Embedding-8B for B)."
        )

    report = build_report(rows)
    report["notes"] = notes
    report["raw_scores"] = {r: {SHORT.get(p, p): round(v, 6) for p, v in rows[r].items()}
                            for r in rows}

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("wrote %s", OUT_JSON)

    print()
    print(render_markdown(report))
    print()
    print("Notes:")
    for n in notes:
        print(" -", n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
