"""Train 4 additional DPO-v1 seeds and regen parses for the 7-seed merged eval.

We have DPO-v1 (seed=42 default), DPO-v1-seed123, DPO-v1-seed999. Adding seeds
7, 314, 1337, 2024 takes us to 7 seeds total. The 7-seed merged headline effect
(stacking per-Q-A deltas: 663 × 7 = 4641 paired observations) absorbs across-seed
sampling variance and sharpens the paired CI from the current 3-seed merged
[−0.64, +2.90] (P=0.900) toward two-sided significance.

Per seed, ~1.5h on GPU 1:
  1. train_radp_dpo.py --seed N  → output/checkpoints/radp_dpo_seed{N}/final  (~48min)
  2. generate_parses.py --fold all (242p HF decode)  → output/parses_full/radp_dpo_seed{N}_eval  (~30min)

Total 4 × 1.5h ≈ 6h sequential on GPU 1. Doesn't touch GPU 0 (gemma4 untouched).

When all seeds done, prints a one-shot 7-seed merged bootstrap result.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] ADD_SEED: %(message)s")
log = logging.getLogger("add_seed")

ROOT = Path("/mnt/data1/work/WigtnOCR-RADP")
STATUS = ROOT / "output/add_seeds_status.json"

# Identical recipe to DPO-v1 (BGE-single scoring, β=0.1, lr=1e-5, 2 epochs)
PAIRS = "output/preference/v1_pairs.jsonl"
BETA = "0.1"
LR = "1e-5"
EPOCHS = "2"

SEEDS = [7, 314, 1337, 2024]

_ENV = {**os.environ, "CUDA_VISIBLE_DEVICES": "1"}


def write_status(stage: str, **kw):
    payload = {"stage": stage, "ts": time.strftime("%Y-%m-%d %H:%M:%S"), **kw}
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    log.info("STATUS → %s", payload)


def train_one_seed(seed: int) -> Path:
    ckpt = ROOT / f"output/checkpoints/radp_dpo_seed{seed}"
    final = ckpt / "final"
    if final.exists() and (final / "adapter_model.safetensors").exists():
        log.info("seed=%d already trained → %s", seed, final)
        return final
    log_path = ckpt.with_suffix(".log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "uv", "run", "python", "scripts/training/train_radp_dpo.py",
        "--pairs", PAIRS,
        "--beta", BETA,
        "--lr", LR,
        "--epochs", EPOCHS,
        "--seed", str(seed),
        "--output_dir", str(ckpt),
    ]
    log.info("training seed=%d  (~48 min)", seed)
    log.info("  $ %s", " ".join(cmd))
    t0 = time.time()
    with log_path.open("a") as f:
        f.write(f"\n==== add_dpo_seeds.py launching at {time.strftime('%F %T')} ====\n")
        p = subprocess.run(cmd, cwd=ROOT, env=_ENV, stdout=f, stderr=subprocess.STDOUT)
    log.info("seed=%d trained in %.1fmin (rc=%d)", seed, (time.time() - t0) / 60, p.returncode)
    if p.returncode != 0:
        raise SystemExit(f"training seed={seed} failed; see {log_path}")
    if not (final / "adapter_model.safetensors").exists():
        raise SystemExit(f"training seed={seed} produced no adapter at {final}")
    return final


def regen_parses(seed: int, adapter: Path) -> Path:
    out_dir = ROOT / f"output/parses_full/radp_dpo_seed{seed}_eval"
    if out_dir.exists() and len(list(out_dir.glob("*.md"))) >= 240:
        log.info("seed=%d parses already done → %s (%d files)", seed, out_dir,
                 len(list(out_dir.glob("*.md"))))
        return out_dir
    log_path = ROOT / f"output/regen_seed{seed}.log"
    cmd = [
        "uv", "run", "python", "scripts/evaluation/generate_parses.py",
        "--base", "/mnt/data1/work/wigtnOCR-v1/output/wigtnocr-2b-merged",
        "--adapter", str(adapter),
        "--fold", "all",
        "--out_dir", str(out_dir),
        "--batch_size", "8",
    ]
    log.info("regen parses seed=%d  (~30 min, 242 pages)", seed)
    log.info("  $ %s", " ".join(cmd))
    t0 = time.time()
    with log_path.open("a") as f:
        f.write(f"\n==== add_dpo_seeds.py regen at {time.strftime('%F %T')} ====\n")
        p = subprocess.run(cmd, cwd=ROOT, env=_ENV, stdout=f, stderr=subprocess.STDOUT)
    log.info("seed=%d parses in %.1fmin (rc=%d)", seed, (time.time() - t0) / 60, p.returncode)
    if p.returncode != 0:
        raise SystemExit(f"regen seed={seed} failed; see {log_path}")
    return out_dir


def run_bootstrap() -> None:
    """Re-run bootstrap_radp_full.py with all 7 seeds injected, producing the
    final perqa json that robustness_boost.py will consume for the 7-seed merge."""
    ci_path = ROOT / "output/results/FULL_HF_ci_242p_7seeds.json"
    perqa_path = ROOT / "output/results/FULL_HF_perqa_242p_7seeds.json"
    cmd = [
        "uv", "run", "python", "scripts/evaluation/bootstrap_radp_full.py",
        "--device", "cuda:0",  # logical 0 (CUDA_VISIBLE_DEVICES=1)
        "--fold", "all",
        "--extra_system", "RADP-DPO-v1=output/parses_full/radp_dpo_eval",
        "--extra_system", "RADP-DPO-v2=output/parses_full/radp_dpo_v2_eval",
        "--extra_system", "RADP-DPO-v3=output/parses_full/radp_dpo_v3_eval",
        "--extra_system", "RADP-DPO-v4=output/parses_full/radp_dpo_v4_eval",
        "--extra_system", "RADP-SimPO=output/parses_full/radp_simpo_eval",
        "--extra_system", "DPO-v1-seed123=output/parses_full/radp_dpo_seed123_eval",
        "--extra_system", "DPO-v1-seed999=output/parses_full/radp_dpo_seed999_eval",
        "--extra_system", "DPO-v1-seed7=output/parses_full/radp_dpo_seed7_eval",
        "--extra_system", "DPO-v1-seed314=output/parses_full/radp_dpo_seed314_eval",
        "--extra_system", "DPO-v1-seed1337=output/parses_full/radp_dpo_seed1337_eval",
        "--extra_system", "DPO-v1-seed2024=output/parses_full/radp_dpo_seed2024_eval",
        "--out_ci", str(ci_path),
        "--out_perqa", str(perqa_path),
    ]
    log.info("final 7-seed bootstrap on 242p")
    log.info("  $ %s", " ".join(cmd))
    p = subprocess.run(cmd, cwd=ROOT, env=_ENV)
    if p.returncode != 0:
        write_status("bootstrap_error", returncode=p.returncode)
        raise SystemExit(p.returncode)
    write_status("DONE_bootstrap_ready", ci_path=str(ci_path), perqa_path=str(perqa_path),
                 next_step="run robustness_boost.py with new perqa to get 7-seed merged Hit@5 CI")


def main() -> int:
    write_status("starting", seeds=SEEDS, pairs=PAIRS, beta=BETA, lr=LR, epochs=EPOCHS)

    for seed in SEEDS:
        write_status(f"train_seed{seed}")
        adapter = train_one_seed(seed)
        write_status(f"regen_seed{seed}")
        regen_parses(seed, adapter)
        write_status(f"done_seed{seed}")

    write_status("running_final_bootstrap")
    run_bootstrap()
    log.info("ALL DONE")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        log.exception("uncaught")
        write_status("crashed")
        raise
