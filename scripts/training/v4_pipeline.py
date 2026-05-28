"""DPO-v4 pipeline — true multi-round (warmstart from DPO-v1) with BGE-M3 single scoring.

Lessons baked in from v2/v3 ablations:
  - BGE-M3 single scoring > 3-retriever average (v1 vs v2: +4.12 → +1.99pp)
  - Curriculum multi-round (fresh LoRA) does NOT compound (v3: +0.22pp)
  - True multi-round needs warmstart: LoRA initialised from prior best DPO weights

This script reuses the round-2 candidates (already sampled from DPO-v1 via vLLM)
but rescores them with BGE-M3 single and trains DPO with warmstart from DPO-v1.

Stages:
  1. Score candidates (BGE-M3 single)
  2. Build pairs (gap ≥ 5pp)
  3. Train DPO-v4 (warmstart from DPO-v1 LoRA, BGE single pairs)
  4. Generate eval parses
  5. Bootstrap 7-way CI

Run:
    nohup uv run python scripts/training/v4_pipeline.py > output/v4_pipeline.log 2>&1 &
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] V4: %(message)s")
log = logging.getLogger("v4_pipeline")

ROOT = Path("/mnt/data1/work/WigtnOCR-RADP")
GATE_PP = 0.05
DPO_V1_ADAPTER = ROOT / "output/checkpoints/radp_dpo/final"
CAND_V3 = ROOT / "output/candidates/dpo_v1_round2_candidates.jsonl"  # reuse
SCORES_BGE = ROOT / "output/candidates/dpo_v1_round2_candidate_scores_bge.jsonl"
PAIRS_BGE = ROOT / "output/preference/dpo_v1_round2_pairs_bge.jsonl"
CKPT_DIR = ROOT / "output/checkpoints/radp_dpo_v4"
PARSES_V4 = ROOT / "output/parses_full/radp_dpo_v4_eval"
CI_OUT = ROOT / "output/results/v4_ci.json"
PERQA_OUT = ROOT / "output/results/v4_perqa.json"
STATUS = ROOT / "output/v4_pipeline_status.json"

_ENV = {**os.environ, "CUDA_VISIBLE_DEVICES": "1"}


def write_status(stage: str, **kw) -> None:
    payload = {"stage": stage, "ts": time.strftime("%Y-%m-%d %H:%M:%S"), **kw}
    STATUS.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    log.info("STATUS → %s", payload)


def run(cmd: list[str], log_path: Path) -> None:
    log.info("$ CUDA_VISIBLE_DEVICES=1 %s", " ".join(cmd))
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a") as f:
        f.write(f"\n=== {time.strftime('%H:%M:%S')} $ {' '.join(cmd)} ===\n")
        p = subprocess.run(cmd, cwd=ROOT, env=_ENV, stdout=f, stderr=subprocess.STDOUT)
    if p.returncode != 0:
        write_status("error", failed_cmd=cmd, returncode=p.returncode)
        raise SystemExit(p.returncode)


def gate_pass(ci_json: Path) -> tuple[bool, dict]:
    d = json.loads(ci_json.read_text())
    hit = False
    summary: dict = {}
    for ck, by_label in d["by_chunker"].items():
        for label, row in by_label.items():
            if "vs_lambda0_ci" not in row:
                continue
            mean_pp = row["vs_lambda0_ci"]["mean"] * 100
            summary.setdefault(label, {})[ck] = round(mean_pp, 3)
            if mean_pp >= GATE_PP * 100:
                hit = True
    return hit, summary


def main() -> int:
    # 1. Score candidates with BGE-M3 single
    write_status("score_bge_single")
    run([
        "uv", "run", "python", "scripts/training/score_candidates.py",
        "--candidates", str(CAND_V3),
        "--out", str(SCORES_BGE),
        "--retrievers", "bge-m3",
        "--n_distractors", "100", "--pool_seed", "42",
        "--device", "cuda:0",
    ], log_path=ROOT / "output/candidates/v4_score.log")

    # 2. Build preference pairs (gap ≥ 5pp)
    write_status("build_pairs_bge")
    run([
        "uv", "run", "python", "scripts/training/build_preference_pairs.py",
        "--candidates", str(CAND_V3),
        "--scores", str(SCORES_BGE),
        "--out", str(PAIRS_BGE),
        "--min_gap", "0.05",
    ], log_path=ROOT / "output/preference/v4_build.log")

    # 3. Train DPO-v4 with warmstart from DPO-v1
    write_status("train_v4_warmstart")
    run([
        "uv", "run", "python", "scripts/training/train_radp_dpo.py",
        "--pairs", str(PAIRS_BGE),
        "--init_adapter", str(DPO_V1_ADAPTER),
        "--output_dir", str(CKPT_DIR),
        "--epochs", "2",
        "--per_device_batch_size", "1",
        "--grad_accum", "8",
        "--beta", "0.1",
        "--lr", "5e-6",  # half of v1's 1e-5 — warmstart is at +4pp already, smaller step
        "--logging_steps", "5",
        "--save_steps", "50",
    ], log_path=ROOT / "output/checkpoints/v4_train.log")

    # 4. Generate eval parses
    write_status("generate_parses")
    run([
        "uv", "run", "python", "scripts/evaluation/generate_parses.py",
        "--base", "/mnt/data1/work/wigtnOCR-v1/output/wigtnocr-2b-merged",
        "--adapter", str(CKPT_DIR / "final"),
        "--fold", "eval",
        "--out_dir", str(PARSES_V4),
        "--batch_size", "8",
    ], log_path=ROOT / "output/results/v4_parses.log")

    # 5. Bootstrap 7-way CI (control + λ=0.1/0.3/0.5 + v1 + DPO-v1/v2/v3/v4)
    write_status("bootstrap_7way")
    run([
        "uv", "run", "python", "scripts/evaluation/bootstrap_radp_full.py",
        "--device", "cuda:0",
        "--extra_system", "RADP-DPO-v1=output/parses_full/radp_dpo_eval",
        "--extra_system", "RADP-DPO-v2=output/parses_full/radp_dpo_v2_eval",
        "--extra_system", "RADP-DPO-v3=output/parses_full/radp_dpo_v3_eval",
        "--extra_system", "RADP-DPO-v4=output/parses_full/radp_dpo_v4_eval",
        "--out_ci", str(CI_OUT),
        "--out_perqa", str(PERQA_OUT),
    ], log_path=ROOT / "output/results/v4_bootstrap.log")

    hit, summary = gate_pass(CI_OUT)
    final = "SUCCESS_GATE_HIT" if hit else "DONE_GATE_MISSED"
    write_status(final, gate_hit=hit, deltas_pp=summary, ci_path=str(CI_OUT))
    log.info("=== FINAL: %s ===  deltas=%s", final, summary)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        log.exception("uncaught")
        write_status("error", error=repr(e))
        raise
