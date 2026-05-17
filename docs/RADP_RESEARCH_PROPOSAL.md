# RADP: Retrieval-Aware Document Parsing via Chunk-Boundary Contrastive Learning

> **연구 기획서 v0.2 — EMNLP 2026 Industry Track 투고용**
>
> 작성일: 2026-05-17 (v0.1) → 2026-05-18 (v0.2, lit review 반영)
> 작성자: Harrison Kim (Braincrew AI)
> 대상: 공동 연구자 회람용
>
> **v0.2 변경점**:
> - Title에 부제목 추가 ("via Chunk-Boundary Contrastive Learning") — M-LongDoc과 naming 차별화
> - Framing 변경: "we discover" → "we confirm + first parser-layer solution"
> - **EMNLP 2026 scope = RADP-B만** (RADP-A는 ACL 2027 Main으로 이전)
> - 필수 baseline 추가: **InSeNT, MoC, LumberChunker**
> - 6-layer pipeline figure (related work positioning)
> - Lit review 결과 (`docs/literature_review/LITERATURE_REVIEW_v1.md`) 반영

---

## TL;DR

기존 document parser는 **인간 가독성** (BC, CS, TEDS, Edit Distance)을 최적화한다. 우리와 동시기 연구들 (OHRBench, EnterpriseDocBench, ConTEB)이 이미 보였듯, 이 지표들은 **downstream RAG retrieval 성능과 약하게 상관**한다 — EnterpriseDocBench의 r=0.14가 대표적.

선행 연구가 **진단**까지는 했지만 **training-time solution**은 비어있다. 모든 기존 방법은 chunker (Late Chunking, LumberChunker, MoC), embedding model (InSeNT, LMAR, BGE-M3), retriever (Reward-RAG), filter (ChunkRAG), 또는 reader (M-LongDoc, RPO) layer를 학습한다. **L1 parser 자체를 retrieval signal로 학습한 사례는 없다**.

본 연구는 다음을 제안한다:

1. **RCPS** (Retrieval-Conditional Parsing Score): retrieval 성능 기반 task-oriented 평가 지표 — MoC의 intrinsic Boundary Clarity와 보완
2. **RADP-B**: chunk-boundary contrastive auxiliary loss로 parsing VLM을 학습 — **L1 parser layer에 retrieval-aware tuning 적용 최초 사례**
3. **(future, ACL 2027) RADP-A**: retrieval-reward DPO 확장

기존 자산 (Qwen3-VL-2B WigtnOCR 모델, KoGovDoc-Bench)을 활용하여 4주 내 EMNLP Industry submission 가능.

**투고 전략**: EMNLP 2026 Industry Track (6/16) primary. ACL 2027 Main은 RADP-A 확장 + RCPS 일반화.

---

## 1. Background

### 1.1 사전 연구 — WigtnOCR v1

- Qwen3-VL-2B + LoRA 기반 한국 정부문서 파서
- OmniDocBench Table TEDS 1위 (0.649)
- 30B teacher 모델과 동등한 Text NED (0.288)
- KoGovDoc-Bench (294 검증 페이지) 공개
- HuggingFace 모델 + 데이터셋 공개
- 프로젝트 페이지: https://hyeongseob91.github.io/projects/wigtn-ocr.html

### 1.2 핵심 발견 — Parsing 품질과 Retrieval 성능의 비상관성

6개 parser × KoGovDoc Q-A 기반 retrieval 평가 결과:

| Parser | BC/CS 순위 | Retrieval (Hit@1) 순위 |
|--------|:---------:|:--------------------:|
| MinerU | 1위 | 5위 |
| WigtnOCR (ours) | 2위 | **1위** |
| ... | ... | ... |

→ **인간 가독성 지표가 RAG 성능을 보장하지 않는다**. 한국어 정부문서 도메인에서 이 패턴을 정량화하는 것이 본 연구의 motivation.

### 1.3 v2 (Gemma 4) 실험은 dead-end로 종결

`docs/V2_FINDINGS_REPORT.md` 참조. Gemma 4 E4B/E2B는 Qwen3-VL-2B 대비 Text NED 3~5배 나쁨. 따라서 v1을 base로 유지하고 **방법론적 contribution**으로 방향 전환.

### 1.4 Concurrent / Prior Work이 점유한 영역 (literature review v1 결과)

