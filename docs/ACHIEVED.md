# ACHIEVED — 이미 이룬 것

> 최종 갱신: 2026-05-27. 각 항목은 근거(문서/Linear/코드)와 함께. 수치는 모두 frozen 73p eval 또는 663 Q-A 기준.

---

## C1 — Parsing↔Retrieval Disconnect 진단 ✅

| 증거 | 수치 | 출처 |
|---|---|---|
| KoGov BC↔RCPS 상관 | Pearson **−0.81** (n=5, Marker 제외) | WIG-165, `output/baselines/moc_bc_correlation.md` |
| H1 (EnterpriseDocBench 재현) | r = **+0.18** (5-parser) — `r<0.5` 약상관 확인 | WIG-165 |
| OHR-Bench cross-domain (scalar) | 2-dom(Law+Manual) **−0.35** / 7-dom **+0.25** (data-mix flip, 정직 보고) | WIG-172 |
| **★ mechanism (cross-domain robust)** | MinerU noise family: BC 평탄(0.71~0.73) / RCPS **−51%** (0.50→0.24) | WIG-172, `paper/figures/fig_noise_family.pdf` |

→ "사람 친화 경계 ≠ 검색 친화 경계"를 한국어+영어, intrinsic 지표가 semantic 내용 품질을 못 본다는 **메커니즘**까지 입증.

---

## C2 — RCPS Metric ✅

- 구현: `src/wigtnocr_radp/evaluation/` (`rcps.py`, `chunkers.py`, `retrievers.py`, `metrics.py`)
- retriever-agnostic: BGE-M3 + multilingual-e5-large + Qwen3-Embedding-8B **3개 평균**
- relevance 판정: `normalize_for_match` (whitespace/markdown 무시 → 포맷 아닌 내용으로 비교)

| Grid | 결과 | 출처 |
|---|---|---|
| 6 parser × 3 retriever | WigtnOCR-v1 **0.583** ≈ Qwen3-VL-30B teacher 0.584 ≫ MinerU 0.21 / Paddle 0.14 / Marker 0.07 | WIG-163 |
| 4 chunker (parser=v1) | md_h3 **0.593** > parser_native 0.583 > LumberChunker 0.557 > fixed500 0.535 | WIG-164 |
| OHR-Bench cross-domain RCPS | gt 0.640 / MinerU 0.595 / Qwen2.5-VL 0.545 (영어서도 변별) | WIG-171 |

---

## C3a — RADP-hidden (contrastive aux loss) ✅ negative

`L_total = L_parse + λ·L_contrast` (InfoNCE, BGE-M3 frozen, decision-A: hidden→projection head).

| λ | RCPS (parser_native) | vs v1 | parseSim |
|---|:---:|:---:|:---:|
| 0.0 (control) | 0.6557 | −0.1pp | 0.872 |
| **0.1** | **0.6788** | **+2.2pp** | 0.874 |
| 0.3 | 0.6694 | +1.3pp | 0.862 |
| 0.5 | 0.6442 | −1.3pp | 0.851 |

- 게이트 5pp / H2 목표 8pp **미달**. λ↑ → RCPS·parseSim **단조 하락** (under-tuning 아님)
- bootstrap 95% CI: 모든 Δ-vs-control이 **0 포함** (유의하지 않음) — WIG-193
- full-scale(2,667p) 재학습으로 data-scale confound 제거 후에도 동일 — WIG-170
- 출처: `docs/WEEK2_FINDINGS.md`, WIG-167~170

→ "파서 hidden state에 aux loss 거는 건 잘못된 레버"를 엄밀히 보임 (정직한 negative).

---

## C3b — RADP-DPO (retrieval-reward DPO) 🟡 marginal (1라운드)

discrete 출력을 RCPS로 채점 → preference pair → DPO. (Linear WIG-194, 코드 아직 push 전)

| 단계 | 산출 |
|---|---|
| candidate 생성 | v1 merged, temp{0.7,1.2} → **5,334** |
| page-local RCPS 채점 | distractor 100(same-page 제외) → **4,496 scored** |
| preference pair | gap≥5pp → **922 pairs** (53%는 tie=짧은 페이지 saturate) |
| DPO 학습 | β=0.1, 2 epoch, LoRA r=8, **48분** |

| System | md_h3 RCPS | Δ vs control [95% CI] |
|---|:---:|:---:|
| control (λ=0) | 0.6551 | — |
| RADP-hidden (λ=0.1) | 0.6664 | +1.13 [−2.53, +4.95] |
| **RADP-DPO** | **0.6963** | **+4.12 [−0.37, +8.35]** |

→ **DPO가 hidden aux의 약 2배.** 정성적으로 v1이 스킵한 표·내용 포함. 단 CI 하한 −0.37 (유의 직전), 게이트 미달. **자체 지표(RCPS) 한정** — 통용 지표 검증은 미완(→ ROADMAP).

---

## 인프라 / 자산 ✅

| 자산 | 내용 |
|---|---|
| KoGovDoc-RAG eval | 663 Q-A (294p, GPT-5.4, 94/100 검증, **frozen**) — WIG-161 |
| Train Q-A | 2,667p × 6,164 Q-A (GPT-5.4) — WIG-169 |
| RCPS / BC / chunker / retriever | `src/wigtnocr_radp/evaluation/` |
| **커버리지 진단** (이번 추가) | `coverage.py` + `coverage_diagnostic.py` + 테스트 (covered/split/absent) |
| 버그 수정 (이번) | `FixedSizeChunker` overlap 무한루프 |
| RADP-DPO 파이프라인 | `generate_candidates / score_candidates / build_preference_pairs / train_radp_dpo` (WIG-194, push 전) |
| 체크포인트 | RADP-hidden λ{0,0.1,0.3,0.5}, RADP-DPO round1 (GPU 서버) |

---

## 가설 판정 요약

| 가설 | 판정 |
|---|---|
| H1 (parsing↔retrieval 약상관) | ✅ 확인 (−0.81 / +0.18) |
| H2 (RADP-hidden ≥8pp) | ❌ 반증 (+1~3pp) |
| H3 (InSeNT orthogonality) | ⊘ H2 실패로 drop |
| (신규) RADP-DPO 우월 | 🟡 시사 (+4pp, 통용 지표 검증 필요) |
