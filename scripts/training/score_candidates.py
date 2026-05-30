"""Stage 1b — Score each candidate by *page-local RCPS with a distractor pool*.

For each (page, candidate) row produced by `generate_candidates.py`:

1. Chunk the candidate markdown (parser_native, min_chars=30).
2. Index those chunks together with a fixed pool of `--n_distractors` chunks
   sampled from *other* train pages (held-out from the same train set). The
   distractor pool is the same for every candidate scored on the same page, so
   the *only* thing that varies is the candidate's own chunks.
3. For each Q-A whose page_id matches: retrieve top-k from the merged pool and
   compute MRR@k. Average across (retriever, k) → per-candidate RCPS score.

Why a distractor pool? With only the candidate's own ~3-5 chunks indexed, MRR
saturates at ~1.0 and gives no useful preference signal. With ~100 distractors
the retrieval task is non-trivial and the scores spread out enough to rank
candidates within a page.

The distractor chunks come from a *random* parser output per page (we use v1's
own candidate-0 = temp 0.7), but the pool is sampled once per pool-seed and
re-used across all candidates of all pages — so the noise is shared.

Output: `output/candidates/v1_train_candidate_scores.jsonl`
        one line per (page_id, candidate_idx) with the page-local RCPS score.

Usage:
    CUDA_VISIBLE_DEVICES=1 uv run python scripts/training/score_candidates.py \
        --n_distractors 100 --pool_seed 42
"""

from __future__ import annotations

import os

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

import argparse  # noqa: E402
import json  # noqa: E402
import logging  # noqa: E402
import random  # noqa: E402
import time  # noqa: E402
from collections import defaultdict  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

from wigtnocr_radp.evaluation import ParserNativeChunker  # noqa: E402
from wigtnocr_radp.evaluation.metrics import mrr_at_k  # noqa: E402
from wigtnocr_radp.evaluation.rcps import load_qa_pairs  # noqa: E402
from wigtnocr_radp.evaluation.retrievers import (  # noqa: E402
    BaseRetriever, BgeM3Retriever, MultilingualE5LargeRetriever, Qwen3EmbeddingRetriever,
)
from wigtnocr_radp.evaluation.types import Chunk, QAPair  # noqa: E402

