"""Arm B (TextNED-DPO) training launch — mirrors the RADP-DPO recipe exactly,
swapping ONLY the preference-pair source.

This is the training half of the retrieval-reward ablation. It calls the SAME
`scripts/training/train_radp_dpo.py` driver, the SAME DPO loss with LoRA-toggle
reference (RadpDPOTrainer), the SAME LoRA config (r=8, α=32), and the SAME
hyperparameters used for the RADP-DPO K-pool runs:

    β = 0.1, lr = 1e-5, epochs = 2, seed = 42, fresh LoRA (π_init = π_ref).

(Recipe source: scripts/training/k16_pipeline.py phase 6 and
scripts/training/add_dpo_seeds.py — both β=0.1/lr=1e-5/2ep. The only input that
differs from RADP-DPO is `--pairs`, which here points at the TextNED-ranked
pairs built by build_preference_pairs_textned.py.)

NOTE on β: the in-repo RADP-DPO recipe is β=0.1. The review brief referenced
β=0.05; expose it via --beta if you must match that exact number, but the
default below mirrors what the headline RADP-DPO runs (R2/R3) actually used so
Arm B is a *controlled* swap of selection signal only.

Phases:
  1. (CPU) Build TextNED pairs from the K-pool candidates — no GPU.
  2. (GPU) Train DPO on those pairs. ~1h on one A100 for ~1.5-2.5k pairs, 2 ep.

This script DOES launch GPU training in phase 2. Run phase 1 alone with
--pairs_only to stay CPU and produce the pairs without touching the GPU.

Usage:
    # CPU-only: build the TextNED pairs and stop
    uv run python experiments/arm_b_textned_distill/train_arm_b.py --pairs_only

    # full: build pairs then train DPO (needs 1 A100)
    CUDA_VISIBLE_DEVICES=1 uv run python experiments/arm_b_textned_distill/train_arm_b.py
"""

from __future__ import annotations

import argparse
import logging
import os
import subprocess
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] ARM_B: %(message)s")
log = logging.getLogger("arm_b_train")

ROOT = Path("/mnt/data1/work/WigtnOCR-RADP")

# Candidate pool — SAME as RADP-DPO R3 (K=14, 37,338 candidates / 2,667 pages).
CANDIDATES = ROOT / "output/candidates/v1_k14_front.jsonl"
PAIRS = ROOT / "output/preference/arm_b_textned_pairs.jsonl"
CKPT_DIR = ROOT / "output/checkpoints/arm_b_textned"

# RADP-DPO recipe (identical to Arm A) — see module docstring.
BETA = "0.1"
LR = "1e-5"
EPOCHS = "2"
SEED = "42"
MIN_GAP = "0.05"

_ENV = {**os.environ, "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES", "1")}


def run(cmd: list[str], log_path: Path, env: dict | None = None) -> None:
    log.info("$ %s", " ".join(cmd))
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a") as f:
        f.write(f"\n=== {time.strftime('%F %T')} $ {' '.join(cmd)} ===\n")
        p = subprocess.run(cmd, cwd=ROOT, env=env or os.environ.copy(),
                           stdout=f, stderr=subprocess.STDOUT)
    if p.returncode != 0:
        raise SystemExit(f"command failed rc={p.returncode}; see {log_path}")


def phase1_build_pairs(args) -> None:
    log.info("phase 1 (CPU): build TextNED preference pairs from %s", CANDIDATES.name)
    run([
        "uv", "run", "python", "scripts/training/build_preference_pairs_textned.py",
        "--candidates", str(args.candidates),
        "--out", str(args.pairs),
        "--min_gap", MIN_GAP,
    ], log_path=ROOT / "experiments/arm_b_textned_distill/logs/build_pairs.log")
    n = sum(1 for _ in args.pairs.open())
    log.info("built %d TextNED preference pairs", n)


def phase2_train(args) -> None:
    log.info("phase 2 (GPU): DPO train on TextNED pairs (β=%s, lr=%s, %s ep, seed=%s)",
             BETA, LR, EPOCHS, SEED)
    run([
        "uv", "run", "python", "scripts/training/train_radp_dpo.py",
        "--pairs", str(args.pairs),
        "--output_dir", str(args.output_dir),
        "--beta", str(args.beta),
        "--lr", LR,
        "--epochs", EPOCHS,
        "--seed", SEED,
        "--per_device_batch_size", "1",
        "--grad_accum", "8",
        "--lora_r", "8",
        "--lora_alpha", "32",
    ], log_path=ROOT / "experiments/arm_b_textned_distill/logs/train.log", env=_ENV)
    log.info("DPO done. final adapter: %s", args.output_dir / "final")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidates", type=Path, default=CANDIDATES)
    ap.add_argument("--pairs", type=Path, default=PAIRS)
    ap.add_argument("--output_dir", type=Path, default=CKPT_DIR)
    ap.add_argument("--beta", default=BETA, help="DPO beta (repo RADP-DPO default 0.1)")
    ap.add_argument("--pairs_only", action="store_true",
                    help="CPU only: build the TextNED pairs and exit (no GPU training)")
    args = ap.parse_args()

    phase1_build_pairs(args)
    if args.pairs_only:
        log.info("--pairs_only set: stopping after CPU pair build. Pairs at %s", args.pairs)
        return 0
    phase2_train(args)
    log.info("=== Arm B training pipeline DONE ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
