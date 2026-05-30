"""Regenerate broken 169p parses one LoRA at a time (single-LoRA vLLM serving).

Workaround for the multi-LoRA + Qwen3-VL bug observed on vllm/vllm-openai:nightly
where some adapters (notably lambda00) produced truncated output.

For each variant:
  1. Stop+remove any existing vllm-radp container
  2. Start vllm-radp with only this variant's LoRA loaded
  3. Wait for ready
  4. Delete tiny parses (<100 bytes) from train fold for this variant
  5. Generate via the OpenAI API for missing pages
  6. Stop the container
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
import time
import urllib.request
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] REGEN: %(message)s")
log = logging.getLogger("regen")

ROOT = Path("/mnt/data1/work/WigtnOCR-RADP")

# (vllm served name, adapter path under output/checkpoints, output dir under parses_full)
VARIANTS = [
    ("lambda00", "radp_b_full_lambda00/final", "radp_b_lambda00_eval"),
    ("lambda01", "radp_b_full_lambda01/final", "radp_b_lambda01_eval"),
    ("lambda03", "radp_b_full_lambda03/final", "radp_b_lambda03_eval"),
    ("lambda05", "radp_b_full_lambda05/final", "radp_b_lambda05_eval"),
    ("dpo-v1", "radp_dpo/final", "radp_dpo_eval"),
    ("dpo-v2", "radp_dpo_v2/final", "radp_dpo_v2_eval"),
    ("dpo-v3", "radp_dpo_v3/final", "radp_dpo_v3_eval"),
    ("dpo-v4", "radp_dpo_v4/final", "radp_dpo_v4_eval"),
    ("simpo", "radp_simpo/final", "radp_simpo_eval"),
]


def start_single_lora(adapter_name: str, adapter_path: str) -> None:
    """Start vllm-radp with a single LoRA loaded."""
    subprocess.run(["docker", "rm", "-f", "vllm-radp"], check=False, capture_output=True)
    cmd = [
        "docker", "run", "-d",
        "--name", "vllm-radp",
        "--runtime", "nvidia",
        "-e", "NVIDIA_VISIBLE_DEVICES=1",
        "-e", "NVIDIA_DRIVER_CAPABILITIES=compute,utility",
        "-e", "HF_HUB_OFFLINE=1",
        "-e", "VLLM_LOGGING_LEVEL=WARNING",
        "-v", "/mnt/data1/work/wigtnOCR-v1/output/wigtnocr-2b-merged:/models/v1-merged:ro",
        "-v", f"{ROOT}/output/checkpoints:/loras:ro",
        "-p", "8001:8001",
        "vllm/vllm-openai:nightly",
        "--model", "/models/v1-merged",
        "--served-model-name", "wigtnocr-v1",
        "--gpu-memory-utilization", "0.5",
        "--max-model-len", "8192",
        "--trust-remote-code",
        "--dtype", "bfloat16",
        "--host", "0.0.0.0", "--port", "8001",
        "--enable-lora",
        "--lora-modules", f"{adapter_name}=/loras/{adapter_path}",
        "--max-lora-rank", "8",
        "--max-loras", "1",
        "--limit-mm-per-prompt", '{"image": 1}',
    ]
    p = subprocess.run(cmd, check=True, capture_output=True, text=True)
    log.info("started container %s", p.stdout.strip()[:12])

    # Wait for /health
    t0 = time.time()
    while True:
        try:
            urllib.request.urlopen("http://localhost:8001/health", timeout=5)
            log.info("vLLM ready after %.1f s", time.time() - t0)
            return
        except Exception:
            if time.time() - t0 > 300:
                raise SystemExit(f"vLLM startup timeout for {adapter_name}")
            time.sleep(5)


async def regen_variant(adapter_name: str, out_dir: Path,
                        train_stems_to_rows: dict[str, dict],
                        concurrency: int = 16) -> int:
    """Generate parses for train fold pages, skipping any non-tiny existing files."""
    from openai import AsyncOpenAI
    from PIL import Image
    import base64, io
    from wigtnocr_radp.training.data import remap_image_path

    client = AsyncOpenAI(base_url="http://localhost:8001/v1", api_key="dummy",
                          timeout=300.0, max_retries=3)
    sem = asyncio.Semaphore(concurrency)

    # Build job list — only missing or tiny (<100B) files
    jobs: list[tuple[str, dict, Path]] = []
    for stem, row in train_stems_to_rows.items():
        out_path = out_dir / f"{stem}.md"
        if out_path.exists() and out_path.stat().st_size >= 100:
            continue
        jobs.append((stem, row, out_path))
    log.info("%s: %d pages to (re)generate", adapter_name, len(jobs))
    if not jobs:
        return 0

    done = [0]

    async def one(stem: str, row: dict, out_path: Path):
        async with sem:
            try:
                img_path = remap_image_path(row["images"][0])
                img = Image.open(img_path).convert("RGB")
                w, h = img.size
                if w * h > 1_048_576:
                    s = (1_048_576 / (w * h)) ** 0.5
                    img = img.resize((max(1, round(w * s)), max(1, round(h * s))), Image.LANCZOS)
                buf = io.BytesIO(); img.save(buf, format="PNG")
                b64 = base64.b64encode(buf.getvalue()).decode()
                system = row["messages"][0]["content"]
                user = row["messages"][1]["content"].replace("<image>", "", 1).lstrip()
                resp = await client.chat.completions.create(
                    model=adapter_name,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": [
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                            {"type": "text", "text": user},
                        ]},
                    ],
                    temperature=0.0,
                    max_tokens=1536,
                )
                md = resp.choices[0].message.content.strip()
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(md + "\n", encoding="utf-8")
                done[0] += 1
            except Exception as e:
                log.warning("%s page=%s failed: %s", adapter_name, stem, e)

    await asyncio.gather(*[one(s, r, p) for s, r, p in jobs])
    return done[0]


def main() -> int:
    # Build train_stem → row mapping (val.jsonl row that produced this page)
    val_jsonl = ROOT / "data/KoGovDoc-Bench/val.jsonl"
    val_rows = [json.loads(l) for l in val_jsonl.read_text().splitlines() if l.strip()]
    from wigtnocr_radp.evaluation.parser_outputs import build_page_id_index
    page_to_stem = build_page_id_index(val_jsonl)

    split = json.loads((ROOT / "data/KoGovDoc-RAG/page_split_v1.json").read_text())
    train_pages = set(split["train_pages"])

    train_stem_to_row: dict[str, dict] = {}
    for i, row in enumerate(val_rows):
        pid = f"val_{i:04d}"
        if pid in train_pages:
            train_stem_to_row[page_to_stem[pid]] = row
    log.info("train fold: %d stems", len(train_stem_to_row))

    for adapter_name, adapter_path, out_subdir in VARIANTS:
        log.info("=" * 60)
        log.info("variant: %s  →  %s", adapter_name, out_subdir)
        log.info("=" * 60)

        # Delete ALL existing train-fold parses (multi-LoRA may have produced
        # subtly broken outputs even at normal length). 73p eval-fold parses
        # are HF-generated and intact — we only touch train-fold files.
        out_dir = ROOT / "output/parses_full" / out_subdir
        deleted = 0
        for stem in train_stem_to_row:
            f = out_dir / f"{stem}.md"
            if f.exists():
                f.unlink()
                deleted += 1
        log.info("deleted %d existing train-fold parses for %s", deleted, adapter_name)

        start_single_lora(adapter_name, adapter_path)
        n = asyncio.run(regen_variant(adapter_name, out_dir, train_stem_to_row))
        log.info("regenerated %d pages for %s", n, adapter_name)

    log.info("stopping container")
    subprocess.run(["docker", "stop", "vllm-radp"], check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
