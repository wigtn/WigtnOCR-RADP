"""RADP-B trainer: HF `Trainer` with the chunk-boundary contrastive aux loss.

`RadpBTrainer` overrides `compute_loss` to add `λ · L_contrast` on top of the
parser's standard cross-entropy `L_parse`:

    1. Forward the VLM, capturing the final hidden layer via a forward hook on
       the language model's output norm (cheaper than `output_hidden_states=True`,
       which would materialise every layer and OOM on full-page images).
    2. Mean-pool that hidden layer over the assistant (label) tokens.
    3. Project the pooled vector into BGE-M3 space (`ContrastiveProjectionHead`).
    4. InfoNCE against the pre-computed positive / negative chunk embeddings
       (`BgeM3EmbeddingCache` + `SamplingStrategy`).

The projection head must be registered as a submodule of `model` *before*
constructing the trainer (see `attach_radp_loss`) so the optimizer picks up its
parameters. ms-swift is intentionally not used — see docs/RADP_RESEARCH_PROPOSAL
§4.1 and the 2026-05-20 framework decision (HF-native stack).
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import torch
from torch import nn
from transformers import Trainer

from wigtnocr_radp.training.contrastive import (
    BgeM3EmbeddingCache,
    RadpBLoss,
    SamplingStrategy,
    mean_pool_hidden,
    mean_pool_span,
)

logger = logging.getLogger("radp_b.trainer")

_RADP_LOSS_ATTR = "radp_b_loss"


def attach_radp_loss(model: nn.Module, radp_loss: RadpBLoss) -> RadpBLoss:
    """Register `radp_loss` (which owns the projection head) as a model submodule.

    This makes the projection-head parameters visible to `Trainer`'s optimizer
    and moves them with the model in `.to(device)`. The PEFT adapter and this
    head are saved separately (see `scripts/training/train_radp_b.py`).
    """
    model.add_module(_RADP_LOSS_ATTR, radp_loss)
    return radp_loss


class RadpBTrainer(Trainer):
    """`Trainer` variant that adds the RADP-B contrastive auxiliary loss."""

    def __init__(
        self,
        *args: Any,
        train_cache: BgeM3EmbeddingCache,
        eval_cache: BgeM3EmbeddingCache,
        sampler: SamplingStrategy,
        radp_loss: RadpBLoss,
        hidden_module: nn.Module,
        contrastive_seed: int = 42,
        anchor_mode: str = "full",
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        # qa_ids are fold-disjoint, so the contrastive lookups must use the
        # cache matching the current fold (train cache has no eval qa_ids).
        self.train_cache = train_cache
        self.eval_cache = eval_cache
        self.sampler = sampler
        self.radp_loss = radp_loss
        self._rng = np.random.default_rng(contrastive_seed)
        # "full" — pool over the entire assistant region (decision-A, pilot).
        # "per_chunk" — pool only over the answer-chunk token span (samples
        # with missing localisation fall back to full pooling).
        if anchor_mode not in ("full", "per_chunk"):
            raise ValueError(f"anchor_mode must be 'full' or 'per_chunk', got {anchor_mode!r}")
        self.anchor_mode = anchor_mode
        # Capture the final hidden layer without `output_hidden_states=True`.
        self._captured_hidden: torch.Tensor | None = None
        hidden_module.register_forward_hook(self._capture_hook)
        # Running aggregates flushed in `log()` so logged values average over
        # the whole logging window (and over grad-accum sub-steps).
        self._parse_sum = 0.0
        self._contrast_sum = 0.0
        self._loss_count = 0

    def _capture_hook(self, module: nn.Module, inputs: Any, output: Any) -> None:
        self._captured_hidden = output[0] if isinstance(output, tuple) else output

    def compute_loss(  # type: ignore[override]
        self,
        model: nn.Module,
        inputs: dict[str, Any],
        return_outputs: bool = False,
        **kwargs: Any,
    ) -> torch.Tensor | tuple[torch.Tensor, Any]:
        qa_ids = inputs.pop("qa_ids")
        page_ids = inputs.pop("page_ids")
        chunk_spans = inputs.pop("chunk_spans", None)

        self._captured_hidden = None
        outputs = model(**inputs)
        parse_loss = outputs.loss
        last_hidden = self._captured_hidden  # (B, T, D), via forward hook
        if last_hidden is None:
            raise RuntimeError("hidden-state hook did not fire — check hidden_module path")

        label_mask = (inputs["labels"] != -100).to(last_hidden.dtype)
        if self.anchor_mode == "per_chunk" and chunk_spans is not None:
            pooled = mean_pool_span(last_hidden, chunk_spans, label_mask)
        else:
            pooled = mean_pool_hidden(last_hidden, label_mask)  # (B, D)

        cache = self.train_cache if model.training else self.eval_cache
        pos_np, neg_np = self.sampler.sample(cache, qa_ids, page_ids, self._rng)
        pos = torch.from_numpy(pos_np).to(device=pooled.device, dtype=torch.float32)
        neg = torch.from_numpy(neg_np).to(device=pooled.device, dtype=torch.float32)

        # Contrastive math in fp32 — BGE-M3 cache is fp32 and InfoNCE is
        # numerically happier outside the bf16 autocast region.
        with torch.autocast(device_type=pooled.device.type, enabled=False):
            total, parse_d, contrast_d = self.radp_loss(
                pooled_hidden=pooled.float(),
                positive_emb=pos,
                negative_embs=neg,
                parse_loss=parse_loss.float(),
            )

        if model.training:  # keep the logged train averages free of eval steps
            self._parse_sum += float(parse_d)
            self._contrast_sum += float(contrast_d)
            self._loss_count += 1

        return (total, outputs) if return_outputs else total

    def log(self, logs: dict[str, float], *args: Any, **kwargs: Any) -> None:
        """Inject averaged L_parse / L_contrast into each logging step."""
        if self._loss_count:
            logs["loss_parse"] = self._parse_sum / self._loss_count
            logs["loss_contrast"] = self._contrast_sum / self._loss_count
            self._parse_sum = self._contrast_sum = 0.0
            self._loss_count = 0
        super().log(logs, *args, **kwargs)
