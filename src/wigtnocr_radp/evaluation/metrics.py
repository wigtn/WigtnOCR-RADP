"""Per-query retrieval metrics: Hit@k, MRR@k, nDCG@k.

All metrics treat relevance as binary at chunk level:
    chunk is relevant iff chunk.page_id == qa.page_id AND qa.answer_span in chunk.text
This is enforced by ChunkRetrievalResult.hit_position().
"""

from __future__ import annotations

import math

from wigtnocr_radp.evaluation.types import ChunkRetrievalResult, QAPair


def hit_at_k(result: ChunkRetrievalResult, qa: QAPair, k: int) -> float:
    """1.0 if a relevant chunk appears in top-k, else 0.0."""
    pos = result.hit_position(qa)
    return 1.0 if (pos is not None and pos <= k) else 0.0


def mrr_at_k(result: ChunkRetrievalResult, qa: QAPair, k: int) -> float:
    """Reciprocal rank of the first relevant chunk in top-k, or 0.0."""
    pos = result.hit_position(qa)
    if pos is None or pos > k:
        return 0.0
    return 1.0 / pos


def ndcg_at_k(result: ChunkRetrievalResult, qa: QAPair, k: int) -> float:
    """Binary-relevance nDCG@k.

    With a single relevant chunk, DCG = 1/log2(rank+1) and IDCG = 1/log2(2) = 1.
    So nDCG@k = 1/log2(rank+1) when rank <= k, else 0.
    """
    pos = result.hit_position(qa)
    if pos is None or pos > k:
        return 0.0
    return 1.0 / math.log2(pos + 1)


def aggregate(values: list[float]) -> float:
    """Mean over queries. Empty list returns 0.0."""
    if not values:
        return 0.0
    return sum(values) / len(values)
