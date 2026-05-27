"""Core types for RCPS evaluation."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from typing import Any

# Markdown-structural characters dropped before relevance matching, so a chunk
# counts as "relevant" by its *content*, not its formatting. Without this the
# metric is unfair across parser families: the gold `answer_span` is taken from
# VLM-style GT markdown and rarely appears verbatim in the differently-formatted
# output of MinerU / PaddleOCR / Marker. See docs/WEEK2_FINDINGS.md.
_MARKDOWN_NOISE = set("|*#`>~_")


def normalize_for_match(s: str) -> str:
    """Lowercased NFKC text with whitespace and markdown structure removed."""
    s = unicodedata.normalize("NFKC", s).lower()
    return "".join(ch for ch in s if ch not in _MARKDOWN_NOISE and not ch.isspace())


@dataclass(frozen=True)
class QAPair:
    """A retrieval-evaluation Q-A pair from KoGovDoc-RAG."""

    qa_id: str
    page_id: str
    doc_id: str
    language: str
    domain: str
    question: str
    answer_span: str  # exact substring of the source markdown
    answer_chunk: str  # auto-expanded context around the span
    question_type: str  # factoid | procedural | tabular | figural
    difficulty: str  # easy | medium | hard
    multi_page: bool = False
    referenced_pages: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> QAPair:
        return cls(
            qa_id=d["qa_id"],
            page_id=d["page_id"],
            doc_id=d["doc_id"],
            language=d["language"],
            domain=d["domain"],
            question=d["question"],
            answer_span=d["answer_span"],
            answer_chunk=d["answer_chunk"],
            question_type=d["question_type"],
            difficulty=d["difficulty"],
            multi_page=bool(d.get("multi_page", False)),
            referenced_pages=tuple(d.get("referenced_pages", ())),
        )


@dataclass(frozen=True)
class Chunk:
    """A retrievable chunk produced by a chunking strategy."""

    chunk_id: str  # unique within a parser's output corpus
    page_id: str  # source page (val_NNNN)
    text: str

    def contains_answer(self, answer_span: str) -> bool:
        """True if the gold answer_span is present in this chunk.

        Relevance signal: a chunk is "relevant" to a QAPair iff it lets a reader
        recover the answer. Matching is done on `normalize_for_match` form, so
        whitespace / markdown formatting differences between parsers do not
        change relevance — only content does.
        """
        return normalize_for_match(answer_span) in normalize_for_match(self.text)


@dataclass(frozen=True)
class ChunkRetrievalResult:
    """Result of retrieving chunks for a single query.

    Ordered list of (chunk, score), best first.
    """

    qa_id: str
    ranked: tuple[tuple[Chunk, float], ...]

    def top_k(self, k: int) -> tuple[Chunk, ...]:
        return tuple(c for c, _ in self.ranked[:k])

    def hit_position(self, qa: QAPair) -> int | None:
        """1-indexed position of the first relevant chunk, or None if no hit."""
        for i, (chunk, _) in enumerate(self.ranked, start=1):
            if chunk.page_id == qa.page_id and chunk.contains_answer(qa.answer_span):
                return i
        return None
