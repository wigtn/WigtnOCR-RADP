"""Sequel to regen_parses_single_lora.py:
   1. Wait for the 9-variant single-LoRA regen to finish (train fold only).
   2. Regenerate ALL 242 pages (train + eval folds) for seed123 and seed999,
      since those were originally generated under the buggy multi-LoRA setup.
   3. Run the final 242p bootstrap CI on all 12 systems.
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] SEED_REGEN: %(message)s")
log = logging.getLogger("seed_regen")

ROOT = Path("/mnt/data1/work/WigtnOCR-RADP")
STATUS = ROOT / "output/seed_regen_status.json"
GATE_PP = 0.05
_ENV = {**os.environ, "CUDA_VISIBLE_DEVICES": "1"}


def write_status(stage: str, **kw):
    payload = {"stage": stage, "ts": time.strftime("%Y-%m-%d %H:%M:%S"), **kw}
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    log.info("STATUS → %s", payload)


def wait_for_regen_done():
    """Wait for regen_parses_single_lora.py to exit."""
    log.info("waiting for 9-variant regen to finish...")
    while subprocess.run(
        ["pgrep", "-f", "regen_parses_single_lora.py"], capture_output=True, text=True
    ).stdout.strip():
        time.sleep(30)
    log.info("9-variant regen done")


def start_single_lora(name: str, path: str):
    subprocess.run(["docker", "rm", "-f", "vllm-radp"], check=False, capture_output=True)
    cmd = [
        "docker", "run", "-d", "--name", "vllm-radp",
        "--runtime", "nvidia",
        "-e", "NVIDIA_VISIBLE_DEVICES=1",
        "-e", "NVIDIA_DRIVER_CAPABILITIES=compute,utility",
        "-e", "HF_HUB_OFFLINE=1", "-e", "VLLM_LOGGING_LEVEL=WARNING",
        "-v", "/mnt/data1/work/wigtnOCR-v1/output/wigtnocr-2b-merged:/models/v1-merged:ro",
        "-v", f"{ROOT}/output/checkpoints:/loras:ro",
        "-p", "8001:8001",
        "vllm/vllm-openai:nightly",
        "--model", "/models/v1-merged", "--served-model-name", "wigtnocr-v1",
        "--gpu-memory-utilization", "0.5", "--max-model-len", "8192",
        "--trust-remote-code", "--dtype", "bfloat16",
        "--host", "0.0.0.0", "--port", "8001",
        "--enable-lora",
        "--lora-modules", f"{name}=/loras/{path}",
        "--max-lora-rank", "8", "--max-loras", "1",
        "--limit-mm-per-prompt", '{"image": 1}',
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    t0 = time.time()
    while True:
        try:
            urllib.request.urlopen("http://localhost:8001/health", timeout=5)
            log.info("vLLM ready (%.1fs)", time.time() - t0)
            return
        except Exception:
            if time.time() - t0 > 300:
                raise SystemExit("vLLM timeout")
            time.sleep(5)


async def regen_all_242(adapter_name: str, out_dir: Path,
                        all_stem_to_row: dict[str, dict], concurrency: int = 16):
    from openai import AsyncOpenAI
    from PIL import Image
    import base64, io
    from wigtnocr_radp.training.data import remap_image_path

    client = AsyncOpenAI(base_url="http://localhost:8001/v1", api_key="dummy",
                          timeout=300.0, max_retries=3)
    sem = asyncio.Semaphore(concurrency)

    # Delete ALL existing parses for this variant — full regen
    deleted = 0
    for stem in all_stem_to_row:
        f = out_dir / f"{stem}.md"
        if f.exists():
            f.unlink()
            deleted += 1
    log.info("deleted %d existing parses for %s (full 242p regen)", deleted, adapter_name)

    jobs = [(stem, row, out_dir / f"{stem}.md") for stem, row in all_stem_to_row.items()]
    log.info("%s: %d pages to regenerate", adapter_name, len(jobs))

    done = [0]

    async def one(stem, row, out_path):
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
                    temperature=0.0, max_tokens=1536,
                )
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(resp.choices[0].message.content.strip() + "\n", encoding="utf-8")
                done[0] += 1
            except Exception as e:
                log.warning("%s page=%s failed: %s", adapter_name, stem, e)

    await asyncio.gather(*[one(s, r, p) for s, r, p in jobs])
    log.info("regenerated %d for %s", done[0], adapter_name)


def main() -> int:
    write_status("waiting_for_9variant_regen")
    wait_for_regen_done()

    # Build all-fold stem → row map (train + eval = 242 pages)
    val_jsonl = ROOT / "data/KoGovDoc-Bench/val.jsonl"
    val_rows = [json.loads(l) for l in val_jsonl.read_text().splitlines() if l.strip()]
    from wigtnocr_radp.evaluation.parser_outputs import build_page_id_index
    page_to_stem = build_page_id_index(val_jsonl)
    split = json.loads((ROOT / "data/KoGovDoc-RAG/page_split_v1.json").read_text())
    all_pages = set(split["train_pages"]) | set(split["eval_pages"])

    all_stem_to_row: dict[str, dict] = {}
    for i, row in enumerate(val_rows):
        pid = f"val_{i:04d}"
        if pid in all_pages:
            all_stem_to_row[page_to_stem[pid]] = row
    log.info("all-fold: %d pages", len(all_stem_to_row))

    seeds = [
        ("dpo-v1-seed123", "radp_dpo_seed123/final", "radp_dpo_seed123_eval"),
        ("dpo-v1-seed999", "radp_dpo_seed999/final", "radp_dpo_seed999_eval"),
    ]
    for name, path, subdir in seeds:
        write_status(f"regen_{name}")
        log.info("=" * 60)
        log.info("seed regen: %s", name)
        log.info("=" * 60)
        start_single_lora(name, path)
        asyncio.run(regen_all_242(name, ROOT / "output/parses_full" / subdir, all_stem_to_row))

    log.info("stopping vllm-radp")
    subprocess.run(["docker", "stop", "vllm-radp"], check=False)
    time.sleep(5)

    # Final bootstrap
    write_status("final_bootstrap_242p")
    ci_path = ROOT / "output/results/plan_d_FINAL_ci_242p.json"
    perqa_path = ROOT / "output/results/plan_d_FINAL_perqa_242p.json"
    cmd = [
        "uv", "run", "python", "scripts/evaluation/bootstrap_radp_full.py",
        "--device", "cuda:0",
        "--fold", "all",
        "--extra_system", "RADP-DPO-v1=output/parses_full/radp_dpo_eval",
        "--extra_system", "RADP-DPO-v2=output/parses_full/radp_dpo_v2_eval",
        "--extra_system", "RADP-DPO-v3=output/parses_full/radp_dpo_v3_eval",
        "--extra_system", "RADP-DPO-v4=output/parses_full/radp_dpo_v4_eval",
        "--extra_system", "RADP-SimPO=output/parses_full/radp_simpo_eval",
        "--extra_system", "DPO-v1-seed123=output/parses_full/radp_dpo_seed123_eval",
        "--extra_system", "DPO-v1-seed999=output/parses_full/radp_dpo_seed999_eval",
        "--out_ci", str(ci_path),
        "--out_perqa", str(perqa_path),
    ]
    log.info("$ %s", " ".join(cmd))
    p = subprocess.run(cmd, cwd=ROOT, env=_ENV)
    if p.returncode != 0:
        write_status("error", failed_cmd=cmd, returncode=p.returncode)
        raise SystemExit(p.returncode)

    # Read final
    d = json.loads(ci_path.read_text())
    summary: dict = {}
    hit = False
    for ck, by_label in d["by_chunker"].items():
        for label, row in by_label.items():
            if "vs_lambda0_ci" not in row:
                continue
            mean_pp = row["vs_lambda0_ci"]["mean"] * 100
            summary.setdefault(label, {})[ck] = round(mean_pp, 3)
            if mean_pp >= GATE_PP * 100:
                hit = True
    final = "SUCCESS_GATE_HIT" if hit else "DONE_GATE_MISSED"
    write_status(final, gate_hit=hit, deltas_pp=summary, ci_path=str(ci_path))
    log.info("=== %s ===", final)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        log.exception("uncaught")
        write_status("error", error=repr(e))
        raise
