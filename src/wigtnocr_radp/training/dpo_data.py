"""RADP-DPO training data: preference pairs (image, prompt, chosen, rejected).

Each example is a single preference pair built by
`scripts/training/build_preference_pairs.py`: two candidate parses of the same
page, ranked by their page-local RCPS score. The collator turns the pair into
two parallel Qwen3-VL chat messages (one ending in `chosen`, one in
`rejected`), tokenises both with the same image, and emits an
`assistant_mask` selecting only the response tokens — the only positions over
which DPO's log-likelihood is computed.

The image is shared across the chosen/rejected halves; we keep it as a single
PIL.Image in the batch and let the trainer broadcast.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch
from PIL import Image
from torch.utils.data import Dataset

logger = logging.getLogger("radp_dpo.data")


@dataclass(frozen=True)
class DPOExample:
    page_id: str
    image_path: Path
    system: str
    user: str       # user instruction with "<image>" stripped
    chosen: str     # higher-RCPS markdown
    rejected: str   # lower-RCPS markdown
    rcps_gap: float


class DPOPreferenceDataset(Dataset[DPOExample]):
    """JSONL-backed dataset of DPO preference pairs."""

    def __init__(self, examples: Sequence[DPOExample]) -> None:
        self._items = list(examples)

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, idx: int) -> DPOExample:
        return self._items[idx]

    @classmethod
    def from_jsonl(cls, path: str | Path) -> DPOPreferenceDataset:
        items: list[DPOExample] = []
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            items.append(DPOExample(
                page_id=r["page_id"], image_path=Path(r["image"]),
                system=r["system_prompt"], user=r["user_prompt"],
                chosen=r["chosen_markdown"], rejected=r["rejected_markdown"],
                rcps_gap=float(r["rcps_gap"]),
            ))
        logger.info("loaded %d preference pairs from %s", len(items), path)
        return cls(items)


class Qwen3VLDPOCollator:
    """Collate DPO preference batches into Qwen3-VL VLM inputs.

    For each example:
      - Build chosen/rejected chat messages with the same image+prompt
      - Tokenise both, pad together
      - Build an `assistant_mask` (1 on response tokens, 0 on prompt+image tokens)

    The two halves are stacked: shape (2B, T) for input_ids/attention_mask, where
    indices [0..B] = chosen and [B..2B] = rejected (matching how the trainer
    splits them).
    """

    def __init__(
        self,
        processor: Any,  # transformers AutoProcessor
        max_seq_length: int = 3072,
        image_max_pixels: int = 1_048_576,
    ) -> None:
        self.processor = processor
        self.tokenizer = processor.tokenizer
        self.max_seq_length = max_seq_length
        self.image_max_pixels = image_max_pixels
        # Cache the assistant-prelude token ids so we can locate the boundary
        # between prompt and response by scanning for them.
        # `<|im_start|>assistant\n` is the Qwen3-VL response prefix.
        self._asst_prelude_ids = self.tokenizer(
            "<|im_start|>assistant\n", add_special_tokens=False
        ).input_ids

    def _load_image(self, path: Path) -> Image.Image:
        img = Image.open(path).convert("RGB")
        w, h = img.size
        if w * h > self.image_max_pixels:
            scale = (self.image_max_pixels / (w * h)) ** 0.5
            img = img.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)
        return img

    def _messages(self, ex: DPOExample, response: str) -> list[dict[str, Any]]:
        return [
            {"role": "system", "content": ex.system},
            {"role": "user", "content": [{"type": "image"}, {"type": "text", "text": ex.user}]},
            {"role": "assistant", "content": response},
        ]

    def _assistant_mask(self, input_ids: torch.Tensor) -> torch.Tensor:
        """1 on assistant-response tokens, 0 elsewhere. Per row."""
        prelude = self._asst_prelude_ids
        plen = len(prelude)
        mask = torch.zeros_like(input_ids, dtype=torch.long)
        for r in range(input_ids.shape[0]):
            row = input_ids[r].tolist()
            # find LAST occurrence of the assistant prelude
            start_idx = -1
            for i in range(len(row) - plen, -1, -1):
                if row[i:i + plen] == prelude:
                    start_idx = i + plen
                    break
            if start_idx < 0:
                continue
            mask[r, start_idx:] = 1
        # Don't count pad tokens (attention_mask handles this too, but keep tight).
        return mask

    def __call__(self, examples: Sequence[DPOExample]) -> dict[str, Any]:
        n = len(examples)
        # Build chosen and rejected text variants for the same image set.
        chosen_texts: list[str] = []
        rejected_texts: list[str] = []
        images: list[Image.Image] = []
        for ex in examples:
            img = self._load_image(ex.image_path)
            images.append(img)
            chosen_texts.append(self.processor.apply_chat_template(
                self._messages(ex, ex.chosen), tokenize=False, add_generation_prompt=False))
            rejected_texts.append(self.processor.apply_chat_template(
                self._messages(ex, ex.rejected), tokenize=False, add_generation_prompt=False))

        # Stack chosen + rejected; image set repeats.
        all_texts = chosen_texts + rejected_texts
        all_images = images + images

        inputs = self.processor(
            text=all_texts, images=all_images, return_tensors="pt", padding=True,
            truncation=True, max_length=self.max_seq_length,
        )
        input_ids = inputs["input_ids"]
        assistant_mask = self._assistant_mask(input_ids)
        # Combine with attention_mask so padding is ignored.
        if "attention_mask" in inputs:
            assistant_mask = assistant_mask * inputs["attention_mask"]

        inputs["assistant_mask"] = assistant_mask
        inputs["n_pairs"] = torch.tensor(n)
        return dict(inputs)
