"""Unit tests for RADP-B contrastive components."""

from __future__ import annotations

import math

import numpy as np
import pytest
import torch

from wigtnocr_radp.training.contrastive import (
    BgeM3EmbeddingCache,
    ChunkMeta,
    ContrastiveProjectionHead,
    RadpBLoss,
    SamplingStrategy,
    info_nce_loss,
    mean_pool_hidden,
)


# --- Projection head --------------------------------------------------------


def test_projection_head_shapes_and_norm() -> None:
    head = ContrastiveProjectionHead(hidden_dim=1536, proj_dim=1024)
    z = head(torch.randn(3, 1536))
    assert z.shape == (3, 1024)
    norms = z.norm(dim=-1)
    assert torch.allclose(norms, torch.ones(3), atol=1e-5)


def test_mean_pool_hidden_basic() -> None:
    h = torch.tensor(
        [
            [[1.0, 2.0], [3.0, 4.0], [0.0, 0.0]],  # last token padded
            [[5.0, 6.0], [0.0, 0.0], [0.0, 0.0]],  # only first token
        ]
    )
    mask = torch.tensor([[1, 1, 0], [1, 0, 0]])
    out = mean_pool_hidden(h, mask)
    assert torch.allclose(out[0], torch.tensor([2.0, 3.0]))
    assert torch.allclose(out[1], torch.tensor([5.0, 6.0]))


def test_mean_pool_all_zeros_mask_safe() -> None:
    # Degenerate sample with no valid tokens — should not NaN
    h = torch.tensor([[[1.0, 2.0]]])
    mask = torch.tensor([[0]])
    out = mean_pool_hidden(h, mask)
    assert torch.isfinite(out).all()


# --- InfoNCE ----------------------------------------------------------------


def test_info_nce_perfect_alignment_gives_low_loss() -> None:
    d = 16
    anchor = torch.nn.functional.normalize(torch.randn(4, d), dim=-1)
    positive = anchor.clone()  # perfect positive
    negatives = torch.nn.functional.normalize(torch.randn(4, 7, d), dim=-1)
    loss = info_nce_loss(anchor, positive, negatives, temperature=0.07)
    # With perfect anchor=positive: a·p / τ ≈ 1/τ ≈ 14, vs random negatives ≈ 0
    # softmax mass on positive ≈ 1 → loss ≈ 0
    assert loss.item() < 0.1


def test_info_nce_random_gives_logK_loss() -> None:
    d = 32
    a = torch.nn.functional.normalize(torch.randn(8, d), dim=-1)
    p = torch.nn.functional.normalize(torch.randn(8, d), dim=-1)
    n = torch.nn.functional.normalize(torch.randn(8, 7, d), dim=-1)
    loss = info_nce_loss(a, p, n, temperature=1.0)
    # With 1+K=8 logits all approx equal, CE ≈ log(8) ≈ 2.079
    assert 1.5 < loss.item() < 2.5


def test_info_nce_shape_validation() -> None:
    with pytest.raises(ValueError):
        info_nce_loss(torch.randn(4, 16), torch.randn(3, 16), torch.randn(4, 7, 16))
    with pytest.raises(ValueError):
        info_nce_loss(torch.randn(4, 16), torch.randn(4, 16), torch.randn(4, 7, 32))


# --- Embedding cache --------------------------------------------------------


def _make_cache(n_pages: int = 3, chunks_per_page: int = 4) -> BgeM3EmbeddingCache:
    n = n_pages * chunks_per_page
    rng = np.random.default_rng(0)
    embs = rng.standard_normal((n, 8)).astype(np.float32)
    metas = []
    for p in range(n_pages):
        for c in range(chunks_per_page):
            row = p * chunks_per_page + c
            is_answer = c == 0
            metas.append(
                ChunkMeta(
                    chunk_id=f"p{p}::c{c}",
                    page_id=f"p{p}",
                    answer_span="ans" if is_answer else None,
                    qa_id=f"qa{p}" if is_answer else None,
                    row=row,
                )
            )
    return BgeM3EmbeddingCache(embs, metas)


