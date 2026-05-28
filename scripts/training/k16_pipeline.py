"""End-to-end K=2→16 DPO pipeline orchestrator.

Phases (all serial, total ~2.5-3h):
  1. Wait both vllm servers ready (vllm-v1@8002 GPU1, vllm-v1-g0@8003 GPU0)
  2. Generate 14 new candidates × 2,667 train pages, split front/back half
     across the two vllm endpoints. ~10-15 min.
  3. Merge existing K=2 + new K=14 → K=16 candidates file.
  4. Score all candidates (page-local RCPS, BGE-only — same retriever as DPO-v1).
     ~30 min on GPU 1.
  5. Build preference pairs (gap ≥ 5pp filter). Expected 1,500-2,500 pairs.
  6. Train DPO-K16 (β=0.1, lr=1e-5, 2 epochs, seed=42). ~1h on GPU 1.
  7. HF parse regen on 242p combined fold. ~30 min on GPU 1.
  8. Bootstrap CI on 242p (existing systems + DPO-K16). 5 min.

Writes status to output/k16_pipeline_status.json after each phase.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import time
import urllib.request
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] K16: %(message)s")
log = logging.getLogger("k16")

ROOT = Path("/mnt/data1/work/WigtnOCR-RADP")
STATUS = ROOT / "output/k16_pipeline_status.json"

V1_MERGED = "/mnt/data1/work/wigtnOCR-v1/output/wigtnocr-2b-merged"

ENV_G1 = {**os.environ, "CUDA_VISIBLE_DEVICES": "1"}

# Outputs
EXISTING_K2 = ROOT / "output/candidates/v1_train_candidates.jsonl"            # 5,334 K=2
NEW_K14_FRONT = ROOT / "output/candidates/v1_k14_front.jsonl"                  # GPU 1
NEW_K14_BACK = ROOT / "output/candidates/v1_k14_back.jsonl"                    # GPU 0
MERGED_K16 = ROOT / "output/candidates/v1_train_candidates_k16.jsonl"
SCORES_K16 = ROOT / "output/candidates/v1_k16_scores.jsonl"
PAIRS_K16 = ROOT / "output/preference/v1_pairs_k16.jsonl"
CKPT_DIR = ROOT / "output/checkpoints/radp_dpo_k16"
PARSES_DIR = ROOT / "output/parses_full/radp_dpo_k16_eval"
CI_OUT = ROOT / "output/results/FULL_HF_ci_242p_k16.json"
PERQA_OUT = ROOT / "output/results/FULL_HF_perqa_242p_k16.json"


def write_status(stage: str, **kw):
    payload = {"stage": stage, "ts": time.strftime("%Y-%m-%d %H:%M:%S"), **kw}
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    log.info("STATUS → %s", payload)


def wait_for_vllm(url: str, name: str, timeout: int = 600) -> None:
    """Wait until /v1/models endpoint responds 200."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            urllib.request.urlopen(url + "/v1/models", timeout=5).read()
            log.info("%s ready (%.0fs)", name, time.time() - t0)
            return
        except Exception:
            time.sleep(5)
    raise SystemExit(f"{name} not ready within {timeout}s")


def phase1_wait_vllm() -> None:
    write_status("phase1_wait_vllm")
    wait_for_vllm("http://localhost:8002", "vllm-v1 (GPU1)")


def phase2_gen_candidates() -> None:
    """Single-endpoint candidate gen on GPU 1 vllm-v1 (concurrency 48, ~20-25 min)."""
    write_status("phase2_gen_candidates")
    gen_log = (ROOT / "output/k16_gen.log").open("a")
    cmd = [
        "uv", "run", "python", "scripts/training/generate_candidates_k16.py",
        "--base_url", "http://localhost:8002/v1", "--model", "v1",
        "--out", str(NEW_K14_FRONT),  # single output file
        "--concurrency", "48",
    ]
    log.info("$ %s", " ".join(cmd))
    p = subprocess.Popen(cmd, cwd=ROOT, stdout=gen_log, stderr=subprocess.STDOUT)
    rc = p.wait()
    if rc != 0:
        raise SystemExit(f"gen failed rc={rc}; see {ROOT}/output/k16_gen.log")
    gen_log.close()


def phase3_merge_k16() -> None:
    write_status("phase3_merge_k16")
    n = 0
    seen: set[tuple[str, int]] = set()
    with MERGED_K16.open("w") as fout:
        for path in [EXISTING_K2, NEW_K14_FRONT]:  # single new file (GPU 1 only)
            if not path.exists():
                log.warning("missing: %s", path)
                continue
            for line in path.read_text().splitlines():
                if not line.strip():
                    continue
                r = json.loads(line)
                key = (r["page_id"], int(r["candidate_idx"]))
                if key in seen:
                    continue
                seen.add(key)
                fout.write(line + "\n")
                n += 1
    log.info("merged K=16: %d candidates (deduped from %d)", n, len(seen))


