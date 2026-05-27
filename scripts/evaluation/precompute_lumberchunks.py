"""Precompute LumberChunker chunks for v1's parser output (PRD §1.5).

LumberChunker calls the 122B vLLM server (GPU 1). Run this once while that
server is up; the saved chunks are then replayed by `PrecomputedChunker` in the
chunking grid — so the 122B can be taken down to free GPU 1 for retrievers.

Usage:
    uv run python scripts/evaluation/precompute_lumberchunks.py
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

from wigtnocr_radp.evaluation.llm_chunkers import LocalInstructLLM, LumberChunker, save_chunks
from wigtnocr_radp.evaluation.parser_outputs import load_parser_outputs

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("precompute_lumberchunks")

V1_PARSES = Path("/mnt/data1/work/wigtnOCR-v1/results/kogovdoc/v1_val/predictions")
VAL_JSONL = Path("data/KoGovDoc-Bench/val.jsonl")
OUT = Path("output/chunks/lumberchunker_v1.jsonl")


def main() -> int:
    pages = load_parser_outputs(V1_PARSES, VAL_JSONL)
    logger.info("LumberChunker over %d v1 pages ...", len(pages))
    chunker = LumberChunker(LocalInstructLLM())
    t0 = time.time()
    chunks = chunker.chunk_corpus(pages)
    save_chunks(chunks, OUT)
    logger.info("wrote %d chunks for %d pages -> %s (%.0fs)",
                len(chunks), len(pages), OUT, time.time() - t0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
