# WigtnOCR-RADP

**Retrieval-Aware Document Parsing — 사람이 읽기 좋은 파싱 ≠ 검색이 잘 되는 파싱**

> 🎯 **EMNLP 2026 Industry Track** 투고 · 논문 초안 **v0.6** · 마감 2026-06-16
>
> 📦 Builds on [WigtnOCR v1](https://huggingface.co/Wigtn/Qwen3-VL-2B-WigtnOCR) + [KoGovDoc-Bench](https://huggingface.co/datasets/Wigtn/KoGovDoc-Bench)
>
> 🇺🇸 **[English README](README.md)** · 🧭 연구 정의 [`docs/RESEARCH_DIRECTION.md`](docs/RESEARCH_DIRECTION.md) · 🗓️ 연혁 [`docs/TIMELINE.md`](docs/TIMELINE.md)

---

## 📌 한 줄 요약

문서 파서는 보통 **사람이 보기 좋은 markdown**(TEDS·edit distance·Boundary Clarity)을 만들도록 학습되지만, 이 지표들은 **downstream 검색을 예측하지 못한다**. 한국 정부문서(6 parser × 3 retriever × 663 Q-A)에서 MoC Boundary Clarity는 검색과 **Pearson r = −0.81** 로 역상관 — 내재적 지표 1위(MinerU)가 검색은 꼴찌다.

우리는 (C1) 이 disconnect를 cross-domain으로 진단하고 메커니즘을 드러내며, (C2) retriever-agnostic 지표 **RCPS**를 제안하고, (C3) **RADP-DPO** — 파서의 **discrete markdown 출력**을 retrieval reward로 DPO 학습 — 를 도입한다. RADP-DPO는 **KoGov Hit@5 +2.11 pp**(P[Δ>0]=0.91), 그리고 결정적으로 **영어 OHR-Bench(n=2,264)에서 +1.03 pp, 양측 유의·1 pp 실무 기준 통과**를 달성한다. 더불어 두 개의 경계 negative(hidden-state **RADP-aux**, reference-free **SimPO**)로 retrieval 신호가 파서의 *어디로* 들어가야 하는지를 규명한다.

---

## 💡 동기 — Parsing 품질 ≠ Retrieval 성능

> **MoC Boundary Clarity(BC) 1위 파서(MinerU, 0.72)가 retrieval Hit@1 0.20으로 6개 중 꼴찌.** 가장 깨끗해 보이는 파서가 가장 검색이 안 된다.

같은 방향을 OHR-Bench(ICCV 2025), EnterpriseDocBench(2026, r≈0.14), When Good OCR Is Not Enough(2026)가 영어·엔터프라이즈에서 독립 보고했다. **선행 연구는 진단에 머물거나 다른 layer(chunking~generation)를 학습한다. L1 파서를 retrieval 신호로 학습한 사례는 없다 — 그게 우리 niche.**

---

## 🧱 Contributions

| | 기여 | 상태 |
|---|---|:---:|
| **C1** | Parsing↔Retrieval disconnect cross-domain 진단 + 메커니즘(noise-family 곡선, 그림 2) | ✅ |
| **C2** | **RCPS** (Retrieval-Conditional Parsing Score) — retriever-agnostic, task-oriented 지표 | ✅ |
| **C3** | **RADP-DPO** — 파서 discrete 출력에 retrieval-reward DPO. **KoGov Hit@5 +2.11 pp**(P=0.91); **영어 OHR-Bench +1.03 pp 양측 유의·1 pp 기준 통과** | ✅ |
| 경계 | 두 negative가 동작 영역을 규명: hidden-state **RADP-aux**(+1~3 pp, 5 pp 게이트 미달), reference-free **SimPO**(negative). 신호는 *discrete 출력* + reference 정책 anchoring으로 들어가야 함 | ✅ |

---

## 🔬 Method

### RCPS — Retrieval-Conditional Parsing Score

파서를 "출력이 얼마나 깨끗한가"가 아니라 "downstream 검색이 그 출력으로 무엇을 할 수 있는가"로 평가한다.

```
RCPS(P, D, R, K) = (1 / |R||K|) · Σ_{r∈R} Σ_{k∈K}  MRR@k( r, chunks_P(D), {qᵢ} )
```

`R = {BGE-M3, multilingual-e5-large, Qwen3-Embedding-8B}`, `K = {1,5,10}`. 청크는 (i) source 페이지 일치 + (ii) 정답 span이 청크의 substring일 때 relevant. retriever 평균으로 embedder 선택에 robust. 구현: [`src/wigtnocr_radp/evaluation/`](src/wigtnocr_radp/evaluation/).

### RADP-DPO — discrete 출력에 retrieval-reward preference 학습 (C3)

파서의 **discrete markdown 출력**을 retrieval reward로 직접 최적화한다. 각 train 페이지마다 production 파서 v1에서 K개 후보 parse를 샘플링 → chunk·index·scoring(retrieval reward) → page-local RCPS gap이 임계 초과인 `(parse_chosen, parse_rejected)` 선호쌍 구성 → DPO:

```
L_DPO = −log σ( β · [ (log π_θ(c) − log π_θ(r)) − (log π_ref(c) − log π_ref(r)) ] )
```

- **LoRA-toggle reference 트릭:** 모델 2벌(2× 메모리) 대신 `π_θ`=파서+LoRA on, `π_ref`=같은 base에 LoRA off. 단일 가속기로 충분.
- **Reward sharpening R1→R2→R3:** R1(page-local RCPS, BGE, β=0.1) → R2(warmstart iterative, β=0.05) → **R3(full-corpus hard-negative pool, K=14)** — distractor를 "retriever가 실제로 정답과 헷갈리는 다른 페이지 청크"로. 보상을 sharpen하면 효과가 1 pp 위로 올라간다.

### RADP-aux — hidden-state contrastive (경계 negative)

다른 파서측 수정: retrieval 신호를 파서의 *hidden* state로 보낸다. `L_total = L_parse + λ·L_contrast`(파서 answer-chunk pooled hidden ↔ frozen BGE-M3 임베딩 InfoNCE). **게이트 미달** — 신호가 `L_parse`를 통한 diffuse gradient backflow로만 배포 markdown에 닿기 때문.

---

## 🧪 실험 (Experiments)

### 셋업

- **KoGovDoc-RAG** — 한국 정부문서 294p 663 Q-A(GPT-5.4, LLM-judge 94/100). RADP-DPO/SimPO·메커니즘은 통합 **242p / 663 Q-A** fold, RADP-aux는 **73p / 202 Q-A** held-out fold, +2,667p train set에 6,164 Q-A.
- **OHR-Bench** — 영어 cross-domain, 7 도메인, **2,264 verbatim Q-A**; C1 메커니즘용 15 parser-output variant.
- **모델** — Qwen3-VL-2B-Instruct + LoRA(r=8, α=32). RCPS는 3 retriever × 3 cutoff, delta는 paired bootstrap(10k).

### C1 — Parsing↔Retrieval disconnect (한국 정부문서)

BC가 RCPS와 **Pearson r = −0.81**(n=5) 역상관. 경계 가장 깨끗한 MinerU(BC 0.72)가 검색 **꼴찌**.

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

각 semantic-noise 패밀리 안에서 **BC는 거의 안 움직이는데 RCPS는 붕괴**. 내재적 지표는 *형식*만 볼 뿐 *내용*을 못 본다.

![Boundary Clarity는 내용 노이즈에 눈이 먼다 — 상단: 세 파서 패밀리 모두 노이즈 강도에 걸쳐 BC 평탄; 하단: MinerU·GOT RCPS 붕괴, Qwen2.5-VL 강건](paper/figures/fig_noise_family.png)

*그림 2 — OHR-Bench 7-도메인 noise-family 곡선. **상단:** BC는 노이즈 강도(clean→mild→moderate→severe)에 평탄. **하단:** RCPS는 MinerU(−51%)·GOT에서 붕괴, Qwen2.5-VL은 강건(−8%).*

### C2 — RCPS는 chunking 전략을 변별한다

| Chunker | RCPS | Hit@1 | MRR@10 |
|---|:---:|:---:|:---:|
| md-h3 | **0.593** | 0.556 | 0.613 |
| parser_native | 0.583 | 0.549 | 0.602 |
| LumberChunker | 0.557 | 0.514 | 0.580 |
| fixed500 | 0.535 | 0.491 | 0.560 |

*표 3 — KoGov chunking-strategy 그리드 (663 Q-A, v1 출력, 3-retriever RCPS 평균).*

### C3 — RADP-DPO가 Hit@5를 ≈2 pp 올린다 (positive)

242p / 663 Q-A KoGov fold에서 모든 RADP-DPO variant가 v1 대비 Hit@5 향상, reward sharpening 축을 따라 증가. n=663에선 양측 CI가 0을 포함(strong-directional, P≈0.90) — 양측 유의는 cross-domain OHR이 보강.

| Variant | Hit@5 (v1=0.6863) | ΔHit@5 vs v1 (pp) [95% CI] | P[Δ>0] | ΔHit@10 | ΔRCPS |
|---|:---:|:---:|:---:|:---:|:---:|
| **RADP-DPO-v5** (R3, hard-neg) | 0.7074 | **+2.11 [−0.96, +5.13]** | **0.91** 🔶 | +2.21 | +1.72 |
| **RADP-DPO-v1** (R1, BGE β=0.1) | 0.7069 | **+2.06 [−0.96, +5.13]** | **0.91** 🔶 | +1.81 | +0.57 |
| **RADP-DPO-v4** (R2, warmstart β=0.05) | 0.7059 | **+1.96 [−1.06, +5.03]** | **0.90** 🔶 | +1.71 | +0.47 |
| RADP-SimPO (ref-free 대조) | 0.6793 | −0.70 [−3.77, +2.31] | 0.32 | −0.96 | −1.56 |

*표 5 — RADP-DPO 진행(R1→R2→R3) + SimPO 대조, parser_native, 242p fold, 10k paired bootstrap. 🔶 = P[Δ>0] ≥ 0.85. 3-seed merge는 R1을 +1.16 pp [−0.64, +2.90](P=0.90)로 tighten.*

**Cross-domain 검증 (영어 OHR-Bench, n=2,264) — 1 pp 기준을 양측 유의로 통과.** 한국어로 학습한 v1을 zero-shot 적용(Hit@5=58.5%). hard-negative variant **R3(RADP-DPO-v5)**가 모든 표준 지표를 양측 유의·1 pp 이상으로 개선:

| 지표 | Δ vs v1 (pp) | 95% CI |
|---|:---:|:---:|
| Hit@5 | **+1.03** | [+0.24, +1.84] |
| Hit@1 | **+1.31** | [+0.55, +2.09] |
| MRR@10 | **+1.17** | [+0.52, +1.86] |
| nDCG@5 | **+1.15** | [+0.49, +1.86] |

*표 5b — OHR-Bench cross-domain, 3-retriever macro, 1k paired bootstrap, 7개 도메인 모두 positive. 학습 신호(train Q-A retrieval reward)·평가 지표·문서 언어가 상호 disjoint → metric circularity와 domain over-fitting 동시 배제. 보상을 page-local(R2: Hit@5 +0.85 pp)에서 hard-negative(R3)로 sharpen하면 1 pp 위로(R3>R2 Hit@1 +0.78 pp).*

**학습 scorer 밖으로 전이되고, text-precision 질의에 집중된다.** 선호쌍 scoring에 쓴 BGE-M3보다 **held-out retriever에서 효과가 더 큼**(ml-e5 +2.41 pp, Qwen3-Emb +2.26 pp vs BGE +1.51 pp) → BGE-overfit 배제. 그리고 **factoid 질의(+3.07 pp)**에 집중 — 정답 span의 verbatim 텍스트가 검색을 좌우하는 부류(논문 표 6).

### C3 — 메커니즘: DPO는 chunking이 아니라 text fidelity를 높인다

| Variant | BC ↑ | CS ↓ | TextNED ↓ vs GT |
|---|:---:|:---:|:---:|
| v1 (ref) | 0.630 | 0.474 | 0.175 |
| **RADP-DPO-v1** | 0.646 | 0.474 | **0.122** |
| **RADP-DPO-v4** | 0.647 | 0.476 | **0.119** |
| RADP-aux λ=0.1 | 0.652 | 0.484 | 0.352 |

*표 7(발췌) — RADP-DPO는 TextNED-vs-GT를 19~32% 감소(0.175→0.119)시키되 **chunking signature는 불변**(BC≈0.63, CS≈0.474 모두 v1과 구분 불가). 이득은 *어떻게* 쪼개느냐가 아니라 *무엇을* 파싱하느냐에서 옴 — cross-domain에서도 재현(OHR TextNED −2.5%, 양측 유의).*

### 경계 negative — RADP-aux / SimPO

| λ | RCPS (md-h3) | Δ vs control [95% CI] | RCPS (parser-native) | Δ vs control [95% CI] |
|---|:---:|:---:|:---:|:---:|
| 0.0 (control) | 0.6551 | — | 0.6557 | — |
| 0.1 | **0.6664** | +1.13 [−2.53, +4.95] | **0.6788** | +2.31 [−1.59, +6.30] |
| 0.3 | 0.6526 | −0.25 [−4.03, +3.12] | 0.6694 | +1.37 [−2.35, +5.11] |
| 0.5 | 0.6407 | −1.44 [−5.92, +2.62] | 0.6442 | −1.15 [−5.78, +3.50] |

*표 4 — RADP-aux λ sweep(73p fold). 피크 +1~3 pp, 모든 Δ-vs-control CI가 0 포함, **사전등록 5 pp 게이트 미달**. reference-free **SimPO**는 전 cell negative(표 5). 둘이 동작 영역을 규명: **discrete 출력 + reference 정책 anchoring preference loss**.*

---

## 🚀 배포 교훈 (Deployment lessons)

1. **내재적 지표만으로 파서를 고르지 말 것.** BC(및 TEDS·edit distance)는 retriever가 뒤집는 순서로 파서를 줄 세운다. ~500문항 RCPS 평가가 결정을 바꾼다.
2. **파서 discrete 출력에 retrieval-reward DPO를 써라.** 이미 ≈0.7 Hit@5인 파서에 선호쌍 수백 개 + LoRA 1회로 +2 pp는 실질 이득이며, 실제 배포 retriever로 전이된다. aux-loss·reference-free SimPO는 피하라(둘 다 실패).
3. **text precision이 검색을 좌우하는 곳에 예산을 써라.** RADP-DPO는 factoid(+3 pp)에 최대, tabular엔 거의 중립 — 구조질의 비중이 크면 chunker/embedder측 학습으로 보완.

---

## 📂 Repository Structure

```
.
├── configs/                  # 실험 설정 (YAML)
├── src/wigtnocr_radp/
│   ├── qa_generation/        # Q-A 생성
│   ├── evaluation/           # RCPS, chunkers, retrievers, coverage, BC, bootstrap CI
│   └── training/             # RADP-aux(contrastive) · RADP-DPO · SimPO (LoRA-toggle reference)
├── scripts/
│   ├── training/             # 후보 생성(K=2..16), 선호쌍, DPO/SimPO, multi-seed 파이프라인
│   ├── evaluation/           # baseline_grid, chunking_grid, coverage, OHR-Bench eval chain, combined CI
│   └── analysis/             # positive_signal_dig, robustness_boost
├── paper/                    # EMNLP 2026 초안(v0.6) + figures
├── data/KoGovDoc-RAG/        # 663 Q-A (frozen, gitignored)
├── docs/                     # RESEARCH_DIRECTION · ACHIEVED · ROADMAP · TIMELINE · plans/
├── output/                   # 결과·체크포인트 (gitignored, GPU 서버)
└── tests/
```

## 🚀 Quick Start

```bash
uv sync                                   # 의존성 (extras: eval / train / data)
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
| **Hyeong-seob Kim**\* | harrison@wigtn.com | Conceptualization, Methodology, Project administration — 연구 계획·방법·RCPS 설계 |
| **Sang-woo Son**\* | sangwoo@wigtn.com | Software, Validation, Investigation — 구현·실험·테스트 |

> \* **Equal contribution (co-first authors).**

---

## 📄 License & Citation

**MIT License**로 배포. BibTeX는 [README.md](README.md#license--citation) 참조 (채택 후 확정).
