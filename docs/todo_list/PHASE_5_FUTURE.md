# Phase 5 — Future: ACL 2027 Main Extension

> **기간**: 2026-06-17 ~ 2027 ARR Cycle (TBD)
> **상태**: 🔮 FUTURE
> **목표**: RADP-A 확장 + RCPS multi-domain 일반화로 ACL 2027 Main 투고

## Why this phase

EMNLP 2026 Industry Track으로 RADP-B + RCPS의 가치를 확보한 후, ACL 2027 Main에서:
- **방법론적 깊이**: RADP-A (retrieval-reward DPO) 추가
- **일반화**: 다국어 (KO + EN + ZH + JA) + 다도메인 (의료, 법률, 학술)
- **이론적 분석**: RADP의 representation alignment 메커니즘

ACL 2027은 Asia/Pacific 확정 (구체적 위치 미정). ARR cycle을 잘 타면 commitment 가능.

## Strategic Considerations

- **ARR cycle timing**: 2027 ACL commitment 가능 cycle 확인 필요
  - Oct 2026 ARR → ACL 2027 가능?
  - Dec 2026 ARR → ACL 2027 가능?
- **EMNLP 2026 결과 시점**: review 받으면 정확한 방향성 보강
- **공동 연구자**: 학생/박사과정 합류 가능성

## Tasks (high-level)

### 5.1 — RADP-A (Retrieval-Reward DPO)

- [ ] Method 설계 정밀화
  - Preference pair 구축 (2 parsing candidates → retrieval reward → DPO)
  - DPO vs GRPO 비교
- [ ] 학습 안정성 분석 (parser DPO는 unexplored territory)
- [ ] RADP-B → RADP-A 순차 학습 vs from-scratch 비교

### 5.2 — Multi-Domain Generalization

- [ ] OHRBench 전 도메인 (Manual, Law, Newspaper, Magazine, Textbook, Academic)
- [ ] 의료 문서 (가능하면 — KOMUChem, MedicalDocBench 등)
- [ ] 법률 문서 (가능하면 — KoLawDoc 등)

### 5.3 — Multilingual Extension

- [ ] 영어 도메인: arXiv extended, EnterpriseDocBench
- [ ] 중국어: ChineseGovDoc (구축 또는 외부 인용)
- [ ] 일본어: 가능하면

### 5.4 — Theoretical Analysis

- [ ] RADP의 representation alignment 효과 정량화
  - chunk embedding space에서 정답 chunk vs 다른 chunks 거리 분석
  - Pre-training vs post-RADP의 representation drift
- [ ] **Theorem candidate**: "RADP-B는 cosine similarity 기반 retrieval의 expected ranking을 개선한다"
- [ ] Empirical evidence + 수식 정리

### 5.5 — RCPS Sophistication

- [ ] Retriever-agnostic property에 대한 formal proof or strong empirical evidence
- [ ] Confidence interval, statistical significance test 추가
- [ ] RCPS variants: RCPS@1 (Hit-based), RCPS@k (graded), RCPS-DCG (nDCG-weighted)

### 5.6 — Comparison with Concurrent Work

- [ ] EMNLP 2026 ~ ACL 2027 사이에 publish된 새 paper들 lit review v2
- [ ] 우리 RADP의 unique angle 재정의 (시장 변화에 따라)

## Deliverables (ACL 2027 paper)

- [ ] 8-page Main track paper
- [ ] Long-form theory section (1.5p)
- [ ] Extensive ablations (3p)
- [ ] Open-source benchmark (multi-domain RAG eval)

## Branching Decision Tree

```
EMNLP 2026 결과:
├─ Accept → Phase 5 progress as planned
│   └─ Reviewer 의견 반영해 ACL 2027 강화
├─ Reject (minor) → resubmit ACL 2027 with revisions
│   └─ Phase 5 더 빠르게 추진
└─ Reject (major) → 방향 재고
    └─ RCPS metric만 따로 short paper로 publish 옵션
```

## Long-term Vision

이 연구의 궁극적 목표:
- **Retrieval-aware document parsing이 표준이 되도록**
- 산업계 (Notion, Google Workspace, MS Office)의 OCR pipeline에 RADP 통합
- 학계에서 "L1 parser layer optimization" 이 retrieval research의 정식 sub-field로 자리잡기
