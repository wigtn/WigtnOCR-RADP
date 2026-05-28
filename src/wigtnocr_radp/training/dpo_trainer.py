"""RADP-DPO trainer — direct preference optimisation on the parser's discrete output.

Loss (per pair, with adapter on = π, adapter off = π_ref):

    ℓ = -log σ( β · ((logπ(y_w|x) - logπ_ref(y_w|x)) - (logπ(y_l|x) - logπ_ref(y_l|x))) )

We exploit the PEFT-DPO trick: the trainable model IS the reference model with
the LoRA adapter disabled, so the same base weights serve both roles. No extra
GPU memory for a copy of the reference model.

Inputs come from `Qwen3VLDPOCollator`: chosen and rejected are stacked
along the batch dim (chosen rows [0..n], rejected rows [n..2n]). The
`assistant_mask` selects only response tokens; the parsing prompt and image
positions are masked out of the log-likelihood.
"""

from __future__ import annotations

import logging
from typing import Any

import torch
import torch.nn.functional as F
from transformers import Trainer

logger = logging.getLogger("radp_dpo.trainer")


def _sequence_logprob(
    logits: torch.Tensor,
    input_ids: torch.Tensor,
    response_mask: torch.Tensor,
) -> torch.Tensor:
    """Sum of teacher-forced log P(token_t | token_<t) over positions where
    `response_mask[t] == 1`. Returns shape (B,).

    The mask is applied to the *target* (next-token) positions. logits[t]
    predicts the token at position t+1, so we shift both labels and mask by 1.
    """
    shift_logits = logits[:, :-1, :].float()  # cast for stable log-softmax
    shift_labels = input_ids[:, 1:]
    shift_mask = response_mask[:, 1:].float()

    log_probs = F.log_softmax(shift_logits, dim=-1)
    # gather along vocab to get log P(label) at each position
    target_log_probs = log_probs.gather(2, shift_labels.unsqueeze(-1)).squeeze(-1)
    return (target_log_probs * shift_mask).sum(dim=-1)


class RadpDPOTrainer(Trainer):
    """HF Trainer subclass implementing DPO with a LoRA-toggled reference."""

    def __init__(
        self,
        *args: Any,
        beta: float = 0.1,
        label_smoothing: float = 0.0,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.beta = beta
        self.label_smoothing = label_smoothing

    def _forward_logprobs(
        self,
        model: torch.nn.Module,
        inputs: dict[str, torch.Tensor],
        response_mask: torch.Tensor,
    ) -> torch.Tensor:
        """One forward over the full (2n, T) batch → log P(response | image+prompt)
        per sequence. Returns shape (2n,)."""
        outputs = model(**{k: v for k, v in inputs.items()
                           if k not in ("assistant_mask", "n_pairs")})
        return _sequence_logprob(outputs.logits, inputs["input_ids"], response_mask)

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

        # π (LoRA adapter ON)
        logp_pi = self._forward_logprobs(model, inputs, response_mask)
        logp_pi_chosen = logp_pi[:n_pairs]
        logp_pi_rejected = logp_pi[n_pairs : 2 * n_pairs]

        # π_ref (LoRA adapter OFF — same base weights, no extra memory)
        with torch.no_grad(), model.disable_adapter():
            logp_ref = self._forward_logprobs(model, inputs, response_mask)
        logp_ref_chosen = logp_ref[:n_pairs]
        logp_ref_rejected = logp_ref[n_pairs : 2 * n_pairs]

        # DPO loss
        pi_diff = logp_pi_chosen - logp_pi_rejected
        ref_diff = logp_ref_chosen - logp_ref_rejected
        margin = self.beta * (pi_diff - ref_diff)
        if self.label_smoothing > 0.0:
            # Conservative DPO (Mitchell et al.) - small label smoothing
            loss = -(
                (1 - self.label_smoothing) * F.logsigmoid(margin)
                + self.label_smoothing * F.logsigmoid(-margin)
            ).mean()
        else:
            loss = -F.logsigmoid(margin).mean()

        # Side-channel metrics for logging.
        with torch.no_grad():
            chosen_rewards = self.beta * (logp_pi_chosen - logp_ref_chosen)
            rejected_rewards = self.beta * (logp_pi_rejected - logp_ref_rejected)
            reward_acc = (chosen_rewards > rejected_rewards).float().mean()
            reward_margin = (chosen_rewards - rejected_rewards).mean()
            self.log({
                "dpo/loss": loss.detach().item(),
                "dpo/chosen_reward": chosen_rewards.mean().item(),
                "dpo/rejected_reward": rejected_rewards.mean().item(),
                "dpo/reward_margin": reward_margin.item(),
                "dpo/reward_accuracy": reward_acc.item(),
                "dpo/logp_pi_chosen": logp_pi_chosen.mean().item(),
                "dpo/logp_pi_rejected": logp_pi_rejected.mean().item(),
            })

        if return_outputs:
            return loss, {"chosen_logp": logp_pi_chosen, "rejected_logp": logp_pi_rejected}
        return loss
