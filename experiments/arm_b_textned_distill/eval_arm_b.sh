#!/bin/bash
# Arm B (TextNED-DPO) evaluation launch — reuses the EXISTING harness on BOTH folds,
# identical protocol to RADP-DPO. Run AFTER experiments/.../train_arm_b.py has produced
# output/checkpoints/arm_b_textned/final.
#
#   Fold 1: KoGov 242p / 663-QA  (Hit@5, parser_native, 3-retriever macro, paired bootstrap)
#   Fold 2: OHR-Bench 2,264-QA   (Hit@5, parser_native, 3-retriever macro, paired bootstrap)
#
# This script is GPU-bound (vLLM parse + retriever encode). It does NOT train.
set +e
cd /mnt/data1/work/WigtnOCR-RADP
ROOT=/mnt/data1/work/WigtnOCR-RADP
V1_MERGED=/mnt/data1/work/wigtnOCR-v1/output/wigtnocr-2b-merged
ADAPTER=$ROOT/output/checkpoints/arm_b_textned/final
LOGDIR=$ROOT/experiments/arm_b_textned_distill/logs
mkdir -p "$LOGDIR"

if [ ! -d "$ADAPTER" ]; then
  echo "ERROR: Arm B adapter not found at $ADAPTER — run train_arm_b.py first." ; exit 1
fi

echo "[$(date)] ============ Arm B EVAL — KoGov fold (242p / 663-QA) ============"
# 1a. Generate Arm-B parses on the combined 242p fold (same generate_parses.py as RADP-DPO).
CUDA_VISIBLE_DEVICES=0 uv run python scripts/evaluation/generate_parses.py \
  --base "$V1_MERGED" \
  --adapter "$ADAPTER" \
  --fold all \
  --out_dir output/parses_full/arm_b_textned_eval \
  --batch_size 8 2>&1 | tee "$LOGDIR/kogov_parse.log" | tail -5

# 1b. Paired bootstrap CI vs v1/λ0 baseline, adding Arm B (and RADP-DPO for the head-to-head).
#     parser_native chunker, 3-retriever macro is handled inside the harness.
CUDA_VISIBLE_DEVICES=0 uv run python scripts/evaluation/bootstrap_radp_full.py \
  --device cuda:0 \
  --fold all \
  --chunkers parser_native \
  --extra_system "RADP-DPO=output/parses_full/radp_dpo_v4_eval" \
  --extra_system "ArmB-TextNED=output/parses_full/arm_b_textned_eval" \
  --out_ci   output/results/arm_b_kogov_ci.json \
  --out_perqa output/results/arm_b_kogov_perqa.json 2>&1 | tee "$LOGDIR/kogov_bootstrap.log" | tail -20

echo "[$(date)] ============ Arm B EVAL — OHR-Bench fold (2,264-QA) ============"
# 2a. Serve v1-merged + Arm-B LoRA via vLLM (same pattern as ohr_v5_eval_chain.sh).
PORT=8002
docker rm -f vllm-v1 vllm-armb 2>/dev/null
docker run -d --name vllm-armb --gpus '"device=0"' \
  -e HF_HUB_OFFLINE=1 -e VLLM_LOGGING_LEVEL=WARNING \
  -v "$V1_MERGED":/models/v1-merged:ro \
  -v "$ROOT/output/checkpoints":/loras:ro \
  -p $PORT:$PORT vllm/vllm-openai:nightly \
  --model /models/v1-merged --served-model-name v1 \
  --enable-lora --lora-modules arm_b=/loras/arm_b_textned/final \
  --gpu-memory-utilization 0.85 --max-model-len 32768 \
  --max-lora-rank 8 --max-loras 1 --trust-remote-code --dtype bfloat16 \
  --host 0.0.0.0 --port $PORT --limit-mm-per-prompt '{"image": 1}'
echo "[$(date)] waiting vllm ready..."
for i in $(seq 1 80); do
  curl -sf http://localhost:$PORT/v1/models 2>/dev/null | grep -q arm_b && { echo "ready after ${i}x5s"; break; }
  sleep 5
done

# 2b. Parse OHR-Bench pages with the Arm-B LoRA → output/parses_ohrbench/arm_b/<domain>/*.md
uv run python scripts/evaluation/ohrbench_parse_only.py \
  --base_url http://localhost:$PORT/v1 --model arm_b \
  --out_dir output/parses_ohrbench/arm_b --concurrency 32 2>&1 | tee "$LOGDIR/ohr_parse.log" | tail -5
docker rm -f vllm-armb 2>/dev/null
sleep 5

# 2c. Score v1 + RADP-DPO(dpo_v4) + Arm B together, paired bootstrap, 3-retriever macro, Hit@5.
CUDA_VISIBLE_DEVICES=0 uv run python scripts/evaluation/ohrbench_v1dpo_full.py \
  --device cuda:0 --n_boot 1000 \
  --models v1,dpo_v4,arm_b \
  --out_perqa output/results/arm_b_ohr_perqa.json \
  --out_ci    output/results/arm_b_ohr_ci.json 2>&1 | tee "$LOGDIR/ohr_scoring.log" | tail -20

echo "[$(date)] ============ Arm B EVAL DONE ============"
echo "KoGov CI:  output/results/arm_b_kogov_ci.json"
echo "OHR   CI:  output/results/arm_b_ohr_ci.json"
echo "Apply the DECISION RULE in experiments/arm_b_textned_distill/README.md to OHR Hit@5."
