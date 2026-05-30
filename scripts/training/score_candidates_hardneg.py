"""Stage 1b' — Score each candidate by retrieval-reward MRR with a HARD-NEGATIVE pool.

Same idea as `score_candidates.py`, but the per-page distractor pool is no longer
a *random* sample of other-page chunks. Instead, for each page we mine the
**hardest** distractors: other-page chunks whose embedding is *closest to this
page's Q-A queries*. These are the "plausible but wrong" chunks the retriever
would actually confuse with the gold answer at deployment.

Why hard negatives? The random-100 pool is too easy — candidate scores barely
spread (v4 build dropped 1543/2248 pairs as low_gap). Hard negatives push the
retrieval task to the regime that matters, so the gap between a well-structured
parse and a poorly-structured one opens up → stronger DPO preference signal.

Pipeline per page (bge-m3 single retriever, matching the DPO-v1/v4 recipe):
  1. universe = chunks of one representative candidate per page (full train corpus).
  2. hard-neg pool = top-`--n_hardneg` other-page universe chunks by
     max-over-queries cosine sim to this page's Q-A questions. Candidate-agnostic,
     so the only thing varying between candidates is their own chunks.
  3. per candidate: index [candidate chunks + hard-neg pool], retrieve each Q-A,
     average MRR@k over k_values → per-candidate retrieval-reward score.

Output: one line per (page_id, candidate_idx) with the hard-neg retrieval score,
drop-in compatible with `build_preference_pairs.py` (field name kept as `rcps`).

Usage:
    CUDA_VISIBLE_DEVICES=1 uv run python scripts/training/score_candidates_hardneg.py \
        --candidates output/candidates/v1_k14_front.jsonl \
        --n_hardneg 100 \
        --out output/candidates/v1_k14_hardneg_scores.jsonl
"""

from __future__ import annotations

import os

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

import argparse  # noqa: E402
import json  # noqa: E402
import logging  # noqa: E402
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
from wigtnocr_radp.evaluation.types import Chunk, QAPair, ChunkRetrievalResult  # noqa: E402

