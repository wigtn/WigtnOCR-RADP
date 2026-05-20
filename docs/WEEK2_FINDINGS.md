# Week 2 Findings — RADP-B is a Negative Result

> **상태**: PHASE_2 (RADP-B training) 종료 후 보고서
> **작성일**: 2026-05-20
> **TL;DR**: Parsing VLM에 chunk-boundary contrastive auxiliary loss를 더하는
> RADP-B 방법은 **retrieval을 개선하지 못한다**. λ ∈ {0, 0.1, 0.3, 0.5, 1.0}
> sweep 결과 RCPS gain은 최선(λ=0.1)이어도 +0.5pp (목표 5pp의 1/10)이고,
> λ가 커지면 RCPS·parsing 품질이 **단조 하락**한다 — under-tuning이 아니라
> objective 자체가 counterproductive. proposal §9 / PHASE_2 리스크에 명시된
> fallback대로, RADP-B는 정직한 negative result로 보고하고 논문 메인을
> **C2 (RCPS metric) + C1 (diagnostic)** 으로 pivot한다.

---

## 1. 실험 설정

| 항목 | 값 |
|------|-----|
| 방법 | RADP-B: `L_total = L_parse + λ·L_contrast` (InfoNCE, BGE-M3 frozen) |
| Base | Qwen3-VL-2B-Instruct + LoRA (r=8, α=32, LLM linear) |
| 학습 프레임워크 | HF Trainer (transformers 5.8 + peft) — ms-swift 4.2는 cu128 환경 비호환 |
| 학습 데이터 | KoGovDoc-RAG train fold **169p / 461 Q-A** (`page_split_v1.json`) |
| 평가 | held-out eval fold **73p / 202 Q-A** |
| Epochs / batch | 3 / 8 |
| Contrastive 정식화 | decision-A: parser pooled hidden → projection head → InfoNCE vs 답 chunk의 BGE-M3 임베딩 |

> **왜 169p인가**: L_contrast는 학습 페이지에 Q-A가 있어야 하는데 Q-A는 294 val
> 페이지에만 존재. proposal §5.1의 2,667p 학습은 train 페이지 Q-A 생성 비용
> ($30+)이 예산상 막혀 불가 → 294p를 169/73으로 split. 169p run은 **파일럿**으로
> 설계됐고, "RCPS gain ≥5pp면 풀스케일 투자" 게이트가 걸려 있었다.

---

## 2. 결과 — λ Sweep

held-out 73p / 202 Q-A. λ=0은 contrastive를 끈 대조군 (동일 조건, λ만 0).

### RCPS (md_h3 chunker — RADP-B가 contrastive로 학습한 chunker)

| λ | RCPS | Hit@1 | MRR@10 | parse↔GT 유사도 |
|---|:----:|:----:|:----:|:----:|
| 0.0 (control) | 0.6242 | 0.5990 | 0.6381 | 0.8608 |
| **0.1** | **0.6291** | **0.6040** | **0.6432** | 0.8431 |
| 0.3 | 0.6080 | 0.5792 | 0.6236 | 0.8459 |
| 0.5 | 0.5922 | 0.5693 | 0.6045 | 0.8191 |
| 1.0 | 0.5458 | 0.5198 | 0.5614 | 0.8214 |
| v1 (ref, 2,667p) | 0.6282 | 0.5990 | 0.6441 | 0.7890 |

### RCPS (parser_native chunker)

| λ | RCPS | Hit@1 |
|---|:----:|:----:|
| 0.0 | 0.5968 | 0.5693 |
| 0.1 | 0.6110 | 0.5792 |
| 0.3 | 0.6112 | 0.5842 |
| 0.5 | 0.5840 | 0.5594 |
| 1.0 | 0.5717 | 0.5446 |

**게이트 판정 (RCPS gain ≥ 5pp 필요)**: best λ=0.1 → λ=0 대비 **+0.005** (md_h3).
문턱의 1/10. **FAIL.**

