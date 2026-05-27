# PLAN-05 — 논문 재구성 & 제출

> 상태: 🟡 draft v0.4 존재, 재구성 필요 (P1+P2) · Linear WIG-173~177 · 마감 6/16
> 현재 draft: `paper/draft/paper.md` (v0.4, RADP-DPO·통용지표 미반영)

## 목적
RADP-DPO(C3b)와 통용 지표 검증(PLAN-01/02/03)을 반영해 논문을 재구성하고, ACL LaTeX로 포팅해 OpenReview 제출.

## P1 — 본문 재구성

### §3 Method
- §3.2 **RADP-hidden** (기존 aux loss) — 유지, "간접적 surrogate"로 명확화
- §3.3 **RADP-DPO** (신규) — discrete 출력 retrieval-reward DPO. "RADP" 우산 아래 두 변형으로 제시

### §4 Experiments
- §4.4 **4-way 비교 표**: control(λ=0) / RADP-hidden(λ=0.1) / RADP-DPO / v1 + paired bootstrap CI (WIG-193 반영)
- **통용 지표 결과 추가** (PLAN-01): 표준 Hit@1/@5/nDCG/MRR
- **BC/CS shift** (PLAN-02): "BC flat/↓ + retrieval↑" 그림
- **경계 분해** (PLAN-03): split/absent로 향상 출처 규명

### Abstract / §1 / §5 (framing)
- 기존: "parser aux loss 한 가지 실패" (비대칭 결론)
- 변경: **"진단(C1) → 측정(C2) → 자연 해법 2종 시도; 출력 직접 학습(DPO)이 hidden의 2배로 우월"**
- 결과 시나리오별 (ROADMAP) 메시지 확정:
  - positive (게이트 통과 + 통용지표↑) / honest marginal / 진단 강화(split 지배)

### Self-check
- 모든 claim에 evidence (수치/그림/표)
- C1 cross-domain 부호 flip을 **abstract에도 정직하게** (현재 −0.35만 표기 → flip 명시)
- decision-A(hidden) negative의 범위 한정 (RADP 전체 부정 아님)

## P2 — 제출 인프라

| 작업 | Linear |
|---|---|
| ACL 2026 LaTeX 포팅 (`paper.md`→`main.tex`) + BibTeX | WIG-174 |
| Figure 1 (6-layer RAG pipeline schematic, TikZ) | WIG-175 |
| Figure 2 (noise-family curve, 이미 있음) 임베드 | — |
| 4-page 분량 체크 (over 시 §4.3 chunking grid → appendix) | WIG-176 |
| 공저자 review (손상우) + self-review 체크리스트 | WIG-176 |
| OpenReview 제출 + 자산 freeze (GitHub public, HF model/data) | WIG-177 |
| **저자 순서·명시 확정** (손상우 공저자) | — |

## 의존
- §4 핵심 표는 **P0(PLAN-01~04) 결과가 나와야** 채워짐 → P0 완결이 선행
- LaTeX 포팅·Figure는 본문 내용과 독립이라 병행 가능

## 타임라인
6/3~6/10 본문 재구성(P1) · 6/10~6/14 LaTeX·Figure·review(P2) · 6/15~16 제출
