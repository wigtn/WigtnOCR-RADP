"""Pre-compute BGE-M3 chunk embeddings for RADP-B contrastive training.

For each page in the train fold (page_split_v1.json -> train_pages):
    1. Load GT markdown from KoGovDoc-Bench val.jsonl.
    2. Chunk it (default: MarkdownHeaderChunker max_level=3 — RCPS sanity best).
    3. Encode each chunk with BGE-M3 (L2-normalized).
    4. For each Q-A on this page, mark the chunk that contains the answer_span
       (= positive chunk for that Q-A). Multiple Q-A can share a chunk.

Output: `data/KoGovDoc-RAG/bge_m3_cache_v1/`
    - embeddings.npy        (N, 1024) float32
    - meta.jsonl            N lines: {chunk_id, page_id, qa_id, answer_span}
      qa_id is null for chunks that are NOT positive for any Q-A on the page
      (these chunks serve as same-page hard negatives during training).
"""

from __future__ import annotations

import argparse
import json
import logging
from collections import Counter
from pathlib import Path

import numpy as np

from wigtnocr_radp.evaluation.chunkers import (
    FixedSizeChunker,
    MarkdownHeaderChunker,
    ParserNativeChunker,
)
from wigtnocr_radp.evaluation.parser_outputs import build_page_id_index
from wigtnocr_radp.evaluation.retrievers import BgeM3Retriever
from wigtnocr_radp.training.contrastive import BgeM3EmbeddingCache, ChunkMeta


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("precompute_bge_cache")


CHUNKERS = {
    "md_h3": MarkdownHeaderChunker(max_level=3),
    "parser_native": ParserNativeChunker(min_chars=30),
    "fixed500": FixedSizeChunker(size=500),
}


