"""Answer-coverage diagnostic — is the parsing-retrieval gap a parser or a chunker problem?

For a *fixed* parser output, classify each Q-A by *where* its gold answer ends up
after chunking:

    covered  — the answer span sits inside a single chunk (retrievable).
    split    — the answer is present in the page markdown but no single chunk
               contains it whole; a chunk boundary cut through it. A *chunker*
               failure, recoverable with overlap / larger windows.
    absent   — the answer span is not in the page markdown at all. A *parser*
               failure: the content was never produced, so no chunking recovers it.
    no_parse — the parser produced no output for the answer's page at all.

`coverage = covered / total` is the *ceiling* on retrieval: a split or absent Q-A
scores zero no matter how good the retriever is. Splitting the non-covered mass
into `split` (chunker) vs `absent` / `no_parse` (parser) attributes the
parsing-retrieval disconnect to a pipeline layer — which decides whether a
parser-side intervention (best-of-N / DPO) can help at all, or whether the lever
is the chunker.

Relevance matching reuses `normalize_for_match` (whitespace / markdown-insensitive),
so this diagnostic is consistent with how RCPS itself judges a chunk relevant.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

from wigtnocr_radp.evaluation.chunkers import BaseChunker
from wigtnocr_radp.evaluation.types import QAPair, normalize_for_match

Location = Literal["covered", "split", "absent", "no_parse"]

#: Non-covered locations attributable to the parser (no chunking can recover them).
PARSER_FAULT: tuple[Location, ...] = ("absent", "no_parse")
#: Non-covered location attributable to the chunker (recoverable by re-chunking).
CHUNKER_FAULT: tuple[Location, ...] = ("split",)


def classify_answer_location(
    answer_span: str,
    page_markdown: str | None,
    chunk_texts_norm: Sequence[str],
) -> Location:
    """Classify where a gold answer lands after a chunker has run on its page.

    Args:
        answer_span: the gold answer substring (raw, un-normalized).
        page_markdown: the parser's full markdown for the answer's page, or
            ``None`` if the parser produced no output for that page.
        chunk_texts_norm: `normalize_for_match` form of every chunk on that page.

    Returns:
        One of ``covered`` / ``split`` / ``absent`` / ``no_parse``.
    """
    if page_markdown is None:
        return "no_parse"
    span = normalize_for_match(answer_span)
    if not span:
        # Degenerate gold (empty after normalization) — count as absent so it
        # can never inflate coverage.
        return "absent"
    if any(span in chunk for chunk in chunk_texts_norm):
        return "covered"
    if span in normalize_for_match(page_markdown):
        return "split"
    return "absent"


@dataclass(frozen=True)
class CoverageReport:
    """Per-chunker answer-location breakdown over a Q-A set."""

    chunker: str
    total: int
    num_chunks: int
    counts: dict[str, int]  # location -> count (covered/split/absent/no_parse)
    by_question_type: dict[str, dict[str, int]]
    by_difficulty: dict[str, dict[str, int]]
    split_examples: list[dict[str, str]]
    absent_examples: list[dict[str, str]]

    def _frac(self, *locations: str) -> float:
        if not self.total:
            return 0.0
        return sum(self.counts.get(loc, 0) for loc in locations) / self.total

    @property
    def coverage(self) -> float:
        """Fraction of Q-A whose answer lands inside a single chunk (retrieval ceiling)."""
        return self._frac("covered")

    @property
    def split_rate(self) -> float:
        """Fraction lost to chunk boundaries (chunker fault — recoverable)."""
        return self._frac(*CHUNKER_FAULT)

    @property
    def parser_fault_rate(self) -> float:
        """Fraction lost because the answer is not in the parser output (parser fault)."""
        return self._frac(*PARSER_FAULT)


def diagnose_coverage(
    qa_pairs: Sequence[QAPair],
    pages: Mapping[str, str],
    chunker: BaseChunker,
    *,
    max_examples: int = 5,
) -> CoverageReport:
    """Run one chunker over fixed parser output and tally answer locations.

    Args:
        qa_pairs: gold Q-A from KoGovDoc-RAG.
        pages: ``{page_id: parser_markdown}`` (a fixed parser's output).
        chunker: the chunking strategy under test.
        max_examples: how many split / absent Q-A to capture for inspection.
    """
    chunks = chunker.chunk_corpus(dict(pages))
    norm_by_page: dict[str, list[str]] = defaultdict(list)
    for chunk in chunks:
        norm_by_page[chunk.page_id].append(normalize_for_match(chunk.text))

    counts: Counter[str] = Counter()
    by_type: dict[str, Counter[str]] = defaultdict(Counter)
    by_diff: dict[str, Counter[str]] = defaultdict(Counter)
    split_examples: list[dict[str, str]] = []
    absent_examples: list[dict[str, str]] = []

    for qa in qa_pairs:
        page_md = pages.get(qa.page_id)
        loc = classify_answer_location(qa.answer_span, page_md, norm_by_page.get(qa.page_id, []))
        counts[loc] += 1
        by_type[qa.question_type][loc] += 1
        by_diff[qa.difficulty][loc] += 1
        if loc == "split" and len(split_examples) < max_examples:
            split_examples.append(_example(qa))
        elif loc == "absent" and len(absent_examples) < max_examples:
            absent_examples.append(_example(qa))

    return CoverageReport(
        chunker=chunker.name,
        total=len(qa_pairs),
        num_chunks=len(chunks),
        counts=dict(counts),
        by_question_type={k: dict(v) for k, v in by_type.items()},
        by_difficulty={k: dict(v) for k, v in by_diff.items()},
        split_examples=split_examples,
        absent_examples=absent_examples,
    )


def _example(qa: QAPair) -> dict[str, str]:
    return {
        "qa_id": qa.qa_id,
        "page_id": qa.page_id,
        "question_type": qa.question_type,
        "question": qa.question,
        "answer_span": qa.answer_span,
    }
