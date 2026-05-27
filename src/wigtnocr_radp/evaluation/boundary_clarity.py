"""MoC Boundary Clarity — intrinsic chunk-boundary quality metric.

Reference: MoC (Mixtures of Text Chunking Learners), arXiv:2503.09600, ACL 2025.

    BC(q | d) = ppl(q | d) / ppl(q)

where `d` is a chunk and `q` is the immediately following chunk. `ppl(q)` is the
perplexity of `q` alone; `ppl(q | d)` is its perplexity with `d` as left context.

    BC → 1  : q is (nearly) independent of d  → clean, well-separated boundary
    BC → 0  : q strongly depends on d          → blurred boundary

Higher BC = better-separated boundaries (an *intrinsic* judgement). RADP's RCPS
is *extrinsic* (task-grounded retrieval utility); contrasting the two is the
point of the correlation analysis in docs/RADP_RESEARCH_PROPOSAL §3.2.
"""

from __future__ import annotations

import logging
import math

import torch

logger = logging.getLogger("wigtnocr_radp.evaluation.boundary_clarity")


class PerplexityLM:
    """Causal-LM perplexity scorer for Boundary Clarity.

    Uses Qwen3-VL-2B's text path (multilingual, KO/EN; same family as the
    project's parser). The BC metric is inherently relative to this LM — the
    choice is documented but does not affect a cross-parser *correlation*.
    """

    def __init__(
        self,
        model_id: str = "Qwen/Qwen3-VL-2B-Instruct",
        device: str = "cuda",
        max_tokens: int = 1024,
    ) -> None:
        from transformers import AutoTokenizer, Qwen3VLForConditionalGeneration

        logger.info("loading perplexity LM: %s", model_id)
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = (
            Qwen3VLForConditionalGeneration.from_pretrained(model_id, dtype=torch.bfloat16)
            .to(device)
            .eval()
        )
        self.device = device
        self.max_tokens = max_tokens

    @torch.inference_mode()
    def _mean_nll(self, target: str, context: str | None) -> float | None:
        """Mean negative log-likelihood of `target` tokens, optionally given `context`.

        The target is kept whole; an over-long context is truncated from the
        left so the most recent context survives.
        """
        tgt_ids = self.tokenizer(target, add_special_tokens=False).input_ids
        tgt_ids = tgt_ids[: self.max_tokens // 2]
        if not tgt_ids:
            return None

        ctx_ids: list[int] = []
        if context:
            ctx_ids = self.tokenizer(context + "\n", add_special_tokens=False).input_ids
            budget = self.max_tokens - len(tgt_ids)
            ctx_ids = ctx_ids[-budget:] if budget > 0 else []

        ids = ctx_ids + tgt_ids
        input_ids = torch.tensor([ids], device=self.device)
        labels = input_ids.clone()
        labels[0, : len(ctx_ids)] = -100  # score target tokens only
        loss = self.model(input_ids=input_ids, labels=labels).loss
        return float(loss)

    def boundary_clarity(self, prev_chunk: str, next_chunk: str) -> float | None:
        """BC for the boundary between `prev_chunk` (d) and `next_chunk` (q)."""
        l_uncond = self._mean_nll(next_chunk, context=None)
        l_cond = self._mean_nll(next_chunk, context=prev_chunk)
        if l_uncond is None or l_cond is None:
            return None
        # BC = ppl(q|d) / ppl(q) = exp(l_cond) / exp(l_uncond)
        return math.exp(l_cond - l_uncond)
