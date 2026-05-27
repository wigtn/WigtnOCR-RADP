# PLAN-04 — RADP-DPO 게이트 돌파

> 상태: 🟢 진행 중 (P0-1) · Linear [WIG-194](https://linear.app/wigtn/issue/WIG-194) · 담당: 손상우
> 코드: `scripts/training/{generate_candidates,score_candidates,build_preference_pairs,train_radp_dpo}.py` (아직 GitHub push 전)

## 목적
RADP-DPO 1라운드의 **+4pp (md_h3, CI [−0.37, +8.35])** 를 **게이트 ≥5pp & 95% CI 하한 > 0**으로 끌어올린다. 또는 통계적으로 정직한 marginal로 확정.

## 현재 상태 (1라운드 완료, 2026-05-27 01:31)
- candidate 5,334 → scored 4,496 → preference 922 pairs (gap≥5pp) → DPO 48분
- 결과: md_h3 +4.12 [−0.37, +8.35], parser_native +3.83 [−0.45, +7.95] — hidden aux의 2배, 게이트 직전

## 방법 (단계)
1. **3-retriever rescoring** (~30분) — 현 학습 신호는 BGE-M3 **단일**, 최종 평가는 3-retriever **평균** → mismatch. preference pair를 3-retriever로 재채점해 학습 타겟을 평가와 일치 → 신호 또렷해질 여지
2. **DPO 재학습 + 재평가** (~1h)
3. **(미달 시) multi-round DPO** (~3-4h) — 1라운드 모델로 다시 candidate 생성 → 재학습 반복. vLLM으로 추론 가속. effect size 계단식 상승 기대

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
