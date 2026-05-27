"""Unit tests for the answer-coverage diagnostic (no data / GPU required)."""

from __future__ import annotations

from wigtnocr_radp.evaluation.chunkers import FixedSizeChunker, MarkdownHeaderChunker
from wigtnocr_radp.evaluation.coverage import (
    classify_answer_location,
    diagnose_coverage,
)
from wigtnocr_radp.evaluation.types import QAPair, normalize_for_match


def _qa(
    qa_id: str,
    page_id: str,
    answer_span: str,
    question_type: str = "factoid",
    difficulty: str = "easy",
) -> QAPair:
    return QAPair(
        qa_id=qa_id,
        page_id=page_id,
        doc_id="doc_0",
        language="ko",
        domain="gov",
        question="q?",
        answer_span=answer_span,
        answer_chunk=answer_span,
        question_type=question_type,
        difficulty=difficulty,
    )


# --- classify_answer_location ----------------------------------------------


def test_classify_covered() -> None:
    page = "The capital is Seoul."
    chunks = [normalize_for_match(page)]
    assert classify_answer_location("Seoul", page, chunks) == "covered"


def test_classify_split() -> None:
    # "CD" exists in the page but is cut across the two chunk boundaries.
    page = "ABCDEF"
    chunks = [normalize_for_match("ABC"), normalize_for_match("DEF")]
    assert classify_answer_location("CD", page, chunks) == "split"


def test_classify_absent() -> None:
    page = "ABCDEF"
    chunks = [normalize_for_match(page)]
    assert classify_answer_location("XYZ", page, chunks) == "absent"


def test_classify_no_parse() -> None:
    assert classify_answer_location("CD", None, []) == "no_parse"


def test_classify_empty_span_is_absent() -> None:
    page = "ABC"
    assert classify_answer_location("   ", page, [normalize_for_match(page)]) == "absent"


def test_classify_ignores_markdown_formatting() -> None:
    # answer is plain; chunk has markdown table pipes / bold around it.
    page = "| **Seoul** | capital |"
    chunks = [normalize_for_match(page)]
    assert classify_answer_location("Seoul", page, chunks) == "covered"


# --- diagnose_coverage ------------------------------------------------------


def test_diagnose_overlap_recovers_split() -> None:
    # Answer straddles the 500-char boundary, so fixed500 splits it but an
    # overlapped window recovers it — the core "chunker fault is recoverable" claim.
    page_id = "val_0000"
    body = "X" * 490 + "ANSWERTOKEN" + "Y" * 100
    pages = {page_id: body}
    qa = [_qa("q1", page_id, "ANSWERTOKEN")]

    no_overlap = diagnose_coverage(qa, pages, FixedSizeChunker(size=500))
    with_overlap = diagnose_coverage(qa, pages, FixedSizeChunker(size=500, overlap=200))

    assert no_overlap.counts.get("split", 0) == 1
    assert with_overlap.counts.get("covered", 0) == 1
    assert with_overlap.coverage > no_overlap.coverage


def test_diagnose_absent_is_chunker_independent() -> None:
    # An answer the parser never produced is `absent` regardless of chunker, and
    # never counts as parser-recoverable `split`.
    page_id = "val_0001"
    pages = {page_id: "completely unrelated parser output"}
    qa = [_qa("q1", page_id, "missing answer text")]

    for chunker in (MarkdownHeaderChunker(max_level=3), FixedSizeChunker(size=500, overlap=200)):
        rep = diagnose_coverage(qa, pages, chunker)
        assert rep.parser_fault_rate == 1.0
        assert rep.split_rate == 0.0


def test_diagnose_no_parse_when_page_missing() -> None:
    # Q-A points at a page the parser produced no output for.
    qa = [_qa("q1", "val_9999", "anything")]
    rep = diagnose_coverage(qa, pages={}, chunker=FixedSizeChunker(size=500))
    assert rep.counts.get("no_parse", 0) == 1
    assert rep.coverage == 0.0


def test_diagnose_breakdown_by_type_and_difficulty() -> None:
    page_id = "val_0002"
    pages = {page_id: "# H\nthe answer is FOO here\n\nand BAR sits in another paragraph"}
    qa = [
        _qa("q1", page_id, "FOO", question_type="factoid", difficulty="easy"),
        _qa("q2", page_id, "BAR", question_type="tabular", difficulty="hard"),
        _qa("q3", page_id, "NOPE", question_type="factoid", difficulty="medium"),
    ]
    rep = diagnose_coverage(qa, pages, MarkdownHeaderChunker(max_level=1))

    assert rep.total == 3
    assert rep.by_question_type["factoid"]["covered"] == 1
    assert rep.by_question_type["factoid"]["absent"] == 1
    assert rep.by_question_type["tabular"]["covered"] == 1
    assert set(rep.by_difficulty) == {"easy", "hard", "medium"}
