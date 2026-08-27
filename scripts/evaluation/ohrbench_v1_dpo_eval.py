"""Legacy-QA OHR-Bench parsing pipeline for v1 + DPO parsers.

The legacy 4,330-page parquet and current 8,561-page parser/PDF bundle are not a
single benchmark version.  This script resolves source documents globally by
basename and reports missing source files; downstream scoring must enforce the
evidence-page coverage gate.  It is retained to reproduce the corrected legacy
compatibility subset, not as a full OHR-Bench v2 evaluation.  A full v2 run must
use ``OHR-Bench_v2.parquet`` together with ``qas_v2.json``.

Pipeline (run as background daemon):
  1. Filter the audited six-domain compatibility corpus and exclude its known
     missing v2 page.
  2. PDF → PNG (pdftoppm, 150 dpi) in a compatibility-only cache.
  3. v1 + DPO-v1 + DPO-v4 (3 models) × OHR-Bench → parses
     (vLLM-async via vllm-v1 @ 8002, ~30min concurrency=32)
  4. Run ``ohrbench_v1dpo_full.py`` for strict-2,036 scoring and paired CIs.

Outputs:
  output/ohrbench_pngs_compat2036/<domain>/<doc>__p<n>.png
  output/parses_ohrbench_compat2036/{v1,dpo_v1,dpo_v4}/<domain>/<doc>__p<n>.md

This preparation script never writes result JSON files and never uses the
legacy ``output/parses_ohrbench`` cache.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Any

import pandas as pd
from PIL import Image

from wigtnocr_radp.ohrbench_paths import (
    document_basename,
    ohr_page_id,
    require_compatibility_cache_path,
    require_supported_ohr_alignment_audit,
    resolve_document_files,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] OHR_EVAL: %(message)s")
log = logging.getLogger("ohr_eval")

ROOT = Path(__file__).resolve().parents[2]
OHR = ROOT / "data/OHR-Bench"
PDFS = OHR / "pdfs_extracted"
PARQUET = OHR / "OHR-Bench.parquet"
ALIGNMENT_AUDIT = ROOT / "output/results/ohrbench_alignment_audit.json"

PARSE_CACHE = ROOT / "output/parses_ohrbench_compat2036"
PNG_CACHE = ROOT / "output/ohrbench_pngs_compat2036"

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


def load_alignment_audit(path: Path) -> dict[str, Any]:
    audit = json.loads(path.read_text(encoding="utf-8"))
    strict = audit.get("c4_strict_compatibility_subset")
    require_supported_ohr_alignment_audit(audit, path=path)
    if not isinstance(strict, dict):
        raise ValueError(f"unsupported OHR alignment audit: {path}")
    if int(strict.get("num_qa", -1)) != 2036:
        raise ValueError(f"alignment audit does not define the 2,036-Q-A subset: {path}")
    return audit


def _pdf_lookup_key(doc_name: str) -> str:
    basename = document_basename(doc_name)
    return basename[:-4] if basename.lower().endswith(".pdf") else basename


def collect_pages_to_parse(alignment_audit: dict[str, Any]) -> list[dict]:
    """Collect only pages in the audited six-domain compatibility corpus."""

    df = pd.read_parquet(PARQUET)
    strict = alignment_audit["c4_strict_compatibility_subset"]
    allowed_domains = set(strict["domain_counts"])
    missing_page = str(strict["excluded"]["missing_v2_page"])
    df = df[df["domain"].astype(str).isin(allowed_domains)].copy()
    df["_page_id"] = [
        ohr_page_id(row["doc_name"], row["page_idx"]) for _, row in df.iterrows()
    ]
    df = df[df["_page_id"] != missing_page]

    resolved, missing_documents = resolve_document_files(
        PDFS,
        df["doc_name"].astype(str),
        suffix=".pdf",
    )
    if missing_documents:
        raise FileNotFoundError(
            "strict compatibility PDF corpus is incomplete: "
            f"{len(missing_documents)} documents missing; sample={list(missing_documents[:5])}"
        )

    out = []
    for _, row in df.iterrows():
        pdf_path = resolved.get(_pdf_lookup_key(str(row["doc_name"])))
        if pdf_path is None:
            raise FileNotFoundError(f"resolved PDF disappeared for {row['doc_name']}")
        pdf_dom = pdf_path.parent.name
        page_idx = int(row["page_idx"])
        out.append({
            "pdf_path": pdf_path,
            "page_idx": page_idx,
            "page_id": str(row["_page_id"]),
            "domain": pdf_dom,
            "doc_name": pdf_path.name,
        })
    page_ids = [page["page_id"] for page in out]
    if len(page_ids) != len(set(page_ids)):
        raise ValueError("strict compatibility corpus contains duplicate canonical page IDs")
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
    succeeded = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(pdf_to_png, pdf, pi, op): (pdf, pi) for pdf, pi, op in todo}
        for fut in as_completed(futs):
            ok = fut.result()
            done += 1
            succeeded += int(ok)
            if done % 200 == 0:
                elapsed = time.time() - t0
                rate = done / max(elapsed, 1e-6)
                eta = (len(todo) - done) / max(rate, 1e-6) / 60
                log.info("  PNG %d/%d (%.1f/s, ETA %.1f min)", done, len(todo), rate, eta)
    if succeeded != len(todo):
        raise RuntimeError(f"PNG conversion incomplete: {succeeded}/{len(todo)} succeeded")
    log.info("PNG done: %d in %.1fmin", succeeded, (time.time() - t0) / 60)
    return succeeded


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
        if not all(done_flags):
            raise RuntimeError(
                f"parser cache incomplete for {subdir}: {sum(done_flags)}/{len(todo)} succeeded"
            )
        log.info("  parsed %d/%d in %.1fmin", sum(done_flags), len(todo), (time.time() - t0) / 60)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base_url", default="http://localhost:8002/v1")
    ap.add_argument("--concurrency", type=int, default=32)
    ap.add_argument("--alignment-audit", type=Path, default=ALIGNMENT_AUDIT)
    ap.add_argument("--skip_png", action="store_true")
    ap.add_argument("--skip_parse", action="store_true")
    args = ap.parse_args()

    require_compatibility_cache_path(PARSE_CACHE)
    require_compatibility_cache_path(PNG_CACHE)
    alignment_audit = load_alignment_audit(args.alignment_audit)

    log.info("=== OHR-Bench strict-2,036 compatibility cache pipeline ===")
    pages = collect_pages_to_parse(alignment_audit)

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
