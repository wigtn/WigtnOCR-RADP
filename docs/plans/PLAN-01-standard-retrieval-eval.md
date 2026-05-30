# PLAN-01 — 표준 Retrieval 지표 검증

> 상태: ❌ 미착수 (P0-2) · 의존: RADP-DPO 출력(PLAN-04) · 담당: TBD

## 목적
RADP-DPO의 +4pp가 **우리 자체 지표(RCPS) 안에서만**의 결과라는 한계를 해소. **통용되는 표준 retrieval 지표**로도 v1 대비 향상을 보인다.

## 왜 (배경)
RCPS는 page-local 채점 + 자체 distractor pool 100개로 설계됐다. reviewer 예상 반론: *"메트릭을 유리하게 설계한 것 아니냐."* → 전체 코퍼스 기반 표준 평가로 교차검증해야 주장이 자기참조를 벗어난다. (`docs/RESEARCH_DIRECTION.md §4` 구멍 1)

## 방법
1. 각 파서(v1 / RADP-hidden λ=0.1 / RADP-DPO)의 출력을 chunker(md_h3, parser_native)로 청킹
2. **전체 코퍼스를 통째로 인덱싱** (page-local distractor 아님) — FAISS in-memory 또는 동일 인메모리 방식
3. 663 Q-A로 표준 지표 산출: **Hit@1 / Hit@5 / Hit@10 / nDCG@10 / MRR@10**
4. 3-retriever(BGE-M3, e5-large, Qwen3-Emb) 각각 + 평균
5. **paired bootstrap 95% CI** (v1 vs DPO, control vs DPO)

## RCPS와의 차이 (핵심)
| | RCPS (기존) | 표준 평가 (이 플랜) |
|---|---|---|
| 검색 범위 | page-local + distractor 100 | **전체 코퍼스 (수천~만 chunk)** |
| 난이도 | 통제됨 | 실제 retrieval 난이도 |
| 지표 | MRR@{1,5,10} 평균 | Hit@1 분리 보고 포함 |

## 입력 / 출력
- 입력: `output/parses_full/{v1, radp_dpo_eval}/`, `data/KoGovDoc-RAG/qa_pairs_v1.jsonl`
- 출력: `output/eval/standard_retrieval_compare.{json,md}` (4-way × 5지표 × 3retriever)

## 판정 기준
- **DPO가 표준 Hit@1에서도 v1·control 대비 +** → §4 핵심 표
- 특히 **순수 Hit@1**이 오르는지 (RCPS의 MRR 평균에 묻히지 않고)

## 구현 노트
- `src/wigtnocr_radp/evaluation/retrievers.py`, `metrics.py` 재사용 (`hit_at_k`/`mrr_at_k`/`ndcg_at_k` 이미 있음)
- `compute_rcps`의 page-local 가정을 corpus-level 인덱싱으로 바꾼 변형 함수 추가
