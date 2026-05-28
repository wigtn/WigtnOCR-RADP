"""Master orchestrator: full HF regen of 242p for all 9 variants + 2 seeds.

Strategy:
  - Stop gemma4 to free GPU 0.
  - Split work across GPU 0 + GPU 1 (parallel bash scripts).
  - Main 9 variants: --fold train (169p train fold; 73p eval is already HF-clean).
  - Seeds: --fold all (242p; no HF baseline existed for them).
  - Wait for both GPUs.
  - Run final 242p bootstrap with v1 ref as primary control.
  - Restart gemma4.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] FULL_HF: %(message)s")
log = logging.getLogger("full_hf")

ROOT = Path("/mnt/data1/work/WigtnOCR-RADP")
STATUS = ROOT / "output/full_hf_status.json"


def write_status(stage: str, **kw):
    payload = {"stage": stage, "ts": time.strftime("%Y-%m-%d %H:%M:%S"), **kw}
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    log.info("STATUS → %s", payload)


def build_bash(gpu: int, jobs: list[tuple[str, str, str, str]]) -> str:
    """Build a bash script that runs each (adapter, out_dir, fold) sequentially on the given GPU.

    jobs: list of (label, adapter_path, out_dir, fold)
    """
    lines = ["set -e"]
    for label, adapter, out_dir, fold in jobs:
        lines.append(f'echo "=== [GPU{gpu}] {label} ({fold}) ===" >&2')
        lines.append(
            f"CUDA_VISIBLE_DEVICES={gpu} uv run python scripts/evaluation/generate_parses.py "
            f"--base /mnt/data1/work/wigtnOCR-v1/output/wigtnocr-2b-merged "
            f"--adapter {adapter} "
            f"--fold {fold} "
            f"--out_dir {out_dir} "
            f"--batch_size 8"
        )
    lines.append(f'echo "=== [GPU{gpu}] all jobs done ==="')
    return "\n".join(lines)


def main() -> int:
    # Stop gemma4 to free GPU 0
    write_status("stopping_gemma4")
    subprocess.run(["docker", "stop", "vllm-gemma4-31b"], check=False)
    time.sleep(5)

    # Stop any leftover vllm-radp
    subprocess.run(["docker", "rm", "-f", "vllm-radp"], check=False, capture_output=True)

    # GPU 0 jobs: 6 main variants (lambda00/01/03/05 + DPO-v1/v2), all 169p train fold
    gpu0_jobs = [
        ("lambda00", "output/checkpoints/radp_b_full_lambda00/final", "output/parses_full/radp_b_lambda00_eval", "train"),
        ("lambda01", "output/checkpoints/radp_b_full_lambda01/final", "output/parses_full/radp_b_lambda01_eval", "train"),
        ("lambda03", "output/checkpoints/radp_b_full_lambda03/final", "output/parses_full/radp_b_lambda03_eval", "train"),
        ("lambda05", "output/checkpoints/radp_b_full_lambda05/final", "output/parses_full/radp_b_lambda05_eval", "train"),
        ("dpo-v1",   "output/checkpoints/radp_dpo/final",              "output/parses_full/radp_dpo_eval", "train"),
        ("dpo-v2",   "output/checkpoints/radp_dpo_v2/final",           "output/parses_full/radp_dpo_v2_eval", "train"),
    ]

    # GPU 1 jobs: 3 main variants (DPO-v3/v4 + SimPO) + 2 seeds (all 242p)
    gpu1_jobs = [
        ("dpo-v3",   "output/checkpoints/radp_dpo_v3/final",           "output/parses_full/radp_dpo_v3_eval", "train"),
        ("dpo-v4",   "output/checkpoints/radp_dpo_v4/final",           "output/parses_full/radp_dpo_v4_eval", "train"),
        ("simpo",    "output/checkpoints/radp_simpo/final",            "output/parses_full/radp_simpo_eval", "train"),
        ("seed123",  "output/checkpoints/radp_dpo_seed123/final",      "output/parses_full/radp_dpo_seed123_eval", "all"),
        ("seed999",  "output/checkpoints/radp_dpo_seed999/final",      "output/parses_full/radp_dpo_seed999_eval", "all"),
    ]

    write_status("starting_parallel_hf_regen")
    log0 = (ROOT / "output/full_hf_gpu0.log").open("a")
    log1 = (ROOT / "output/full_hf_gpu1.log").open("a")

    proc0 = subprocess.Popen(["bash", "-c", build_bash(0, gpu0_jobs)],
                              cwd=ROOT, stdout=log0, stderr=subprocess.STDOUT)
    proc1 = subprocess.Popen(["bash", "-c", build_bash(1, gpu1_jobs)],
                              cwd=ROOT, stdout=log1, stderr=subprocess.STDOUT)
    log.info("launched GPU 0 pid=%d, GPU 1 pid=%d", proc0.pid, proc1.pid)

    write_status("waiting_for_both_gpus", gpu0_pid=proc0.pid, gpu1_pid=proc1.pid)
    proc0.wait()
    log.info("GPU 0 done (rc=%d)", proc0.returncode)
    proc1.wait()
    log.info("GPU 1 done (rc=%d)", proc1.returncode)

    if proc0.returncode != 0 or proc1.returncode != 0:
        write_status("error", gpu0_rc=proc0.returncode, gpu1_rc=proc1.returncode)
        raise SystemExit(1)

    # Final 242p bootstrap
    write_status("final_bootstrap_242p")
    ci_path = ROOT / "output/results/FULL_HF_ci_242p.json"
    perqa_path = ROOT / "output/results/FULL_HF_perqa_242p.json"
    cmd = [
        "uv", "run", "python", "scripts/evaluation/bootstrap_radp_full.py",
        "--device", "cuda:1",
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
    p = subprocess.run(cmd, cwd=ROOT, env=env)
    if p.returncode != 0:
        write_status("error", bootstrap_failed=True, rc=p.returncode)
        raise SystemExit(p.returncode)

    # Parse results
    d = json.loads(ci_path.read_text())
    summary: dict = {}
    for ck, by_label in d["by_chunker"].items():
        for label, row in by_label.items():
            if "vs_lambda0_ci" not in row:
                continue
            mean_pp = row["vs_lambda0_ci"]["mean"] * 100
            summary.setdefault(label, {})[ck] = round(mean_pp, 3)

    # Restart gemma4
    write_status("restarting_gemma4")
    subprocess.run(["docker", "start", "vllm-gemma4-31b"], check=False)

    write_status("DONE", deltas_pp_vs_lambda0=summary, ci_path=str(ci_path),
                 note="Δ shown vs lambda00 (RADP-B matched control). For DPO/SimPO comparison, use v1 ref RCPS as anchor.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        log.exception("uncaught")
        write_status("error", error=repr(e))
        raise
