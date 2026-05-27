"""Chunking strategies — turn parser markdown output into retrievable chunks.

All chunkers consume `(page_id, markdown)` pairs and produce `list[Chunk]`.
ChunkID is deterministic: `f"{page_id}::{strategy}#{i}"`.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod

from wigtnocr_radp.evaluation.types import Chunk


class BaseChunker(ABC):
    """Abstract chunker. Implementations return a flat list[Chunk]."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier used in chunk_id and config keys."""

    @abstractmethod
    def chunk(self, page_id: str, markdown: str) -> list[Chunk]:
        """Split markdown into chunks. Empty input → empty output."""

    def chunk_corpus(self, pages: dict[str, str]) -> list[Chunk]:
        """Apply chunking across many pages."""
        out: list[Chunk] = []
        for page_id, md in pages.items():
            out.extend(self.chunk(page_id, md))
        return out


class FixedSizeChunker(BaseChunker):
    """Split text into fixed-character windows with optional overlap.

    Snaps boundaries to whitespace when possible to avoid cutting words.
    """

    def __init__(self, size: int = 500, overlap: int = 0) -> None:
        if size <= 0:
            raise ValueError(f"size must be > 0, got {size}")
        if overlap < 0 or overlap >= size:
            raise ValueError(f"overlap must be in [0, size), got {overlap}")
        self.size = size
        self.overlap = overlap

    @property
    def name(self) -> str:
        return f"fixed{self.size}" + (f"_ov{self.overlap}" if self.overlap else "")

    def chunk(self, page_id: str, markdown: str) -> list[Chunk]:
        text = markdown.strip()
        if not text:
            return []
        chunks: list[Chunk] = []
        step = self.size - self.overlap
        i = 0
        idx = 0
        n = len(text)
        while i < n:
            end = min(i + self.size, n)
            # Snap end back to a word boundary, but only if that still advances
            # past i+overlap. Otherwise `i = end - overlap` could stall (or move
            # backwards) and loop forever on whitespace-sparse text with overlap>0.
            if end < n and not text[end].isspace():
                snap = text.rfind(" ", i + step // 2, end)
                if snap > i + self.overlap:
                    end = snap
            piece = text[i:end].strip()
            if piece:
                chunks.append(
                    Chunk(
                        chunk_id=f"{page_id}::{self.name}#{idx}",
                        page_id=page_id,
                        text=piece,
                    )
                )
                idx += 1
            if end >= n:
                break
            i = end - self.overlap
        return chunks


_HEADER_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


class MarkdownHeaderChunker(BaseChunker):
    """Split on markdown headers up to a given level.

    A chunk = (header line + everything until the next same-or-higher-level header).
    Pages without any header fall back to a single chunk (the whole page).
    """

    def __init__(self, max_level: int = 3) -> None:
        if not 1 <= max_level <= 6:
            raise ValueError(f"max_level must be in [1, 6], got {max_level}")
        self.max_level = max_level

    @property
    def name(self) -> str:
        return f"md_h{self.max_level}"

    def chunk(self, page_id: str, markdown: str) -> list[Chunk]:
        text = markdown.strip()
        if not text:
            return []

        # Find header positions at or below max_level
        boundaries: list[int] = []
        for m in _HEADER_RE.finditer(text):
            level = len(m.group(1))
            if level <= self.max_level:
                boundaries.append(m.start())

        if not boundaries:
            return [
                Chunk(
                    chunk_id=f"{page_id}::{self.name}#0",
                    page_id=page_id,
                    text=text,
                )
            ]

        # Add a preamble chunk if content exists before the first header
        chunks: list[Chunk] = []
        idx = 0
        if boundaries[0] > 0:
            preamble = text[: boundaries[0]].strip()
            if preamble:
                chunks.append(
                    Chunk(
                        chunk_id=f"{page_id}::{self.name}#{idx}",
                        page_id=page_id,
                        text=preamble,
                    )
                )
                idx += 1

        # Slice between consecutive header boundaries
        for i, start in enumerate(boundaries):
            end = boundaries[i + 1] if i + 1 < len(boundaries) else len(text)
            piece = text[start:end].strip()
            if piece:
                chunks.append(
                    Chunk(
                        chunk_id=f"{page_id}::{self.name}#{idx}",
                        page_id=page_id,
                        text=piece,
                    )
                )
                idx += 1
        return chunks


class ParserNativeChunker(BaseChunker):
    """Use the parser output's natural paragraph boundaries (blank lines).

    Falls back to whole-page chunk if no blank lines present.
    """

    def __init__(self, min_chars: int = 30) -> None:
        self.min_chars = min_chars

    @property
    def name(self) -> str:
        return "parser_native"

    def chunk(self, page_id: str, markdown: str) -> list[Chunk]:
        text = markdown.strip()
        if not text:
            return []
        pieces = [p.strip() for p in re.split(r"\n\s*\n+", text)]
        pieces = [p for p in pieces if len(p) >= self.min_chars]
        if not pieces:
            return [
                Chunk(
                    chunk_id=f"{page_id}::{self.name}#0",
                    page_id=page_id,
                    text=text,
                )
            ]
        return [
            Chunk(
                chunk_id=f"{page_id}::{self.name}#{i}",
                page_id=page_id,
                text=p,
            )
            for i, p in enumerate(pieces)
        ]
