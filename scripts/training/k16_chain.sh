#!/bin/bash
# Wait for (A) k16_pipeline DONE → commit (A) → launch (d) k16_multiseed.
# Designed to run as a long-lived background process; exits only when (d) ends.
set +e  # do not abort on individual command failures (we log + continue)
cd /mnt/data1/work/WigtnOCR-RADP

STATUS=output/k16_pipeline_status.json
echo "[chain] start: $(date)"

# Poll for (A) DONE every 60s
while true; do
  if grep -q '"stage": "DONE"' "$STATUS" 2>/dev/null; then
    echo "[chain] (A) DONE detected at $(date)"
    break
  fi
  sleep 60
done

# Commit (A) results
echo "[chain] committing (A) results"
bash scripts/utils/auto_commit.sh \
  "feat(eval): (A) K16 pipeline DONE — DPO-K16 seed=42 on 242p" \
  output/k16_pipeline_status.json \
  output/results/FULL_HF_ci_242p_k16.json \
  output/results/FULL_HF_perqa_242p_k16.json \
  output/checkpoints/radp_dpo_k16/final/adapter_config.json

# Launch (d)
echo "[chain] launching (d) k16_multiseed at $(date)"
uv run python scripts/training/k16_multiseed.py 2>&1 | tee output/k16_multiseed.log

echo "[chain] DONE: $(date)"
