# Phase 3 — Week 3: Cross-domain + Writing

> **기간**: 2026-05-31 ~ 2026-06-07
> **상태**: ⏳ PLANNED
> **목표**: Generalization 실험, paper writing 시작, figures 7개 확정

## Tasks

### 3.1 — OHRBench Cross-domain Zero-shot Evaluation

- [ ] OHRBench Manual + Law subset 다운로드 + Q-A 추출
- [ ] RADP-B 모델로 zero-shot 파싱 + retrieval evaluation
- [ ] vs v1 baseline 비교
- [ ] **목표**: cross-domain에서도 RCPS 개선 보임 → generalization 증명
- [ ] **Figure 작성**: cross-domain bar chart

### 3.2 — RCPS vs MoC Boundary Clarity Correlation

- [ ] MoC의 intrinsic Boundary Clarity / Stickiness 계산
- [ ] 우리 RCPS와 Pearson r 산출
- [ ] **목표 (paper claim)**: intrinsic ≠ extrinsic → RCPS의 가치 입증
- [ ] **Figure 작성**: scatter plot + r 값

### 3.3 — Paper Outline + 7 Figures 확정

- [ ] **Section breakdown** (Industry track 4 page limit):
  1. Intro (0.5p)
  2. Related Work (0.5p)
  3. Method (RADP-B + RCPS) (1p)
  4. Experiments (1.5p)
  5. Discussion + Deployment Lessons (0.5p)
- [ ] **Figures 후보**:
  1. RAG 6-layer figure (related work positioning)
  2. Parsing metric vs RCPS scatter (Figure 1, diagnostic)
  3. λ trade-off plot (Phase 2 결과)
  4. InSeNT orthogonality 4-way bar (Phase 2)
  5. Baseline grid heatmap (6 parsers × 3 retrievers)
  6. Cross-domain (KoGov vs OHRBench Manual/Law) bar
  7. RCPS vs MoC Boundary Clarity scatter
- [ ] **Tables**:
  - Table 1: Main results (RCPS, Hit@1, MRR@10, NED)
  - Table 2: Ablation (λ sweep)
  - Table 3: InSeNT orthogonality (4-way)
  - Table 4: Cross-domain
  - (선택) Table 5: Per-parser breakdown

### 3.4 — First Draft Writing (Sections 1~3)

- [ ] **Abstract** (150 words)
- [ ] **Intro**
  - Motivation: parsing↔retrieval mismatch
  - "We confirm + first parser-layer solution"
  - 3-layer contribution summary
- [ ] **Related Work** — lit review 결과 재포장
  - OCR-RAG correlation 연구
  - Chunking optimization
  - Contrastive embedding
  - Retrieval reward
  - **6-layer figure로 positioning 시각화**
- [ ] **Method**
  - RADP-B loss formulation
  - Positive/Negative sampling
  - RCPS definition + property analysis

### 3.5 — EnterpriseDocBench Reproduction 마무리

- [ ] Phase 1에서 산출한 r 값을 paper에 인용
- [ ] "We confirm prior finding (r=0.14 in EnterpriseDocBench) with r=0.XX in KoGovDoc-RAG"

### 3.6 — Repo Polish (paper와 동기화)

- [ ] 학습 코드 정리 + reproducibility 보장
- [ ] HuggingFace 모델 업로드 준비 (`Wigtn/Qwen3-VL-2B-WigtnOCR-RADP-B`)
- [ ] KoGovDoc-RAG Q-A pair 데이터셋 업로드 준비

## Deliverables

- [ ] `output/results/cross_domain_ohrbench.json`
- [ ] `output/results/rcps_vs_moc_correlation.json`
- [ ] `output/figures/figure{4,5,6,7}.pdf` (cross-domain, RCPS-MoC, baseline grid, others)
- [ ] `paper/main.tex` first draft (Sections 1~3)
- [ ] `paper/figures/` 동기화

## Time Budget

| Task | 예상 시간 | GPU |
|------|:--------:|:---:|
| 3.1 OHRBench cross-domain | 1일 | 3h |
| 3.2 RCPS-MoC correlation | 0.5일 | — |
| 3.3 Outline + figures | 1일 | — |
| 3.4 Writing Sec 1-3 | 3일 | — |
| 3.5 EnterpriseDocBench | 0.5일 | — |
| 3.6 Repo polish | 0.5일 | — |
| **Total** | **~6.5 일** | ~3 GPU-시간 |

여유 있음. Phase 2가 늦어졌으면 buffer로 활용.
