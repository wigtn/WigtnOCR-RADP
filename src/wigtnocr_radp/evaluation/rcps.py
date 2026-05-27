"""RCPS — Retrieval-Conditional Parsing Score.

Definition (RADP_RESEARCH_PROPOSAL.md §3.C2):

    RCPS(parser P, Q-A set D, retrievers R, k_values K)
        = (1/|R||K|) × Σ_{r ∈ R, k ∈ K} MRR@k(r, chunks_P(D), questions_D)

A task-oriented, extrinsic chunking-quality metric: average MRR across multiple
retrievers and cutoffs, so the score is robust to retriever choice (statistical
property explored in §5.5.6 of the proposal).
"""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from wigtnocr_radp.evaluation.chunkers import BaseChunker
from wigtnocr_radp.evaluation.metrics import aggregate, hit_at_k, mrr_at_k, ndcg_at_k
from wigtnocr_radp.evaluation.retrievers import BaseRetriever
from wigtnocr_radp.evaluation.types import QAPair


logger = logging.getLogger("wigtnocr_radp.evaluation.rcps")


def load_qa_pairs(path: str | Path) -> list[QAPair]:
    """Load KoGovDoc-RAG jsonl into QAPair list."""
    p = Path(path)
    pairs: list[QAPair] = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            pairs.append(QAPair.from_dict(json.loads(line)))
    return pairs


def compute_rcps(
    qa_pairs: Sequence[QAPair],
    parser_pages: Mapping[str, str],
    retrievers: Sequence[BaseRetriever],
    chunker: BaseChunker,
    k_values: Sequence[int] = (1, 5, 10),
) -> dict[str, Any]:
    """End-to-end: parser_pages → chunks → retrieve → metrics → RCPS.

    Args:
        qa_pairs: ground-truth Q-A from KoGovDoc-RAG.
        parser_pages: {page_id: parser_markdown_output}. Pages missing from this map
            are skipped (their Q-A will all hit-position=None → 0 score). The
            quality of the parser's output is exactly what RCPS measures.
        retrievers: one or more dense retrievers. RCPS averages across them.
        chunker: chunking strategy (FixedSize / MarkdownHeader / ParserNative).
        k_values: cutoffs (defaults to {1, 5, 10}).

    Returns:
        {
          "rcps": <scalar>,
          "by_retriever": {name: {"hit@k": {k: v}, "mrr@k": {...}, "ndcg@k": {...}}},
          "by_difficulty": {"easy": {"hit@1": v, ...}, ...},  # aggregated across retrievers
          "meta": {chunker, num_queries, num_chunks, num_pages, k_values}
        }
    """
    if not retrievers:
        raise ValueError("at least one retriever is required")
    if not k_values:
        raise ValueError("at least one k value is required")

    chunks = chunker.chunk_corpus(dict(parser_pages))
    logger.info(
        "RCPS: chunker=%s produced %d chunks over %d pages",
        chunker.name,
        len(chunks),
        len(parser_pages),
    )

    if not chunks:
        return {
            "rcps": 0.0,
            "by_retriever": {},
            "by_difficulty": {},
            "meta": {
                "chunker": chunker.name,
                "num_queries": len(qa_pairs),
                "num_chunks": 0,
                "num_pages": len(parser_pages),
                "k_values": list(k_values),
                "retrievers": [r.name for r in retrievers],
            },
        }

    max_k = max(k_values)
    qa_list = list(qa_pairs)

    by_retriever: dict[str, dict[str, dict[int, float]]] = {}
    rcps_terms: list[float] = []
    # per-(retriever, k) -> per-difficulty buckets of mrr scores
    diff_buckets: dict[tuple[str, int, str], list[float]] = {}

    for retr in retrievers:
        logger.info("indexing %d chunks with retriever=%s", len(chunks), retr.name)
        retr.index(chunks)
        results = retr.search(qa_list, top_k=max_k)
        assert len(results) == len(qa_list)

        retr_metrics: dict[str, dict[int, float]] = {"hit": {}, "mrr": {}, "ndcg": {}}
        for k in k_values:
            hits = [hit_at_k(r, qa, k) for r, qa in zip(results, qa_list, strict=True)]
            mrrs = [mrr_at_k(r, qa, k) for r, qa in zip(results, qa_list, strict=True)]
            ndcgs = [ndcg_at_k(r, qa, k) for r, qa in zip(results, qa_list, strict=True)]
            retr_metrics["hit"][k] = aggregate(hits)
            retr_metrics["mrr"][k] = aggregate(mrrs)
            retr_metrics["ndcg"][k] = aggregate(ndcgs)
            rcps_terms.append(retr_metrics["mrr"][k])
            for qa, m in zip(qa_list, mrrs, strict=True):
                diff_buckets.setdefault((retr.name, k, qa.difficulty), []).append(m)

        by_retriever[retr.name] = retr_metrics

    rcps_score = sum(rcps_terms) / len(rcps_terms)

    # Cross-retriever mean per difficulty per k
    by_difficulty: dict[str, dict[str, float]] = {}
    for diff in {qa.difficulty for qa in qa_list}:
        by_difficulty[diff] = {}
        for k in k_values:
            cross = []
            for retr in retrievers:
                vals = diff_buckets.get((retr.name, k, diff), [])
                if vals:
                    cross.append(aggregate(vals))
            by_difficulty[diff][f"mrr@{k}"] = aggregate(cross) if cross else 0.0

    return {
        "rcps": rcps_score,
        "by_retriever": by_retriever,
        "by_difficulty": by_difficulty,
        "meta": {
            "chunker": chunker.name,
            "num_queries": len(qa_list),
            "num_chunks": len(chunks),
            "num_pages": len(parser_pages),
            "k_values": list(k_values),
            "retrievers": [r.name for r in retrievers],
        },
    }
