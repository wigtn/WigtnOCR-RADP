"""Master orchestrator for dual-GPU final regen + bootstrap.

State at launch:
  - GPU 1: regen_parses_single_lora.py is running (vLLM single-LoRA regen of remaining variants).
    Already-done: lambda00, lambda01, lambda03, lambda05, dpo-v1, dpo-v2, dpo-v3.
    In progress / TODO: dpo-v4, simpo.
  - GPU 0: free (gemma4 stopped by master before launch).

This script:
  1. Launches HF-transformers re-regen of lambda00 + lambda01 on GPU 0 (sequential).
     These two variants are known broken under vLLM single-LoRA (44 + 4 tiny outputs);
     HF gives correct outputs (proven on 73p eval fold).
  2. Waits for GPU 1's regen_parses_single_lora.py to finish.
  3. Runs seed123/seed999 regen on GPU 1 (vLLM single-LoRA).
  4. Waits for everything (GPU 0 + GPU 1) to be done.
  5. Stops vLLM, runs final 12-system bootstrap on 242p.
  6. Restarts gemma4 vllm container.

Output: output/master_dual_status.json + output/master_dual.log
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] MASTER: %(message)s")
log = logging.getLogger("master")

ROOT = Path("/mnt/data1/work/WigtnOCR-RADP")
STATUS = ROOT / "output/master_dual_status.json"
GATE_PP = 0.05


def write_status(stage: str, **kw):
    payload = {"stage": stage, "ts": time.strftime("%Y-%m-%d %H:%M:%S"), **kw}
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    log.info("STATUS → %s", payload)


def launch_hf_regen_gpu0() -> subprocess.Popen:
    """Sequentially regenerate lambda00 then lambda01 on GPU 0 with HF transformers.
    Backgrounded — returns the wrapper Popen handle."""
    script = """
set -e
echo "=== HF regen lambda00 on GPU 0 ===" >&2
CUDA_VISIBLE_DEVICES=0 uv run python scripts/evaluation/generate_parses.py \
    --base /mnt/data1/work/wigtnOCR-v1/output/wigtnocr-2b-merged \
    --adapter output/checkpoints/radp_b_full_lambda00/final \
    --fold train \
    --out_dir output/parses_full/radp_b_lambda00_eval \
    --batch_size 8

echo "=== HF regen lambda01 on GPU 0 ===" >&2
CUDA_VISIBLE_DEVICES=0 uv run python scripts/evaluation/generate_parses.py \
    --base /mnt/data1/work/wigtnOCR-v1/output/wigtnocr-2b-merged \
    --adapter output/checkpoints/radp_b_full_lambda01/final \
    --fold train \
    --out_dir output/parses_full/radp_b_lambda01_eval \
    --batch_size 8

