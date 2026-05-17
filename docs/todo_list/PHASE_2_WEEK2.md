# Phase 2 — Week 2: RADP-B Training

> **기간**: 2026-05-25 ~ 2026-05-31
> **상태**: ⏳ PLANNED
> **목표**: RADP-B method 구현, 학습, v1 대비 개선 증명, InSeNT orthogonality 실험

## Critical Path

```
Contrastive loss head 구현 → 첫 학습 (λ=0.3) → vs v1 비교
                                ↓
                            λ sweep → InSeNT 결합 ablation
```

## Tasks

### 2.1 — Method B 구현

- [ ] **ms-swift 4.2 fork** 또는 custom trainer 작성
  - 기존 v1 학습 protocol 보존 (LoRA rank=8, alpha=32 등)
  - Contrastive loss head 추가 (separate forward pass)
- [ ] **BGE-M3 frozen embedding integration**
  - 학습 중 inference만 (gradient 끊김)
  - 메모리 효율: pre-compute embeddings 캐싱
- [ ] **Positive / Negative sampling 구현**
  - Positive: 같은 Q-A의 정답 chunks (다른 parsing temperature run)
  - Negative (in-batch): 다른 Q-A의 chunks
  - Hard negative: 같은 페이지 내 다른 chunk (semantic neighbor)
- [ ] **InfoNCE loss + λ coefficient 조합**
  - `L_total = L_parse + λ · L_contrast`
- [ ] **Config**: `configs/training/radp_b_base.yaml` 활성화 (placeholder → 실 동작)
- [ ] **Unit tests** (`tests/test_radp_b_loss.py`)

### 2.2 — 첫 학습 Run

- [ ] **Baseline run**: λ=0.3, 3 epochs, 기존 v1 hparam
  - GPU: 2× RTX PRO 6000, ~6h 예상
  - Output: `output/checkpoints/radp_b_lambda03/`
- [ ] **학습 로그 분석**
  - L_parse 곡선 vs v1 학습 곡선 비교 (회귀 여부)
  - L_contrast 곡선 (수렴하는가)
  - eval loss + RCPS on validation split
- [ ] **첫 평가**
  - RCPS, Hit@1, MRR@10, Text NED (v1 대비)
  - **목표 (H2)**: parsing 품질 ±0.02pp, retrieval Hit@1 +8pp

### 2.3 — λ Sweep Ablation

- [ ] λ ∈ {0.1, 0.3, 0.5, 1.0} × 3 epochs
  - 각 ~6h, 총 ~24 GPU-시간
  - Output: `output/checkpoints/radp_b_lambda{01,03,05,10}/`
- [ ] **Trade-off 분석**
  - λ 낮음 → contrastive 약함 → parsing 보존, retrieval gain 적음
  - λ 높음 → contrastive 강함 → parsing 회귀 risk, retrieval gain 큼
- [ ] **Optimal λ 결정** → Phase 3 paper writing에서 default로 사용
- [ ] **Figure 작성**: λ vs (parsing NED, retrieval RCPS) 2-axis plot

### 2.4 — Negative Sampling Ablation

- [ ] In-batch only
- [ ] In-batch + hard negative
- [ ] **Hard negative 효과 정량화**
- [ ] Mini-table: 어떤 sampling이 가장 좋은가

### 2.5 — InSeNT Orthogonality 결합 실험 (Critical — lit review 권장)

- [ ] **InSeNT-tuned BGE-M3** 준비
  - 공식 release 사용 또는 BGE-M3에 InSeNT 직접 학습 (~1일)
- [ ] **4-way comparison**
  | 조건 | Parser | Embedding |
  |------|--------|-----------|
  | A | v1 baseline | BGE-M3 (frozen) |
  | B | v1 baseline | InSeNT-tuned |
  | C | RADP-B | BGE-M3 (frozen) |
  | D | RADP-B | InSeNT-tuned |
- [ ] **H3 검증**: D > max(B, C) → orthogonality 증명
  - 목표: D 대비 single-layer 결과 +3pp 이상
- [ ] **결과 figure**: 4-way bar chart with error bars

### 2.6 — 학습 안정성 분석

- [ ] **Gradient norm 추적** — collapse 여부
- [ ] **Loss 분해**: L_parse, L_contrast 비율 시간 추적
- [ ] **Catastrophic forgetting check**: OmniDocBench 일부에서 v1 학습 데이터 외 평가
- [ ] **Issue 발견 시 대응**
  - LR scheduler 조정
  - Gradient clipping 강화
  - Warmup 늘림

### 2.7 — Documentation Update

- [ ] `docs/RADP_RESEARCH_PROPOSAL.md` v0.4 (Week 2 결과 반영)
- [ ] `docs/method/RADP_B_TRAINING_RECIPE.md` 신규 작성
  - Reproducibility 보장 (hparam, seed, env)
- [ ] Training log + plots을 `output/figures/`에 저장

## Deliverables

- [ ] `src/wigtnocr_radp/training/radp_b.py` (method 구현)
- [ ] `output/checkpoints/radp_b_*/` (4개 λ 변형)
- [ ] `output/results/week2_lambda_sweep.json`
- [ ] `output/results/week2_insent_orthogonality.json`
- [ ] `output/figures/figure2_lambda_tradeoff.pdf`
- [ ] `output/figures/figure3_insent_orthogonality.pdf`

## Blockers / Open Decisions

- [ ] **ms-swift 4.2 fork vs 새 trainer** — fork가 빠르지만 contrastive head 통합 복잡
- [ ] **InSeNT 학습 데이터** — 공식 release 사용 가능 여부 확인 필요 (Week 1 끝까지)
- [ ] **Pre-compute embedding 캐시 크기** — 학습 data 2,667p × 평균 5 chunks × 1024 dim = ~50MB OK

## Time Budget

| Task | 예상 시간 | GPU |
|------|:--------:|:---:|
| 2.1 Method 구현 | 2일 | — |
| 2.2 첫 학습 | 1일 | 6h |
| 2.3 λ sweep | 2일 | 24h |
| 2.4 Negative sampling | 0.5일 | 6h |
| 2.5 InSeNT 결합 | 2일 | 12h (4 runs) |
| 2.6 안정성 분석 | 0.5일 | — |
| 2.7 Docs | 0.5일 | — |
| **Total** | **~8.5 일** | ~48 GPU-시간 |

→ 1주 기한 빠듯. 2.4 (negative sampling)을 후순위로 두거나 Week 3로 이전 가능.

## Risk

- **RADP-B gain < 5pp**: Week 2 끝에 판단. 대응 옵션:
  1. λ 더 다양하게 (0.05, 0.7, 1.5) 추가 sweep
  2. Hard negative 비율 증가
  3. Contrastive loss를 InfoNCE → triplet으로 변경
  4. Fallback: Method를 minor contribution으로 격하, paper main은 RCPS metric으로 pivot
- **학습 collapse**: 즉시 LR/coefficient 조정. λ=0.1부터 시작.
