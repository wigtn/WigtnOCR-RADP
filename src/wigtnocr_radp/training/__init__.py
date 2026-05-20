"""RADP-B training — parser fine-tuning with chunk-boundary contrastive auxiliary loss.

Contrastive primitives (`contrastive.py`):
    ContrastiveProjectionHead: parser hidden_state → contrastive space (BGE-M3 dim).
    info_nce_loss: InfoNCE over (anchor, positives, negatives).
    BgeM3EmbeddingCache: pre-computed BGE-M3 chunk embeddings keyed by page_id.
    SamplingStrategy: produces (positives, negatives) for each batch sample.
    RadpBLoss: composes L_total = L_parse + λ · L_contrast.

Training pipeline (HF-native — transformers + peft):
    RadpBDataset / Qwen3VLContrastiveCollator (`data.py`): per-Q-A examples.
    RadpBTrainer / attach_radp_loss (`trainer.py`): Trainer with the aux loss.

Reference: docs/RADP_RESEARCH_PROPOSAL.md §4.1 (with design decision A —
projection-head variant for stable training).
"""

from wigtnocr_radp.training.contrastive import (
    BgeM3EmbeddingCache,
    ContrastiveProjectionHead,
    RadpBLoss,
    SamplingStrategy,
    info_nce_loss,
)
from wigtnocr_radp.training.data import (
    Qwen3VLContrastiveCollator,
    RadpBDataset,
    RadpBExample,
    remap_image_path,
)
from wigtnocr_radp.training.trainer import RadpBTrainer, attach_radp_loss

__all__ = [
    "BgeM3EmbeddingCache",
    "ContrastiveProjectionHead",
    "Qwen3VLContrastiveCollator",
    "RadpBDataset",
    "RadpBExample",
    "RadpBLoss",
    "RadpBTrainer",
    "SamplingStrategy",
    "attach_radp_loss",
    "info_nce_loss",
    "remap_image_path",
]
