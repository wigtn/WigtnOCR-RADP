# Phase 4 — Week 4: Polish & Submit

> **기간**: 2026-06-08 ~ 2026-06-14 (Buffer: 6/15~6/16)
> **상태**: ⏳ PLANNED
> **목표**: First draft 완성, 부족한 실험 보충, format check, submit

## Critical Path

```
Sections 4-5 writing → Internal review → Format polish → Submit (6/15~6/16)
```

## Tasks

### 4.1 — Paper Writing (Sections 4~5)

- [ ] **Section 4 — Experiments**
  - Datasets (KoGovDoc-RAG + OHRBench subset)
  - Baselines (6 parsers, 3 retrievers, 4+ chunking strategies)
  - Metrics (RCPS, Hit@1, MRR@10, NED, BC/CS)
  - Main results table
  - Ablations (λ, negative sampling, InSeNT orthogonality)
- [ ] **Section 5 — Discussion + Deployment Lessons**
  - Lessons learned (subset of V2 L1-L13)
  - Limitations
  - Future work (RADP-A → ACL 2027 명시)
- [ ] **Conclusion** (5~10 lines)

### 4.2 — Abstract + Intro 최종

- [ ] Abstract 다듬기 (150 word limit)
- [ ] Intro의 contribution 정리 3-bullet (C1 + C2 + C3)
- [ ] "First parser-layer retrieval-aware fine-tuning" claim 강조

### 4.3 — 부족한 실험 보충

- [ ] Phase 1~3 결과 review → 빠진 실험 식별
- [ ] **추가 가능 후보**:
  - [ ] λ 더 fine-grained sweep (0.05, 0.7)
  - [ ] BGE-M3 외 jina-v3로 contrastive signal 변경 실험
  - [ ] Multi-page Q-A 별도 성능 분석
  - [ ] Per-language (ko vs en) 성능 분석
- [ ] **시간 부족 시**: appendix로 미루기

### 4.4 — Figure Polish

- [ ] 모든 figure consistency (color, font, scale)
- [ ] Vector format (PDF) 변환
- [ ] Caption 명확성 review
- [ ] Print readability (인쇄 시 가독성)

### 4.5 — Internal Review

- [ ] 공동 연구자 review (24h 안에)
- [ ] Self-review:
  - [ ] Claims 모두 evidence backing 있는가
  - [ ] Limitation을 honest하게 적었는가
  - [ ] Notation consistency
  - [ ] Reference 누락 없는가 (lit review 14편 모두 cite?)
- [ ] Spell check + grammar (Grammarly or DeepL Write)

### 4.6 — EMNLP Industry Track Format Check

- [ ] **Page limit**: 8 pages (4 main + 4 reference/appendix) 확인
- [ ] **Anonymization**: blind review 가능한가
  - 우리 case는 Industry Track으로 author 명시 가능할 수도 — CFP 재확인
- [ ] **Template**: 공식 LaTeX template 사용
- [ ] **Submission portal** (OpenReview) 준비
  - 메타데이터 (제목, 저자, abstract, 키워드)
  - 보조 자료 (code, dataset URL)

### 4.7 — Submission

- [ ] **D-1 (6/14)**: Final draft + all figures locked
- [ ] **D-Day (6/15 또는 6/16)**: OpenReview submit
- [ ] **Confirmation 수신**: 학회 시스템에서 submission ID
- [ ] **Sanity**: PDF가 submission portal에서 정상 렌더링되는가
- [ ] **공개 자산 freeze**:
  - HuggingFace 모델 업로드 (`Wigtn/Qwen3-VL-2B-WigtnOCR-RADP-B`)
  - KoGovDoc-RAG 데이터셋 업로드
  - GitHub repo public (paper submission 직후)

### 4.8 — Post-submission

- [ ] **세션 기록**: lessons learned, 다음 paper을 위한 process 개선점
- [ ] **공동 연구자에게 감사 노트**
- [ ] **휴식 1일** — Phase 5 (ACL 2027) 시작 전

## Deliverables

- [ ] `paper/main.pdf` (final submission)
- [ ] `paper/main.tex` + figures + .bib
- [ ] OpenReview submission ID
- [ ] Public repo (GitHub, with paper-ready commit)
- [ ] HuggingFace artifacts (model + dataset)

## Time Budget

| Task | 예상 시간 |
|------|:--------:|
| 4.1 Sections 4-5 | 2일 |
| 4.2 Abstract polish | 0.5일 |
| 4.3 Extra experiments | 1일 |
| 4.4 Figure polish | 0.5일 |
| 4.5 Internal review | 1일 |
| 4.6 Format check | 0.5일 |
| 4.7 Submission | 0.5일 |
| 4.8 Post | 0.5일 (선택) |
| **Total** | **~6.5 일** |

## Submission Day Checklist (6/15 ~ 6/16)

- [ ] PDF preview confirmed
- [ ] Author list / affiliation 최종 확인
- [ ] Acknowledgments 작성 (funding, 공동 연구자)
- [ ] Code anonymized (GitHub url을 OpenReview에는 anonymous로?)
- [ ] **Submit before deadline**
- [ ] 확인 이메일 저장

## Emergency Plan

만약 Phase 3가 늦어져서 첫 draft가 6/12까지 안 끝나면:
1. Scope 축소: cross-domain (3.1) 또는 RCPS-MoC (3.2) 중 하나 drop
2. λ sweep을 3개 값으로 축소 (full 4개 → core 3개)
3. Section 5 (Discussion) 1단락으로 축소
4. 최후의 수단: **ACL 2027 Main으로 timeline 이전** (이미 plan에 포함된 안전망)
