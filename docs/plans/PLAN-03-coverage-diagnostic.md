# PLAN-03 — 경계 분해 (커버리지 진단: 향상이 경계냐 내용이냐)

> 상태: 🟡 코드 완료, 실행 전 (P0-4) · 의존: v1 출력은 지금 가능 / DPO 출력 필요 · 담당: TBD
> 상세 설계 근거: [`docs/STAGE4_PARSER_VS_CHUNKER_DIAGNOSTIC.md`](../STAGE4_PARSER_VS_CHUNKER_DIAGNOSTIC.md)

## 목적
RADP-DPO의 검색 향상(③)이 **경계 변화(②) 때문인지**, 아니면 단순히 **파서가 답 내용을 더 받아써서(받아쓰기 정확도)** 인지를 가른다. 사용자 가설의 핵심(②)이 분리 입증되는 지점.

## 왜 (배경)
DPO 모델이 "v1이 스킵한 표·내용을 포함"한다는 정성 근거는 **(B)내용 효과**(답이 비로소 조각에 들어감)를 시사할 수 있다. 이건 경계(청킹)와 무관. 향상이 (A)경계 때문인지 (B)내용 때문인지 안 갈리면 가설 ②가 미증명. (`docs/RESEARCH_DIRECTION.md §4` 구멍 2)

## 방법 — 답 위치 3분류
`src/wigtnocr_radp/evaluation/coverage.py` (구현·테스트 완료):

| 분류 | 정의 | 귀책 |
|---|---|---|
| **covered** | 답이 단일 청크에 통째로 있음 | 정상 |
| **split** | 답이 페이지엔 있는데 청크 경계가 가름 | **청커**(회수 가능) |
| **absent** | 답이 파서 출력에 아예 없음 | **파서**(회수 불가) |

실행: `uv run python scripts/evaluation/coverage_diagnostic.py` (검색기·GPU 불필요)

## 판정 기준 (핵심)
v1 → DPO 변화에서:
- **`split` ↓ 가 주도** → 경계가 답을 덜 자르게 됨 = **②경계 효과 = 가설 입증** ✅
- **`absent` ↓ 가 주도** → 답 내용을 더 받아씀 = (B)내용 효과 (경계 가설과 다른 얘기)

## 분기 영향 (ROADMAP 연결)
v1 단독 진단에서 **`split`이 지배적**이면 → "파서 천장이 청킹이 가른 답"이라, DPO를 더 돌려도(PLAN-04 multi-round) 한계 → **multi-round 투자 판단에 반영.** 그래서 **PLAN-04보다 먼저/병행** 권장.

## 입력 / 출력
- 입력: `output/parses_full/{v1, radp_dpo_eval}/`, `data/KoGovDoc-RAG/qa_pairs_v1.jsonl`
- 출력: `output/diagnostics/coverage_diagnostic_v1.{json,md}` (+ DPO 버전)

## 지금 당장 가능한 것
v1 출력만 있으면 (GPU 서버 데이터) **v1의 covered/split/absent 분포**를 바로 측정 가능 → "검색 천장 중 청킹 탓 비율"이 즉시 나옴. DPO 출력 나오면 v1과 diff.
