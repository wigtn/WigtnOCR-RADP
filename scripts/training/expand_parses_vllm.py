"""Expand existing eval parses (73 pages) to full 294-page fold via vLLM multi-LoRA.

Reuses the same vLLM container that serves multiple adapters concurrently.
For each (model, page) pair where the parse file doesn't yet exist, builds
an OpenAI chat-completion request with the image and saves the response.

Usage:
    uv run python scripts/training/expand_parses_vllm.py \
        --base_url http://localhost:8001/v1 \
        --concurrency 16
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

from wigtnocr_radp.evaluation.parser_outputs import build_page_id_index
from wigtnocr_radp.training.data import remap_image_path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("expand_parses_vllm")

# (vLLM lora-module name) → (output dir under parses_full)
MODEL_TO_DIR = {
    "lambda00": "radp_b_lambda00_eval",
    "lambda01": "radp_b_lambda01_eval",
    "lambda03": "radp_b_lambda03_eval",
    "lambda05": "radp_b_lambda05_eval",
    "dpo-v1": "radp_dpo_eval",
    "dpo-v2": "radp_dpo_v2_eval",
    "dpo-v3": "radp_dpo_v3_eval",
    "dpo-v4": "radp_dpo_v4_eval",
    "simpo": "radp_simpo_eval",
    "dpo-v1-seed123": "radp_dpo_seed123_eval",
    "dpo-v1-seed999": "radp_dpo_seed999_eval",
}


def load_image_b64(path: Path, max_pixels: int = 1_048_576) -> str:
    from PIL import Image
    img = Image.open(path).convert("RGB")
    w, h = img.size
    if w * h > max_pixels:
        scale = (max_pixels / (w * h)) ** 0.5
        img = img.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)
    import io
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


async def gen_one(
    client: AsyncOpenAI,
    sem: asyncio.Semaphore,
    model: str,
    row: dict,
    out_path: Path,
    max_tokens: int = 1536,
) -> bool:
    """Generate one parse and save to out_path. Returns True on success."""
    if out_path.exists():
        return False  # already done
    async with sem:
        try:
            img_path = remap_image_path(row["images"][0])
            b64 = load_image_b64(img_path)
            system = row["messages"][0]["content"]
            user = row["messages"][1]["content"].replace("<image>", "", 1).lstrip()
            resp = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                        {"type": "text", "text": user},
                    ]},
                ],
                temperature=0.0,  # greedy for eval consistency
                max_tokens=max_tokens,
            )
            md = resp.choices[0].message.content.strip()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(md + "\n", encoding="utf-8")
            return True
        except Exception as e:
            log.warning("model=%s page=%s failed: %s", model, out_path.name, e)
            return False


async def amain(args: argparse.Namespace) -> int:
    val_jsonl = Path(args.val_jsonl)
    split = json.loads(Path(args.split).read_text())
    # All 294 pages = train_pages ∪ eval_pages
    all_pages = set(split["train_pages"]) | set(split["eval_pages"])
    log.info("target pages: %d (%d train + %d eval from split)",
             len(all_pages), len(split["train_pages"]), len(split["eval_pages"]))

    # val.jsonl row index → page_id 매핑
    val_rows = [json.loads(line) for line in val_jsonl.read_text().splitlines() if line.strip()]
    page_stems = build_page_id_index(val_jsonl)

    # Build (model, row_idx, row, page_id, stem) jobs for missing files
    parses_root = Path(args.parses_root)
    models = args.models if args.models else list(MODEL_TO_DIR.keys())
    jobs: list[tuple[str, dict, Path]] = []
    for model in models:
        out_dir = parses_root / MODEL_TO_DIR[model]
        for i, row in enumerate(val_rows):
            page_id = f"val_{i:04d}"
            if page_id not in all_pages:
                continue
            stem = page_stems[page_id]
            out_path = out_dir / f"{stem}.md"
            if out_path.exists():
                continue
            jobs.append((model, row, out_path))
    log.info("queued %d (model, page) jobs across %d models", len(jobs), len(models))
    if not jobs:
        log.info("nothing to do")
        return 0

    client = AsyncOpenAI(base_url=args.base_url, api_key="dummy", timeout=300.0, max_retries=3)
    sem = asyncio.Semaphore(args.concurrency)

    done = 0
    t0 = time.time()

    async def task(model: str, row: dict, out_path: Path):
        nonlocal done
        ok = await gen_one(client, sem, model, row, out_path)
        if ok:
            done += 1
            if done % 50 == 0:
                elapsed = time.time() - t0
                rate = done / max(elapsed, 1e-6)
                eta_min = (len(jobs) - done) / max(rate, 1e-6) / 60
                log.info("%d/%d  (%.1f/s, %.1f min elapsed, ETA %.1f min)",
                         done, len(jobs), rate, elapsed / 60, eta_min)

    await asyncio.gather(*[task(m, r, p) for m, r, p in jobs])
    log.info("done: wrote %d parses in %.1f min", done, (time.time() - t0) / 60)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base_url", default="http://localhost:8001/v1")
    ap.add_argument("--val_jsonl", default="data/KoGovDoc-Bench/val.jsonl")
    ap.add_argument("--split", default="data/KoGovDoc-RAG/page_split_v1.json")
    ap.add_argument("--parses_root", default="output/parses_full")
    ap.add_argument("--models", nargs="+", default=None,
                    help="vLLM lora-module names (default: all 9)")
    ap.add_argument("--concurrency", type=int, default=16)
    args = ap.parse_args()
    return asyncio.run(amain(args))


if __name__ == "__main__":
    raise SystemExit(main())
