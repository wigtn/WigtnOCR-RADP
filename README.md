# WigtnOCR-RADP

**Retrieval-Aware Document Parsing via Chunk-Boundary Contrastive Learning**

> 🎯 **EMNLP 2026 Industry Track 투고 준비 중** (마감 2026-06-16)
> 📦 Builds on [WigtnOCR v1](https://hyeongseob91.github.io/projects/wigtn-ocr.html) + [KoGovDoc-Bench](https://huggingface.co/datasets/Wigtn/KoGovDoc-Bench)
> 📊 진행 상황: [`docs/todo_list/`](docs/todo_list/) 참조

---

## 📌 한 줄 요약

기존 document parser는 "사람이 읽기 좋은" markdown을 만들도록 학습된다. 하지만 RAG 파이프라인에서 진짜 중요한 건 **검색이 잘 되는 chunk**다. 이 두 목표는 같지 않다 — 그래서 우리는 **parser 자체를 retrieval 신호로 학습**한다.

---

## 💡 Why this project — 동기와 배경

### 문제: Parsing 품질 ≠ Retrieval 성능

WigtnOCR v1 개발 중 발견한 역설:

> **OmniDocBench BC/CS 메트릭 1위를 한 parser(MinerU)가 retrieval Hit@1에서는 5위였다.**

즉 "잘 파싱된" 문서가 RAG의 검색 단계를 잘 통과하지 못한다. 같은 시기 OHRBench (ICCV 2025), EnterpriseDocBench (2026), When Good OCR Is Not Enough (2026)도 비슷한 발견을 영어·중국어 도메인에서 정량화했다 — EnterpriseDocBench는 parsing↔retrieval Pearson r = 0.14를 보고했다.

### 갭: Training-time solution이 없다

선행 연구는 모두 **진단**에 머물거나, RAG 파이프라인의 **다른 layer**를 학습한다:

| Layer | Component | 학습한 선행 연구 |
|-------|-----------|----------------|
| L1: Parsing (image→text) | VLM parser | **(비어 있음)** ← 우리가 채움 |
| L2: Chunking | Chunker | LumberChunker, MoC, Meta-Chunking, Late Chunking |
| L3: Embedding | Encoder | InSeNT, LMAR, BGE-M3 |
| L4: Retrieval | Retriever | Reward-RAG |
| L5: Filtering | Filter | ChunkRAG |
| L6: Generation | Reader | M-LongDoc, RPO, RAG-Reward |

**L1 parser layer에 retrieval-aware fine-tuning을 적용한 사례는 없다**. 이게 우리 RADP의 정확한 niche.

---

## 🔬 What we propose

### 3-Layer Contribution

#### C1. Diagnostic Confirmation
한국어 정부문서 + 학술 논문 도메인에서 parsing↔retrieval 약한 상관관계를 정량화. 영어/엔터프라이즈에서 보인 선행 결과의 **independent confirmation** (6 parsers × 3 retrievers × 500~1000 Q-A grid).

#### C2. RCPS (Retrieval-Conditional Parsing Score)
Task-oriented extrinsic chunking quality metric:

```
RCPS(parser P, Q-A set D, retrievers R, k_values K)
    = (1/|R||K|) × Σ_{r ∈ R, k ∈ K} MRR@k(r, chunks_P(D), questions_D)
```

MoC (ACL 2025)의 intrinsic Boundary Clarity와 **complementary**.

#### C3. RADP-B (the Method)
v1 LoRA 학습에 chunk-boundary contrastive auxiliary loss를 추가:

```
L_total = L_parse + λ · L_contrast
```

- **Positive**: 같은 Q-A의 정답 span을 포함한 chunks (다른 parsing run)
- **Negative**: in-batch + hard (same page) negatives
- **Embedding**: BGE-M3 (frozen)

**L1 parser layer를 retrieval signal로 fine-tune한 최초 사례.**

> RADP-A (retrieval-reward DPO)는 **ACL 2027 Main**으로 이전 — timeline + scooping risk 완화

### Research Hypotheses

| ID | 가설 |
|:-:|------|
| H1 | KoGovDoc-RAG의 parsing↔retrieval Pearson r < 0.5 (선행 r ≈ 0.14 재현) |
| H2 | RADP-B는 parsing 품질 ±0.02pp 변화 이내에서 retrieval Hit@1 ≥ 8pp 개선 |
| H3 | RADP-B + InSeNT는 single-layer 대비 추가 ≥ 3pp 개선 (orthogonality 증명) |

---

## 📂 Repository Structure

```
.
├── configs/                  # 모든 실험 설정 (YAML)
│   ├── data/                 # 데이터셋 paths
│   ├── qa_generation/        # GPT-4o Q-A 생성 변형
│   ├── training/             # RADP-B 학습 (Week 2)
│   └── evaluation/           # RCPS pipeline (Week 1)
│
├── src/wigtnocr_radp/        # 임포트 가능한 라이브러리
│   ├── qa_generation/        # Q-A 생성 generator + schema/validator
│   ├── evaluation/           # RCPS metric (Week 1)
│   └── utils/                # config 로더, language heuristics
│
├── scripts/                  # CLI entry points (얇은 wrapper)
│   └── qa_generation/
│       └── generate_qa.py
│
├── data/                     # KoGovDoc-Bench (gitignored, 별도 다운로드)
│
├── docs/                     # 연구 문서
│   ├── RADP_RESEARCH_PROPOSAL.md     # 기획서 v0.2
│   ├── V2_FINDINGS_REPORT.md          # Gemma 4 backbone 실험 (negative result)
│   ├── paper/                          # 14개 paper 요약 (lit review)
│   ├── literature_review/              # 종합 보고서 (scooping analysis)
│   ├── qa_generation/                  # Q-A schema, prompt, 샘플
│   └── todo_list/                      # 진행 상황 트래킹 ← 현재 진행도 빠르게 확인
│
├── output/                   # 학습/생성/평가 출력 (gitignored)
├── tests/                    # 단위 테스트
└── pyproject.toml            # uv 프로젝트
```

---

## 🚀 Quick Start

### 1) 환경 셋업

```bash
# 사전 요구사항: Python 3.11+, uv, hf CLI

# 의존성 설치
uv sync

# 환경변수 (.env 생성)
cp .env.example .env
# 에디터로 .env 열고 OPENAI_API_KEY 입력
```

### 2) KoGovDoc-Bench 다운로드 (109 MB, public)

```bash
hf download Wigtn/KoGovDoc-Bench --repo-type dataset --local-dir data/KoGovDoc-Bench
```

### 3) Q-A pair 생성 prototype

```bash
# 5 다양 페이지 sanity check
uv run python scripts/qa_generation/generate_qa.py \
    --config configs/qa_generation/diverse_5.yaml

# Dry-run (API 호출 없음)
uv run python scripts/qa_generation/generate_qa.py \
    --config configs/qa_generation/diverse_5.yaml --dry-run

# Full 294 validation set (~$3.5, ~10분)
uv run python scripts/qa_generation/generate_qa.py \
    --config configs/qa_generation/default.yaml
```

출력: `output/qa_pairs/*.jsonl`, `output/qa_pairs/*.log`

---

## ⚙️ Config 시스템

모든 실험 설정값은 YAML로 분리되어 `configs/` 안에 있다. 코드는 절대 hardcoded value를 갖지 않고, 모두 config에서 읽어온다.

| Config | 용도 | 상태 |
|--------|------|:----:|
| `configs/data/kogovdoc_bench.yaml` | 데이터셋 paths + 메타데이터 | ✅ |
| `configs/qa_generation/default.yaml` | GPT-4o 전체 생성 (294p) | ✅ |
| `configs/qa_generation/gpt4o_mini.yaml` | 저비용 변형 (cost 1/10) | ✅ |
| `configs/qa_generation/diverse_5.yaml` | 5-page prototype | ✅ |
| `configs/training/radp_b_base.yaml` | RADP-B 학습 hparams | ⏳ Week 2 |
| `configs/evaluation/rcps_default.yaml` | RCPS pipeline | ⏳ Week 1 |

**새 실험 추가**: 기존 yaml을 복사하고 변경할 부분만 수정.

---

## 📚 Documentation

| 문서 | 내용 |
|------|------|
| [`docs/RADP_RESEARCH_PROPOSAL.md`](docs/RADP_RESEARCH_PROPOSAL.md) | 연구 기획서 v0.2 (방법론, 실험, 일정, risk) |
| [`docs/V2_FINDINGS_REPORT.md`](docs/V2_FINDINGS_REPORT.md) | Gemma 4 backbone 실험 (negative result, v1 선택 근거) |
| [`docs/literature_review/LITERATURE_REVIEW_v1.md`](docs/literature_review/LITERATURE_REVIEW_v1.md) | 14편 paper 종합 분석 (scooping risk + novelty positioning) |
| [`docs/paper/`](docs/paper/) | 개별 paper 요약 14개 |
| [`docs/qa_generation/`](docs/qa_generation/) | Q-A schema, prompt 설계, 샘플 출력 |
| [`docs/todo_list/`](docs/todo_list/) | **Phase × Task 진행 상황** (체크박스 트래킹) |

---

## 🗓️ Roadmap

```
[Phase 0] Foundation (5/17~)             ✅ DONE
    Literature review, repo scaffolding, Q-A prototype

[Phase 1] Week 1 (5/18 ~ 5/24)           🔄 IN PROGRESS
    Full Q-A generation, RCPS metric, baseline grid

[Phase 2] Week 2 (5/25 ~ 5/31)           ⏳ NEXT
    RADP-B implementation, λ sweep, InSeNT ablation

[Phase 3] Week 3 (6/1 ~ 6/7)             ⏳
    Cross-domain (OHRBench), writing begin

[Phase 4] Week 4 (6/8 ~ 6/14)            ⏳
    First draft, polish, submit

[Submit] 2026-06-16                       🎯
    EMNLP 2026 Industry Track

[Future] ACL 2027 Main (Asia/Pacific)    🔮
    RADP-A extension, RCPS multi-domain generalization
```

상세는 [`docs/todo_list/`](docs/todo_list/) 참조.

---

## 🤝 공동 연구자 — 시작 가이드

이 프로젝트에 합류했다면:

1. **읽기 순서**
   - `README.md` (이 문서) — 큰 그림
   - `docs/RADP_RESEARCH_PROPOSAL.md` — 연구 기획 (필수)
   - `docs/literature_review/LITERATURE_REVIEW_v1.md` — 현재 학계 위치
   - `docs/V2_FINDINGS_REPORT.md` — backbone 선택 배경
   - `docs/todo_list/` — 어디까지 됐는지

2. **환경 셋업**
   - 위 Quick Start 따라 진행
   - OpenAI API key 필요 (Q-A 생성용)
   - GPU 없어도 Phase 1까지는 진행 가능 (학습은 Phase 2부터)

3. **역할 분담** (`docs/RADP_RESEARCH_PROPOSAL.md §8`)
   - Method / 학습 (Harrison)
   - Q-A construction
   - Baseline 재구현 (MoC, LumberChunker, InSeNT 등)
   - Evaluation infra (RCPS pipeline)
   - Writing 분담

4. **첫 미팅 안건** (`docs/RADP_RESEARCH_PROPOSAL.md §11`)
   - 역할 분담 확정
   - InSeNT baseline 재현 우선순위
   - OHRBench cross-domain 도메인 선택
   - RCPS의 mathematical sophistication 수준
   - 공저자 순서

---

## 🔗 Related Artifacts

- **v1 model** (HF): https://huggingface.co/Wigtn/Qwen3-VL-2B-WigtnOCR
- **v1 benchmark**: https://huggingface.co/datasets/Wigtn/KoGovDoc-Bench
- **v1 project page**: https://hyeongseob91.github.io/projects/wigtn-ocr.html

---

## 📄 License

Apache 2.0 — same as upstream WigtnOCR v1.

## ✍️ Citation

BibTeX는 EMNLP 2026 채택 후 추가.

## 📮 Contact

- Harrison Kim — harry@brain-crew.com
- Braincrew AI · SoundMind Inc. (B2B2G RAG service)
