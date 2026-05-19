"""Unit tests for chunking strategies."""

from __future__ import annotations

import pytest

from wigtnocr_radp.evaluation.chunkers import (
    FixedSizeChunker,
    MarkdownHeaderChunker,
    ParserNativeChunker,
)


# --- FixedSizeChunker -------------------------------------------------------


def test_fixed_empty() -> None:
    assert FixedSizeChunker(size=100).chunk("p1", "") == []
    assert FixedSizeChunker(size=100).chunk("p1", "   ") == []


def test_fixed_short_under_size() -> None:
    c = FixedSizeChunker(size=100).chunk("p1", "short text")
    assert len(c) == 1
    assert c[0].text == "short text"


def test_fixed_splits_long() -> None:
    c = FixedSizeChunker(size=50).chunk("p1", "a" * 130)
    assert len(c) >= 2
    assert all(c[i].chunk_id == f"p1::fixed50#{i}" for i in range(len(c)))


def test_fixed_invalid_size() -> None:
    with pytest.raises(ValueError):
        FixedSizeChunker(size=0)
    with pytest.raises(ValueError):
        FixedSizeChunker(size=100, overlap=100)


# --- MarkdownHeaderChunker --------------------------------------------------


def test_md_no_headers_fallback() -> None:
    c = MarkdownHeaderChunker(max_level=3).chunk("p1", "just body text without headers")
    assert len(c) == 1
    assert "body" in c[0].text


def test_md_basic_split() -> None:
    md = "# Title\nbody A\n## Sub\nbody B\n# Title 2\nbody C"
    c = MarkdownHeaderChunker(max_level=2).chunk("p1", md)
    assert len(c) == 3
    assert c[0].text.startswith("# Title")
    assert c[1].text.startswith("## Sub")
    assert c[2].text.startswith("# Title 2")


def test_md_preamble_kept() -> None:
    md = "preamble text\n# Title\nbody"
    c = MarkdownHeaderChunker(max_level=1).chunk("p1", md)
    assert len(c) == 2
    assert c[0].text == "preamble text"


def test_md_respects_max_level() -> None:
    # h3 below max_level=2 should NOT split
    md = "# T1\nbody1\n### h3 ignored\nstill in T1\n# T2\nbody2"
    c = MarkdownHeaderChunker(max_level=2).chunk("p1", md)
    assert len(c) == 2  # only h1 boundaries


# --- ParserNativeChunker ----------------------------------------------------


def test_parser_native_split_by_blank() -> None:
    md = "para one is long enough.\n\npara two is also long enough.\n\npara three same."
    c = ParserNativeChunker(min_chars=5).chunk("p1", md)
    assert len(c) == 3


def test_parser_native_min_chars_filter() -> None:
    md = "long paragraph that passes filter.\n\nx\n\nanother long one passes filter."
    c = ParserNativeChunker(min_chars=20).chunk("p1", md)
    # "x" should be filtered, leaving 2
    assert len(c) == 2
    assert all(len(x.text) >= 20 for x in c)


def test_parser_native_fallback_when_all_filtered() -> None:
    c = ParserNativeChunker(min_chars=1000).chunk("p1", "small text here")
    assert len(c) == 1
    assert c[0].text == "small text here"


# --- contains_answer signal -------------------------------------------------


def test_contains_answer_signal() -> None:
    from wigtnocr_radp.evaluation.types import Chunk

    ch = Chunk(chunk_id="c1", page_id="p1", text="The capital is Seoul, located in Korea.")
    assert ch.contains_answer("Seoul")
    assert ch.contains_answer("capital is Seoul")
    assert not ch.contains_answer("Tokyo")
