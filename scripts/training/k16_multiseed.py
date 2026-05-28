"""(d) on K=16: DPO-K16 multi-seed for robust statistical sig.

Launches after (A) K16 pipeline completes — uses the SAME K=16 preference pair
file (output/preference/v1_pairs_k16.jsonl) produced by (A) phase 5, but trains
4 additional seeds (7, 314, 1337, 2024) with identical hyperparameters to the
seed=42 main run.

Final 5-seed merged bootstrap stacks per-Q-A deltas across {seed=42, 7, 314,
1337, 2024} (663 × 5 = 3,315 paired observations) to produce the paper-grade
robust positive: mean Δ with 95% CI that excludes 0 (target).

Total ~6h on GPU 1 sequential. Each seed: ~1.5h (train 48min + regen 30min).

Pre-conditions (asserted at start):
  - output/preference/v1_pairs_k16.jsonl exists (A phase 5)
  - output/checkpoints/radp_dpo_k16/final exists (A phase 6, seed=42 baseline)
  - output/parses_full/radp_dpo_k16_eval/ exists (A phase 7)
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] K16_MS: %(message)s")
log = logging.getLogger("k16_ms")

ROOT = Path("/mnt/data1/work/WigtnOCR-RADP")
STATUS = ROOT / "output/k16_multiseed_status.json"

PAIRS = "output/preference/v1_pairs_k16.jsonl"
V1_MERGED = "/mnt/data1/work/wigtnOCR-v1/output/wigtnocr-2b-merged"
SEEDS = [7, 314, 1337, 2024]
ENV_G1 = {**os.environ, "CUDA_VISIBLE_DEVICES": "1"}


def write_status(stage: str, **kw):
    payload = {"stage": stage, "ts": time.strftime("%Y-%m-%d %H:%M:%S"), **kw}
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    log.info("STATUS → %s", payload)


def assert_a_completed() -> None:
    """Block until (A) K16 pipeline left its expected outputs."""
    pairs = ROOT / PAIRS
    ckpt = ROOT / "output/checkpoints/radp_dpo_k16/final"
    parses = ROOT / "output/parses_full/radp_dpo_k16_eval"
    if not pairs.exists():
        raise SystemExit(f"missing: {pairs} — run (A) k16_pipeline.py first")
    if not (ckpt / "adapter_model.safetensors").exists():
        raise SystemExit(f"missing: {ckpt} — (A) phase 6 not done")
    if not parses.exists() or len(list(parses.glob("*.md"))) < 240:
        raise SystemExit(f"missing: {parses} — (A) phase 7 not done")
    log.info("(A) outputs verified: pairs / ckpt / parses all present")


def train_seed(seed: int) -> Path:
    ckpt_dir = ROOT / f"output/checkpoints/radp_dpo_k16_seed{seed}"
    final = ckpt_dir / "final"
    if (final / "adapter_model.safetensors").exists():
        log.info("seed=%d already trained", seed)
        return final
    log_path = ckpt_dir.with_suffix(".log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "uv", "run", "python", "scripts/training/train_radp_dpo.py",
        "--pairs", PAIRS,
        "--beta", "0.1", "--lr", "1e-5", "--epochs", "2",
        "--seed", str(seed),
        "--output_dir", str(ckpt_dir),
    ]
    log.info("training K16-seed%d (~48min)", seed)
    t0 = time.time()
    with log_path.open("a") as f:
        f.write(f"\n==== k16_multiseed train at {time.strftime('%F %T')} ====\n")
        p = subprocess.run(cmd, cwd=ROOT, env=ENV_G1, stdout=f, stderr=subprocess.STDOUT)
    log.info("seed=%d trained in %.1fmin (rc=%d)", seed, (time.time() - t0) / 60, p.returncode)
    if p.returncode != 0:
        raise SystemExit(f"train seed={seed} failed; see {log_path}")
    return final


def regen_seed(seed: int, adapter: Path) -> Path:
    out_dir = ROOT / f"output/parses_full/radp_dpo_k16_seed{seed}_eval"
    if out_dir.exists() and len(list(out_dir.glob("*.md"))) >= 240:
        log.info("seed=%d parses already done", seed)
        return out_dir
    log_path = ROOT / f"output/k16_seed{seed}_regen.log"
    cmd = [
        "uv", "run", "python", "scripts/evaluation/generate_parses.py",
        "--base", V1_MERGED,
        "--adapter", str(adapter),
        "--fold", "all",
        "--out_dir", str(out_dir),
        "--batch_size", "8",
    ]
    log.info("regen parses K16-seed%d (~30min)", seed)
    t0 = time.time()
    with log_path.open("a") as f:
        f.write(f"\n==== k16_multiseed regen at {time.strftime('%F %T')} ====\n")
        p = subprocess.run(cmd, cwd=ROOT, env=ENV_G1, stdout=f, stderr=subprocess.STDOUT)
    log.info("seed=%d regen in %.1fmin (rc=%d)", seed, (time.time() - t0) / 60, p.returncode)
    if p.returncode != 0:
        raise SystemExit(f"regen seed={seed} failed; see {log_path}")
    return out_dir


def final_bootstrap() -> None:
    ci_path = ROOT / "output/results/FULL_HF_ci_242p_k16_5seeds.json"
    perqa_path = ROOT / "output/results/FULL_HF_perqa_242p_k16_5seeds.json"
    extra = [
        "--extra_system", "RADP-DPO-v1=output/parses_full/radp_dpo_eval",
        "--extra_system", "RADP-DPO-K16=output/parses_full/radp_dpo_k16_eval",
    ]
    for s in SEEDS:
        extra += ["--extra_system", f"K16-seed{s}=output/parses_full/radp_dpo_k16_seed{s}_eval"]
    cmd = [
        "uv", "run", "python", "scripts/evaluation/bootstrap_radp_full.py",
        "--device", "cuda:0", "--fold", "all",
        *extra,
        "--out_ci", str(ci_path),
        "--out_perqa", str(perqa_path),
    ]
    log.info("$ %s", " ".join(cmd))
    p = subprocess.run(cmd, cwd=ROOT, env=ENV_G1)
    if p.returncode != 0:
        raise SystemExit("final bootstrap failed")

    # 5-seed merged headline (CPU only, uses robustness_boost style merge inline)
    # Reuse robustness_boost to compute 5-seed merged Δ vs v1 on parser_native Hit@5.
    log.info("computing 5-seed merged stats via robustness_boost variant")
    # Inline merge
    import numpy as np
    raw = json.loads(perqa_path.read_text())
    systems = raw["systems"]
    REF = "v1 (ref)"
    DPO_SEEDS = ["RADP-DPO-K16"] + [f"K16-seed{s}" for s in SEEDS]
    summary = {}
    for ck in ("md_h3", "parser_native"):
        ref_h5 = np.stack([
            (np.asarray(systems[f"{REF}__{ck}"][f"{r}__mrr@5"], dtype=float) > 0).astype(float)
            for r in ("bge-m3", "ml-e5-large", "qwen3-emb-8b")
        ]).mean(0)
        per_seed_means = []
        stacked_var = []
        for lbl in DPO_SEEDS:
            v_h5 = np.stack([
                (np.asarray(systems[f"{lbl}__{ck}"][f"{r}__mrr@5"], dtype=float) > 0).astype(float)
                for r in ("bge-m3", "ml-e5-large", "qwen3-emb-8b")
            ]).mean(0)
            stacked_var.append(v_h5)
            per_seed_means.append(float((v_h5 - ref_h5).mean() * 100))
        var = np.concatenate(stacked_var)
        ref = np.concatenate([ref_h5] * len(DPO_SEEDS))
        # 10k bootstrap
        rng = np.random.default_rng(42)
        n = len(var)
        diffs = var - ref
        pos = 0
        boots = []
        for _ in range(10000):
            idx = rng.integers(0, n, n)
            m = diffs[idx].mean()
            boots.append(m)
            if m > 0:
                pos += 1
        boots = np.array(boots)
        lo, hi = np.quantile(boots, [0.025, 0.975])
        summary[ck] = {
            "5seed_merged_delta_pp": float(diffs.mean() * 100),
            "ci_lo_pp": float(lo * 100),
            "ci_hi_pp": float(hi * 100),
            "p_pos": pos / 10000,
            "per_seed_delta_pp": per_seed_means,
            "across_seed_std_pp": float(np.std(per_seed_means, ddof=1)),
        }
    write_status("DONE", ci_path=str(ci_path), perqa_path=str(perqa_path), summary=summary)


def main() -> int:
    log.info("=== K16 multi-seed (d) pipeline start ===")
    assert_a_completed()
    for seed in SEEDS:
        write_status(f"train_seed{seed}")
        adapter = train_seed(seed)
        write_status(f"regen_seed{seed}")
        regen_seed(seed, adapter)
        write_status(f"done_seed{seed}")
    write_status("final_bootstrap")
    final_bootstrap()
    log.info("=== K16 multi-seed (d) DONE ===")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        log.exception("uncaught")
        write_status("crashed")
        raise
