# ROADMAP — 앞으로 할 것

> 최종 갱신: 2026-05-28. 마감 **2026-06-16** (EMNLP 2026 Industry Track). 각 항목 상세는 `docs/plans/`.

---

## 임계경로 (한눈에)

```
[P0 증명 완결]  DPO 게이트 돌파 + 통용 지표 3종 검증   ← 지금 여기 (가장 급함)
      │
[P1 논문 반영]  C3 재구성(hidden+DPO 4-way) + framing 업데이트
      │
[P2 제출]       LaTeX 포팅 · Figure · BibTeX · 공저자 review · OpenReview
      │
   🎯 6/16 submit
```

---

## P0 — 증명 완결 (Critical, ~6/3 목표)

> 목표: RESEARCH_DIRECTION §5의 "완결 조건" 3종 + DPO 게이트(≥5pp, CI 하한>0).

| # | 작업 | 플랜 | 의존 | 담당 |
|---|---|---|---|---|
| P0-1 | **게이트 돌파** — DPO 4변형 +4pp 천장 → length bias 진단 → **SimPO pivot (진행 중)** | `PLAN-04` | — | 손상우 |
| P0-2 | **표준 retrieval 검증** — 풀코퍼스 vectordb, Hit@1/@5/@10·nDCG·MRR, v1 vs DPO | `PLAN-01` | DPO 출력 | — |
| P0-3 | **BC/CS 변화** — DPO 전후, "비-상승" 확인 | `PLAN-02` | DPO 출력 | — |
| P0-4 | **경계 분해** — covered/split/absent, v1 vs DPO (향상이 경계냐 내용이냐) | `PLAN-03` | v1 출력은 지금 가능 / DPO 출력 | — |

### RADP-DPO 진행 현황 (손상우, ~2026-05-28)

DPO 4변형 모두 **+4pp 천장**, 게이트(≥5pp) 미달:

| 변형 | Δ (md_h3) |
|---|:---:|
| v1 (BGE 단일, fresh, lr=1e-5) | **+4.12** ✅ best |
| v2 (3-retriever) | +1.99 |
| v3 (3-ret curriculum) | +0.22 |
| v4 (BGE 단일, warmstart) | +3.18 |

- **3-retriever rescoring은 역효과** (가설과 반대 — signal 희석. BGE-M3 단일이 한국어 정부문서에 가장 align). → 그 자체로 ablation 거리.
- 천장 원인 진단 = **length bias** (markdown 100~12,000자, DPO `log π = Σ log p` 가 긴 출력 편향).
- → **SimPO pivot** (length-normalized, reference-free, γ margin; β=2.0, γ=1.0). 진행 중, 결과 미기록.
- ⚠️ parser/RAG/VLM에 SimPO 첫 적용 — 직접 증거 없음.

**판정 기준 (이상적 결과)**: 표준 Hit@1 ↑ **and** BC/CS flat-or-↓ **and** split ↓ → "검색 친화 경계로 이동" 통용 지표 확증.

> ⚠️ 분기: P0-4(경계 분해)에서 `split`이 지배적이면 → "파서 천장은 청킹이 가른 답"이라 DPO를 더 돌려도 한계 → P0-1의 multi-round 투자 판단에 반영. **P0-4를 P0-1보다 먼저 또는 병행**할 가치.

---

## P1 — 논문 재구성 (~6/3 ~ 6/10)

| # | 작업 | 플랜 |
|---|---|---|
| P1-1 | §3.2 RADP-hidden + §3.3 RADP-DPO (RADP 우산 아래 두 변형) | `PLAN-05` |
| P1-2 | §4.4 **4-way 비교 표** (control / hidden / DPO / v1) + bootstrap CI | `PLAN-05` |
| P1-3 | §4에 통용 지표 결과(P0-2) + BC/CS shift(P0-3) + 경계 분해(P0-4) 반영 | `PLAN-05` |
| P1-4 | Abstract·§1·§5 framing: "한 가지 시도 실패" → "출력 직접 학습이 우월, 통용 지표로 확증" | `PLAN-05` |

---

## P2 — 제출 인프라 (~6/10 ~ 6/16)

| # | 작업 | Linear |
|---|---|---|
| P2-1 | ACL 2026 LaTeX 포팅 (`paper.md` → `main.tex`) + BibTeX 변환 | WIG-174 |
| P2-2 | Figure 1 (6-layer RAG schematic, TikZ) | WIG-175 |
| P2-3 | 공저자 review + self-review 체크리스트 | WIG-176 |
| P2-4 | OpenReview 제출 + 공개 자산 freeze (GitHub public, HF) | WIG-177 |
| P2-5 | **저자 순서·명시 확정** (손상우 공저자) | — |

---

## 타임라인

| 기간 | 집중 |
|---|---|
| ~6/3 | **P0 증명 완결** (게이트 + 통용 지표 3종) |
| 6/3 ~ 6/10 | P1 논문 재구성 |
| 6/10 ~ 6/14 | P2 LaTeX·Figure·review |
| 6/15 ~ 6/16 | 최종 제출 (buffer) |

---

## 결과 시나리오별 논문 방향

| 결과 | 논문 메시지 |
|---|---|
| 게이트 통과 + 통용 지표 ↑ + BC flat/↓ | **Positive**: "검색 친화 경계 파서 가능, 출력 직접 학습이 lever" (강한 Industry 기여) |
| +4pp marginal 유지 (통용 지표도 약하게 +) | **정직한 honest result**: "출력 학습이 hidden의 2배지만 통계적 확증엔 표본 한계" + deployment lesson |
| split 지배 (경계가 천장) | **진단 강화**: "disconnect의 상당부는 청킹이 답을 가름 → 파서만으론 한계" (C1 보강, next=청킹/embedding) |

세 경우 모두 발표 가치 있음 — negative/marginal도 정직하게 보고하는 게 이 논문의 정체성.

---

## 참고 — 미사용/보류

- InSeNT orthogonality(H3): RADP-hidden negative로 drop
- MoC chunker / Late Chunking: cite-only (`docs/PHASE1_5_BASELINE_DECISIONS.md`)
- ACL 2027 Main: RADP-DPO 본격 정식화 + cross-lingual/domain 일반화 (EMNLP 결과 후)
