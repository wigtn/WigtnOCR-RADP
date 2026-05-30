#!/bin/bash
# Watchdog: wait until DPO-v1 parse hits 4041 .md files,
# then swap GPU1 vllm to DPO-v4 LoRA and run DPO-v4 parse.
set +e
cd /mnt/data1/work/WigtnOCR-RADP

PARSE_DIR=output/parses_ohrbench
PORT=8003

echo "[$(date)] watchdog start — waiting for DPO-v1 parse"
while true; do
  n=$(find $PARSE_DIR/dpo_v1 -name "*.md" 2>/dev/null | wc -l)
  echo "[$(date)] dpo-v1 parses: $n / 4041"
  if [ "$n" -ge 4041 ]; then
    echo "[$(date)] DPO-v1 complete"
    break
  fi
  sleep 120
done

echo "[$(date)] restart vllm GPU1 with DPO-v4 LoRA"
docker rm -f vllm-v1-gpu1 2>/dev/null
docker run -d --name vllm-v1-gpu1 \
  --gpus '"device=1"' \
  -e HF_HUB_OFFLINE=1 -e VLLM_LOGGING_LEVEL=WARNING \
  -v /mnt/data1/work/wigtnOCR-v1/output/wigtnocr-2b-merged:/models/v1-merged:ro \
  -v /mnt/data1/work/WigtnOCR-RADP/output/checkpoints:/loras:ro \
  -p $PORT:$PORT \
  vllm/vllm-openai:nightly \
  --model /models/v1-merged --served-model-name v1 \
  --enable-lora --lora-modules dpo-v4=/loras/radp_dpo_v4/final \
  --gpu-memory-utilization 0.85 --max-model-len 16384 \
  --max-lora-rank 8 --max-loras 1 \
  --trust-remote-code --dtype bfloat16 \
  --host 0.0.0.0 --port $PORT \
  --limit-mm-per-prompt '{"image": 1}'

echo "[$(date)] waiting for DPO-v4 vllm ready..."
for i in $(seq 1 80); do
  if curl -sf http://localhost:$PORT/v1/models 2>/dev/null | grep -q dpo-v4; then
    echo "[$(date)] ready after ${i}x5s"
    break
  fi
  sleep 5
done

echo "[$(date)] === DPO-v4 parse start ==="
uv run python scripts/evaluation/ohrbench_parse_only.py \
  --base_url http://localhost:$PORT/v1 \
  --model dpo-v4 --out_dir $PARSE_DIR/dpo_v4 --concurrency 32 2>&1
echo "[$(date)] === DPO-v4 parse done: $(find $PARSE_DIR/dpo_v4 -name '*.md' | wc -l) parses ==="