echo "=== HF regen GPU 0 done ==="
"""
    log.info("launching HF regen for lambda00 + lambda01 on GPU 0 (background)")
    out_log = (ROOT / "output/hf_regen_gpu0.log").open("a")
    return subprocess.Popen(["bash", "-c", script], cwd=ROOT, stdout=out_log, stderr=subprocess.STDOUT)


def wait_for_pid_by_name(name: str, label: str) -> None:
    log.info("waiting for %s to finish", label)
    while subprocess.run(
        ["pgrep", "-f", name], capture_output=True, text=True
    ).stdout.strip():
        time.sleep(30)
    log.info("%s done", label)


def start_single_lora_vllm(name: str, path: str, gpu: int = 1, port: int = 8001):
    subprocess.run(["docker", "rm", "-f", "vllm-radp"], check=False, capture_output=True)
    cmd = [
        "docker", "run", "-d", "--name", "vllm-radp",
        "--runtime", "nvidia",
        "-e", f"NVIDIA_VISIBLE_DEVICES={gpu}",
        "-e", "NVIDIA_DRIVER_CAPABILITIES=compute,utility",
        "-e", "HF_HUB_OFFLINE=1", "-e", "VLLM_LOGGING_LEVEL=WARNING",
        "-v", "/mnt/data1/work/wigtnOCR-v1/output/wigtnocr-2b-merged:/models/v1-merged:ro",
        "-v", f"{ROOT}/output/checkpoints:/loras:ro",
        "-p", f"{port}:{port}",
        "vllm/vllm-openai:nightly",
        "--model", "/models/v1-merged", "--served-model-name", "wigtnocr-v1",
        "--gpu-memory-utilization", "0.5", "--max-model-len", "8192",
        "--trust-remote-code", "--dtype", "bfloat16",
        "--host", "0.0.0.0", "--port", str(port),
        "--enable-lora",
        "--lora-modules", f"{name}=/loras/{path}",
        "--max-lora-rank", "8", "--max-loras", "1",
        "--limit-mm-per-prompt", '{"image": 1}',
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    t0 = time.time()
    while True:
        try:
            urllib.request.urlopen(f"http://localhost:{port}/health", timeout=5)
            log.info("vLLM ready on port %d (%.1fs)", port, time.time() - t0)
            return
        except Exception:
            if time.time() - t0 > 300:
                raise SystemExit(f"vLLM timeout for {name}")
            time.sleep(5)


async def regen_all_242(adapter_name: str, out_dir: Path,
                        all_stem_to_row: dict[str, dict], port: int = 8001,
                        concurrency: int = 16):
    from openai import AsyncOpenAI
    from PIL import Image
    import base64, io
    from wigtnocr_radp.training.data import remap_image_path

    client = AsyncOpenAI(base_url=f"http://localhost:{port}/v1", api_key="dummy",
                          timeout=300.0, max_retries=3)
    sem = asyncio.Semaphore(concurrency)

    # Delete existing & regenerate ALL 242 pages for this seed
    deleted = 0
    for stem in all_stem_to_row:
        f = out_dir / f"{stem}.md"
        if f.exists():
            f.unlink()
            deleted += 1
    log.info("deleted %d existing parses for %s", deleted, adapter_name)

    jobs = [(stem, row, out_dir / f"{stem}.md") for stem, row in all_stem_to_row.items()]
    log.info("%s: generating %d pages", adapter_name, len(jobs))

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
                resp = await client.chat.completions.create(
                    model=adapter_name,
                    messages=[
                        {"role": "system", "content": row["messages"][0]["content"]},
                        {"role": "user", "content": [
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                            {"type": "text", "text": row["messages"][1]["content"].replace("<image>", "", 1).lstrip()},
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
    log.info("regenerated %d/%d for %s", done[0], len(jobs), adapter_name)


def main() -> int:
    write_status("phase_a_launching_gpu0_hf_regen")
    gpu0_proc = launch_hf_regen_gpu0()

    write_status("phase_a_wait_gpu1_regen")
    wait_for_pid_by_name("regen_parses_single_lora.py", "GPU 1 9-variant regen")

    # Build all-fold stem→row map
    val_jsonl = ROOT / "data/KoGovDoc-Bench/val.jsonl"
    val_rows = [json.loads(l) for l in val_jsonl.read_text().splitlines() if l.strip()]
    from wigtnocr_radp.evaluation.parser_outputs import build_page_id_index
    page_to_stem = build_page_id_index(val_jsonl)
    split = json.loads((ROOT / "data/KoGovDoc-RAG/page_split_v1.json").read_text())
    all_pages = set(split["train_pages"]) | set(split["eval_pages"])
    all_stem_to_row = {page_to_stem[f"val_{i:04d}"]: row for i, row in enumerate(val_rows)
                       if f"val_{i:04d}" in all_pages}

    # Seed regen on GPU 1 (since GPU 0 is busy with HF)
    seeds = [
        ("dpo-v1-seed123", "radp_dpo_seed123/final", "radp_dpo_seed123_eval"),
        ("dpo-v1-seed999", "radp_dpo_seed999/final", "radp_dpo_seed999_eval"),
    ]
    for name, path, subdir in seeds:
        write_status(f"phase_b_regen_{name}")
        start_single_lora_vllm(name, path, gpu=1, port=8001)
        asyncio.run(regen_all_242(name, ROOT / "output/parses_full" / subdir, all_stem_to_row, port=8001))

    log.info("stopping vllm-radp")
    subprocess.run(["docker", "stop", "vllm-radp"], check=False)
    time.sleep(5)

    # Wait for GPU 0 HF regen
    write_status("phase_c_wait_gpu0_hf_regen")
    log.info("waiting for GPU 0 HF regen to finish...")
    gpu0_proc.wait()
    log.info("GPU 0 HF regen finished (returncode=%d)", gpu0_proc.returncode)
    if gpu0_proc.returncode != 0:
        write_status("error", reason="GPU 0 HF regen failed", returncode=gpu0_proc.returncode)
        raise SystemExit(gpu0_proc.returncode)

    # Final bootstrap on 242p
    write_status("phase_d_final_bootstrap_242p")
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
    env = {**os.environ, "CUDA_VISIBLE_DEVICES": "1"}
    log.info("$ %s", " ".join(cmd))
    p = subprocess.run(cmd, cwd=ROOT, env=env)
    if p.returncode != 0:
        write_status("error", failed_cmd=cmd, returncode=p.returncode)
        raise SystemExit(p.returncode)

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

    # Restart gemma4
    write_status("phase_e_restart_gemma4")
    subprocess.run(["docker", "start", "vllm-gemma4-31b"], check=False)
    log.info("gemma4 restart issued")

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
