"""RADP-B training — parser fine-tuning with chunk-boundary contrastive auxiliary loss.

Public API:
    ContrastiveProjectionHead: parser hidden_state → contrastive space (BGE-M3 dim).
    info_nce_loss: InfoNCE over (anchor, positives, negatives).
    BgeM3EmbeddingCache: pre-computed BGE-M3 chunk embeddings keyed by page_id.
    SamplingStrategy: produces (positives, negatives) for each batch sample.
    RadpBLoss: composes L_total = L_parse + λ · L_contrast.

Reference: docs/RADP_RESEARCH_PROPOSAL.md §4.1 (with design decision A —
projection-head variant for stable training; see PROMPT_v3 of training notes).
"""

from wigtnocr_radp.training.contrastive import (
    BgeM3EmbeddingCache,
    ContrastiveProjectionHead,
    RadpBLoss,
    SamplingStrategy,
    info_nce_loss,
)

__all__ = [
    "BgeM3EmbeddingCache",
    "ContrastiveProjectionHead",
    "RadpBLoss",
    "SamplingStrategy",
    "info_nce_loss",
]
