"""OHR compatibility phase 2 — async vLLM parsing of audited cached PNGs.

Reads PNGs from ``output/ohrbench_pngs_compat2036/{domain}/*.png`` and writes
parses to a caller-supplied compat/strict cache.  The legacy mixed-release
``output/parses_ohrbench`` cache is rejected.  Resumable: existing non-empty
Markdown files are skipped.
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import logging
import time
from pathlib import Path

from openai import AsyncOpenAI

from wigtnocr_radp.ohrbench_paths import require_compatibility_cache_path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] PARSE: %(message)s")
log = logging.getLogger("parse")

ROOT = Path(__file__).resolve().parents[2]
PNG_DIR = ROOT / "output/ohrbench_pngs_compat2036"

SYSTEM_PROMPT = """You are WigtnOCR, a specialized document parser for Korean government documents.
Convert the given document page image into well-structured Markdown format.

You MUST:
- Use # symbols for headings based on document hierarchy
- Convert tables to Markdown | format
- Preserve all Korean text exactly
- Mark 조/항/목 legal structures with appropriate heading levels
- Handle mixed text+table+diagram layouts"""

USER_PROMPT = """Convert this document page image to well-structured Markdown.
Output ONLY the Markdown content. No explanations, no commentary."""


async def parse_one(client, sem, model, png, out_md):
    if out_md.exists() and out_md.stat().st_size > 50:
        return True
    async with sem:
        try:
            b64 = base64.b64encode(png.read_bytes()).decode()
            resp = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                        {"type": "text", "text": USER_PROMPT},
                    ]},
                ],
                temperature=0.0, max_tokens=1536,
            )
            md = resp.choices[0].message.content.strip()
            out_md.parent.mkdir(parents=True, exist_ok=True)
            out_md.write_text(md + "\n", encoding="utf-8")
            return True
        except Exception as e:
            log.warning("%s @ %s failed: %s", model, png.name, e)
            return False


async def amain(args):
    pngs = sorted(PNG_DIR.glob("*/*.png"))
    log.info("found %d PNGs", len(pngs))
    if not pngs:
        raise FileNotFoundError(f"no compatibility PNGs found under {PNG_DIR}")
    out_root = args.out_dir

    todo = []
    for png in pngs:
        out_md = out_root / png.parent.name / (png.stem + ".md")
        if out_md.exists() and out_md.stat().st_size > 50:
            continue
        todo.append((png, out_md))
    log.info("todo: %d (skipping %d already done)", len(todo), len(pngs) - len(todo))
    if not todo:
        return 0

    client = AsyncOpenAI(base_url=args.base_url, api_key="dummy",
                         timeout=300.0, max_retries=3)
    sem = asyncio.Semaphore(args.concurrency)

    done = [0]
    t0 = time.time()

    async def wrapped(png, out_md):
        ok = await parse_one(client, sem, args.model, png, out_md)
        if ok:
            done[0] += 1
        if done[0] > 0 and done[0] % 200 == 0:
            elapsed = time.time() - t0
            rate = done[0] / max(elapsed, 1e-6)
            eta = (len(todo) - done[0]) / max(rate, 1e-6) / 60
            log.info("  %d/%d (%.1f/s, ETA %.1f min)",
                     done[0], len(todo), rate, eta)

    await asyncio.gather(*[wrapped(p, o) for p, o in todo])
    log.info("done: %d parses in %.1fmin", done[0], (time.time() - t0) / 60)
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base_url", default="http://localhost:8002/v1")
    ap.add_argument("--model", required=True)
    ap.add_argument("--out_dir", required=True, type=Path)
    ap.add_argument("--concurrency", type=int, default=32)
    args = ap.parse_args()
    require_compatibility_cache_path(PNG_DIR)
    require_compatibility_cache_path(args.out_dir)
    return asyncio.run(amain(args))


if __name__ == "__main__":
    raise SystemExit(main())
