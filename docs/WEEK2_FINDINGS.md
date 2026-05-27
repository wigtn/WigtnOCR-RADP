# Week 2 Findings — RADP-B is a Negative Result

> **상태**: PHASE_2 (RADP-B training) 종료 후 보고서
> **작성일**: 2026-05-20 (최초) · **2026-05-21 갱신** — PHASE_1을 깨끗하게
> 재완성한 뒤(3-retriever 평가 기준 통일) λ sweep 전체를 **재평가**한 수치로 교체.
> **TL;DR**: Parsing VLM에 chunk-boundary contrastive auxiliary loss를 더하는
> RADP-B 방법은 **retrieval을 개선하지 못한다**. λ ∈ {0, 0.1, 0.3, 0.5, 1.0}
> sweep 결과 RCPS gain은 최선(λ=0.1)이어도 +1.8pp (목표 5pp 미달)이고,
> λ가 커지면 RCPS·parsing 품질이 **단조 하락**한다 — under-tuning이 아니라
> objective 자체가 counterproductive. 게다가 contrastive를 **전혀 안 쓴** v1
> 레퍼런스가 모든 RADP-B 체크포인트를 이긴다. proposal §9 / PHASE_2 리스크에
> 명시된 fallback대로, RADP-B는 정직한 negative result로 보고하고 논문 메인을
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
평가 = **3-retriever (bge-m3 + multilingual-e5-large + qwen3-emb-8b) RCPS 평균**
— PHASE_1 baseline/chunking grid와 동일 기준 (2026-05-21 재평가).

### RCPS (md_h3 chunker — RADP-B가 contrastive로 학습한 chunker)

| λ | RCPS | Hit@1 | MRR@10 | parse↔GT 유사도 |
|---|:----:|:----:|:----:|:----:|
| 0.0 (control) | 0.6368 | 0.6056 | 0.6539 | 0.8608 |
| **0.1** | **0.6544** | **0.6271** | **0.6702** | 0.8431 |
| 0.3 | 0.6340 | 0.6040 | 0.6504 | 0.8459 |
| 0.5 | 0.6148 | 0.5908 | 0.6281 | 0.8191 |
| 1.0 | 0.5686 | 0.5380 | 0.5856 | 0.8214 |
| v1 (ref, 2,667p) | **0.6724** | **0.6386** | **0.6905** | 0.7890 |

### RCPS (parser_native chunker)

| λ | RCPS | Hit@1 |
|---|:----:|:----:|
| 0.0 | 0.6124 | 0.5776 |
| 0.1 | 0.6463 | 0.6122 |
| 0.3 | 0.6305 | 0.5990 |
| 0.5 | 0.6028 | 0.5743 |
| 1.0 | 0.5927 | 0.5611 |
| v1 (ref, 2,667p) | **0.6569** | **0.6254** |

**게이트 판정 (RCPS gain ≥ 5pp 필요)**: best λ=0.1 → λ=0 대비 **+1.8pp** (md_h3),
**+3.4pp** (parser_native). 두 chunker 모두 5pp 문턱 미달. **FAIL.**

원자료: `output/results/week2_lambda_sweep.json` (3-retriever 재평가본).

---

## 3. 왜 실패했나

1. **단조 하락**. λ를 키울수록 RCPS도 parsing 충실도(parse↔GT)도 떨어진다
   (RCPS 0.654→0.569, 유사도 0.843→0.821). 효과가 0 근처에서 흔들리는 게
   아니라 **음의 방향으로 단조** — contrastive gradient가 파서에 도달은 하되,
   파서를 retrieval에 **나쁜** 쪽으로 민다. λ=0.1이라는 가장 약한 nudge만
   살짝 +이고, 그보다 키우면 전부 손해.

2. **objective mismatch**. decision-A 정식화는 *전체 markdown*의 pooled hidden을
   *하나의 답 chunk* 임베딩에 정렬시킨다. 이는 페이지 전체를 충실히 표현해야 하는
   parsing CE와 경쟁하며, 실제 chunk 경계를 retrieval-friendly하게 바꾸는 것과는
   거리가 먼 간접 신호다.

3. **λ=0.1의 +1.8~3.4pp는 게이트 미달**. 두 chunker 모두 부호는 +지만 5pp
   문턱(PHASE_2 리스크가 정한 floor)에 못 미친다. 풀스케일 투자를 정당화할
   크기가 아니다.

4. **결정적: contrastive를 안 쓴 v1 레퍼런스가 모든 RADP-B 체크포인트를 이긴다**.
   v1(2,667p, contrastive 없음) RCPS = 0.672(md_h3) / 0.657(parser_native) >
   최고 RADP-B 0.654 / 0.646. contrastive aux loss는 *도움이 안 될 뿐 아니라*,
   같은 파서를 그냥 더 많은 데이터로 parsing만 학습시킨 것보다 못하다. 또한
   λ 체크포인트들은 v1보다 teacher 포맷에 더 가까운데(parseSim 0.82~0.86 >
   v1 0.79) retrieval은 더 나쁘다 — RADP-B 내부에서도 C1(파싱 품질 ≠ retrieval)
   재확인.

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