_RETRIEVER_BUILDERS = {
    "bge-m3": lambda dev: BgeM3Retriever(device=dev, batch_size=32),
    "ml-e5-large": lambda dev: MultilingualE5LargeRetriever(device=dev, batch_size=32),
    "qwen3-emb-8b": lambda dev: Qwen3EmbeddingRetriever(device=dev, batch_size=8),
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("score_candidates")


def chunk_markdown(page_id: str, md: str, chunker: ParserNativeChunker) -> list[Chunk]:
    return chunker.chunk(page_id, md)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidates", type=Path, default=Path("output/candidates/v1_train_candidates.jsonl"))
    ap.add_argument("--train_qa", type=Path, default=Path("output/qa_pairs/train_2667_5_4.jsonl"))
    ap.add_argument("--out", type=Path, default=Path("output/candidates/v1_train_candidate_scores.jsonl"))
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--k_values", type=int, nargs="+", default=[1, 5, 10])
    ap.add_argument("--n_distractors", type=int, default=100)
    ap.add_argument("--pool_seed", type=int, default=42)
    ap.add_argument("--retrievers", nargs="+", default=["bge-m3"],
                    choices=list(_RETRIEVER_BUILDERS),
                    help="one or more retrievers; the per-Q-A RCPS averages over all of them × k")
    ap.add_argument("--limit", type=int, default=None, help="restrict to first N (page, candidate) rows")
    args = ap.parse_args()

    # Load candidates and group by page
    cand_rows = [json.loads(l) for l in args.candidates.read_text().splitlines() if l.strip()]
    if args.limit:
        cand_rows = cand_rows[: args.limit]
    by_page: dict[str, list[dict]] = defaultdict(list)
    for row in cand_rows:
        by_page[row["page_id"]].append(row)
    logger.info("loaded %d candidates across %d pages", len(cand_rows), len(by_page))

    # Q-A indexed by page
    all_qa = load_qa_pairs(args.train_qa)
    qa_by_page: dict[str, list[QAPair]] = defaultdict(list)
    for qa in all_qa:
        qa_by_page[qa.page_id].append(qa)
    logger.info("loaded %d Q-A across %d pages", len(all_qa), len(qa_by_page))

    # Pre-encode the entire distractor *universe* (candidate-0 chunks of every
    # page) once. Per-page distractor pools then sample from this universe
    # *excluding same-page chunks*, using page_id-seeded RNG so the sample is
    # deterministic per page. This avoids leaking a page's own chunks into its
    # distractor set (which would distort the ranking between candidates).
    chunker = ParserNativeChunker(min_chars=30)
    universe_chunks: list[Chunk] = []
    universe_owner_page: list[str] = []
    for page_id, cands in by_page.items():
        c0 = next((c for c in cands if c["candidate_idx"] == 0), cands[0])
        for ck in chunk_markdown(page_id, c0["markdown"], chunker):
            universe_chunks.append(ck)
            universe_owner_page.append(page_id)
    logger.info("distractor universe: %d chunks across %d pages", len(universe_chunks), len(by_page))

    retrievers: list[BaseRetriever] = [_RETRIEVER_BUILDERS[name](args.device) for name in args.retrievers]
    logger.info("retrievers: %s", [r.name for r in retrievers])
    # Encode the distractor universe once per retriever, keyed by retriever name.
    universe_emb_by_r: dict[str, np.ndarray] = {}
    for r in retrievers:
        universe_emb_by_r[r.name] = r.encode_documents([c.text for c in universe_chunks])
        logger.info("encoded distractor universe [%s], shape=%s", r.name, universe_emb_by_r[r.name].shape)

    # Map page_id → list of universe indices NOT belonging to that page, for fast filtering.
    owner_arr = np.asarray(universe_owner_page)
    not_same_page: dict[str, np.ndarray] = {
        pid: np.where(owner_arr != pid)[0] for pid in by_page
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fout = args.out.open("w", encoding="utf-8")

    n_done = 0
    n_skipped_no_qa = 0
    n_skipped_no_chunks = 0
    t0 = time.time()
    from wigtnocr_radp.evaluation.types import ChunkRetrievalResult

    for page_id, cands in by_page.items():
        qas = qa_by_page.get(page_id, [])
        if not qas:
            n_skipped_no_qa += len(cands)
            continue
        # Encode Q-A queries once per page, per retriever.
        q_emb_by_r = {r.name: r.encode_queries([q.question for q in qas]) for r in retrievers}

        # Page-specific distractor pool: deterministic sample from other pages' chunks.
        eligible = not_same_page[page_id]
        n_take = min(args.n_distractors, len(eligible))
        page_rng = np.random.default_rng(abs(hash(page_id)) % (2**32) ^ args.pool_seed)
        pool_idx = page_rng.choice(eligible, size=n_take, replace=False)
        distractor_emb_by_r = {name: emb[pool_idx] for name, emb in universe_emb_by_r.items()}
        distractor_pool = [universe_chunks[i] for i in pool_idx]

        for cand in cands:
            cand_chunks = chunk_markdown(page_id, cand["markdown"], chunker)
            if not cand_chunks:
                n_skipped_no_chunks += 1
                fout.write(json.dumps({
                    "page_id": page_id, "candidate_idx": cand["candidate_idx"],
                    "temperature": cand["temperature"], "rcps": 0.0, "n_qa": len(qas),
                    "n_chunks": 0, "skipped": "no_chunks",
                }, ensure_ascii=False) + "\n")
                continue

            # Average MRR across all (retriever, k) — the RCPS definition.
            scores: list[float] = []
            for r in retrievers:
                cand_emb = r.encode_documents([c.text for c in cand_chunks])
                doc_emb = np.concatenate([cand_emb, distractor_emb_by_r[r.name]], axis=0)
                pool_chunks = list(cand_chunks) + list(distractor_pool)
                sims = q_emb_by_r[r.name] @ doc_emb.T
                max_k = max(args.k_values)
                top_k_eff = min(max_k, doc_emb.shape[0])
                top_idxs = np.argpartition(-sims, kth=top_k_eff - 1, axis=1)[:, :top_k_eff]
                results = []
                for qi, qa in enumerate(qas):
                    idxs = top_idxs[qi]
                    ranked_idxs = idxs[np.argsort(-sims[qi, idxs])]
                    ranked = tuple((pool_chunks[j], float(sims[qi, j])) for j in ranked_idxs)
                    results.append(ChunkRetrievalResult(qa_id=qa.qa_id, ranked=ranked))
                for k in args.k_values:
                    for rr, qa in zip(results, qas):
                        scores.append(mrr_at_k(rr, qa, k))
            rcps = float(np.mean(scores)) if scores else 0.0

            fout.write(json.dumps({
                "page_id": page_id, "candidate_idx": cand["candidate_idx"],
                "temperature": cand["temperature"], "rcps": round(rcps, 6),
                "n_qa": len(qas), "n_chunks": len(cand_chunks),
                "n_retrievers": len(retrievers),
            }, ensure_ascii=False) + "\n")
            n_done += 1

        if n_done % 500 == 0 and n_done > 0:
            elapsed = time.time() - t0
            logger.info("scored %d candidates in %.1f min (%.1f/s)", n_done, elapsed / 60, n_done / max(elapsed, 1))

    fout.close()
    logger.info(
        "wrote %d scored candidates to %s  (skipped: no_qa=%d, no_chunks=%d)",
        n_done, args.out, n_skipped_no_qa, n_skipped_no_chunks,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
