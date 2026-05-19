"""Contrastive components for RADP-B.

Design (decision A — projection-head variant, 2026-05-19):

    The Qwen3-VL parser produces last-layer hidden states for each generated
    token. We pool them per-sample (mean over text tokens) and pass through a
    small MLP projection head to land in BGE-M3's 1024-d L2-normalized space.

    Positive / negative chunks are *not* re-embedded during training — their
    BGE-M3 embeddings are pre-computed once (`BgeM3EmbeddingCache`) and looked
    up by chunk_id. This avoids the non-differentiable
        parser → discrete markdown → BGE-M3
    path that proposal §4.1's literal reading would require.

    The aux loss is InfoNCE:
        L_contrast = -log( exp(a·p / τ) / (exp(a·p / τ) + Σ exp(a·n / τ)) )
    where  a = projected parser embedding,  p = positive BGE-M3 embedding,
    n = in-batch + hard-negative BGE-M3 embeddings.

    Frozen BGE-M3 = the *teacher* the parser is aligned toward in retrieval
    space, while the standard parsing CE loss preserves text fidelity.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from torch import Tensor, nn


# --- Projection head ----------------------------------------------------------


class ContrastiveProjectionHead(nn.Module):
    """Two-layer MLP: parser hidden → BGE-M3 embedding space.

    Args:
        hidden_dim: parser's last hidden_states dim (Qwen3-VL-2B ≈ 1536).
        proj_dim: target dim, must match BGE-M3 (1024).
        dropout: small dropout for regularisation.
    """

    def __init__(self, hidden_dim: int, proj_dim: int = 1024, dropout: float = 0.1) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, proj_dim),
        )
        self.norm = nn.LayerNorm(proj_dim)

    def forward(self, hidden: Tensor) -> Tensor:
        """Pool-then-project. Caller must mean-pool `hidden` over tokens first.

        Args:
            hidden: (batch, hidden_dim) pooled parser hidden states.
        Returns:
            (batch, proj_dim) L2-normalized embeddings.
        """
        z = self.norm(self.net(hidden))
        return torch.nn.functional.normalize(z, p=2.0, dim=-1)


def mean_pool_hidden(hidden_states: Tensor, attention_mask: Tensor) -> Tensor:
    """Mean-pool over masked tokens.

    Args:
        hidden_states: (B, T, D)
        attention_mask: (B, T) with 1 for valid tokens, 0 for padding.
    """
    mask = attention_mask.to(hidden_states.dtype).unsqueeze(-1)  # (B, T, 1)
    summed = (hidden_states * mask).sum(dim=1)  # (B, D)
    denom = mask.sum(dim=1).clamp_min(1.0)  # (B, 1)
    return summed / denom


# --- InfoNCE loss -------------------------------------------------------------


def info_nce_loss(
    anchor: Tensor,
    positive: Tensor,
    negatives: Tensor,
    temperature: float = 0.07,
) -> Tensor:
    """InfoNCE with one positive and K negatives per anchor.

    Args:
        anchor:    (B, D) L2-normalized.
        positive:  (B, D) L2-normalized.
        negatives: (B, K, D) L2-normalized.
        temperature: τ.

    Returns:
        scalar loss (mean over batch).
    """
    if anchor.dim() != 2 or positive.dim() != 2 or negatives.dim() != 3:
        raise ValueError(
            f"shape: anchor {anchor.shape}, positive {positive.shape}, negatives {negatives.shape}"
        )
    if anchor.size(0) != positive.size(0) or anchor.size(0) != negatives.size(0):
        raise ValueError("batch dim mismatch")
    if anchor.size(-1) != positive.size(-1) or anchor.size(-1) != negatives.size(-1):
        raise ValueError("embedding dim mismatch")

    pos_sim = (anchor * positive).sum(dim=-1, keepdim=True) / temperature  # (B, 1)
    neg_sim = torch.einsum("bd,bkd->bk", anchor, negatives) / temperature  # (B, K)
    logits = torch.cat([pos_sim, neg_sim], dim=1)  # (B, 1+K), index 0 = positive
    target = torch.zeros(anchor.size(0), dtype=torch.long, device=anchor.device)
    return torch.nn.functional.cross_entropy(logits, target)


# --- BGE-M3 embedding cache ---------------------------------------------------


@dataclass(frozen=True)
class ChunkMeta:
    chunk_id: str
    page_id: str
    answer_span: str | None  # None for non-answer chunks; set for pos chunks
    qa_id: str | None  # None for non-answer chunks
    row: int  # row index into the embedding matrix


class BgeM3EmbeddingCache:
    """Lookup of BGE-M3 chunk embeddings by chunk_id / page_id / qa_id.

    Layout on disk:
        <dir>/embeddings.npy        (N, 1024) float32
        <dir>/meta.jsonl            N lines of {chunk_id, page_id, qa_id, answer_span}

    Built once with `precompute_cache.py` (offline), loaded into RAM in trainer.
    """

    def __init__(
        self,
        embeddings: np.ndarray,
        metas: Sequence[ChunkMeta],
    ) -> None:
        if embeddings.shape[0] != len(metas):
            raise ValueError(
                f"embeddings/metas mismatch: {embeddings.shape[0]} vs {len(metas)}"
            )
        self.embeddings = embeddings.astype(np.float32)
        self.metas = list(metas)
        self._by_chunk: dict[str, int] = {m.chunk_id: m.row for m in self.metas}
        self._by_page: dict[str, list[int]] = {}
        self._by_qa: dict[str, list[int]] = {}
        for m in self.metas:
            self._by_page.setdefault(m.page_id, []).append(m.row)
            if m.qa_id:
                self._by_qa.setdefault(m.qa_id, []).append(m.row)

    @classmethod
    def load(cls, cache_dir: str | Path) -> BgeM3EmbeddingCache:
        cache_dir = Path(cache_dir)
        embeddings = np.load(cache_dir / "embeddings.npy")
        metas: list[ChunkMeta] = []
        with (cache_dir / "meta.jsonl").open("r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                d = json.loads(line)
                metas.append(
                    ChunkMeta(
                        chunk_id=d["chunk_id"],
                        page_id=d["page_id"],
                        answer_span=d.get("answer_span"),
                        qa_id=d.get("qa_id"),
                        row=i,
                    )
                )
        return cls(embeddings, metas)

    def save(self, cache_dir: str | Path) -> None:
        cache_dir = Path(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        np.save(cache_dir / "embeddings.npy", self.embeddings)
        with (cache_dir / "meta.jsonl").open("w", encoding="utf-8") as f:
            for m in self.metas:
                f.write(
                    json.dumps(
                        {
                            "chunk_id": m.chunk_id,
                            "page_id": m.page_id,
                            "qa_id": m.qa_id,
                            "answer_span": m.answer_span,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )

    # Lookups ---------------------------------------------------------------

    def embedding(self, chunk_id: str) -> np.ndarray:
        return self.embeddings[self._by_chunk[chunk_id]]

    def chunks_on_page(self, page_id: str) -> list[int]:
        """Row indices of all cached chunks belonging to a page."""
        return self._by_page.get(page_id, [])

    def chunks_for_qa(self, qa_id: str) -> list[int]:
        """Row indices of positive (answer-containing) chunks for a Q-A."""
        return self._by_qa.get(qa_id, [])


# --- Sampling strategy --------------------------------------------------------


@dataclass
class SamplingStrategy:
    """Build (positive, negative_rows) for each batch sample at train time.

    Args:
        num_in_batch_neg: how many in-batch negatives per anchor (capped at B-1).
        num_hard_neg: how many same-page (semantic neighbor) hard negatives.
    """

    num_in_batch_neg: int = 7
    num_hard_neg: int = 1

    def sample(
        self,
        cache: BgeM3EmbeddingCache,
        qa_ids: Sequence[str],
        page_ids: Sequence[str],
        rng: np.random.Generator,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Pick one positive and K negatives per anchor.

        Returns:
            positives: (B, 1024) float32
            negatives: (B, K, 1024) float32  where K = num_in_batch_neg + num_hard_neg
        """
        b = len(qa_ids)
        pos = np.zeros((b, cache.embeddings.shape[1]), dtype=np.float32)
        neg = np.zeros(
            (b, self.num_in_batch_neg + self.num_hard_neg, cache.embeddings.shape[1]),
            dtype=np.float32,
        )

        # Positives: pick one row from chunks_for_qa
        pos_rows: list[int] = []
        for i, qa_id in enumerate(qa_ids):
            cand = cache.chunks_for_qa(qa_id)
            if not cand:
                # fallback: any chunk on the page (should not happen if cache covers all Q-A)
                cand = cache.chunks_on_page(page_ids[i])
            if not cand:
                raise ValueError(f"no candidate positive for qa_id={qa_id}")
            row = int(rng.choice(cand))
            pos_rows.append(row)
            pos[i] = cache.embeddings[row]

        # In-batch negatives: positives of *other* samples in this batch
        for i in range(b):
            others = [pos_rows[j] for j in range(b) if j != i]
            if len(others) < self.num_in_batch_neg:
                # small batch — duplicate-sample with replacement
                rows = rng.choice(others, size=self.num_in_batch_neg, replace=True) if others else np.array([], dtype=int)
            else:
                rows = rng.choice(others, size=self.num_in_batch_neg, replace=False)
            for k, r in enumerate(rows):
                neg[i, k] = cache.embeddings[int(r)]

        # Hard negatives: same page, different chunk
        for i in range(b):
            same_page = [
                r for r in cache.chunks_on_page(page_ids[i]) if r != pos_rows[i]
            ]
            if not same_page:
                # fallback: an in-batch negative (no hard available)
                hard_rows = rng.choice(
                    [pos_rows[j] for j in range(b) if j != i] or [pos_rows[i]],
                    size=self.num_hard_neg,
                    replace=True,
                )
            else:
                hard_rows = rng.choice(
                    same_page,
                    size=min(self.num_hard_neg, len(same_page)),
                    replace=False,
                )
                if len(hard_rows) < self.num_hard_neg:
                    extra = rng.choice(
                        same_page, size=self.num_hard_neg - len(hard_rows), replace=True
                    )
                    hard_rows = np.concatenate([hard_rows, extra])
            for k, r in enumerate(hard_rows):
                neg[i, self.num_in_batch_neg + k] = cache.embeddings[int(r)]

        return pos, neg


# --- Composite loss -----------------------------------------------------------


class RadpBLoss(nn.Module):
    """L_total = L_parse + λ · L_contrast.

    `L_parse` is supplied by the parser's standard outputs.loss (cross-entropy
    over generated tokens). This module only adds the contrastive term.
    """

    def __init__(
        self,
        projection_head: ContrastiveProjectionHead,
        lambda_: float = 0.3,
        temperature: float = 0.07,
    ) -> None:
        super().__init__()
        self.projection_head = projection_head
        self.lambda_ = float(lambda_)
        self.temperature = float(temperature)

    def forward(
        self,
        pooled_hidden: Tensor,
        positive_emb: Tensor,
        negative_embs: Tensor,
        parse_loss: Tensor,
    ) -> tuple[Tensor, Tensor, Tensor]:
        """Returns (L_total, L_parse, L_contrast). All scalars."""
        anchor = self.projection_head(pooled_hidden)
        l_contrast = info_nce_loss(
            anchor=anchor,
            positive=positive_emb,
            negatives=negative_embs,
            temperature=self.temperature,
        )
        l_total = parse_loss + self.lambda_ * l_contrast
        return l_total, parse_loss.detach(), l_contrast.detach()