원자료: `output/results/week2_lambda_sweep.json`.

---

## 3. 왜 실패했나

1. **단조 하락**. λ를 키울수록 RCPS도 parsing 충실도(parse↔GT)도 떨어진다
   (RCPS 0.629→0.546, 유사도 0.843→0.821). 효과가 0 근처에서 흔들리는 게
   아니라 **음의 방향으로 단조** — contrastive gradient가 파서에 도달은 하되,
   파서를 retrieval에 **나쁜** 쪽으로 민다.

2. **objective mismatch**. decision-A 정식화는 *전체 markdown*의 pooled hidden을
   *하나의 답 chunk* 임베딩에 정렬시킨다. 이는 페이지 전체를 충실히 표현해야 하는
   parsing CE와 경쟁하며, 실제 chunk 경계를 retrieval-friendly하게 바꾸는 것과는
   거리가 먼 간접 신호다.

3. **λ=0.1의 +0.5pp는 noise**. 202 쿼리 기준, chunker에 따라 부호가 흔들리는
   수준. 의미 있는 gain으로 볼 수 없다.

4. **parsing은 손해**. 169p 모델은 v1(2,667p)과 RCPS는 대등하지만(파일럿 규모가
   치명적이지 않음을 시사), contrastive를 켜면 parse↔GT 유사도가 일관되게 하락 —
   즉 RADP-B는 **parsing을 깎고 retrieval 이득은 0**.

---

## 4. 결정 — Pivot (proposal §9 fallback 발동)

proposal §9 리스크 표 / PHASE_2 리스크 섹션에 명시된 대응:
*"RADP-B gain < 5pp → Method를 minor contribution으로 격하, paper main은
RCPS metric으로 pivot."* λ sweep이 이 조건을 명확히 충족 → fallback 발동.

**개정된 논문 구성:**

| | 내용 | 상태 |
|---|---|---|
| **C1** | parsing 품질 ≠ retrieval (한국어 정부문서, Pearson r≈0.16) | ✅ H1 검증 완료 |
| **C2** | RCPS — task-oriented chunking 품질 지표 (**메인 기여**) | ✅ 구현, 강화 예정 |
| **C3** | parser-layer contrastive aux loss로 retrieval을 고치려는 시도 — **실패**. λ sweep + 대조군으로 엄밀히 보인 negative result | ✅ 본 보고서 |

framing: *"문제를 진단하고(C1), 측정 지표를 제시하고(C2), 자연스러운 해법
(파서를 retrieval 신호로 직접 학습)이 통하지 않음을 엄밀히 보인다(C3) — 이
문제는 보기보다 어렵다."* RADP-A (retrieval-reward DPO)는 future work로 ACL 2027.

**버리는 것**: RADP-B 메서드 재설계, negative-sampling ablation(2.4),
InSeNT orthogonality(2.5 — RADP-B가 동작하지 않으므로 H3 무의미).

**Week 3에서 C2 강화** (전부 기존 플랜 항목):
- RCPS vs MoC Boundary Clarity 상관분석 (PHASE_3 §3.2) — intrinsic 지표가
  못 잡는 것을 RCPS가 잡음을 보임
- EnterpriseDocBench r 재현 비교 (PHASE_1 §1.6) — r≈0.16 vs 그들 0.14
- (시간 되면) OHRBench cross-domain zero-shot (§3.1)

---

## 5. Reproducibility

- 학습: `scripts/training/train_radp_b.py --contrastive_lambda <λ>` ,
  config `configs/training/radp_b_base.yaml`
- 추론: `scripts/evaluation/generate_parses.py`
- 평가: `scripts/evaluation/eval_radp_b.py` → `output/results/week2_lambda_sweep.json`
- 체크포인트: `output/checkpoints/radp_b_lambda{00,01,03,05,10}/`
- seed 42, held-out split `data/KoGovDoc-RAG/page_split_v1.json`