def phase4_score() -> None:
    """Page-local RCPS scoring on merged K=16 candidates (BGE-only)."""
    write_status("phase4_score")
    cmd = [
        "uv", "run", "python", "scripts/training/score_candidates.py",
        "--candidates", str(MERGED_K16),
        "--out", str(SCORES_K16),
        "--retrievers", "bge-m3",  # same as DPO-v1
        "--device", "cuda:0",      # logical 0 with CUDA_VISIBLE_DEVICES=1
    ]
    log_path = ROOT / "output/k16_score.log"
    with log_path.open("a") as f:
        f.write(f"\n==== k16_pipeline phase4 at {time.strftime('%F %T')} ====\n")
        p = subprocess.run(cmd, cwd=ROOT, env=ENV_G1, stdout=f, stderr=subprocess.STDOUT)
    if p.returncode != 0:
        raise SystemExit(f"score failed rc={p.returncode}; see {log_path}")


def phase5_build_pairs() -> None:
    write_status("phase5_build_pairs")
    cmd = [
        "uv", "run", "python", "scripts/training/build_preference_pairs.py",
        "--candidates", str(MERGED_K16),
        "--scores", str(SCORES_K16),
        "--out", str(PAIRS_K16),
        "--min_gap", "0.05",
    ]
    log.info("$ %s", " ".join(cmd))
    p = subprocess.run(cmd, cwd=ROOT)
    if p.returncode != 0:
        raise SystemExit("build_pairs failed")
    n_pairs = sum(1 for _ in PAIRS_K16.open())
    log.info("built %d preference pairs (target ≥1,500 for K=16)", n_pairs)


def phase6_train_dpo() -> None:
    write_status("phase6_train_dpo")
    cmd = [
        "uv", "run", "python", "scripts/training/train_radp_dpo.py",
        "--pairs", str(PAIRS_K16),
        "--beta", "0.1", "--lr", "1e-5", "--epochs", "2", "--seed", "42",
        "--output_dir", str(CKPT_DIR),
    ]
    log_path = CKPT_DIR.with_suffix(".log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log.info("$ %s", " ".join(cmd))
    with log_path.open("a") as f:
        f.write(f"\n==== k16_pipeline phase6 at {time.strftime('%F %T')} ====\n")
        p = subprocess.run(cmd, cwd=ROOT, env=ENV_G1, stdout=f, stderr=subprocess.STDOUT)
    if p.returncode != 0:
        raise SystemExit(f"DPO train failed; see {log_path}")


def phase7_regen() -> None:
    write_status("phase7_regen")
    cmd = [
        "uv", "run", "python", "scripts/evaluation/generate_parses.py",
        "--base", V1_MERGED,
        "--adapter", str(CKPT_DIR / "final"),
        "--fold", "all",
        "--out_dir", str(PARSES_DIR),
        "--batch_size", "8",
    ]
    log_path = ROOT / "output/k16_regen.log"
    log.info("$ %s", " ".join(cmd))
    with log_path.open("a") as f:
        f.write(f"\n==== k16_pipeline phase7 at {time.strftime('%F %T')} ====\n")
        p = subprocess.run(cmd, cwd=ROOT, env=ENV_G1, stdout=f, stderr=subprocess.STDOUT)
    if p.returncode != 0:
        raise SystemExit(f"regen failed; see {log_path}")


def phase8_bootstrap() -> None:
    write_status("phase8_bootstrap")
    cmd = [
        "uv", "run", "python", "scripts/evaluation/bootstrap_radp_full.py",
        "--device", "cuda:0",
        "--fold", "all",
        "--extra_system", "RADP-DPO-v1=output/parses_full/radp_dpo_eval",
        "--extra_system", "RADP-DPO-K16=" + str(PARSES_DIR.relative_to(ROOT)),
        "--out_ci", str(CI_OUT),
        "--out_perqa", str(PERQA_OUT),
    ]
    log.info("$ %s", " ".join(cmd))
    p = subprocess.run(cmd, cwd=ROOT, env=ENV_G1)
    if p.returncode != 0:
        raise SystemExit("bootstrap failed")

    # Summary
    d = json.loads(CI_OUT.read_text())
    write_status("DONE", ci_path=str(CI_OUT), perqa_path=str(PERQA_OUT),
                 summary={ck: {
                     label: round(row["vs_lambda0_ci"]["mean"] * 100, 2)
                     for label, row in by_label.items()
                     if "vs_lambda0_ci" in row
                 } for ck, by_label in d["by_chunker"].items()})


def main() -> int:
    log.info("=== K16 pipeline start ===")
    phase1_wait_vllm()
    phase2_gen_candidates()
    phase3_merge_k16()
    phase4_score()
    phase5_build_pairs()
    phase6_train_dpo()
    phase7_regen()
    phase8_bootstrap()
    log.info("=== K16 pipeline DONE ===")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        log.exception("uncaught")
        write_status("crashed")
        raise
