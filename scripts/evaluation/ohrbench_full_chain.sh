#!/bin/bash
# Chain: wait DPO-v4 parse done → run scoring → combined KoGov+OHR CI.
# Threshold is 4040 (one outlier page doesn't parse even at 32K max-len).

echo "ERROR: this legacy mixed-release chain is disabled because it targets quarantined OHR artifacts." >&2
echo "Use the compat2036 producer/scorer defaults only after regenerating the audited compatibility caches." >&2
exit 2

set +e
cd /mnt/data1/work/WigtnOCR-RADP

PARSE_DIR=output/parses_ohrbench
THRESHOLD=4040

echo "[$(date)] === Chain start: wait for DPO-v4 parse ==="
while true; do
  n=$(find $PARSE_DIR/dpo_v4 -name "*.md" 2>/dev/null | wc -l)
  echo "[$(date)] dpo-v4: $n / 4041"
  if [ "$n" -ge "$THRESHOLD" ]; then
    echo "[$(date)] DPO-v4 parse done"
    break
  fi
  sleep 120
done

echo "[$(date)] === Stop vLLM containers (free GPUs for scoring) ==="
docker rm -f vllm-v1-gpu0 vllm-v1-gpu1 2>&1 | tail -2
sleep 5

echo "[$(date)] === Phase 3: scoring (3 model × 3 retriever × parser_native) ==="
CUDA_VISIBLE_DEVICES=0 uv run python scripts/evaluation/ohrbench_v1dpo_full.py \
  --device cuda:0 \
  --out_perqa output/results/ohrbench_v1dpo_perqa.json \
  --out_ci output/results/ohrbench_v1dpo_ci.json \
  --n_boot 1000 \
  --models v1,dpo_v1,dpo_v4 \
  2>&1 | tee logs/ohr_scoring.log

echo "[$(date)] === Phase 4: combined KoGov+OHR paired CI ==="
uv run python scripts/evaluation/ohrbench_combined_ci.py \
  --kogov_perqa output/results/FULL_HF_perqa_242p_7seeds.json \
  --ohr_perqa output/results/ohrbench_v1dpo_perqa.json \
  --out output/results/combined_kogov_ohr_ci.json \
  2>&1 | tee logs/ohr_combined_ci.log

echo "[$(date)] === Chain complete ==="
echo "Outputs:"
echo "  output/results/ohrbench_v1dpo_perqa.json"
echo "  output/results/ohrbench_v1dpo_ci.json"
echo "  output/results/combined_kogov_ohr_ci.json"