| 영역 | 선행 연구 | 우리 차별 |
|------|----------|----------|
| Parsing↔Retrieval r 정량화 | EnterpriseDocBench (r=0.14), OHRBench, When Good OCR Is Not Enough | 한국어 도메인 + 6 parser SOTA 비교 + **training solution까지** |
| Contrastive chunk embedding | InSeNT (BGE), LMAR | **Parser VLM을 학습** (그들은 embedding) — orthogonal하게 결합 가능 |
| Intrinsic chunking metric | MoC (Boundary Clarity/Stickiness) | RCPS = **extrinsic, task-grounded** — intrinsic과 보완 |
| Chunking method | Late Chunking, LumberChunker, Meta-Chunking | 모두 post-parsing text 입력; 우리는 **image input → retrieval-aligned chunks** end-to-end |
| Retrieval reward fine-tuning | RPO (generator DPO), Reward-RAG (retriever) | RADP-A (parser DPO) → **ACL 2027 Main**으로 이전, EMNLP scope에서 제외 |
| "Retrieval-Aware Tuning" naming | M-LongDoc (reader-side) | Parser-side 차별화 부제목으로 |

---

## 2. Research Question & Hypothesis

### Research Question

**Q1**: 한국어 정부문서 도메인에서도 parsing 품질과 retrieval 성능의 약한 상관관계가 재현되는가? (선행 연구가 영어/엔터프라이즈에서 보인 것이 한국어에서도 holds?)

**Q2**: Parsing VLM의 학습 단계에서 chunk boundary를 retrieval embedding 의미와 정렬시키면 (L1 layer 학습), 후속 RAG 단계 변경 없이도 retrieval 성능을 얼마나 개선할 수 있는가?

**Q3**: RADP-B는 embedding-layer 방법(InSeNT)과 **orthogonal**한가? 두 방법을 결합하면 추가 gain이 있는가?

### Hypothesis

**H1**: KoGovDoc-RAG에서 6 parser × 3 retriever grid의 parsing↔retrieval Pearson r은 < 0.5 (선행 연구의 r ≈ 0.14 와 같은 약한 상관관계 재현).

**H2**: RADP-B는 v1 baseline 대비 parsing 품질을 거의 손상시키지 않으면서 (Text NED 변화 ±0.02pp 이내) retrieval Hit@1을 ≥ 8pp 개선한다.

**H3**: RADP-B + InSeNT (parser layer + embedding layer)는 single-layer 적용 대비 추가 ≥ 3pp 개선을 제공한다. (orthogonality 증명)

---

## 3. Contributions

### C1. Diagnostic Confirmation (not discovery)
- 한국어 정부문서 + 학술 논문 도메인에서 parsing↔retrieval 약한 상관관계 정량화
- 선행 연구 (EnterpriseDocBench, OHRBench) 결과를 다른 언어·도메인에서 **independent confirmation**
- 6 parsers × 3 retrievers × 500~1000 Q-A grid

### C2. Metric — RCPS (Retrieval-Conditional Parsing Score)
- **Task-oriented, extrinsic** chunking quality metric
- MoC의 intrinsic Boundary Clarity와 **complementary**
- Retriever-agnostic property에 대한 statistical analysis
- Reference implementation 공개

```text
RCPS(parser P, Q-A set D, retrievers R, k_values K)
    = (1/|R||K|) × Σ_{r ∈ R, k ∈ K} MRR@k(r, chunks_P(D), questions_D)
```

### C3. Method — RADP-B
- **L1 parser layer에 retrieval-aware fine-tuning 적용 최초 사례**
- Chunk-boundary contrastive auxiliary loss를 v1 LoRA 학습에 추가
- 공개 모델 + 학습 코드 + 학습 데이터

### C4. Layer-Wise Positioning Analysis
- RAG pipeline 6-layer 도식 (figure 1)
- 각 layer를 학습한 prior work 매핑
- RADP가 L1을 처음 학습함을 시각화 + ablation 결합 실험

### 미포함 (ACL 2027 Main으로 이전)
- RADP-A (retrieval-reward DPO)
- RCPS의 generalization to multi-domain
- Multilingual generalization (영중일)

---

## 4. Methodology

### 4.1 RADP-B: Chunk-Boundary Contrastive Loss

#### Loss formulation

```
L_total = L_parse + λ · L_contrast

L_parse        : standard cross-entropy loss for VLM parsing (v1 unchanged)
L_contrast     : InfoNCE loss on chunk embeddings (BGE-M3 frozen)
λ              : balancing coefficient (search range: 0.1 ~ 1.0)
```

#### Positive / Negative pair 정의

- **Positive**: 같은 Q-A pair의 정답 span을 포함한 chunks (서로 다른 parsing run에서)
- **Negative (in-batch)**: 다른 Q-A pair의 chunks
- **Hard negative**: 같은 페이지 내 다른 chunk (semantic neighbors)

