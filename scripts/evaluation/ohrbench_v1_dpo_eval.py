"""OHR-Bench cross-domain evaluation for v1 + DPO parsers.

Purpose: validate the KoGov DPO finding on an independent, English-language
benchmark, testing cross-domain generalisation. The KoGov fold (n=663) is
underpowered — its two-sided CI straddles zero — so an independent benchmark with
more verbatim-answerable Q-A across 7 domains (Law, Manual, Finance, News,
Academic, Textbook, Administration) both (a) tests generalisation to a different
language and document mix and (b) supplies the sample size for a powered two-sided
test. We report whatever the cross-domain data show, in either direction.

Pipeline (run as background daemon, ~3h total):
  1. PDF → PNG (pdftoppm, 150 dpi, ~40min CPU for 4,330 pages)
  2. v1 + DPO-v1 + DPO-v4 (3 models) × OHR-Bench → parses
     (vLLM-async via vllm-v1 @ 8002, ~30min concurrency=32)
  3. RCPS scoring with same 3 retrievers as KoGov (BGE-M3, mE5-large, Qwen3-Emb-8B)
     on parser_native chunker, ~1h GPU 1
  4. Verbatim filter (answer span must be substring of parse) + paired CI
     on KoGov∪OHR-Bench combined Q-A.

Outputs:
  output/parses_ohrbench/{v1,radp_dpo,radp_dpo_v4}/<domain>/<doc>__p<n>.md
  output/results/ohrbench_v1_dpo_perqa.json
  output/results/ohrbench_v1_dpo_ci.json
  output/results/combined_kogov_ohrbench_ci.json — paired CI on union
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import io
import json
import logging
import os
import subprocess
import time
from pathlib import Path

import pandas as pd
from PIL import Image

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] OHR_EVAL: %(message)s")
log = logging.getLogger("ohr_eval")

ROOT = Path("/mnt/data1/work/WigtnOCR-RADP")
OHR = ROOT / "data/OHR-Bench"
PDFS = OHR / "pdfs_extracted"
PARQUET = OHR / "OHR-Bench.parquet"

# Domain naming difference between pdfs.zip and parquet
PDF_TO_PARQUET = {
    "law": "law", "manual": "manual", "finance": "finance",
    "textbook": "textbook", "news": "news",
    "academic": "paper", "administration": "notes",
}

PARSE_CACHE = ROOT / "output/parses_ohrbench"
PNG_CACHE = ROOT / "output/ohrbench_pngs"

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


def page_id(doc_name: str, page_idx: int) -> str:
    base = doc_name.rsplit("/", 1)[-1]
    return f"{base}__p{int(page_idx)}"


def pdf_to_png(pdf_path: Path, page_idx: int, out_png: Path) -> bool:
    """Convert a single PDF page to PNG via pdftoppm.

    parquet page_idx is 0-indexed; pdftoppm is 1-indexed → use page_idx + 1.
    """
    if out_png.exists() and out_png.stat().st_size > 1000:
        return True
    out_png.parent.mkdir(parents=True, exist_ok=True)
    stem = out_png.with_suffix("")
    page_1idx = int(page_idx) + 1  # 0-indexed → 1-indexed
    try:
        subprocess.run(
            ["pdftoppm", "-f", str(page_1idx), "-l", str(page_1idx), "-r", "150",
             str(pdf_path), str(stem), "-png"],
            check=True, capture_output=True, timeout=60,
        )
        # pdftoppm appends -<page_1idx>.png (with no padding for small numbers)
        # Try common patterns
        for cand in [
            stem.parent / f"{stem.name}-{page_1idx}.png",
            stem.parent / f"{stem.name}-{page_1idx:02d}.png",
            stem.parent / f"{stem.name}-{page_1idx:03d}.png",
        ]:
            if cand.exists():
                cand.rename(out_png)
                return True
        # Fallback: glob for any file matching stem-*.png
        for f in stem.parent.glob(f"{stem.name}-*.png"):
            f.rename(out_png)
            return True
    except Exception as e:
        log.warning("pdftoppm failed on %s page=%d: %s", pdf_path.name, page_idx, e)
    return False


def collect_pages_to_parse() -> list[dict]:
    """Iterate parquet → list of {pdf_path, page_idx, page_id, domain}."""
    df = pd.read_parquet(PARQUET)
    out = []
    for _, row in df.iterrows():
        parquet_dom = str(row["domain"])
        # reverse map
        pdf_doms = [k for k, v in PDF_TO_PARQUET.items() if v == parquet_dom]
        if not pdf_doms:
            continue
        pdf_dom = pdf_doms[0]
        doc_name = str(row["doc_name"]).rsplit("/", 1)[-1]
        if not doc_name.endswith(".pdf"):
            doc_name = doc_name + ".pdf"
        pdf_path = PDFS / pdf_dom / doc_name
        if not pdf_path.exists():
            continue
        page_idx = int(row["page_idx"])
        out.append({
            "pdf_path": pdf_path,
            "page_idx": page_idx,
            "page_id": page_id(str(row["doc_name"]), page_idx),
            "domain": pdf_dom,
            "doc_name": doc_name,
        })
    log.info("collected %d (pdf, page) pairs across %d unique pages",
             len(out), len({(p["pdf_path"], p["page_idx"]) for p in out}))
    return out


def phase_pdf_to_png(pages: list[dict]) -> int:
    """Convert all unique (pdf, page) to PNGs cached under PNG_CACHE/<domain>/."""
    log.info("=== Phase 1: PDF → PNG (parallel) ===")
    PNG_CACHE.mkdir(parents=True, exist_ok=True)
    seen: set[tuple[Path, int]] = set()
    todo = []
    for p in pages:
        key = (p["pdf_path"], p["page_idx"])
        if key in seen:
            continue
        seen.add(key)
        png_path = PNG_CACHE / p["domain"] / f"{p['page_id']}.png"
        if png_path.exists() and png_path.stat().st_size > 1000:
            continue
        todo.append((p["pdf_path"], p["page_idx"], png_path))
    log.info("PNG cache hit: %d / %d", len(seen) - len(todo), len(seen))
    if not todo:
        return 0

    # Parallel via subprocess pool
    from concurrent.futures import ThreadPoolExecutor, as_completed
    done = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(pdf_to_png, pdf, pi, op): (pdf, pi) for pdf, pi, op in todo}
        for fut in as_completed(futs):
            ok = fut.result()
            done += 1
            if done % 200 == 0:
                elapsed = time.time() - t0
                rate = done / max(elapsed, 1e-6)
                eta = (len(todo) - done) / max(rate, 1e-6) / 60
                log.info("  PNG %d/%d (%.1f/s, ETA %.1f min)", done, len(todo), rate, eta)
    log.info("PNG done: %d in %.1fmin", done, (time.time() - t0) / 60)
    return done


async def parse_one(client, sem, model: str, png_path: Path, out_path: Path,
                     temperature: float, max_tokens: int) -> bool:
    if out_path.exists() and out_path.stat().st_size > 50:
        return True
    async with sem:
        try:
            with png_path.open("rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            resp = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                        {"type": "text", "text": USER_PROMPT},
                    ]},
                ],
                temperature=temperature, max_tokens=max_tokens,
            )
            md = resp.choices[0].message.content.strip()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(md + "\n", encoding="utf-8")
            return True
        except Exception as e:
            log.warning("parse %s @ %s failed: %s", model, png_path.name, e)
            return False


async def phase_parse(pages: list[dict], models: list[tuple[str, str, str]],
                       base_url: str, concurrency: int):
    """models: list of (served_name, output_subdir, comment)."""
    from openai import AsyncOpenAI
    client = AsyncOpenAI(base_url=base_url, api_key="dummy", timeout=300.0, max_retries=3)
    log.info("=== Phase 2: vLLM parse for %d pages × %d models ===", len(pages), len(models))

    sem = asyncio.Semaphore(concurrency)
    for model_name, subdir, comment in models:
        log.info("--- model: %s (%s) ---", model_name, comment)
        out_dir = PARSE_CACHE / subdir
        out_dir.mkdir(parents=True, exist_ok=True)
        todo = []
        for p in pages:
            png_path = PNG_CACHE / p["domain"] / f"{p['page_id']}.png"
            if not png_path.exists():
                continue
            out_path = out_dir / p["domain"] / f"{p['page_id']}.md"
            if out_path.exists() and out_path.stat().st_size > 50:
                continue
            todo.append((png_path, out_path))
        log.info("  todo: %d pages", len(todo))
        if not todo:
            continue
        t0 = time.time()
        tasks = [parse_one(client, sem, model_name, pp, op, 0.0, 1536) for pp, op in todo]
        done_flags = await asyncio.gather(*tasks)
        log.info("  parsed %d/%d in %.1fmin", sum(done_flags), len(todo), (time.time() - t0) / 60)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base_url", default="http://localhost:8002/v1")
    ap.add_argument("--concurrency", type=int, default=32)
    ap.add_argument("--skip_png", action="store_true")
    ap.add_argument("--skip_parse", action="store_true")
    args = ap.parse_args()

    log.info("=== OHR-Bench v1+DPO eval pipeline ===")
    pages = collect_pages_to_parse()

    if not args.skip_png:
        phase_pdf_to_png(pages)

    if not args.skip_parse:
        # vllm-v1 currently serves base v1 only. For DPO-v1/v4 we need to restart vllm with
        # LoRA modules. For simplicity, first do v1 with current server, then user can
        # restart vllm with LoRAs for DPO variants.
        # Or use single-LoRA vllm pattern (memory: vllm-multi-lora-qwen3vl-bug).
        models = [
            ("v1", "v1", "production parser baseline"),
        ]
        asyncio.run(phase_parse(pages, models, args.base_url, args.concurrency))

    log.info("Phase 1-2 done; Phase 3 (scoring) + Phase 4 (CI) — separate scripts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
