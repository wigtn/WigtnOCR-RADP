# Phase 1 — Week 1: Data + RCPS Metric

> **기간**: 2026-05-18 ~ 2026-05-24
> **상태**: 🔄 IN PROGRESS
> **목표**: KoGovDoc-RAG 데이터 구축, RCPS metric 구현, baseline grid 1차 완성

## Critical Path

```
Q-A full generation → Human verify → Baseline grid → RCPS metric → Figure 1 (diagnostic)
                                          ↓
                                   MoC/LumberChunker/Late Chunking 추가
```

## Tasks

### 1.1 — Full Q-A Generation (294 validation pages)

- [ ] **Prompt v3 검토**: difficulty 분포 강제 (현재 easy 편중)
  - v2 prototype: easy 5, medium 1, hard 0
  - 목표: easy 40 / medium 40 / hard 20
- [ ] **Multi-page Q-A 추가**: 현재 0% → 목표 30%
  - 페이지 그룹화 (같은 `doc_id` 모아서 cross-page 질문)
- [ ] **Full run 실행** (`configs/qa_generation/default.yaml`)
  - 예상: 294p × ~$0.012 = **$3.5**, ~10분
  - 출력: `output/qa_pairs/default_gpt4o.jsonl`
- [ ] **자동 통계 분석**
  - Skip rate, valid Q-A 수, type/difficulty 분포
  - Per-domain (kogov vs arxiv) breakdown
- [ ] **`output/qa_pairs/default_gpt4o.jsonl` → 정식 데이터셋 archive**
  - `data/KoGovDoc-RAG/qa_pairs_v1.jsonl` 로 복사
  - 향후 모든 평가는 이 frozen set 사용

### 1.2 — Human Verification (100 sample Q-A)

- [ ] Random sample 100개 추출 (도메인·언어·type 비율 유지)
- [ ] Verification UI 또는 jupyter notebook 작성
  - 각 Q-A: question, answer_span, answer_chunk, source page link
  - 평가 axes: (1) question 자연스러움 (2) answer 정확성 (3) span 위치 정확
- [ ] 100개 검증 완료 후 metadata 업데이트
  - `metadata.human_verified = true`
  - `metadata.verification_notes`에 issue 기록
- [ ] **신뢰도 추정**: agreement rate, false positive rate
  - 목표: ≥ 85% accept rate
  - 그 이하면 prompt v4 필요

### 1.3 — RCPS Metric Implementation

- [ ] `src/wigtnocr_radp/evaluation/rcps.py` 구현
  - 인터페이스: `compute_rcps(qa_pairs, parser_outputs, retrievers, k_values) -> dict`
  - 출력: per-retriever-k Hit@k, MRR@k, nDCG@k + 종합 RCPS
- [ ] Retriever wrapper 통합
  - BGE-M3
  - multilingual-e5-large
  - jina-embeddings-v3
- [ ] Chunking strategy 추상화
  - `MarkdownHeaderChunker`
  - `FixedSizeChunker`
  - `ParserNativeChunker` (parser 출력 그대로)
- [ ] Unit tests (`tests/test_rcps.py`)
- [ ] **Sanity check**: WigtnOCR v1 자체 출력으로 RCPS 산출 → 합리적 range 확인

### 1.4 — Baseline Grid (1차)

- [ ] 6 parser 후보 결정 및 셋업
  - [ ] WigtnOCR v1 (ours, base)
  - [ ] MinerU 2.5
  - [ ] Docling
  - [ ] Marker
  - [ ] Nougat
  - [ ] MarkItDown
- [ ] 각 parser로 KoGovDoc-Bench 294p 파싱 출력 생성
  - `output/parser_outputs/{parser_name}/val_*.md`
- [ ] **Baseline grid run**: 6 × 3 retrievers × Q-A pairs
  - 표 형태로 결과 정리
  - **Figure 1 그리기**: parsing metric (BC/CS) vs RCPS scatter plot
  - 약한 상관관계 visual 증명 (Pearson r 산출)

### 1.5 — Additional Baselines (lit review 권장)

- [ ] **MoC** (ACL 2025) 재구현 또는 공식 release 사용
  - Boundary Clarity / Stickiness 메트릭 산출
  - vs RCPS correlation 분석 → intrinsic vs extrinsic 차이 보이기
- [ ] **LumberChunker** (EMNLP 2024 Findings)
  - 공식 release: GitHub 확인
  - KoGovDoc 페이지에 적용
- [ ] **Late Chunking** (Jina, 2024)
  - jina-embeddings-v3로 long-context pooling
- [ ] **Meta-Chunking** (선택 — 시간 되면)
- [ ] Chunking baseline grid에 통합 → Figure 2 (chunking strategy comparison)

### 1.6 — EnterpriseDocBench r 재현 (1일 작업)

- [ ] 그들 paper에서 r=0.14 산출 방법 확인
- [ ] 우리 KoGovDoc-RAG에서 동일 방법으로 r 산출
- [ ] **결과 표 작성**: "We confirm prior finding in Korean domain (r = 0.XX, vs r = 0.14 in [EnterpriseDocBench])"

### 1.7 — Documentation Update

- [ ] `docs/RADP_RESEARCH_PROPOSAL.md` v0.3 갱신 (Week 1 결과 반영)
- [ ] `docs/qa_generation/PROMPT_v2.md` 작성 (v1 → v2 변경점 명시)
- [ ] `docs/literature_review/LITERATURE_REVIEW_v1.md` → v1.1 (실제 baseline 재현 결과 반영)

## Deliverables

- [ ] `data/KoGovDoc-RAG/qa_pairs_v1.jsonl` (frozen Q-A set, 500~1000개)
- [ ] `src/wigtnocr_radp/evaluation/rcps.py` (RCPS reference implementation)
- [ ] `output/baselines/grid_v1.json` (6 parser × 3 retriever 결과)
- [ ] `output/figures/figure1_parsing_vs_rcps.pdf` (diagnostic finding)
- [ ] 100개 human-verified Q-A subset (paper의 evaluation 기반)

## Blockers / Open Decisions

- [ ] **MoC / LumberChunker 공식 release 사용 가능 여부** — 안 되면 paper 인용만
- [ ] **Q-A 학습용 추가 생성 여부** — 2,667 train pages × 1 Q-A = ~$32 추가 비용
- [ ] **OHRBench Manual/Law subset 다운로드** — Week 3 cross-domain 평가 준비

## Time Budget

| Task | 예상 시간 | 비고 |
|------|:--------:|------|
| 1.1 Full Q-A gen | 1일 (prompt iter + run) | $4 |
| 1.2 Human verify | 1일 (100개 × 5분) | Harrison or 공동연구자 |
| 1.3 RCPS impl | 1.5일 | retriever 통합 시간 포함 |
| 1.4 Baseline grid | 2일 | parser 셋업이 큰 변수 |
| 1.5 Add'l baselines | 1.5일 | release 활용 가정 |
| 1.6 EnterpriseDocBench | 0.5일 | 단일 metric 산출 |
| 1.7 Docs | 0.5일 | 갱신 |
| **Total** | **~8 일** | 1주 기한에 빠듯 |

→ 1.2 (human verify)와 1.4 (parser 셋업)을 공동 연구자에게 분담 권장.
