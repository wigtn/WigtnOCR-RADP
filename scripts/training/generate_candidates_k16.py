"""Stage 1a (vLLM) — Generate 14 additional v1 candidates per page (K=2→K=16).

Existing candidates: output/candidates/v1_train_candidates.jsonl
  = 5,334 candidates / 2,667 pages × K=2 (temp 0.7, 1.2, top_p 0.95)

This script adds 14 new candidates per page with a diverse (temp, top_p) schedule
to maximise sampling spread and produce larger candidate-RCPS gaps for stronger
DPO preference signal.

Schedule (14 samples per page):
  (0.3, 0.9) × 2 ; (0.5, 0.9) × 2 ; (0.7, 1.0) × 1 ;
  (1.0, 0.95) × 2 ; (1.2, 1.0) × 1 ;
  (1.5, 0.9) × 2 ; (1.8, 0.85) × 2 ; (2.0, 0.8) × 2

Output: output/candidates/v1_train_candidates_k16_new14.jsonl
  Each record has candidate_idx = 2..15 (continues from existing 0,1)
  to avoid collision when merged with existing K=2 file.

Total candidates to generate: 14 × 2,667 = 37,338
vLLM async concurrency=32 → ~30-40 min on v1-merged @ GPU 1.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import logging
import time
from pathlib import Path

from openai import AsyncOpenAI

from wigtnocr_radp.training.data import remap_train_image_path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("gen_k16")

V1_DATASETS = Path("/mnt/data1/work/wigtnOCR-v1/datasets")

# (temp, top_p, n_samples) — 14 samples/page total
SCHEDULE: list[tuple[float, float, int]] = [
    (0.3, 0.9, 2),    # low-temp focused
    (0.5, 0.9, 2),
    (0.7, 1.0, 1),    # 기존 0.7과 다른 top_p (top_p=1.0)
    (1.0, 0.95, 2),
    (1.2, 1.0, 1),    # 기존 1.2와 다른 top_p (top_p=1.0)
    (1.5, 0.9, 2),
    (1.8, 0.85, 2),
    (2.0, 0.8, 2),    # high-temp extreme
]


def encode_image(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode()


async def gen_one(
    client: AsyncOpenAI,
    sem: asyncio.Semaphore,
    model: str,
    page_id: str,
    row: dict,
    images_root: Path,
    temperature: float,
    top_p: float,
    candidate_idx: int,
    max_tokens: int,
) -> dict | None:
    async with sem:
        try:
            img_path = remap_train_image_path(row["images"][0], images_root)
            b64 = encode_image(img_path)
            system = row["messages"][0]["content"]
            user = row["messages"][1]["content"].replace("<image>", "").lstrip()
            resp = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                        {"type": "text", "text": user},
                    ]},
                ],
                temperature=temperature, top_p=top_p, max_tokens=max_tokens,
            )
            return {
                "page_id": page_id,
                "doc_id": row["images"][0].split("/")[-2],
                "candidate_idx": candidate_idx,
                "temperature": temperature,
                "top_p": top_p,
                "markdown": resp.choices[0].message.content.strip(),
            }
        except Exception as e:
            logger.warning("page %s idx=%d temp=%.2f top_p=%.2f failed: %s",
                           page_id, candidate_idx, temperature, top_p, e)
            return None


async def amain(args: argparse.Namespace) -> int:
    rows = [json.loads(line) for line in args.train_jsonl.read_text().splitlines() if line.strip()]
    if args.limit:
        rows = rows[: args.limit]
    pages_all = [(f"train_{i:04d}", row) for i, row in enumerate(rows)]
    end = args.end if args.end is not None else len(pages_all)
    pages = pages_all[args.start:end]
    logger.info("loaded %d train pages (slice [%d:%d] of %d)", len(pages), args.start, end, len(pages_all))

    # Build the per-page list of (candidate_idx, temp, top_p)
    # candidate_idx starts at 2 (0 and 1 are existing K=2 file)
    schedule_flat: list[tuple[int, float, float]] = []
    idx = 2
    for temp, top_p, n in SCHEDULE:
        for _ in range(n):
            schedule_flat.append((idx, temp, top_p))
            idx += 1
    assert len(schedule_flat) == 14, f"got {len(schedule_flat)} samples, expected 14"
    logger.info("schedule: %d new samples per page → %d total", len(schedule_flat), len(schedule_flat) * len(pages))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    seen: set[tuple[str, int]] = set()
    if args.resume and args.out.exists():
        for line in args.out.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            seen.add((r["page_id"], int(r["candidate_idx"])))
        logger.info("resume: skipping %d existing (page, idx) pairs", len(seen))

    client = AsyncOpenAI(base_url=args.base_url, api_key="dummy", timeout=180.0, max_retries=3)
    sem = asyncio.Semaphore(args.concurrency)
    fout = args.out.open("a", encoding="utf-8")
    write_lock = asyncio.Lock()

    total_jobs = [
        (pid, row, cand_idx, temp, top_p)
        for pid, row in pages
        for cand_idx, temp, top_p in schedule_flat
        if (pid, cand_idx) not in seen
    ]
    total = len(total_jobs)
    logger.info("%d new (page, candidate_idx) candidates to generate (concurrency=%d)",
                total, args.concurrency)
    if total == 0:
        return 0
    done = 0
    t0 = time.time()

    async def task(page_id: str, row: dict, cand_idx: int, temp: float, top_p: float) -> None:
        nonlocal done
        rec = await gen_one(client, sem, args.model, page_id, row, args.train_images_root,
                            temp, top_p, cand_idx, args.max_new_tokens)
        if rec is None:
            return
        async with write_lock:
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fout.flush()
        done += 1
        if done % 500 == 0 or done == total:
            elapsed = time.time() - t0
            rate = done / max(elapsed, 1e-6)
            eta_min = (total - done) / max(rate, 1e-6) / 60
            logger.info("%d/%d  (%.1f/s, %.1f min elapsed, ETA %.1f min)",
                        done, total, rate, elapsed / 60, eta_min)

    tasks = [asyncio.create_task(task(pid, row, ci, t, tp))
             for (pid, row, ci, t, tp) in total_jobs]
    await asyncio.gather(*tasks)
    fout.close()
    logger.info("wrote %d candidates to %s", done, args.out)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base_url", default="http://localhost:8002/v1")
    ap.add_argument("--model", default="v1", help="served-model-name on vllm-v1")
    ap.add_argument("--train_jsonl", type=Path, default=Path("data/KoGovDoc-RAG/train_2667.jsonl"))
    ap.add_argument("--train_images_root", type=Path, default=V1_DATASETS)
    ap.add_argument("--out", type=Path,
                    default=Path("output/candidates/v1_train_candidates_k16_new14.jsonl"))
    ap.add_argument("--max_new_tokens", type=int, default=1536)
    ap.add_argument("--concurrency", type=int, default=32)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--start", type=int, default=0, help="page index start (inclusive)")
    ap.add_argument("--end", type=int, default=None, help="page index end (exclusive)")
    ap.add_argument("--resume", action="store_true", default=True)
    args = ap.parse_args()
    return asyncio.run(amain(args))


if __name__ == "__main__":
    raise SystemExit(main())
