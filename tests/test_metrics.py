"""Unit tests for retrieval metrics."""

from __future__ import annotations

import math

from wigtnocr_radp.evaluation.metrics import hit_at_k, mrr_at_k, ndcg_at_k
from wigtnocr_radp.evaluation.types import Chunk, ChunkRetrievalResult, QAPair


def _qa(answer_span: str = "needle", page_id: str = "p1") -> QAPair:
    return QAPair(
        qa_id="qa1",
        page_id=page_id,
        doc_id="d1",
        language="en",
        domain="kogov",
        question="q?",
        answer_span=answer_span,
        answer_chunk="...",
        question_type="factoid",
        difficulty="easy",
    )


def _chunk(text: str, page_id: str = "p1", cid: str = "p1::c0") -> Chunk:
    return Chunk(chunk_id=cid, page_id=page_id, text=text)


def _result(chunks: list[Chunk]) -> ChunkRetrievalResult:
    ranked = tuple((c, 1.0 - i * 0.01) for i, c in enumerate(chunks))
    return ChunkRetrievalResult(qa_id="qa1", ranked=ranked)


def test_hit_position_first() -> None:
    qa = _qa("needle")
    r = _result([_chunk("hay needle hay"), _chunk("xxx")])
    assert r.hit_position(qa) == 1


def test_hit_position_third() -> None:
    qa = _qa("needle")
    r = _result([_chunk("xxx"), _chunk("yyy"), _chunk("hay needle")])
    assert r.hit_position(qa) == 3


def test_hit_position_wrong_page() -> None:
    qa = _qa("needle", page_id="p1")
    # answer is in text but page mismatch — should NOT count
    r = _result([_chunk("hay needle", page_id="p2")])
    assert r.hit_position(qa) is None


def test_hit_position_no_hit() -> None:
    qa = _qa("needle")
    r = _result([_chunk("xxx"), _chunk("yyy")])
    assert r.hit_position(qa) is None


def test_hit_at_k() -> None:
    qa = _qa("needle")
    r = _result([_chunk("xxx"), _chunk("yyy"), _chunk("hay needle")])
    assert hit_at_k(r, qa, 1) == 0.0
    assert hit_at_k(r, qa, 3) == 1.0
    assert hit_at_k(r, qa, 5) == 1.0


def test_mrr_at_k() -> None:
    qa = _qa("needle")
    r = _result([_chunk("xxx"), _chunk("hay needle")])  # rank 2
    assert mrr_at_k(r, qa, 1) == 0.0
    assert mrr_at_k(r, qa, 2) == 0.5
    assert mrr_at_k(r, qa, 10) == 0.5


def test_ndcg_at_k() -> None:
    qa = _qa("needle")
    r = _result([_chunk("xxx"), _chunk("hay needle")])  # rank 2
    # nDCG@2 = 1/log2(3) = 1/1.585 ≈ 0.6309
    assert math.isclose(ndcg_at_k(r, qa, 2), 1.0 / math.log2(3.0), rel_tol=1e-9)
    assert ndcg_at_k(r, qa, 1) == 0.0


def test_empty_ranked() -> None:
    qa = _qa("needle")
    r = ChunkRetrievalResult(qa_id="qa1", ranked=())
    assert hit_at_k(r, qa, 5) == 0.0
    assert mrr_at_k(r, qa, 5) == 0.0
    assert ndcg_at_k(r, qa, 5) == 0.0
