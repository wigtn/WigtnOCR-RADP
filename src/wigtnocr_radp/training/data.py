"""RADP-B training data: per-Q-A examples + Qwen3-VL collation.

Each training example pairs a document page (image + GT markdown) with one
Q-A pair from that page:

    - L_parse    uses the (image -> markdown) supervision (val.jsonl messages).
    - L_contrast uses the qa_id / page_id to look up BGE-M3 chunk embeddings
      (see `BgeM3EmbeddingCache`); the collator only carries the ids through.

The image paths stored in `val.jsonl` point at a now-removed scratch directory
(`/mnt/.../research-vlm-based-document-parsing/...`). `remap_image_path` rebases
them onto the repo-local copy under `data/KoGovDoc-Bench/images/`.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image
from torch.utils.data import Dataset

logger = logging.getLogger("radp_b.data")

DEFAULT_IMAGES_ROOT = Path("data/KoGovDoc-Bench/images")
_IMAGE_PLACEHOLDER = "<image>"


def remap_image_path(stored_path: str, images_root: str | Path = DEFAULT_IMAGES_ROOT) -> Path:
    """Rebase a stale absolute image path onto the repo-local images root.

    val.jsonl stores paths like ``.../images/documents/kogov_008/page_0544.png``.
    Everything up to and including ``/images/`` is dropped and the remainder is
    joined onto `images_root`. Paths without an ``/images/`` segment are returned
    as-is (already repo-local).
    """
    marker = "/images/"
    idx = stored_path.find(marker)
    if idx < 0:
        return Path(stored_path)
    return Path(images_root) / stored_path[idx + len(marker) :]


@dataclass(frozen=True)
class RadpBExample:
    """One (page, Q-A) training example."""

    qa_id: str
    page_id: str
    image_path: Path
    system: str
    user: str       # user instruction text, with the literal "<image>" stripped
    assistant: str  # GT markdown — the L_parse target


def _load_val_pages(val_jsonl: Path) -> dict[str, dict[str, Any]]:
    """Return {page_id: val.jsonl row}. page_id = val_{row_index:04d}."""
    pages: dict[str, dict[str, Any]] = {}
    with val_jsonl.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            pages[f"val_{i:04d}"] = json.loads(line)
    return pages


def _example_from_row(
    qa_id: str, page_id: str, row: dict[str, Any], images_root: str | Path
) -> RadpBExample:
    messages = row["messages"]
    system = messages[0]["content"]
    user = messages[1]["content"]
    assistant = messages[2]["content"]
    # The user turn carries a literal "<image>" sentinel; the processor inserts
    # the real vision tokens, so strip it from the text.
    user = user.replace(_IMAGE_PLACEHOLDER, "", 1).lstrip()
    return RadpBExample(
        qa_id=qa_id,
        page_id=page_id,
        image_path=remap_image_path(row["images"][0], images_root),
        system=system,
        user=user,
        assistant=assistant,
    )


class RadpBDataset(Dataset[RadpBExample]):
    """Per-Q-A dataset for one fold of `page_split_v1.json`."""

    def __init__(self, examples: Sequence[RadpBExample]) -> None:
        self.examples = list(examples)

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, idx: int) -> RadpBExample:
        return self.examples[idx]

    @classmethod
    def from_fold(
        cls,
        *,
        split_path: str | Path,
        qa_path: str | Path,
        val_jsonl: str | Path,
        fold: str,
        images_root: str | Path = DEFAULT_IMAGES_ROOT,
    ) -> RadpBDataset:
        """Build the dataset for a fold ("train" | "eval").

        One example per Q-A pair whose page belongs to the fold. Q-A whose page
        is missing from val.jsonl, or whose image file is absent, are skipped
        with a warning.
        """
        split = json.loads(Path(split_path).read_text())
        key = {"train": "train_pages", "eval": "eval_pages"}[fold]
        fold_pages = set(split[key])

        pages = _load_val_pages(Path(val_jsonl))

        examples: list[RadpBExample] = []
        n_qa = n_missing_page = n_missing_img = 0
        with Path(qa_path).open("r", encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                pid = d["page_id"]
                if pid not in fold_pages:
                    continue
                n_qa += 1
                row = pages.get(pid)
                if row is None:
                    n_missing_page += 1
                    continue
                ex = _example_from_row(d["qa_id"], pid, row, images_root)
                if not ex.image_path.exists():
                    n_missing_img += 1
                    logger.warning("qa_id=%s: image not found: %s", d["qa_id"][:8], ex.image_path)
                    continue
                examples.append(ex)

        logger.info(
            "fold=%s: %d/%d Q-A usable (missing page=%d, missing image=%d, %d pages)",
            fold, len(examples), n_qa, n_missing_page, n_missing_img, len(fold_pages),
        )
        if not examples:
            raise RuntimeError(f"no usable examples for fold={fold!r}")
        return cls(examples)


class Qwen3VLContrastiveCollator:
    """Collate `RadpBExample`s into Qwen3-VL model inputs + contrastive ids.

    Produces a dict with the standard VLM tensors (`input_ids`, `attention_mask`,
    `pixel_values`, `image_grid_thw`, `labels`) plus two plain-list keys
    (`qa_ids`, `page_ids`) consumed by `RadpBTrainer.compute_loss`.

    Label masking: tokens belonging to the system+user prompt (and image tokens,
    which live inside the user turn) are set to -100, so L_parse is computed only
    over the assistant markdown. The prompt length is obtained by rendering the
    prompt-only conversation through the same processor — a strict prefix of the
    full conversation for Qwen chat templates.
    """

    def __init__(
        self,
        processor: Any,
        image_max_pixels: int = 1_048_576,
        max_seq_length: int = 3072,
    ) -> None:
        self.processor = processor
        self.image_max_pixels = int(image_max_pixels)
        self.max_seq_length = int(max_seq_length)
        # Right padding so the prompt prefix stays at positions [0, prompt_len).
        if processor.tokenizer.padding_side != "right":
            processor.tokenizer.padding_side = "right"

    def _load_image(self, path: Path) -> Image.Image:
        """Load an image, downscaling to `image_max_pixels` (aspect preserved).

        Full-page document scans are large; the Qwen3-VL processor would expand
        them into thousands of vision tokens. Capping the pixel budget bounds
        sequence length (and therefore activation memory) before the processor's
        own smart-resize runs.
        """
        img = Image.open(path).convert("RGB")
        w, h = img.size
        if w * h > self.image_max_pixels:
            scale = (self.image_max_pixels / (w * h)) ** 0.5
            img = img.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)
        return img

    @staticmethod
    def _messages(ex: RadpBExample, with_answer: bool) -> list[dict[str, Any]]:
        msgs: list[dict[str, Any]] = [
            {"role": "system", "content": ex.system},
            {
                "role": "user",
                "content": [{"type": "image"}, {"type": "text", "text": ex.user}],
            },
        ]
        if with_answer:
            msgs.append({"role": "assistant", "content": ex.assistant})
        return msgs

    def _render(self, ex: RadpBExample, with_answer: bool) -> str:
        return self.processor.apply_chat_template(
            self._messages(ex, with_answer),
            tokenize=False,
            add_generation_prompt=not with_answer,
        )

    def __call__(self, examples: Sequence[RadpBExample]) -> dict[str, Any]:
        images = [self._load_image(ex.image_path) for ex in examples]
        full_texts = [self._render(ex, with_answer=True) for ex in examples]

        enc = self.processor(
            text=full_texts, images=images, return_tensors="pt", padding=True
        )
        labels = enc["input_ids"].clone()

        for i, ex in enumerate(examples):
            prompt_text = self._render(ex, with_answer=False)
            prompt_len = self.processor(
                text=[prompt_text], images=[images[i]], return_tensors="pt"
            )["input_ids"].shape[1]
            if prompt_len >= self.max_seq_length:
                raise ValueError(
                    f"prompt ({prompt_len} tok) >= max_seq_length ({self.max_seq_length}); "
                    f"raise max_seq_length or lower image_max_pixels"
                )
            labels[i, :prompt_len] = -100
        labels[enc["attention_mask"] == 0] = -100
        enc["labels"] = labels

        # Truncate over-long sequences from the right (assistant tail only — the
        # image region sits well inside the prompt, so it is never cut). This
        # caps activation/logit memory; in practice it clips a single outlier
        # page (~6.8k tok markdown) out of the whole train fold.
        if enc["input_ids"].shape[1] > self.max_seq_length:
            for key in ("input_ids", "attention_mask", "mm_token_type_ids", "labels"):
                if key in enc:
                    enc[key] = enc[key][:, : self.max_seq_length]

        batch = dict(enc)
        batch["qa_ids"] = [ex.qa_id for ex in examples]
        batch["page_ids"] = [ex.page_id for ex in examples]
        return batch
