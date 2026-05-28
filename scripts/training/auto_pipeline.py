"""Autonomous pipeline: Step 1 → gate check → (optional) Step 2 → final result.

Runs unattended overnight:
  1. Waits for the already-running `radp_dpo_v2` training to complete.
  2. Generates eval parses, runs 4-way bootstrap with v1, λ=0, λ=0.1, DPO-v1, DPO-v2.
  3. Reads the 95% CI table. If max paired Δ vs control ≥ 0.05 (5pp gate) on
     either chunker, declares SUCCESS and stops.
  4. Otherwise launches Step 2 (multi-round DPO): generate fresh candidates from
     DPO-v2, score with 3 retrievers, build pairs, train DPO-v3, eval. Re-checks
     the gate after Step 2 with all 6 systems compared.
  5. Writes `output/auto_pipeline_status.json` and `output/auto_pipeline.log`.

Run:
    nohup uv run python scripts/training/auto_pipeline.py > output/auto_pipeline.log 2>&1 &
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Any

# All subprocess invocations run on physical GPU 1 (GPU 0 is occupied by user's vLLM service).
_ENV = {**os.environ, "CUDA_VISIBLE_DEVICES": "1"}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] AUTO: %(message)s")
log = logging.getLogger("auto_pipeline")

ROOT = Path("/mnt/data1/work/WigtnOCR-RADP")
GATE_PP = 0.05  # 5pp
DPO_V2_FINAL = ROOT / "output/checkpoints/radp_dpo_v2/final/adapter_model.safetensors"
DPO_V2_ADAPTER = ROOT / "output/checkpoints/radp_dpo_v2/final"
STATUS = ROOT / "output/auto_pipeline_status.json"


def write_status(stage: str, **kw: Any) -> None:
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    payload = {"stage": stage, "ts": time.strftime("%Y-%m-%d %H:%M:%S"), **kw}
    STATUS.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    log.info("STATUS → %s", payload)


def run(cmd: list[str], log_path: Path | None = None) -> int:
    log.info("$ CUDA_VISIBLE_DEVICES=1 %s", " ".join(cmd))
    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a") as f:
            f.write(f"\n=== {time.strftime('%H:%M:%S')} $ {' '.join(cmd)} ===\n")
            p = subprocess.run(cmd, cwd=ROOT, env=_ENV, stdout=f, stderr=subprocess.STDOUT)
    else:
        p = subprocess.run(cmd, cwd=ROOT, env=_ENV)
    if p.returncode != 0:
        log.error("FAILED with code %d: %s", p.returncode, cmd)
        write_status("error", failed_cmd=cmd, returncode=p.returncode)
        raise SystemExit(p.returncode)
    return p.returncode


def wait_for_file(path: Path, label: str, max_min: int = 240) -> None:
    log.info("waiting for %s (%s)...", label, path)
    t0 = time.time()
    while not path.exists():
        if (time.time() - t0) / 60 > max_min:
            write_status("error", reason=f"timeout waiting for {label}")
            raise SystemExit(2)
        time.sleep(60)
    log.info("found %s after %.1f min", label, (time.time() - t0) / 60)


def gate_pass(ci_json: Path) -> tuple[bool, dict[str, dict[str, float]]]:
    """Return (gate_hit, {label: {chunker: delta_mean_pp, ...}})."""
    d = json.loads(ci_json.read_text())
    hit = False
    summary: dict[str, dict[str, float]] = {}
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
    write_status("waiting_for_dpo_v2_training")
    # 1. Wait for in-progress DPO v2 training to complete.
    wait_for_file(DPO_V2_FINAL, "DPO v2 final adapter", max_min=180)

    write_status("step1_generate_parses")
    # 2. Eval parses for DPO v2.
    parses_v2 = ROOT / "output/parses_full/radp_dpo_v2_eval"
    if not (parses_v2 / "val_0001.md").exists() and len(list(parses_v2.glob("*.md")) if parses_v2.exists() else []) < 70:
        run([
            "uv", "run", "python", "scripts/evaluation/generate_parses.py",
            "--base", "/mnt/data1/work/wigtnOCR-v1/output/wigtnocr-2b-merged",
            "--adapter", str(DPO_V2_ADAPTER),
            "--fold", "eval",
            "--out_dir", str(parses_v2),
            "--batch_size", "8",
        ], log_path=ROOT / "output/results/auto_generate_parses_v2.log")

    write_status("step1_bootstrap")
    # 3. Bootstrap eval with DPO-v1 and DPO-v2.
    ci_path = ROOT / "output/results/auto_step1_ci.json"
    run([
        "uv", "run", "python", "scripts/evaluation/bootstrap_radp_full.py",
        "--device", "cuda:0",
        "--extra_system", "RADP-DPO-v1=output/parses_full/radp_dpo_eval",
        "--extra_system", "RADP-DPO-v2=output/parses_full/radp_dpo_v2_eval",
        "--out_ci", str(ci_path),
        "--out_perqa", str(ROOT / "output/results/auto_step1_perqa.json"),
    ], log_path=ROOT / "output/results/auto_bootstrap_step1.log")

    hit, summary = gate_pass(ci_path)
    log.info("Step 1 gate: hit=%s, summary=%s", hit, summary)
    write_status("step1_eval_done", gate_hit=hit, deltas_pp=summary, ci_path=str(ci_path))

    if hit:
        write_status("SUCCESS_STEP1", gate_hit=True, deltas_pp=summary, ci_path=str(ci_path))
        log.info("✅ GATE HIT IN STEP 1 — stopping")
        return 0

    # 4. Step 2 — multi-round DPO using DPO-v1 (the best so far at +4.12pp) as the
    # new base for candidate gen. DPO-v2 (+1.99pp) was a worse base than v1, so
    # we anchor round 2 on the strongest model. Uses the vLLM container
    # (vllm-radp) already serving v1-merged + dpo-v1 LoRA on port 8001.
    log.info("❌ Step 1 gate missed. Beginning Step 2 (multi-round DPO on DPO-v1 via vLLM)")
    write_status("step2_generate_candidates")
    cand_v3 = ROOT / "output/candidates/dpo_v1_round2_candidates.jsonl"
    run([
        "uv", "run", "python", "scripts/training/generate_candidates_vllm.py",
        "--base_url", "http://localhost:8001/v1",
        "--model", "dpo-v1",
        "--out", str(cand_v3),
        "--temperatures", "0.7", "1.2",
        "--max_new_tokens", "1536",
        "--concurrency", "16",
        "--resume",
    ], log_path=ROOT / "output/candidates/auto_step2_gen.log")

    # Stop the vLLM container before DPO training to free GPU memory.
    log.info("stopping vLLM container before training")
    subprocess.run(["docker", "stop", "vllm-radp"], check=False)

    write_status("step2_score_candidates")
    scores_v3 = ROOT / "output/candidates/dpo_v1_round2_candidate_scores_3r.jsonl"
    run([
        "uv", "run", "python", "scripts/training/score_candidates.py",
        "--candidates", str(cand_v3),
        "--out", str(scores_v3),
        "--retrievers", "bge-m3", "ml-e5-large", "qwen3-emb-8b",
        "--n_distractors", "100", "--pool_seed", "42",
        "--device", "cuda:0",
    ], log_path=ROOT / "output/candidates/auto_step2_score.log")

    write_status("step2_build_pairs")
    pairs_v3 = ROOT / "output/preference/dpo_v1_round2_pairs.jsonl"
    run([
        "uv", "run", "python", "scripts/training/build_preference_pairs.py",
        "--candidates", str(cand_v3),
        "--scores", str(scores_v3),
        "--out", str(pairs_v3),
        "--min_gap", "0.05",
    ], log_path=ROOT / "output/preference/auto_step2_build.log")

    write_status("step2_train_dpo_v3")
    # DPO v3 = fresh LoRA on v1 merged base, trained with round-2 preferences
    # (candidates sampled from DPO-v1, scored with 3-retriever). Round 2 because
    # the preferences are sourced from a retrieval-aware model's distribution,
    # not from the production parser's.
    run([
        "uv", "run", "python", "scripts/training/train_radp_dpo.py",
        "--pairs", str(pairs_v3),
        "--output_dir", "output/checkpoints/radp_dpo_v3",
        "--epochs", "2",
        "--per_device_batch_size", "1",
        "--grad_accum", "8",
        "--beta", "0.1",
        "--lr", "1e-5",
        "--logging_steps", "5",
        "--save_steps", "50",
    ], log_path=ROOT / "output/checkpoints/auto_step2_train.log")

    write_status("step2_generate_parses")
    parses_v3 = ROOT / "output/parses_full/radp_dpo_v3_eval"
    run([
        "uv", "run", "python", "scripts/evaluation/generate_parses.py",
        "--base", "/mnt/data1/work/wigtnOCR-v1/output/wigtnocr-2b-merged",
        "--adapter", "output/checkpoints/radp_dpo_v3/final",
        "--fold", "eval",
        "--out_dir", str(parses_v3),
        "--batch_size", "8",
    ], log_path=ROOT / "output/results/auto_generate_parses_v3.log")

    write_status("step2_bootstrap")
    ci_path2 = ROOT / "output/results/auto_step2_ci.json"
    run([
        "uv", "run", "python", "scripts/evaluation/bootstrap_radp_full.py",
        "--device", "cuda:0",
        "--extra_system", "RADP-DPO-v1=output/parses_full/radp_dpo_eval",
        "--extra_system", "RADP-DPO-v2=output/parses_full/radp_dpo_v2_eval",
        "--extra_system", "RADP-DPO-v3=output/parses_full/radp_dpo_v3_eval",
        "--out_ci", str(ci_path2),
        "--out_perqa", str(ROOT / "output/results/auto_step2_perqa.json"),
    ], log_path=ROOT / "output/results/auto_bootstrap_step2.log")

    hit2, summary2 = gate_pass(ci_path2)
    final = "SUCCESS_STEP2" if hit2 else "DONE_GATE_MISSED"
    write_status(final, gate_hit=hit2, deltas_pp=summary2, ci_path=str(ci_path2))
    log.info("=== FINAL: %s ===  deltas=%s", final, summary2)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        write_status("interrupted")
        raise
    except Exception as e:
        log.exception("uncaught exception")
        write_status("error", error=repr(e))
        raise