def test_cache_lookups() -> None:
    c = _make_cache(n_pages=3, chunks_per_page=4)
    # 3 pages × 4 chunks = 12 chunks, 3 Q-A
    assert len(c.embeddings) == 12
    assert c.chunks_on_page("p0") == [0, 1, 2, 3]
    assert c.chunks_for_qa("qa1") == [4]  # second page's first chunk
    assert c.chunks_for_qa("missing") == []


def test_cache_save_load_roundtrip(tmp_path) -> None:
    c1 = _make_cache(n_pages=2, chunks_per_page=3)
    c1.save(tmp_path)
    c2 = BgeM3EmbeddingCache.load(tmp_path)
    assert np.array_equal(c1.embeddings, c2.embeddings)
    assert len(c1.metas) == len(c2.metas)
    assert c1.metas[0].chunk_id == c2.metas[0].chunk_id


# --- Sampling strategy ------------------------------------------------------


def test_sampling_shapes() -> None:
    c = _make_cache(n_pages=4, chunks_per_page=4)
    rng = np.random.default_rng(0)
    s = SamplingStrategy(num_in_batch_neg=3, num_hard_neg=1)
    pos, neg = s.sample(
        c,
        qa_ids=[f"qa{i}" for i in range(4)],
        page_ids=[f"p{i}" for i in range(4)],
        rng=rng,
    )
    assert pos.shape == (4, 8)
    assert neg.shape == (4, 4, 8)


def test_sampling_hard_neg_from_same_page() -> None:
    """Hard negatives should come from the anchor's own page (different chunk)."""
    c = _make_cache(n_pages=3, chunks_per_page=4)
    rng = np.random.default_rng(0)
    s = SamplingStrategy(num_in_batch_neg=0, num_hard_neg=1)
    pos, neg = s.sample(
        c, qa_ids=["qa0", "qa1", "qa2"], page_ids=["p0", "p1", "p2"], rng=rng
    )
    # neg[i, 0] must be one of page i's rows but NOT the positive row
    for i, pid in enumerate(["p0", "p1", "p2"]):
        page_rows = c.chunks_on_page(pid)
        page_embs = c.embeddings[page_rows]
        # find which row matches
        matches = [np.allclose(neg[i, 0], page_embs[j]) for j in range(len(page_embs))]
        assert any(matches), f"hard neg for {pid} not from same page"


# --- Composite loss ---------------------------------------------------------


def test_radp_b_loss_composes_correctly() -> None:
    head = ContrastiveProjectionHead(hidden_dim=16, proj_dim=8)
    loss = RadpBLoss(head, lambda_=0.3, temperature=0.07)
    pooled = torch.randn(4, 16)
    p = torch.nn.functional.normalize(torch.randn(4, 8), dim=-1)
    n = torch.nn.functional.normalize(torch.randn(4, 5, 8), dim=-1)
    parse = torch.tensor(1.5)
    total, parse_detached, contrast = loss(pooled, p, n, parse)
    expected = parse + 0.3 * contrast
    assert torch.allclose(total, expected, atol=1e-5)
    assert math.isfinite(total.item())


def test_radp_b_loss_lambda_zero_recovers_parse_loss() -> None:
    head = ContrastiveProjectionHead(hidden_dim=16, proj_dim=8)
    loss = RadpBLoss(head, lambda_=0.0)
    pooled = torch.randn(2, 16)
    p = torch.nn.functional.normalize(torch.randn(2, 8), dim=-1)
    n = torch.nn.functional.normalize(torch.randn(2, 5, 8), dim=-1)
    parse = torch.tensor(2.5)
    total, _, _ = loss(pooled, p, n, parse)
    assert torch.allclose(total, parse)
