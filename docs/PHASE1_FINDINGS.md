# PHASE_1 (Week 1) Findings — Data, RCPS, Baseline Grids

> 작성일: 2026-05-21
> Week 1 (KoGovDoc-RAG 구축 · RCPS metric · baseline grid) 종합 결과.
> 상세 결정 기록: `docs/PHASE1_5_BASELINE_DECISIONS.md`.

## TL;DR

H1 (parsing 품질 ↔ retrieval 약한 상관, r < 0.5) **검증됨** — Pearson r ≈ 0.18~0.32,
EnterpriseDocBench의 r=0.14를 한국어 정부문서 도메인에서 재현. RCPS metric 구현 완료.
6-parser × 3-retriever, 4-chunker grid 완성.

---

## 1.1 Q-A 생성 — KoGovDoc-RAG

- KoGovDoc-Bench 294 validation 페이지에 대해 **663 Q-A** 생성 (GPT-5.4, PROMPT v3).
- frozen: `data/KoGovDoc-RAG/qa_pairs_v1.jsonl`. 향후 모든 평가의 고정 셋.

## 1.2 Q-A 검증

- 100개 stratified 샘플 (도메인·언어·type 비율 유지) 검증 — **94/100 accept**
  (PRD 목표 ≥85% 충족). LLM-assisted 검증 (human 아님 — caveat 기록).
- 주요 reject 패턴: multi-part 질문을 단일 span으로 답한 경우. (`qa_verification_results_v1.json`)

## 1.3 RCPS metric

- `src/wigtnocr_radp/evaluation/` 구현: chunkers, retrievers, `compute_rcps`.
- relevance 판정은 whitespace/markdown 무시 정규화 매칭 (`normalize_for_match`) —
  parser를 포맷이 아닌 내용으로 비교.

## 1.4 Baseline Grid — 6 parser × 3 retriever

retriever = bge-m3 + multilingual-e5-large + qwen3-emb-8b (RCPS는 평균). chunker = parser_native.

| Parser | RCPS | Hit@1 |
|--------|:----:|:----:|
| Qwen3-VL-30B (teacher) | 0.584 | 0.545 |
| WigtnOCR-2B (ours, v1) | 0.583 | 0.549 |
| Qwen3-VL-2B (base) | 0.532 | 0.500 |
| MinerU | 0.212 | 0.197 |
| PaddleOCR | 0.140 | 0.125 |
| Marker | 0.073 (38p) | 0.068 |

VLM 파서(0.53~0.58) ≫ 비-VLM 파서(0.07~0.21). MinerU/PaddleOCR/Marker는 한국어
정부문서에서 출력이 비거나 깨짐(모지바케) — 직접 검증 확인. 낮은 RCPS는 artifact가
아니라 실제 파싱 실패.

## 1.5 Chunking-strategy Grid — parser=v1

| Chunker | RCPS |
|---------|:----:|
| md_h3 | 0.593 |
| parser_native | 0.583 |
| lumberchunker | 0.557 |
| fixed500 | 0.535 |

마크다운 헤더 청킹이 최선 — 정부문서의 명시적 구조를 활용. **LumberChunker(LLM
서사 청킹)는 3위로 단순 규칙 청커를 못 이김** — 장편 서사용 설계라 표·양식 위주
정부문서엔 transfer 약함. MoC·Late Chunking은 cite-only (§PHASE1_5_BASELINE_DECISIONS).

## 1.6 EnterpriseDocBench r 재현 (H1 검증)

intrinsic chunk 품질(BC/CS) ↔ extrinsic retrieval(RCPS) Pearson r:

| 집합 | Pearson BC↔RCPS | H1 (r<0.5) |
|------|:---------------:|:----------:|
| 6 parser | +0.323 | ✅ |
| 5 parser (Marker 제외) | +0.175 | ✅ |

→ **We confirm the prior finding (r=0.14 in EnterpriseDocBench) in the Korean
government-document domain (r ≈ 0.18, 5-parser).** 인간 가독성 기반 파싱 품질
지표는 retrieval 성능을 약하게만 예측 — RADP의 핵심 동기(C1) 정량 확인.
(추가: MoC Boundary Clarity ↔ RCPS는 §3.2에서 별도 분석.)

---

## 산출물

- `data/KoGovDoc-RAG/qa_pairs_v1.jsonl` — frozen Q-A (663)
- `data/KoGovDoc-RAG/qa_verification_results_v1.json` — 100-QA 검증
- `src/wigtnocr_radp/evaluation/` — RCPS 구현
- `output/baselines/grid_v1_parser_native.{json,md}` — baseline grid
- `output/baselines/chunking_grid_v1.{json,md}` — chunking grid
- `output/baselines/correlation_v1.{json,md}` — H1 / EnterpriseDocBench r

## PHASE_1 미진 항목 (writing 단계로 이전)

- Figure 1 (BC vs RCPS scatter) — PHASE_3 figure 확정 시 생성.
- proposal v0.3 본문 갱신 — writing 단계.
