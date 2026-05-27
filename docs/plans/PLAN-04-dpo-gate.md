# PLAN-04 — 게이트 돌파 (DPO → SimPO)

> 상태: 🟢 진행 중 (P0-1) · Linear [WIG-194](https://linear.app/wigtn/issue/WIG-194) · 담당: 손상우
> 코드: `scripts/training/{generate_candidates,score_candidates,build_preference_pairs,train_radp_dpo}.py` + `simpo_trainer.py` (아직 GitHub push 전 — GPU 서버 로컬 + Linear 코멘트에만)

## 목적
RADP-DPO 1라운드의 **+4pp (md_h3, CI [−0.37, +8.35])** 를 **게이트 ≥5pp & 95% CI 하한 > 0**으로 끌어올린다. 또는 통계적으로 정직한 marginal로 확정.

## 진행 현황 (손상우, ~2026-05-28)

candidate 5,334 → scored 4,496 → preference 922 pairs → DPO. **4변형 모두 +4pp 천장:**

| 변형 | Δ (md_h3) | Δ (parser_native) |
|---|:---:|:---:|
| **v1** (BGE 단일, fresh, lr=1e-5) | **+4.12** ✅ best | +3.83 |
| v2 (3-retriever) | +1.99 | +1.70 |
| v3 (3-ret curriculum) | +0.22 | — |
| v4 (BGE 단일, warmstart, lr=5e-6) | +3.18 | — |

게이트(≥5pp) 미달, CI 하한 −0.37(v1).

### 닫힌 가설 / 발견
- ❌ **3-retriever rescoring** — "학습-평가 잣대 일치" 가설이 **역효과**(+4.12→+1.99). 3 retriever 의견 불일치 → preference 신호 희석. BGE-M3 단일이 우연히 한국어 정부문서에 가장 align. → **ablation 데이터**("signal matching naive하면 안 됨").
- ❌ **multi-round / curriculum / warmstart** — v3/v4 모두 v1 미달. multi-round plateau(early gain → exponential decay) 패턴.

### 현재 방향 — SimPO pivot
- **진단**: DPO 천장 = **length bias**. `log π = Σ log p(token)` 합산이 토큰 수에 비례 → markdown 100~12,000자(100배)에서 긴 출력 편향.
- **SimPO** (Meng et al. 2024): `r = (1/|y|)·Σ log π` (length-normalized) + reference-free + γ margin. β=2.0, γ=1.0. ~2시간(ref-free라 DPO보다 빠름).
- 예상: ≥+5pp ~50% / +4-5pp ~20% / 미달 ~30%. 어느 결과든 **DPO vs SimPO ablation이 contribution**.
- ⚠️ parser/RAG/VLM에 SimPO 첫 적용 — 직접 증거 없음. **결과 아직 Linear 미기록.**
- fallback: SimPO γ/β sweep → LD-DPO → ORPO → β-DPO.

## 판정 기준
- **통과**: 표준/RCPS에서 Δ ≥ 5pp **and** 95% CI 하한 > 0 → C3b positive
- **미달 유지**: "+4pp, hidden의 2배지만 표본 한계로 marginal" 정직 보고 (ROADMAP 시나리오 2)

## 의존 / 분기
- **PLAN-03(경계 분해)와 상호참조**: v1에서 `split` 지배면 파서 천장이 청킹이라 multi-round ROI 낮음 → multi-round 전에 PLAN-03 먼저 보는 게 합리적
- 게이트 결과가 PLAN-05(논문 framing)의 positive/marginal 분기를 결정

## 기술 메모 (재현용)
- base: v1 merged (`wigtnocr-2b-merged`), sampling temp{0.7,1.2} top_p0.95
- page-local RCPS scoring: distractor 100 (same-page 제외, per-page deterministic seed), universe 13,166 chunks 사전 인코딩
- DPO: β=0.1, lr=1e-5, 2 epoch, LoRA r=8 α=32 all-linear, **LoRA-toggle reference trick** (B init=0 → π_init=π_ref)
- eval: 4-way paired bootstrap N=1000
