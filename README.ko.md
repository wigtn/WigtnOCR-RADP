# WigtnOCR-RADP

**Retrieval-Aware Document Parsing — 사람이 읽기 좋은 파싱 ≠ 검색이 잘 되는 파싱**

> 🎯 EMNLP 2026 Industry Track 투고 준비 (마감 2026-06-16)
> 📦 Builds on [WigtnOCR v1](https://huggingface.co/Wigtn/Qwen3-VL-2B-WigtnOCR) + [KoGovDoc-Bench](https://huggingface.co/datasets/Wigtn/KoGovDoc-Bench)
> 🇺🇸 **[English README](README.md)** &nbsp;·&nbsp; 🧭 연구 정의·가설은 [`docs/RESEARCH_DIRECTION.md`](docs/RESEARCH_DIRECTION.md), 진행은 [`docs/ACHIEVED.md`](docs/ACHIEVED.md) / [`docs/ROADMAP.md`](docs/ROADMAP.md)

---

## 📌 한 줄 요약

문서 파서는 보통 **사람이 보기 좋은 markdown**을 만들도록 학습된다. 하지만 RAG에서 진짜 중요한 건 **검색이 잘 되는 chunk**다. 우리는 이 둘이 다름을 진단하고(C1), 그 차이를 재는 지표를 만들고(C2), **파서를 검색 신호로 직접 학습**해 그 차이를 좁힐 수 있는지 검증한다(C3 — 정직한 negative).

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
| **C3** | 파서를 retrieval 신호로 학습한 **정직한 negative** — chunk-boundary contrastive aux loss(**RADP**)는 풀스케일·공정비교에서 +1~3pp(사전등록 5pp 게이트 미달). aux-loss는 잘못된 레버 | ✅ |
| → 다음 | 파서의 **discrete output**을 retrieval reward로 학습(DPO/RL) — C3 negative가 동기 | 🔄 future work |

RCPS:
```
RCPS(parser P, Q-A set D, retrievers R, k_values K) = (1/|R||K|) Σ_{r∈R, k∈K} MRR@k(r, chunks_P(D), questions_D)
```

RADP:
```
L_total = L_parse + λ · L_contrast
```

---

## 🧪 실험 (Experiments)

### 셋업

- **KoGovDoc-RAG** — 한국 정부문서 294페이지 위 663 Q-A (GPT-5.4 생성, LLM-as-judge 검증 94/100 accept). RADP 풀스케일 학습용으로 2,667페이지 v1 train set에 6,164 Q-A 추가, 평가는 held-out **73페이지 / 202 Q-A** fold 사용.
- **OHR-Bench** — 7개 도메인(Law·Manual·Finance·Newspaper·Textbook·Academic·Administration; 1,043 verbatim-answerable Q-A) cross-domain 복제. 15개 parser-output variant(실제 3 + formatting-noise 3 + semantic-noise 9).
- **모델** — Qwen3-VL-2B-Instruct + LoRA(r=8, α=32), 전체 v1 train set; λ ∈ {0, 0.1, 0.3, 0.5} (λ=0 은 production 파서 v1을 재현하는 matched control).

### C1 — Parsing↔Retrieval disconnect (한국 정부문서)

RCPS는 6개 파서에서 0.07–0.58 분포. VLM 계열이 상위, OCR 계열이 하위. 내재적 Boundary Clarity가 RCPS와 **Pearson r = −0.81** 로 **역상관**(n=5, 38p Marker 제외). 경계가 가장 깨끗한 MinerU(BC 0.72)가 검색은 **꼴찌**.

| Parser | BC | RCPS | Hit@1 |
|---|:---:|:---:|:---:|
| Qwen3-VL-30B (teacher) | 0.691 | **0.584** | 0.545 |
| WigtnOCR-2B (ours, v1) | 0.694 | 0.583 | 0.549 |
| Qwen3-VL-2B (base) | 0.677 | 0.532 | 0.500 |
| MinerU | **0.722** | 0.212 | 0.197 |
| PaddleOCR | 0.649 | 0.140 | 0.125 |
| Marker (38p) | 0.667 | 0.073 | 0.068 |

*표 1 — KoGov: BC vs RCPS, Pearson r = −0.81 (n=5, Marker 제외).*

### C1 — 메커니즘 (cross-domain, OHR-Bench)

핵심 발견: **각 semantic-noise 패밀리 안에서 Boundary Clarity는 거의 안 움직이는데 RCPS는 붕괴한다.** 내재적 경계 지표는 *형식*만 볼 뿐 *내용*을 못 본다 — 검색 가능한 내용을 파괴하는 의미 노이즈가 BC를 떨어뜨리지 않는다.

![Boundary Clarity는 내용 노이즈에 눈이 먼다 — 상단: 세 파서 패밀리 모두 노이즈 강도에 걸쳐 BC가 평탄; 하단: MinerU·GOT의 RCPS는 붕괴, Qwen2.5-VL은 강건](paper/figures/fig_noise_family.png)

*그림 2 — OHR-Bench 7-도메인 noise-family 곡선. **상단:** Boundary Clarity는 노이즈 강도(clean → mild → moderate → severe)에 걸쳐 거의 평탄. **하단:** RCPS는 MinerU(−51%)·GOT에서 붕괴, Qwen2.5-VL은 더 강건(−8%). 내재적 지표는 검색이 의존하는 의미적 내용 품질을 인지하지 못한다.*

| Family (n) | BC range | RCPS (clean → severe) | ΔRCPS |
|---|:---:|:---:|:---:|
| MinerU + semantic noise (4) | 0.708–0.735 | 0.50 → 0.24 | **−51%** |
| GOT + semantic noise (3) | 0.495–0.650 | (no clean) → 0.26 | — |
| Qwen2.5-VL + semantic noise (4) | 0.610–0.619 | 0.47 → 0.43 | −8% |

*표 2 — OHR-Bench 패밀리별 noise-perturbation 요약. disconnect(BC 평탄, semantic noise에서 RCPS 하락)는 MinerU·GOT에서 극적, Qwen2.5-VL은 더 강건. 15-variant 전체를 합친 BC↔RCPS scalar는 data-mix에 민감(Law+Manual −0.35, 7-도메인 전체 +0.25)하므로, 견고한 발견은 모든 도메인에서 재현되는 위 패밀리별 메커니즘이다.*

### C2 — RCPS는 chunking 전략을 변별한다

쓸모 있는 지표는 실무자가 비교할 대안을 갈라줘야 한다. v1 파서의 KoGov 출력에서 RCPS는 네 가지 chunking 전략을 깔끔히 정렬한다 — markdown-header(md-h3) > parser-native > LumberChunker > fixed-size. 표면이 아니라 *검색 가능성*을 포착한다(내재적 지표라면 경계가 가장 깨끗한 fixed-size를 1위로 올렸을 것).

| Chunker | RCPS | Hit@1 | MRR@10 |
|---|:---:|:---:|:---:|
| md-h3 | **0.593** | 0.556 | 0.613 |
| parser_native | 0.583 | 0.549 | 0.602 |
| LumberChunker | 0.557 | 0.514 | 0.580 |
| fixed500 | 0.535 | 0.491 | 0.560 |

*표 3 — KoGov chunking-strategy 그리드 (663 Q-A, v1 파서 출력, 3-retriever RCPS 평균).*

### C3 — 파서 측 수정은 격차를 못 좁힌다 (negative)

RADP를 풀스케일(2,667p) 학습 후 73페이지/202 Q-A held-out fold에서 평가. contrastive loss의 이득은 **게이트 미달**: λ=0.1이 피크(+1.1pp md-h3 / +2.3pp parser-native), 그 이상에서는 RCPS가 단조 감소하고 `parseSim`도 동반 하락 — 두 목적이 **같은 LoRA 파라미터를 두고 경쟁**한다. 사전등록 **5pp 게이트 실패**.

| λ | RCPS (md-h3) | RCPS (parser-native) | parseSim |
|---|:---:|:---:|:---:|
| 0.0 (control) | 0.6551 | 0.6557 | 0.872 |
| **0.1** | **0.6664** | **0.6788** | 0.874 |
| 0.3 | 0.6526 | 0.6694 | 0.862 |
| 0.5 | 0.6407 | 0.6442 | 0.851 |
| v1 (ref) | 0.6724 | 0.6569 | 0.789 |

*표 4 — 풀스케일 λ sweep, 73페이지 eval fold. control 대비 최고: +1.13pp(md-h3) / +2.31pp(parser-native) — 게이트(≥5pp) 실패. control이 v1을 재현해 data-scale 교란 제거 확인.*

**왜 실패하나 (C1 연결).** 파서의 `L_parse` 타깃 자체가 사람이 읽기 좋은 markdown — 바로 그 구조의 내재적 경계 지표가 retrieval과 역상관한다(그림 2). 파서의 *hidden* 표현에 건 보조 목적은 1차 목적이 심은 prior를 벗어날 수 없다. 사람-가독성 prior를 넘으려면 학습 신호가 파서의 **discrete output**으로 들어가야 한다 — 이것이 retrieval-reward(DPO/RL) 학습을 다음 단계로 만든다(future work).

---

## 🚀 배포 교훈 (Deployment lessons)

1. **내재적 지표만으로 파서를 고르지 말 것.** Boundary Clarity(및 TEDS·edit distance)는 downstream retriever가 뒤집는 순서로 파서를 줄 세울 수 있다. 도메인 대표 held-out에서 ~500문항 RCPS 평가는 몇 시간이면 끝나고 결정을 바꾼다.
2. **파서 hidden state 보조 손실은 잘못된 레버.** 풀스케일·공정비교에서 이득은 게이트 미달(+1~3pp). 투자 대비 효과 없음.
3. **disconnect은 확률적이 아니라 기계적.** 내재적 구조는 멀쩡해 보여도 내용은 파괴될 수 있다(그림 2) — 파서 표면 품질이 아니라 retrieval을 직접 모니터링하라.

---

## 📂 Repository Structure

```
.
├── configs/                  # 실험 설정 (YAML)
├── src/wigtnocr_radp/
│   ├── qa_generation/        # Q-A 생성
│   ├── evaluation/           # RCPS, chunkers, retrievers, coverage 진단, BC
│   └── training/             # RADP(contrastive) / DPO
├── scripts/
│   ├── qa_generation/
│   ├── training/             # train_radp_b, DPO generate/score/build/train
│   └── evaluation/           # baseline_grid, chunking_grid, coverage_diagnostic, bootstrap
├── paper/                    # EMNLP 2026 초안 + figures
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
| [`paper/draft/paper.md`](paper/draft/paper.md) | EMNLP 2026 Industry Track 초안 |
| [`docs/RADP_RESEARCH_PROPOSAL.md`](docs/RADP_RESEARCH_PROPOSAL.md) | 최초 기획서 (역사적 기록) |

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

## 🤝 Authors (WIGTN)

이 연구는 **WigtnOCR v1** (Qwen3-VL-2B 기반 문서 파싱 fine-tuning)의 **후속 연구**다.

| 저자 (OpenReview) | Email | 기여 (CRediT) |
|------|-------|--------------|
| **Hyeong-seob Kim**\* | harrison@wigtn.com | Conceptualization, Methodology, Project administration — 연구 계획 수립, 방법·RCPS 메트릭 설계 |
| **Sang-woo Son**\* | sangwoo@wigtn.com | Software, Validation, Investigation — 구현·실험·테스트 |

> \* **Equal contribution (co-first authors).** Hyeong-seob Kim은 연구 설계·방법론을, Sang-woo Son은 구현·실험을 주도. 기여 가이드는 [CONTRIBUTING.md](CONTRIBUTING.md) 참조.

---

## 📄 License & Citation

[MIT License](LICENSE)로 배포. *(upstream WigtnOCR v1은 Apache-2.0.)* BibTeX는 [README.md](README.md#license--citation) 참조 (채택 후 확정).