#### Embedding

- BGE-M3 (multilingual, 한·영·중 지원) 사용
- 학습 중 frozen — retrieval gradient만 contrastive signal로
- (확장 실험) InSeNT-tuned BGE-M3 사용 → RADP-B + InSeNT orthogonality 실험

#### 학습 설정 (v1 protocol 그대로)

- Base: Qwen3-VL-2B-Instruct
- LoRA: rank=8, alpha=32, target=all-linear
- Epochs: 3
- LR: 1e-4 (parse), 5e-5 (contrastive coefficient learnable)
- Batch / Grad accum: 1 × 4
- GPUs: 2× RTX PRO 6000

Config: `configs/training/radp_b_base.yaml`

### 4.2 (Future — ACL 2027) RADP-A: Retrieval-Reward DPO

EMNLP 2026 scope에서는 제외. Future work mention으로 1단락. 자세한 설계는 ACL 2027 plan으로.

---

## 5. Experimental Design

### 5.1 Datasets

| 이름 | 용도 | 크기 | 비고 |
|------|------|------|------|
| KoGovDoc (train) | RADP-B 학습 | 2,667p | 기존 v1 학습셋 |
| **KoGovDoc-RAG (new)** | RCPS 평가 | 294p + 500~1000 Q-A | **신규 구축, GPT-4o 자동 생성 + human verify** |
| ArXivPapers | 영문 generalization | 864p | 기존 v1 학습셋 |
| **OHRBench (subset)** | Cross-domain zero-shot eval | Manual + Law 일부 | **신규 — 1일 작업, generalization 증명** |

### 5.2 Q-A pair 구축 프로토콜

상세: `docs/qa_generation/SCHEMA.md`, `docs/qa_generation/PROMPT_v1.md`

1. **Generation**: GPT-4o (2024-08-06) structured outputs + 검증 schema
2. **Constraints**: 답은 specific span에 한정 (open-ended 금지)
3. **Distribution**: factoid 50% / procedural 30% / tabular 15% / figural 5%
4. **Difficulty**: easy 40% / medium 40% / hard 20%
5. **Quality filter**: teacher reasoning leak 페이지 자동 skip
6. **Verification**: 무작위 100개 직접 검증, 자동 generation 신뢰도 추정
7. **OHRBench alignment**: 그들 prompt pattern 참고하여 cross-domain 비교 가능성 확보

### 5.3 Baselines

#### Parser baselines (6개)
- WigtnOCR v1 (ours, base)
- MinerU 2.5
- Docling
- Marker
- Nougat
- MarkItDown

#### Retriever baselines (3개)
- BGE-M3 (multilingual SOTA)
- multilingual-e5-large
- jina-embeddings-v3

#### Chunking strategy baselines (강화 — lit review 반영)
- Fixed-size (500, 1000 chars)
- Markdown-aware (header-based)
- **LumberChunker** (LLM narrative boundary)
- **Meta-Chunking** (PPL-based boundary)
- **MoC** (MoE chunker — intrinsic metric proposer)
- **Late Chunking** (long-context embedding)
- **Ours: RADP-B**

#### Embedding-layer baselines (critical — InSeNT orthogonality 증명용)
- BGE-M3 (frozen)
- BGE-M3 + InSeNT-tuned
- BGE-M3 + LMAR-tuned

#### 결합 ablation (필수)
- RADP-B + BGE-M3 frozen
- RADP-B + InSeNT-tuned → **orthogonality H3 증명**

### 5.4 Evaluation Metrics

| Metric | 산식 | 용도 |
|--------|------|------|
| Hit@1, Hit@5, Hit@10 | retrieval 정확도 | retrieval 성능 |
| MRR@10 | mean reciprocal rank | ranking 품질 |
| nDCG@10 | normalized DCG | graded relevance |
| **RCPS** | mean(MRR@k for k, r in K×R) | 종합 task-oriented score |
| MoC Boundary Clarity / Stickiness | (그들 정의) | intrinsic comparison |
| BC, CS, TEDS | 기존 OmniDocBench metrics | parsing 품질 (회귀 방지) |
| Text NED | edit distance | 텍스트 정확도 |

### 5.5 Key Ablations

