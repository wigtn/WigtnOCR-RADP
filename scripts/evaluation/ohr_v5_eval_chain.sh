#!/bin/bash

echo "ERROR: this legacy mixed-release chain is disabled because it targets quarantined OHR artifacts." >&2
echo "Use the compat2036 pipeline, or a fresh full-v2 pipeline, with new output names." >&2
exit 2

set +e
cd /mnt/data1/work/WigtnOCR-RADP
PORT=8002
echo "[$(date)] === v5 eval chain start ==="
docker rm -f vllm-v1 vllm-v5 vllm-v1-gpu0 vllm-v1-gpu1 2>/dev/null
docker run -d --name vllm-v5 --gpus '"device=1"' \
  -e HF_HUB_OFFLINE=1 -e VLLM_LOGGING_LEVEL=WARNING \
  -v /mnt/data1/work/wigtnOCR-v1/output/wigtnocr-2b-merged:/models/v1-merged:ro \
  -v /mnt/data1/work/WigtnOCR-RADP/output/checkpoints:/loras:ro \
  -p $PORT:$PORT vllm/vllm-openai:nightly \
  --model /models/v1-merged --served-model-name v1 \
  --enable-lora --lora-modules v5=/loras/radp_dpo_v5_hardneg/final \
  --gpu-memory-utilization 0.85 --max-model-len 32768 \
  --max-lora-rank 8 --max-loras 1 --trust-remote-code --dtype bfloat16 \
  --host 0.0.0.0 --port $PORT --limit-mm-per-prompt '{"image": 1}'
echo "[$(date)] waiting vllm ready..."
for i in $(seq 1 80); do
  curl -sf http://localhost:$PORT/v1/models 2>/dev/null | grep -q v5 && { echo "[$(date)] ready after ${i}x5s"; break; }
  sleep 5
done
echo "[$(date)] === v5 parse (4040 pages) ==="
uv run python scripts/evaluation/ohrbench_parse_only.py \
  --base_url http://localhost:$PORT/v1 --model v5 \
  --out_dir output/parses_ohrbench/v5 --concurrency 32 2>&1 | tail -5
echo "[$(date)] v5 parse done: $(find output/parses_ohrbench/v5 -name '*.md' | wc -l)"
docker rm -f vllm-v5 2>/dev/null
sleep 5
echo "[$(date)] === score v1,dpo_v4,v5 ==="
CUDA_VISIBLE_DEVICES=0 uv run python scripts/evaluation/ohrbench_v1dpo_full.py \
  --device cuda:0 --out_perqa output/results/ohr_v5_perqa.json \
  --out_ci output/results/ohr_v5_ci.json --n_boot 1000 \
  --models v1,dpo_v4,v5 2>&1 | tee logs/ohr_v5_scoring.log
echo "[$(date)] === v5 eval done ==="
