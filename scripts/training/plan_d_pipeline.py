"""Plan D orchestrator — runs Phase 2-4 after Phase 1 (parse expansion) completes.

Phase 1 (parse expansion via vLLM, separate process): already running.
Phase 2: train DPO-v1 with 2 additional seeds (123, 999). Sequential, ~50min each.
Phase 3: restart vLLM with new adapters; generate parses for new seeds on 242p.
Phase 4: final bootstrap on 242p with all 11 systems (control, λ, v1, DPO 1-4, SimPO, DPO seed 123, DPO seed 999).
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] PLAN_D: %(message)s")
log = logging.getLogger("plan_d")

ROOT = Path("/mnt/data1/work/WigtnOCR-RADP")
STATUS = ROOT / "output/plan_d_status.json"
GATE_PP = 0.05  # 5pp gate

_ENV = {**os.environ, "CUDA_VISIBLE_DEVICES": "1"}


def write_status(stage: str, **kw: Any) -> None:
    payload = {"stage": stage, "ts": time.strftime("%Y-%m-%d %H:%M:%S"), **kw}
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    log.info("STATUS → %s", payload)


def run(cmd: list[str], log_path: Path) -> None:
    log.info("$ %s", " ".join(cmd))
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a") as f:
        f.write(f"\n=== {time.strftime('%H:%M:%S')} $ {' '.join(cmd)} ===\n")
        p = subprocess.run(cmd, cwd=ROOT, env=_ENV, stdout=f, stderr=subprocess.STDOUT)
    if p.returncode != 0:
        write_status("error", failed_cmd=cmd, returncode=p.returncode)
        raise SystemExit(p.returncode)


def wait_phase_1_done() -> None:
    """Wait for expand_parses_vllm.py process to finish."""
    log.info("waiting for Phase 1 (parse expansion) to finish...")
    t0 = time.time()
    while True:
        # Check if process is still running
        result = subprocess.run(
            ["pgrep", "-f", "expand_parses_vllm.py"], capture_output=True, text=True
        )
        if not result.stdout.strip():
            elapsed = (time.time() - t0) / 60
            log.info("Phase 1 process ended after %.1f min wait", elapsed)
            break
        time.sleep(30)


def stop_vllm() -> None:
    log.info("stopping vllm-radp container")
    subprocess.run(["docker", "stop", "vllm-radp"], check=False)


def start_vllm_with_seeds() -> None:
    """Restart vLLM with original 9 LoRAs + 2 new seeds."""
    log.info("restarting vllm-radp with seed adapters added")
    subprocess.run(["docker", "rm", "-f", "vllm-radp"], check=False)
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
        "--lora-modules",
        "lambda00=/loras/radp_b_full_lambda00/final",
        "lambda01=/loras/radp_b_full_lambda01/final",
        "lambda03=/loras/radp_b_full_lambda03/final",
        "lambda05=/loras/radp_b_full_lambda05/final",
        "dpo-v1=/loras/radp_dpo/final",
        "dpo-v2=/loras/radp_dpo_v2/final",
        "dpo-v3=/loras/radp_dpo_v3/final",
        "dpo-v4=/loras/radp_dpo_v4/final",
        "simpo=/loras/radp_simpo/final",
        "dpo-v1-seed123=/loras/radp_dpo_seed123/final",
        "dpo-v1-seed999=/loras/radp_dpo_seed999/final",
        "--max-lora-rank", "8",
        "--max-loras", "12",
        "--limit-mm-per-prompt", '{"image": 1}',
    ]
    p = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if p.returncode != 0:
        write_status("error", failed_cmd=cmd, stderr=p.stderr)
        raise SystemExit(1)
    # Wait for ready
    import urllib.request
    log.info("waiting for vLLM ready (with seed adapters)...")
    t0 = time.time()
    while True:
        try:
            urllib.request.urlopen("http://localhost:8001/health", timeout=5)
            log.info("vLLM ready after %.1f min", (time.time() - t0) / 60)
            return
        except Exception:
            if (time.time() - t0) / 60 > 5:
                write_status("error", reason="vLLM startup timeout")
                raise SystemExit(1)
            time.sleep(5)


def main() -> int:
    # Wait for Phase 1 (parse expansion) to finish
    write_status("phase1_wait_parse_expansion")
    wait_phase_1_done()

    # Stop vLLM to free GPU 1 for training
    write_status("stopping_vllm_for_training")
    stop_vllm()
    time.sleep(5)

    # Phase 2a: Train DPO-v1 with seed 123
    write_status("phase2a_train_seed123")
    run([
        "uv", "run", "python", "scripts/training/train_radp_dpo.py",
        "--pairs", "output/preference/v1_pairs.jsonl",
        "--output_dir", "output/checkpoints/radp_dpo_seed123",
        "--epochs", "2", "--per_device_batch_size", "1", "--grad_accum", "8",
        "--beta", "0.1", "--lr", "1e-5",
        "--seed", "123",
        "--logging_steps", "5", "--save_steps", "100",
    ], log_path=ROOT / "output/checkpoints/seed123_train.log")

    # Phase 2b: Train DPO-v1 with seed 999
    write_status("phase2b_train_seed999")
    run([
        "uv", "run", "python", "scripts/training/train_radp_dpo.py",
        "--pairs", "output/preference/v1_pairs.jsonl",
        "--output_dir", "output/checkpoints/radp_dpo_seed999",
        "--epochs", "2", "--per_device_batch_size", "1", "--grad_accum", "8",
        "--beta", "0.1", "--lr", "1e-5",
        "--seed", "999",
        "--logging_steps", "5", "--save_steps", "100",
    ], log_path=ROOT / "output/checkpoints/seed999_train.log")

    # Phase 3: Restart vLLM with new seeds; generate parses
    write_status("phase3_vllm_restart")
    start_vllm_with_seeds()

    write_status("phase3_generate_parses")
    # Map seeds to output dirs (create them)
    (ROOT / "output/parses_full/radp_dpo_seed123_eval").mkdir(parents=True, exist_ok=True)
    (ROOT / "output/parses_full/radp_dpo_seed999_eval").mkdir(parents=True, exist_ok=True)

    # Reuse expand_parses_vllm; the new seed mappings are already in MODEL_TO_DIR.
    # The script skips already-existing files, so only the new seed dirs get filled.
    run([
        "uv", "run", "python", "scripts/training/expand_parses_vllm.py",
        "--base_url", "http://localhost:8001/v1",
        "--models", "dpo-v1-seed123", "dpo-v1-seed999",
        "--concurrency", "16",
    ], log_path=ROOT / "output/parses_full/expand_seeds.log")

    write_status("stopping_vllm_after_seeds")
    stop_vllm()
    time.sleep(5)

    # Phase 4: Final bootstrap on 242p
    write_status("phase4_final_bootstrap")
    ci_path = ROOT / "output/results/plan_d_ci_242p.json"
    perqa_path = ROOT / "output/results/plan_d_perqa_242p.json"
    run([
        "uv", "run", "python", "scripts/evaluation/bootstrap_radp_full.py",
        "--device", "cuda:0",
        "--fold", "all",  # use train+eval = 242p
        "--extra_system", "RADP-DPO-v1=output/parses_full/radp_dpo_eval",
        "--extra_system", "RADP-DPO-v2=output/parses_full/radp_dpo_v2_eval",
        "--extra_system", "RADP-DPO-v3=output/parses_full/radp_dpo_v3_eval",
        "--extra_system", "RADP-DPO-v4=output/parses_full/radp_dpo_v4_eval",
        "--extra_system", "RADP-SimPO=output/parses_full/radp_simpo_eval",
        "--extra_system", "DPO-v1-seed123=output/parses_full/radp_dpo_seed123_eval",
        "--extra_system", "DPO-v1-seed999=output/parses_full/radp_dpo_seed999_eval",
        "--out_ci", str(ci_path),
        "--out_perqa", str(perqa_path),
    ], log_path=ROOT / "output/results/plan_d_bootstrap.log")

    # Parse final result and decide
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
    log.info("=== FINAL: %s === summary=%s", final, summary)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        log.exception("uncaught")
        write_status("error", error=repr(e))
        raise