1. λ (contrastive coefficient): 0.1 / 0.3 / 0.5 / 1.0
2. Embedding model 선택 (BGE-M3 vs jina-v3 for contrastive signal)
3. Negative sampling 전략 (in-batch only vs + hard negative)
4. **RADP-B (parser layer) vs InSeNT (embedding layer) vs 결합** → orthogonality 증명
5. v1 baseline vs RADP final (Hit@1, MRR@10, RCPS)
6. **RCPS vs MoC Boundary Clarity correlation** — intrinsic의 한계 보이기
7. **OHRBench cross-domain zero-shot** — generalization
8. **(reproducibility)** EnterpriseDocBench의 r 값 재현 (수치 비교)

---

## 6. Timeline (lit review 반영하여 baseline 추가됨)

### Week 1 (5/18 ~ 5/24) — Foundation
- [x] **Literature review** — `docs/literature_review/LITERATURE_REVIEW_v1.md`
- [x] **Repo scaffolding** — configs/, src/wigtnocr_radp/, scripts/
- [x] **Q-A schema + prompt + generation script** — `docs/qa_generation/`
- [ ] **Q-A pair generation pipeline** + 1차 500개 생성
- [ ] **Q-A 100개 human verify** + 신뢰도 추정
- [ ] **RCPS metric** 구현 + reference implementation (`src/wigtnocr_radp/evaluation/`)
- [ ] **Baseline grid (1차)**: 6 parsers × 3 retrievers × KoGovDoc-RAG
- [ ] **MoC, LumberChunker, Late Chunking baseline 추가** ← lit review 결과

### Week 2 (5/25 ~ 5/31) — RADP-B + InSeNT
- [ ] Method B 구현 (ms-swift 4.2 위에 contrastive loss head 추가)
- [ ] 1차 학습 run (~6h GPU, λ=0.3)
- [ ] vs v1 baseline 비교 (RCPS, Hit@1, 회귀 여부)
- [ ] λ sweep ablation (3개 값, 각 ~6h)
- [ ] **InSeNT 결합 ablation** ← lit review 권장 (~1일 GPU squeeze)

### Week 3 (6/1 ~ 6/7) — Cross-domain + Writing
- [ ] **OHRBench (Manual, Law subset) zero-shot 평가** ← lit review 권장
- [ ] **MoC Boundary Clarity vs RCPS correlation 분석**
- [ ] Paper outline + figure 7개 확정 (포함: layer-positioning figure)
- [ ] First draft 시작
- [ ] **EnterpriseDocBench r 값 재현 수치 비교** ← lit review 권장

### Week 4 (6/8 ~ 6/14) — Write & Polish
- [ ] First draft 완성 (6/8 ~ 6/11)
- [ ] 부족한 실험 보충 (6/12 ~ 6/13)
- [ ] Internal review + format check (6/14)

### Buffer (6/15 ~ 6/16) — Emergency

**Submission**: 2026-06-16 EMNLP Industry Track

> RADP-A는 EMNLP scope에서 제외. ACL 2027 Main으로 확장 (Asia/Pacific 학회, ARR 차후 cycle).

---

## 7. Publication Strategy

### Shot 1 — EMNLP 2026 Industry Track (6/16)
- **타겟 contribution**: C1 (diagnostic confirmation) + C2 (RCPS) + C3 (RADP-B) + C4 (layer positioning)
- **추가 강조**: deployment lessons, KoGovDoc-Bench 자산
- **방어 포인트** (lit review 결과):
  - EnterpriseDocBench와의 차별: confirmation + solution
  - InSeNT와의 차별: layer + orthogonality 결합 실험
  - M-LongDoc과의 차별: parser layer + 부제목

### Shot 2 — ACL 2027 Main (Asia/Pacific, ARR 차후 cycle)
- **타겟 contribution**: RADP-A + RCPS multi-domain 일반화 + 이론 분석
- **추가 실험**:
  - 다중 도메인 (의료, 법률, 학술)
  - 다중 언어 (KO, EN, ZH, JA)
  - RADP-A retrieval reward DPO + 학습 안정성 분석
  - Theoretical analysis (RADP의 representation alignment 효과)

---

## 8. Team & Roles (TBD)

| Role | 담당 | 책임 |
|------|------|------|
| Lead / Method | Harrison | RADP method, 모델 학습, 전체 실험 설계 |
| Q-A construction | TBD | KoGovDoc-RAG 구축 (생성, 검증, 품질 관리) |
| Baseline implementation | TBD | LumberChunker / MoC / Late Chunking / InSeNT baseline 재현 |
| Evaluation infra | TBD | RCPS pipeline, baseline grid 자동화 |
| Writing | 공동 | abstract / intro / method / experiments / discussion 분담 |

> 공동 연구자와 협의하여 확정.

