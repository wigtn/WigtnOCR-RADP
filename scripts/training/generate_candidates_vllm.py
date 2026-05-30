"""Stage 1a (vLLM variant) — Generate per-page markdown candidates via vLLM OpenAI API.

Same output format as `generate_candidates.py` but uses vLLM's OpenAI-compatible
server (with optional LoRA module) for ~3-5× speedup over HF transformers.

The vLLM server is expected to already be running with the desired LoRA loaded
as `--lora-modules <name>=<path>`; pass `--model <name>` to select it.

Usage:
    # Start vLLM container first (see docker-compose), then:
    uv run python scripts/training/generate_candidates_vllm.py \
        --base_url http://localhost:8001/v1 --model dpo-v1 \
        --temperatures 0.7 1.2 --concurrency 16 --resume
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
logger = logging.getLogger("generate_candidates_vllm")

V1_DATASETS = Path("/mnt/data1/work/wigtnOCR-v1/datasets")


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
    max_tokens: int,
    top_p: float,
    candidate_idx: int,
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
                "markdown": resp.choices[0].message.content.strip(),
            }
        except Exception as e:
            logger.warning("page %s temp=%.2f failed: %s", page_id, temperature, e)
            return None


async def amain(args: argparse.Namespace) -> int:
    rows = [json.loads(line) for line in args.train_jsonl.read_text().splitlines() if line.strip()]
    if args.limit:
        rows = rows[: args.limit]
    pages = [(f"train_{i:04d}", row) for i, row in enumerate(rows)]
    logger.info("loaded %d train pages", len(pages))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    seen: set[tuple[str, float]] = set()
    if args.resume and args.out.exists():
        for line in args.out.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            seen.add((r["page_id"], float(r["temperature"])))
        logger.info("resume: skipping %d existing (page, temp) pairs", len(seen))

    client = AsyncOpenAI(base_url=args.base_url, api_key="dummy", timeout=180.0, max_retries=3)
    sem = asyncio.Semaphore(args.concurrency)
    fout = args.out.open("a", encoding="utf-8")
    write_lock = asyncio.Lock()

    total = sum(1 for pid, _ in pages for t in args.temperatures if (pid, t) not in seen)
    logger.info("%d (page, temp) candidates to generate (concurrency=%d)", total, args.concurrency)
    if total == 0:
        return 0
    done = 0
    t0 = time.time()

    async def task(page_id: str, row: dict, temperature: float, candidate_idx: int) -> None:
        nonlocal done
        rec = await gen_one(client, sem, args.model, page_id, row, args.train_images_root,
                            temperature, args.max_new_tokens, args.top_p, candidate_idx)
        if rec is None:
            return
        async with write_lock:
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fout.flush()
        done += 1
        if done % 100 == 0 or done == total:
            elapsed = time.time() - t0
            rate = done / max(elapsed, 1e-6)
            eta_min = (total - done) / max(rate, 1e-6) / 60
            logger.info("%d/%d  (%.1f/s, %.1f min elapsed, ETA %.1f min)",
                        done, total, rate, elapsed / 60, eta_min)

    tasks = [
        asyncio.create_task(task(pid, row, t, ti))
        for pid, row in pages
        for ti, t in enumerate(args.temperatures)
        if (pid, t) not in seen
    ]
    await asyncio.gather(*tasks)
    fout.close()
    logger.info("wrote %d candidates to %s", done, args.out)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base_url", default="http://localhost:8001/v1")
    ap.add_argument("--model", default="dpo-v1", help="served-model-name (LoRA module name or base)")
    ap.add_argument("--train_jsonl", type=Path, default=Path("data/KoGovDoc-RAG/train_2667.jsonl"))
    ap.add_argument("--train_images_root", type=Path, default=V1_DATASETS)
    ap.add_argument("--out", type=Path, default=Path("output/candidates/vllm_train_candidates.jsonl"))
    ap.add_argument("--temperatures", type=float, nargs="+", default=[0.7, 1.2])
    ap.add_argument("--top_p", type=float, default=0.95)
    ap.add_argument("--max_new_tokens", type=int, default=1536)
    ap.add_argument("--concurrency", type=int, default=16)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()
    return asyncio.run(amain(args))


if __name__ == "__main__":
    raise SystemExit(main())
