#!/bin/bash
# Orchestrator: v1 parse → vllm reload DPO-v1 → parse → reload DPO-v4 → parse.
set +e
cd /mnt/data1/work/WigtnOCR-RADP

PNG_DIR=output/ohrbench_pngs
PARSE_DIR=output/parses_ohrbench
PORT=8002

count_parses() { find "$1" -name "*.md" 2>/dev/null | wc -l; }

echo "[$(date)] === Phase 2 chain start ==="
echo "[$(date)] PNG count: $(find $PNG_DIR -name '*.png' | wc -l)"

# v1 (current vllm-v1)
echo "[$(date)] === v1 parse ==="
uv run python scripts/evaluation/ohrbench_parse_only.py \
  --model v1 --out_dir $PARSE_DIR/v1 --concurrency 32 2>&1 | tail -10
echo "[$(date)] v1 done: $(count_parses $PARSE_DIR/v1)"

# DPO-v1
echo "[$(date)] === restart vllm with DPO-v1 LoRA ==="
docker rm -f vllm-v1 2>/dev/null
docker run -d --name vllm-v1 \
  --gpus '"device=1"' \
  -e HF_HUB_OFFLINE=1 -e VLLM_LOGGING_LEVEL=WARNING \
  -v /mnt/data1/work/wigtnOCR-v1/output/wigtnocr-2b-merged:/models/v1-merged:ro \
  -v /mnt/data1/work/WigtnOCR-RADP/output/checkpoints:/loras:ro \
  -p $PORT:$PORT \
  vllm/vllm-openai:nightly \
  --model /models/v1-merged --served-model-name v1 \
  --enable-lora --lora-modules dpo-v1=/loras/radp_dpo/final \
  --gpu-memory-utilization 0.6 --max-model-len 8192 \
  --max-lora-rank 8 --max-loras 1 \
  --trust-remote-code --dtype bfloat16 \
  --host 0.0.0.0 --port $PORT \
  --limit-mm-per-prompt '{"image": 1}'
echo "[$(date)] waiting for vllm ready..."
for i in $(seq 1 60); do
  if curl -sf http://localhost:$PORT/v1/models 2>/dev/null | grep -q dpo-v1; then
    echo "[$(date)] ready after ${i}x5s"
    break
  fi
  sleep 5
done

echo "[$(date)] === DPO-v1 parse ==="
uv run python scripts/evaluation/ohrbench_parse_only.py \
  --model dpo-v1 --out_dir $PARSE_DIR/dpo_v1 --concurrency 32 2>&1 | tail -10
echo "[$(date)] dpo-v1 done: $(count_parses $PARSE_DIR/dpo_v1)"

# DPO-v4
echo "[$(date)] === restart vllm with DPO-v4 LoRA ==="
docker rm -f vllm-v1 2>/dev/null
docker run -d --name vllm-v1 \
  --gpus '"device=1"' \
  -e HF_HUB_OFFLINE=1 -e VLLM_LOGGING_LEVEL=WARNING \
  -v /mnt/data1/work/wigtnOCR-v1/output/wigtnocr-2b-merged:/models/v1-merged:ro \
  -v /mnt/data1/work/WigtnOCR-RADP/output/checkpoints:/loras:ro \
  -p $PORT:$PORT \
  vllm/vllm-openai:nightly \
  --model /models/v1-merged --served-model-name v1 \
  --enable-lora --lora-modules dpo-v4=/loras/radp_dpo_v4/final \
  --gpu-memory-utilization 0.6 --max-model-len 8192 \
  --max-lora-rank 8 --max-loras 1 \
  --trust-remote-code --dtype bfloat16 \
  --host 0.0.0.0 --port $PORT \
  --limit-mm-per-prompt '{"image": 1}'
for i in $(seq 1 60); do
  if curl -sf http://localhost:$PORT/v1/models 2>/dev/null | grep -q dpo-v4; then
    echo "[$(date)] ready after ${i}x5s"
    break
  fi
  sleep 5
done

echo "[$(date)] === DPO-v4 parse ==="
uv run python scripts/evaluation/ohrbench_parse_only.py \
  --model dpo-v4 --out_dir $PARSE_DIR/dpo_v4 --concurrency 32 2>&1 | tail -10
echo "[$(date)] dpo-v4 done: $(count_parses $PARSE_DIR/dpo_v4)"

echo "[$(date)] === Phase 2 done ==="