---

## 9. Risks & Mitigation (lit review 반영하여 갱신)

| Risk | 시점 | Likelihood | Impact | Mitigation |
|------|:---:|:---:|:---:|------|
| **C1이 scoop당함** | 이미 부분적으로 발생 | High | High | "confirm + first solution" framing으로 전환 (✅ v0.2 반영) |
| **InSeNT가 RADP-B를 위협** | Week 2 결과 시점 | Medium | High | Orthogonality 결합 실험 필수 — 추가 gain 보이면 방어 가능 |
| Q-A 자동 생성 품질 불량 | Week 1 | Medium | High | Page quality filter (✅ prompt 적용), human-in-the-loop 100개 검증 |
| RADP-B gain < 5pp | Week 2 | Low | Medium | hyperparameter sweep, hard negative 추가, fallback: ablation paper로 축소 |
| 학습 collapse | Week 2~3 | Low | Medium | LR scheduler 조정, gradient clipping 강화, λ 작게 시작 |
| Baseline 재현 실패 (MoC, InSeNT, LumberChunker) | Week 1~2 | Medium | Medium | 공식 release 우선 사용, 안 되면 paper 인용만 + 부분 재현 |
| 시간 부족 | Week 4 | Medium | High | ACL 2027 Main으로 timeline 미루는 옵션 살림 |

---

## 10. Required Resources

| 항목 | 비용 | 비고 |
|------|------|------|
| GPU | ~60 GPU-시간 (2× RTX PRO 6000) | 기존 보유 + InSeNT/MoC 재현 추가 |
| OpenAI API (Q-A generation) | ~$40 | 500~1000 Q-A 생성 + 학습 데이터 일부 |
| Storage | ~150 GB | 체크포인트 + 데이터 + baseline 모델 |
| Human verification | ~10~15 시간 | 100개 Q-A 검증 |

---

## 11. Open Decisions (회의 안건)

1. **공동 연구자 역할 분담** — §8의 4개 trach 중 어디
2. **InSeNT baseline 재현 우선순위** — 직접 학습 vs 그들 공개 모델 사용
3. **OHRBench zero-shot 도메인 선택** — Manual / Law / Newspaper / Magazine 중 1~2개
4. **RCPS의 mathematical sophistication 수준** — simple aggregate vs statistical property 정리
5. **Code & model release 정책** — Apache 2.0 + HuggingFace 그대로 (✅ v1 기조 유지)
6. **공저자 순서 및 affiliation 정리**

---

## 12. References (lit review 결과)

전체 14개 paper 요약: `docs/paper/PAPER-*.md`
종합 보고서: `docs/literature_review/LITERATURE_REVIEW_v1.md`

### Core citations (must cite)
- **OCR Hinders RAG / OHRBench** (Zhang et al., ICCV 2025) — OCR↔RAG mismatch 핵심 evidence
- **When Good OCR Is Not Enough** (2026-04) — concurrent confirmation
- **EnterpriseDocBench** (2026) — parsing→retrieval r=0.14
- **InSeNT / Context is Gold** (Le et al., 2025) — closest contrastive prior, MUST cite
- **MoC** (Liu et al., ACL 2025) — intrinsic metric proposer, RCPS와 비교
- **LumberChunker** (Duarte et al., EMNLP 2024 Findings)
- **Late Chunking** (Jina AI, 2024)
- **Meta-Chunking** (Zhao et al., 2024)
- **M-LongDoc** (EMNLP 2025) — naming clash, 차별화 명시
- **ColPali** (Faysse et al., ICLR 2025) — alternative paradigm
- **RPO** (2025) — closest to RADP-A (future work에서 인용)
- **OmniDocBench** (CVPR 2025) — parsing baseline
- **MinerU 2.5** (2025) — SOTA parsing
- **BGE-M3** (Chen et al., 2024) — embedding foundation
- **ChunkRAG** (2024) — post-retrieval filtering baseline

### Internal references
- WigtnOCR v1 project page: https://hyeongseob91.github.io/projects/wigtn-ocr.html
- KoGovDoc-Bench: https://huggingface.co/datasets/Wigtn/KoGovDoc-Bench
- v1 model: https://huggingface.co/Wigtn/Qwen3-VL-2B-WigtnOCR
- v2 findings: `docs/V2_FINDINGS_REPORT.md`

---

**문서 버전**: v0.2 (2026-05-18, lit review v1 반영)
**다음 업데이트**: Week 2 RADP-B 첫 학습 결과 + InSeNT 결합 ablation 결과 반영 v0.3
