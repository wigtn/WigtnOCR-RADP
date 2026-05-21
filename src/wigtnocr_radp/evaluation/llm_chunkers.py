"""LLM-based chunking baselines for the RCPS chunking grid (PRD §1.5 / §5.3).

LumberChunker (Duarte et al., EMNLP 2024 Findings; arXiv:2406.17526): a document
is split into base segments; an LLM is repeatedly asked which upcoming segment
first introduces a notable topic shift, and the document is cut there. Chunks
are therefore topically coherent and variable-length.

The reference paper uses Gemini; here a local instruction model is used (no API
budget — see memory: api-budget-constraint). The model id is configurable.
"""

from __future__ import annotations

import logging
import re

from wigtnocr_radp.evaluation.types import Chunk

logger = logging.getLogger("wigtnocr_radp.evaluation.llm_chunkers")


class LocalInstructLLM:
    """Instruction LLM via a local vLLM OpenAI-compatible server.

    The model runs in a separate vLLM container (soundmind-model-serving) — this
    class is just an HTTP client, so LumberChunker holds no GPU memory itself.
    Default targets the `qwen3.5-122b-gptq-vl` service (122B on GPU 1, port 8020).
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8020/v1",
        model: str = "qwen3.5-122b-vl",
    ) -> None:
        from openai import OpenAI

        self.client = OpenAI(base_url=base_url, api_key="EMPTY", timeout=120.0)
        self.model = model

    def complete(self, prompt: str, max_new_tokens: int = 32) -> str:
        """One short completion. Thinking is disabled — we only want a number."""
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_new_tokens,
            temperature=0.0,
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        )
        return resp.choices[0].message.content or ""


def _base_segments(markdown: str) -> list[str]:
    """Split markdown into base units: non-empty lines (table rows kept whole)."""
    return [ln.strip() for ln in markdown.splitlines() if ln.strip()]


class LumberChunker:
    """LLM narrative-boundary chunker (arXiv:2406.17526).

    Args:
        llm: a `LocalInstructLLM` (or any object with `.complete(prompt) -> str`).
        window: number of upcoming base segments shown to the LLM per decision.
        max_segments_per_chunk: hard cap so a chunk cannot grow unbounded.
    """

    def __init__(self, llm: LocalInstructLLM, window: int = 8, max_segments_per_chunk: int = 12) -> None:
        self.llm = llm
        self.window = window
        self.max_segments_per_chunk = max_segments_per_chunk

    @property
    def name(self) -> str:
        return "lumberchunker"

    _PROMPT = (
        "아래는 한 문서를 순서대로 나눈 구획들이다. 구획 {start}부터 읽었을 때, "
        "내용·주제가 처음으로 뚜렷하게 바뀌는 구획의 번호를 답하라. "
        "끝까지 바뀌지 않으면 'none'이라고 답하라. 숫자 또는 'none'만 출력하라.\n\n{body}"
    )

    def _boundary(self, segments: list[str], start: int) -> int:
        """Return the index where a topic shift first occurs, or the window end."""
        end = min(start + self.window, len(segments))
        body = "\n".join(f"[{i}] {segments[i][:200]}" for i in range(start, end))
        reply = self.llm.complete(self._PROMPT.format(start=start, body=body))
        m = re.search(r"\d+", reply)
        if m:
            idx = int(m.group())
            if start < idx <= end:  # a real cut strictly after `start`
                return idx
        return end

    def chunk(self, page_id: str, markdown: str) -> list[Chunk]:
        segments = _base_segments(markdown)
        if not segments:
            return []
        if len(segments) == 1:
            return [Chunk(chunk_id=f"{page_id}::{self.name}#0", page_id=page_id, text=segments[0])]

        chunks: list[Chunk] = []
        pos = 0
        while pos < len(segments):
            cut = self._boundary(segments, pos)
            cut = min(cut, pos + self.max_segments_per_chunk)
            text = "\n".join(segments[pos:cut])
            chunks.append(
                Chunk(chunk_id=f"{page_id}::{self.name}#{len(chunks)}", page_id=page_id, text=text)
            )
            pos = cut
        return chunks

    def chunk_corpus(self, pages: dict[str, str]) -> list[Chunk]:
        out: list[Chunk] = []
        for i, (page_id, md) in enumerate(pages.items(), 1):
            out.extend(self.chunk(page_id, md))
            if i % 25 == 0:
                logger.info("LumberChunker: %d/%d pages", i, len(pages))
        return out