_RETRIEVER_BUILDERS = {
    "bge-m3": lambda dev: BgeM3Retriever(device=dev, batch_size=32),
    "ml-e5-large": lambda dev: MultilingualE5LargeRetriever(device=dev, batch_size=32),
    "qwen3-emb-8b": lambda dev: Qwen3EmbeddingRetriever(device=dev, batch_size=8),
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("score_candidates_hardneg")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidates", type=Path, default=Path("output/candidates/v1_k14_front.jsonl"))
    ap.add_argument("--train_qa", type=Path, default=Path("output/qa_pairs/train_2667_5_4.jsonl"))
    ap.add_argument("--out", type=Path, default=Path("output/candidates/v1_k14_hardneg_scores.jsonl"))
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--k_values", type=int, nargs="+", default=[1, 5, 10])
    ap.add_argument("--n_hardneg", type=int, default=100,
                    help="number of hardest other-page chunks to use as the distractor pool")
    ap.add_argument("--retriever", default="bge-m3", choices=list(_RETRIEVER_BUILDERS),
                    help="single retriever for the reward (bge-m3 = DPO-v1/v4 recipe)")
    ap.add_argument("--limit", type=int, default=None, help="restrict to first N (page, candidate) rows")
    args = ap.parse_args()

    cand_rows = [json.loads(l) for l in args.candidates.read_text().splitlines() if l.strip()]
    if args.limit:
        cand_rows = cand_rows[: args.limit]
    by_page: dict[str, list[dict]] = defaultdict(list)
    for row in cand_rows:
        by_page[row["page_id"]].append(row)
    logger.info("loaded %d candidates across %d pages", len(cand_rows), len(by_page))

    all_qa = load_qa_pairs(args.train_qa)
    qa_by_page: dict[str, list[QAPair]] = defaultdict(list)
    for qa in all_qa:
        qa_by_page[qa.page_id].append(qa)
    logger.info("loaded %d Q-A across %d pages", len(all_qa), len(qa_by_page))

    # Universe = one representative candidate's chunks per page (full train corpus).
    chunker = ParserNativeChunker(min_chars=30)
    universe_chunks: list[Chunk] = []
    universe_owner_page: list[str] = []
    for page_id, cands in by_page.items():
        rep = next((c for c in cands if c["candidate_idx"] == 0), cands[0])
        for ck in chunker.chunk(page_id, rep["markdown"]):
            universe_chunks.append(ck)
            universe_owner_page.append(page_id)
    logger.info("universe: %d chunks across %d pages", len(universe_chunks), len(by_page))

    retriever: BaseRetriever = _RETRIEVER_BUILDERS[args.retriever](args.device)
    logger.info("retriever: %s", retriever.name)
    universe_emb = retriever.encode_documents([c.text for c in universe_chunks])
    logger.info("encoded universe, shape=%s", universe_emb.shape)

    owner_arr = np.asarray(universe_owner_page)
    not_same_page: dict[str, np.ndarray] = {pid: np.where(owner_arr != pid)[0] for pid in by_page}

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fout = args.out.open("w", encoding="utf-8")

    n_done = n_skip_no_qa = n_skip_no_chunks = 0
    t0 = time.time()

    for page_id, cands in by_page.items():
        qas = qa_by_page.get(page_id, [])
        if not qas:
            n_skip_no_qa += len(cands)
            continue
        q_emb = retriever.encode_queries([q.question for q in qas])  # (nq, d)

        # HARD-NEG pool: other-page universe chunks ranked by max-over-queries sim.
        eligible = not_same_page[page_id]
        elig_emb = universe_emb[eligible]                       # (n_elig, d)
        sims = q_emb @ elig_emb.T                               # (nq, n_elig)
        hardness = sims.max(axis=0)                             # (n_elig,) hardest for any query
        n_take = min(args.n_hardneg, len(eligible))
        top = np.argpartition(-hardness, kth=n_take - 1)[:n_take]
        pool_idx = eligible[top]
        distractor_emb = universe_emb[pool_idx]
        distractor_pool = [universe_chunks[i] for i in pool_idx]

        for cand in cands:
            cand_chunks = chunker.chunk(page_id, cand["markdown"])
            if not cand_chunks:
                n_skip_no_chunks += 1
                fout.write(json.dumps({
                    "page_id": page_id, "candidate_idx": cand["candidate_idx"],
                    "temperature": cand.get("temperature"), "rcps": 0.0, "n_qa": len(qas),
                    "n_chunks": 0, "skipped": "no_chunks",
                }, ensure_ascii=False) + "\n")
                continue

            cand_emb = retriever.encode_documents([c.text for c in cand_chunks])
            doc_emb = np.concatenate([cand_emb, distractor_emb], axis=0)
            pool_chunks = list(cand_chunks) + list(distractor_pool)
            qsims = q_emb @ doc_emb.T
            max_k = max(args.k_values)
            top_k_eff = min(max_k, doc_emb.shape[0])
            top_idxs = np.argpartition(-qsims, kth=top_k_eff - 1, axis=1)[:, :top_k_eff]

            results = []
            for qi, qa in enumerate(qas):
                idxs = top_idxs[qi]
                ranked_idxs = idxs[np.argsort(-qsims[qi, idxs])]
                ranked = tuple((pool_chunks[j], float(qsims[qi, j])) for j in ranked_idxs)
                results.append(ChunkRetrievalResult(qa_id=qa.qa_id, ranked=ranked))

            scores: list[float] = []
            for k in args.k_values:
                for rr, qa in zip(results, qas):
                    scores.append(mrr_at_k(rr, qa, k))
            rcps = float(np.mean(scores)) if scores else 0.0

            fout.write(json.dumps({
                "page_id": page_id, "candidate_idx": cand["candidate_idx"],
                "temperature": cand.get("temperature"), "rcps": round(rcps, 6),
                "n_qa": len(qas), "n_chunks": len(cand_chunks), "n_hardneg": n_take,
            }, ensure_ascii=False) + "\n")
            n_done += 1

        if n_done % 2000 == 0 and n_done > 0:
            el = time.time() - t0
            logger.info("scored %d candidates in %.1f min (%.1f/s)", n_done, el / 60, n_done / max(el, 1))

    fout.close()
    logger.info("wrote %d scored candidates to %s  (skipped: no_qa=%d, no_chunks=%d)",
                n_done, args.out, n_skip_no_qa, n_skip_no_chunks)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
