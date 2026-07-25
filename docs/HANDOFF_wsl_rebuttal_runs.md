# Handoff — WSL 실행 2건 (Prod per-domain absent · MinerU table-ON retrieval)

> 2026-07-26. 승인 완료(Harrison). 근거·기대값: `docs/FINDINGS_per_domain_prod.md`.
> 실행 owner: 손상우. 스크립트·문서는 `rebuttal/family-neutral-absent` 브랜치에 커밋됨.

## Step 0 — 준비 (WSL, 1회)

```bash
cd <WigtnOCR-RADP>
git fetch origin && git checkout rebuttal/family-neutral-absent && git pull
# 필요 스크립트: scripts/analysis/{absent_per_domain,perqa_source_rcps,grid_single_parser}.py
# mineru_val_tableon predictions 294개도 같은 브랜치에 있음.
```

## Run 1 — [최우선, 수 초] Prod per-domain absent (L1/L4)

```bash
cd <WigtnOCR-RADP>
uv run python scripts/analysis/absent_per_domain.py \
    --parser-dir /mnt/data1/work/wigtnOCR-v1/results/kogovdoc/v1_val/predictions \
    --label Prod
```

**게이트 (통과 못 하면 수치 사용 금지):** overall L1 = 20.2% ± 0.2pp, overall L4 = 16.9% ± 0.2pp.
구현 자체는 MinerU table-ON으로 검증 완료(공식 수치 10개 자릿수 재현) — 게이트가 깨지면
원인은 구현이 아니라 v1_val 입력(예측 파일 세대 불일치)이니 predictions 타임스탬프부터 볼 것.

**회신 양식:** 스크립트 출력 표 전체(원값 분수 포함)를 그대로 붙여넣기.

## Run 2 — [오늘 착수, 15–40분] MinerU table-ON RCPS/Hit@1

`baseline_grid.py` 수정 불필요 — 전용 러너가 동일 파이프라인(같은 chunker/3-retriever/
`compute_rcps`)을 쓰고, per-QA JSON까지 떨궈서 per-domain 분해가 바로 이어진다.

```bash
cd <WigtnOCR-RADP>
# (1) 본 계산 — Table 1 비교 기준인 parser_native 먼저
uv run python scripts/analysis/grid_single_parser.py \
    --parser-dir results/kogovdoc/mineru_val_tableon/predictions \
    --label MinerU-tableON --chunker parser_native --device cuda

# (2) per-domain 분해 (초 단위)
uv run python scripts/analysis/perqa_source_rcps.py \
    --perqa output/results/perqa_MinerU-tableON_parser_native.json \
    --system MinerU-tableON

# (3) 선택: md_h3 재현이 필요하면 --chunker md_h3로 (1)-(2) 반복
```

**비교 기준(table-OFF, 논문 그리드):** RCPS 0.212 / Hit@1 0.197.
**정합 체크:** 상우의 E2E table-ON 재실행과 같은 predictions
(`results/kogovdoc/mineru_val_tableon/predictions/`, 294개)를 쓰는지 경로 확인 — 다른
사본이면 headline(35.1pp)의 운명 판정이 어긋난다.

**회신 양식:** `output/results/grid_MinerU-tableON_parser_native.json` +
per-domain 표 + (있으면) md_h3 동일 세트.

## Run 3 — [겸사, 1초] 4a 최종 봉인

```bash
wc -l /mnt/data1/work/wigtnOCR-v1/datasets/training/train.jsonl \
      /mnt/data1/work/wigtnOCR-v1/datasets/training/val.jsonl
# 기대: 2667 / 294. 다르면 그 값이 2,664/2,994 유령 숫자의 출처이므로 즉시 공유.
```
