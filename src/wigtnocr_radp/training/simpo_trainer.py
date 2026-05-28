"""RADP-SimPO trainer — Simple Preference Optimization (Meng et al. 2024).

Differences from DPO:
  - No reference model (single forward pass per pair, halving compute)
  - Length-normalized log-prob (per-token mean) → robust to long-vs-short bias
  - Explicit target margin γ → noisy preference pairs filtered out

Loss:
    r(x, y) = (1/|y|) Σ log π_θ(y_t | y_<t, x)   (per-token mean log-prob)
    L = -log σ(β · (r(x, y_w) - r(x, y_l)) - γ)

Reuses `Qwen3VLDPOCollator` (chosen/rejected stacked along batch dim,
assistant_mask isolates the response tokens to score).
"""

from __future__ import annotations

import logging
from typing import Any

import torch
import torch.nn.functional as F
from transformers import Trainer

logger = logging.getLogger("radp_simpo.trainer")


def _seq_logprob_per_token(
    logits: torch.Tensor,
    input_ids: torch.Tensor,
    response_mask: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Per-sequence (summed log-prob, num response tokens). Shapes (B,), (B,).

    Sums teacher-forced log P(token_t | token_<t) over positions where
    `response_mask[t] == 1`, after the standard 1-step shift. SimPO needs both
    the sum and the count to compute the per-token mean reward.
    """
    shift_logits = logits[:, :-1, :].float()
    shift_labels = input_ids[:, 1:]
    shift_mask = response_mask[:, 1:].float()

    log_probs = F.log_softmax(shift_logits, dim=-1)
    target_log_probs = log_probs.gather(2, shift_labels.unsqueeze(-1)).squeeze(-1)
    summed = (target_log_probs * shift_mask).sum(dim=-1)
    counts = shift_mask.sum(dim=-1)
    return summed, counts


class RadpSimpoTrainer(Trainer):
    """SimPO trainer for parser preference learning.

    Hyperparameters (SimPO paper defaults):
      - beta ≈ 2.0 (much larger than DPO's 0.1 because SimPO removes the
        reference subtraction, so the per-token logp differences are smaller).
      - gamma ≈ 0.5-1.6 (target margin; larger γ → more aggressive separation
        of chosen vs rejected).
    """

    def __init__(
        self,
        *args: Any,
        beta: float = 2.0,
        gamma: float = 1.0,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.beta = beta
        self.gamma = gamma

    def compute_loss(
        self,
        model: torch.nn.Module,
        inputs: dict[str, torch.Tensor],
        return_outputs: bool = False,
        num_items_in_batch: int | None = None,
    ) -> torch.Tensor | tuple[torch.Tensor, dict[str, torch.Tensor]]:
        n_pairs = int(inputs.pop("n_pairs").item()) if "n_pairs" in inputs else inputs["input_ids"].shape[0] // 2
        response_mask = inputs.pop("assistant_mask")
        if response_mask.shape != inputs["input_ids"].shape:
            raise RuntimeError(
                f"assistant_mask shape {response_mask.shape} != input_ids {inputs['input_ids'].shape}"
            )

        # One forward pass covers both chosen and rejected (stacked).
        outputs = model(**{k: v for k, v in inputs.items()
                           if k not in ("assistant_mask", "n_pairs")})
        logp_sum, n_tokens = _seq_logprob_per_token(
            outputs.logits, inputs["input_ids"], response_mask
        )
        # Per-token mean (length-normalized)
        logp_avg = logp_sum / n_tokens.clamp(min=1.0)

        chosen_avg = logp_avg[:n_pairs]
        rejected_avg = logp_avg[n_pairs : 2 * n_pairs]

        # SimPO loss
        margin = self.beta * (chosen_avg - rejected_avg) - self.gamma
        loss = -F.logsigmoid(margin).mean()

        # Metrics (no_grad)
        with torch.no_grad():
            chosen_reward = self.beta * chosen_avg
            rejected_reward = self.beta * rejected_avg
            reward_acc = (chosen_reward > rejected_reward).float().mean()
            reward_margin = (chosen_reward - rejected_reward).mean()
            self.log({
                "simpo/loss": loss.detach().item(),
                "simpo/chosen_reward": chosen_reward.mean().item(),
                "simpo/rejected_reward": rejected_reward.mean().item(),
                "simpo/reward_margin": reward_margin.item(),
                "simpo/reward_accuracy": reward_acc.item(),
                "simpo/logp_chosen_avg": chosen_avg.mean().item(),
                "simpo/logp_rejected_avg": rejected_avg.mean().item(),
                "simpo/chosen_tokens_mean": n_tokens[:n_pairs].mean().item(),
                "simpo/rejected_tokens_mean": n_tokens[n_pairs : 2 * n_pairs].mean().item(),
                "simpo/gamma": self.gamma,
                "simpo/beta": self.beta,
            })

        if return_outputs:
            return loss, {"chosen_logp_avg": chosen_avg, "rejected_logp_avg": rejected_avg}
        return loss
