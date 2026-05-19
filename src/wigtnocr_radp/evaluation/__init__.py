"""RCPS evaluation — Retrieval-Conditional Parsing Score.

Public API:
    QAPair, Chunk, ChunkRetrievalResult: core types.
    hit_at_k, mrr_at_k, ndcg_at_k: per-query retrieval metrics.
    BaseChunker, FixedSizeChunker, MarkdownHeaderChunker, ParserNativeChunker.
    BaseRetriever, BgeM3Retriever.
    compute_rcps: end-to-end evaluation orchestrator.

Reference: docs/RADP_RESEARCH_PROPOSAL.md §3.C2, §5.4
"""

from wigtnocr_radp.evaluation.chunkers import (
    BaseChunker,
    FixedSizeChunker,
    MarkdownHeaderChunker,
    ParserNativeChunker,
)
from wigtnocr_radp.evaluation.metrics import hit_at_k, mrr_at_k, ndcg_at_k
from wigtnocr_radp.evaluation.rcps import compute_rcps
from wigtnocr_radp.evaluation.retrievers import BaseRetriever, BgeM3Retriever
from wigtnocr_radp.evaluation.types import Chunk, ChunkRetrievalResult, QAPair

__all__ = [
    "BaseChunker",
    "BaseRetriever",
    "BgeM3Retriever",
    "Chunk",
    "ChunkRetrievalResult",
    "FixedSizeChunker",
    "MarkdownHeaderChunker",
    "ParserNativeChunker",
    "QAPair",
    "compute_rcps",
    "hit_at_k",
    "mrr_at_k",
    "ndcg_at_k",
]