def load_gt_markdown(val_jsonl: Path) -> dict[str, str]:
    """Return {page_id: gt_markdown} for all val.jsonl rows."""
    out: dict[str, str] = {}
    with val_jsonl.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            d = json.loads(line)
            out[f"val_{i:04d}"] = d["messages"][2]["content"]
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", type=Path, default=Path("data/KoGovDoc-RAG/page_split_v1.json"))
    ap.add_argument("--qa", type=Path, default=Path("data/KoGovDoc-RAG/qa_pairs_v1.jsonl"))
    ap.add_argument("--val_jsonl", type=Path, default=Path("data/KoGovDoc-Bench/val.jsonl"))
    ap.add_argument("--chunker", choices=tuple(CHUNKERS), default="md_h3")
    ap.add_argument("--out_dir", type=Path, default=Path("data/KoGovDoc-RAG/bge_m3_cache_v1"))
    ap.add_argument("--fold", choices=("train", "eval", "all"), default="train")
    ap.add_argument("--device", default="cuda:1")
    ap.add_argument("--batch_size", type=int, default=64)
    args = ap.parse_args()

    split = json.loads(args.split.read_text())
    if args.fold == "train":
        page_ids = set(split["train_pages"])
    elif args.fold == "eval":
        page_ids = set(split["eval_pages"])
    else:
        page_ids = set(split["train_pages"]) | set(split["eval_pages"])
    logger.info("fold=%s, %d pages", args.fold, len(page_ids))

    # Load GT markdown only for pages we need
    gt_all = load_gt_markdown(args.val_jsonl)
    pages = {pid: gt_all[pid] for pid in page_ids if pid in gt_all}
    missing = page_ids - pages.keys()
    if missing:
        logger.warning("%d pages missing from val.jsonl: %s", len(missing), list(missing)[:5])

    # Chunk
    chunker = CHUNKERS[args.chunker]
    all_chunks = chunker.chunk_corpus(pages)
    chunks_by_page: dict[str, list[int]] = {}
    for idx, c in enumerate(all_chunks):
        chunks_by_page.setdefault(c.page_id, []).append(idx)
    logger.info("chunker=%s produced %d chunks over %d pages",
                chunker.name, len(all_chunks), len(chunks_by_page))

    # Map each Q-A on these pages to its positive chunk (the one containing answer_span)
    qa_positive: dict[str, list[tuple[str, str]]] = {}  # chunk_id -> list of (qa_id, answer_span)
    qa_count = 0
    qa_orphan = 0
    with args.qa.open("r", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            pid = d["page_id"]
            if pid not in page_ids:
                continue
            qa_count += 1
            candidates = chunks_by_page.get(pid, [])
            hit_chunk_id: str | None = None
            for ci in candidates:
                if all_chunks[ci].contains_answer(d["answer_span"]):
                    hit_chunk_id = all_chunks[ci].chunk_id
                    break
            if hit_chunk_id is None:
                qa_orphan += 1
                logger.warning(
                    "qa_id=%s on %s: no chunk contains answer_span %r (chunker boundary issue)",
                    d["qa_id"][:8], pid, d["answer_span"][:30],
                )
                continue
            qa_positive.setdefault(hit_chunk_id, []).append((d["qa_id"], d["answer_span"]))

    logger.info(
        "Q-A coverage: %d/%d on this fold (orphan=%d, %.1f%%)",
        qa_count - qa_orphan, qa_count, qa_orphan,
        100.0 * qa_orphan / max(qa_count, 1),
    )

    # Encode with BGE-M3
    logger.info("loading BGE-M3 on %s", args.device)
    retr = BgeM3Retriever(device=args.device, batch_size=args.batch_size)
    texts = [c.text for c in all_chunks]
    embeddings = retr.encode_documents(texts)
    logger.info("encoded shape: %s, norm sample: %.4f",
                embeddings.shape, float(np.linalg.norm(embeddings[0])))

    # Build metas; explode per Q-A so each (chunk, qa_id) gets its own meta row
    # — actually we keep ONE row per chunk; the multiple Q-A using the same
    # chunk all reference that row. So we duplicate chunk rows once per Q-A
    # that points at them, to make BgeM3EmbeddingCache.chunks_for_qa easy.
    final_embs: list[np.ndarray] = []
    final_metas: list[ChunkMeta] = []
    row = 0
    for ci, chunk in enumerate(all_chunks):
        emb = embeddings[ci]
        qa_hits = qa_positive.get(chunk.chunk_id, [])
        if qa_hits:
            for qa_id, ans_span in qa_hits:
                final_embs.append(emb)
                final_metas.append(
                    ChunkMeta(
                        chunk_id=chunk.chunk_id,
                        page_id=chunk.page_id,
                        answer_span=ans_span,
                        qa_id=qa_id,
                        row=row,
                    )
                )
                row += 1
        else:
            # non-positive chunk: kept as same-page hard negative material
            final_embs.append(emb)
            final_metas.append(
                ChunkMeta(
                    chunk_id=chunk.chunk_id,
                    page_id=chunk.page_id,
                    answer_span=None,
                    qa_id=None,
                    row=row,
                )
            )
            row += 1

    cache = BgeM3EmbeddingCache(np.stack(final_embs), final_metas)
    out_dir = args.out_dir / args.fold / chunker.name
    cache.save(out_dir)
    logger.info("wrote cache to %s (rows=%d)", out_dir, len(final_metas))

    # Quick stats for the manifest
    n_positive = sum(1 for m in final_metas if m.qa_id is not None)
    n_negative = sum(1 for m in final_metas if m.qa_id is None)
    n_chunks = len({m.chunk_id for m in final_metas})
    page_count = Counter(m.page_id for m in final_metas)

    summary = {
        "fold": args.fold,
        "chunker": chunker.name,
        "num_pages": len(pages),
        "num_chunks_unique": n_chunks,
        "num_meta_rows": len(final_metas),
        "num_positive_meta_rows": n_positive,
        "num_negative_meta_rows": n_negative,
        "qa_orphan_count": qa_orphan,
        "qa_total_in_fold": qa_count,
        "embeddings_dtype": str(cache.embeddings.dtype),
        "embeddings_shape": list(cache.embeddings.shape),
        "embedding_size_mb": float(cache.embeddings.nbytes / 1e6),
        "median_chunks_per_page": int(np.median(list(page_count.values()))),
    }
    (out_dir / "manifest.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
