# WigtnOCR-RADP

**Retrieval-Aware Document Parsing — 사람이 읽기 좋은 파싱 ≠ 검색이 잘 되는 파싱**

> 🎯 EMNLP 2026 Industry Track 투고 준비 (마감 2026-06-16)
> 📦 Builds on [WigtnOCR v1](https://huggingface.co/Wigtn/Qwen3-VL-2B-WigtnOCR) + [KoGovDoc-Bench](https://huggingface.co/datasets/Wigtn/KoGovDoc-Bench)
> 🧭 연구 정의·가설은 [`docs/RESEARCH_DIRECTION.md`](docs/RESEARCH_DIRECTION.md), 진행은 [`docs/ACHIEVED.md`](docs/ACHIEVED.md) / [`docs/ROADMAP.md`](docs/ROADMAP.md)

---

## 📌 한 줄 요약

문서 파서는 보통 **사람이 보기 좋은 markdown**을 만들도록 학습된다. 하지만 RAG에서 진짜 중요한 건 **검색이 잘 되는 chunk**다. 우리는 이 둘이 다름을 진단하고(C1), 그 차이를 재는 지표를 만들고(C2), **파서를 검색 신호로 직접 학습**해 그 차이를 좁힐 수 있는지 검증한다(C3).

---

## 💡 동기 — Parsing 품질 ≠ Retrieval 성능

WigtnOCR v1 개발 중 발견한 역설:

> **MoC Boundary Clarity(BC) 1위 파서(MinerU)가 retrieval에서는 꼴찌.** KoGov 5-parser에서 BC↔RCPS Pearson = **−0.81** (예쁜 경계일수록 검색이 더 안 됨).

같은 방향을 OHR-Bench(ICCV 2025), EnterpriseDocBench(2026, r≈0.14), When Good OCR Is Not Enough(2026)가 영어·엔터프라이즈에서 독립적으로 보고했다. **선행 연구는 진단에 머물거나 파이프라인의 다른 layer(chunking~generation)를 학습한다. L1 파서 layer를 retrieval 신호로 학습한 사례는 없다 — 그게 우리 niche.**

---

## 🔬 핵심 가설 — 증명해야 할 인과 사슬

```
① 파서를 검색 신호로 학습하면  →  ② 청크 경계가 "사람 친화"에서 "검색 친화"로 이동하고
                              →  ③ 그 경계의 조각들이 검색(Hit@/MRR)에서 더 높은 점수를 낸다
```

핵심은 **③이 ②"때문에"** 일어났음을, 그리고 **우리 자체 지표뿐 아니라 기존 통용 지표로도** 보이는 것이다. (자세한 정의·현재 위치는 [`docs/RESEARCH_DIRECTION.md`](docs/RESEARCH_DIRECTION.md))

---

## 🧱 3-Layer Contribution (현재 상태)

| | 기여 | 상태 |
|---|---|:---:|
| **C1** | Parsing↔Retrieval disconnect 진단 (BC↔RCPS −0.81 + OHR-Bench cross-domain mechanism) | ✅ |
| **C2** | **RCPS** (Retrieval-Conditional Parsing Score) — retriever-agnostic, task-oriented 지표 | ✅ |
| **C3** | 파서를 retrieval 신호로 학습 — 두 방식 | 🔄 |
| C3a | **RADP-hidden**: hidden-state contrastive aux loss (`L_parse + λ·L_contrast`) | ✅ negative (+1~3pp) |
| C3b | **RADP-DPO**: discrete output을 retrieval reward로 DPO | 🟡 +4pp (marginal, 검증 진행) |

RCPS:
```
RCPS(parser P, Q-A set D, retrievers R, k_values K) = (1/|R||K|) Σ_{r∈R, k∈K} MRR@k(r, chunks_P(D), questions_D)
```

> ⚠️ **현재 +4pp는 우리 자체 지표(RCPS) 안에서의 결과다.** "정말 검색 친화 파서다"가 되려면 **표준 retrieval 지표 + BC/CS 비-상승 + 경계 변화 분해**가 필요하다 → [`docs/ROADMAP.md`](docs/ROADMAP.md)

---

## 📊 지금 어디까지 왔나 (2026-05-27)

- ✅ **C1 진단 / C2 지표 / 6-parser·4-chunker baseline** — 모두 확보
- ✅ **RADP-hidden** 풀스케일 negative 확정 (게이트 미달, 정직한 보고)
- 🟡 **RADP-DPO** 1라운드 완료 — RCPS +4pp (hidden의 2배), 단 95% CI가 0을 살짝 포함 (marginal)
- ❌ **미검증 (다음 핵심)**: 표준 retrieval 지표 / DPO 후 BC/CS 변화 / 검색 향상이 경계냐 내용이냐
- 📦 **인프라**: KoGovDoc-RAG 663 Q-A(frozen), RCPS·BC 구현, 커버리지 진단(이번 추가), DPO 파이프라인(Linear WIG-194)

상세: [`docs/ACHIEVED.md`](docs/ACHIEVED.md) · 할 일: [`docs/ROADMAP.md`](docs/ROADMAP.md)

---

## 📂 Repository Structure

```
.
├── configs/                  # 실험 설정 (YAML)
├── src/wigtnocr_radp/
│   ├── qa_generation/        # Q-A 생성
│   ├── evaluation/           # RCPS, chunkers, retrievers, coverage 진단, BC
│   └── training/             # RADP-hidden(contrastive) / RADP-DPO
├── scripts/
│   ├── qa_generation/
│   ├── training/             # train_radp_b, (WIG-194) generate/score/build/train_dpo
│   └── evaluation/           # baseline_grid, chunking_grid, coverage_diagnostic, bootstrap
├── data/KoGovDoc-RAG/        # 663 Q-A (frozen, gitignored)
├── docs/                     # ↓ 아래 Documentation
├── output/                   # 결과·체크포인트 (gitignored, GPU 서버)
└── tests/
```

---

## 📚 Documentation (읽기 순서)

| 문서 | 내용 |
|------|------|
| [`docs/RESEARCH_DIRECTION.md`](docs/RESEARCH_DIRECTION.md) | **연구 정의 — 가설, 증명 사슬, 현재 위치, 완결 조건** ★ |
| [`docs/ACHIEVED.md`](docs/ACHIEVED.md) | 이미 이룬 것 (C1/C2/C3 + 인프라, 근거 링크) |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | 앞으로 할 것 (우선순위·타임라인·게이트) |
| [`docs/plans/`](docs/plans/) | 각 작업 상세 플랜 (PLAN-01~05) |
| [`docs/RADP_RESEARCH_PROPOSAL.md`](docs/RADP_RESEARCH_PROPOSAL.md) | 최초 기획서 (역사적 기록) |
| [`docs/EXPERIMENTS_post-H1.md`](docs/EXPERIMENTS_post-H1.md), [`docs/WEEK2_FINDINGS.md`](docs/WEEK2_FINDINGS.md) | 실험 종합 / RADP-hidden negative |

---

## 🚀 Quick Start

```bash
uv sync                                   # 의존성
cp .env.example .env                      # OPENAI_API_KEY 입력
hf download Wigtn/KoGovDoc-Bench --repo-type dataset --local-dir data/KoGovDoc-Bench

# 커버리지 진단 (GPU 불필요, CPU 수 초)
uv run python scripts/evaluation/coverage_diagnostic.py
```

---

## 🤝 공동 연구자

- **Harrison Kim** (harry@brain-crew.com) — 방법·학습·평가 인프라
- **손상우 (Sangwoo)** — RADP-DPO 파이프라인·실험 (Linear WIG-194)

> 저자 순서·명시는 합의 후 확정 (현 draft는 `Harrison Kim, et al.`).

## 📄 License & Citation

Apache 2.0 (upstream WigtnOCR v1과 동일). BibTeX는 채택 후.
