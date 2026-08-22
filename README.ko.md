# WigtnOCR-RADP

**Retrieval-Aware Document Parsing (RADP) — *보기에* 가장 깨끗한 파서가 검색에 가장 좋은 파서는 아니다.**

> ✅ **EMNLP 2026 Industry Track · Submission #384 · Accepted**
>
> 🖼️ OpenReview에는 현재 **Accept (Poster)** 로 기록되어 있다. 발표 형식은 잠정적이며
> oral로 변경될 가능성이 남아 있다.
>
> ⏳ **Camera-ready 마감: 2026년 8월 30일 (AoE)**
>
> 📄 제목: *Retrieval-Conditional Parsing Score (RCPS): Choosing Document Parsers by Retrieval, Not by Appearance*
>
> 📦 Builds on [WigtnOCR v1](https://huggingface.co/Wigtn/Qwen3-VL-2B-WigtnOCR) + [KoGovDoc-Bench](https://huggingface.co/datasets/Wigtn/KoGovDoc-Bench)
>
> 🇺🇸 **[English README](README.md)** · 🧭 연구 정의 [`docs/RESEARCH_DIRECTION.md`](docs/RESEARCH_DIRECTION.md) · 🗓️ 연혁 [`docs/TIMELINE.md`](docs/TIMELINE.md)

---

## 📌 한 줄 요약

RAG에 쓰이는 문서 파서는 보통 **내재적(intrinsic) "깨끗함" 지표**(edit distance·Boundary Clarity)로 고른다. 294페이지 평가셋(한국 정부문서 KoGov 229페이지 + arXiv 65페이지; full-set 파서 5종 + 38페이지 subset의 Marker, 3 retriever × 663 Q–A)에서 BC와 검색의 상관은 비교 가능한 full-set 파서 4종에서 **r = −0.74**, Marker subset을 더하면 **r = −0.81 (n = 5)** 다. 둘 다 소표본 기술통계다. 별도 감사한 tables-on 비교에서는 MinerU 대신 Prod를 고르면 **Hit@1이 +42.6 pp (0.123 → 0.549; 4.47×)** 바뀐다.

**헤드라인은 학습이 아니라 "선택(selection)"이다.** 기여는 네 가지:

- **C1** — parsing↔retrieval **disconnect**와 그 메커니즘 진단 (내재적 지표는 *내용*이 아니라 *형식*만 본다).
- **C2** — **retriever-free coverage 진단**: 어느 layer를 먼저 점검할지 구분한다. 명시한 exact-span 정규화에서 reference 답의 **20.2%** 가 파서 출력에 *absent*이며, 8개 chunker 전반에서 일정하다.
- **C3** — **RCPS** (Retrieval-Conditional Parsing Score): 학습 없이 검색 기반으로 파서·청커를 고르는 **프로토콜**. ablation으로 single-embedder MRR이 아님을 보임.
- **C4** — 파서측 학습의 **경계(bounded)** 지도. source-page가 맞는 엄격한 OHR 6-domain compatibility subset(2,036 Q–A)에서 RADP-DPO 두 checkpoint가 Prod 대비 Hit@5 **+0.95 pp**, **+1.15 pp**다. 정렬된 RADP-Distill per-QA artifact가 없어 objective 간 비교는 보류한다.

현재 저장소에는 **KoGovDoc-RAG** 평가 파일(294페이지 = KoGov 229 + arXiv 65 / 663 Q–A),
RCPS 구현, 선별된 결과 산출물이 있다. 아직 제공되지 않은 체크포인트와 camera-ready 공개 예정
항목은 아래에서 명시적으로 구분한다.

---

## 💡 동기 — Parsing 품질 ≠ Retrieval 성능

> **BC가 가장 높은 축인 MinerU(0.72)가 별도 tables-on run에서 retrieval Hit@1은 0.123에 그친다.** VLM 상위권의 0.50–0.55와 크게 벌어진다.

같은 방향을 OHR-Bench(ICCV 2025), EnterpriseDocBench(2026), When Good OCR Is Not Enough(2026)가 영어·엔터프라이즈에서 독립 보고했다. **선행 연구는 진단에 머물거나 다른 layer(chunking → retriever → generator)를 학습한다. L1 파서 자체를 검색 신호로 *고르거나* *학습*한 사례는 없다 — 그게 우리 niche.**

---

## 🧱 Contributions

| | 기여 | 헤드라인 결과 |
|---|---|---|
| **C1** | parsing↔retrieval **disconnect**와 메커니즘. 정렬된 영어 OHR subset에서 semantic noise가 커질 때 검색은 하락하지만 BC는 거의 고정되거나 비단조로 변한다. | full-set BC↔RCPS **r = −0.74**(기술통계); tables-on 파서 비교 **Hit@1 +42.6 pp** (0.123→0.549; 4.47×) |
| **C2** | **retriever-free coverage 진단** — reference span을 *covered / chunk 사이에 split / 정규화된 파서 출력에서 absent* 로 분류. retriever를 돌리기 *전에* 계산한다. | **20.2% exact-span absent** vs ≤2.3% split, 8개 chunker 전반 일정 ⇒ 파서 출력을 먼저 점검 |
| **C3** | **RCPS** — retriever-평균·format-normalised·held-out Q–A **프로토콜**, 학습 없이 파서·청커 선택. ablation: single-embedder MRR이 **아님**. | retriever-평균이 top 파서를 뒤집음; naive MRR 대비 **Kendall τ = 0.80** |
| **C4** | 파서측 학습의 **경계** 지도. 동일 subset의 artifact를 복구하기 전까지 objective 간 비교는 보류한다. | strict 6-domain OHR subset: **R2 +0.95 pp**, **R3 +1.15 pp** Hit@5 vs Prod (n=2,036) |

---

## 🔬 Method

### RCPS — Retrieval-Conditional Parsing Score (C3)

파서를 *출력이 얼마나 깨끗한가*가 아니라 *downstream 검색이 그 출력으로 무엇을 하는가*로 점수 매긴다. RCPS는 **새 유사도 함수가 아니라** 보통의 retrieval MRR을 세 가지 선택으로 감싼 **프로토콜**이다: **(i) extrinsic** (텍스트가 아니라 held-out Q–A probe로 채점), **(ii) retriever-평균** (여러 embedder 평균 — 프로덕션 embedder 하나에 순위가 좌우되지 않게), **(iii) format-normalised** relevance (whitespace/markdown 정규화 후 chunk 텍스트가 답 span을 포함하면 relevant).

```
RCPS(P, D, R, K) = (1 / |R||K|) · Σ_{r∈R} Σ_{k∈K}  MRR@k( r, chunks_P(D), {qᵢ} )
```

`R = {BGE-M3, multilingual-e5-large, Qwen3-Embedding-8B}`, `K = {1, 5, 10}`. chunk이 **relevant**한 것은 그 출처 페이지가 답의 페이지와 일치하고 gold span이 chunk의 substring일 때(공백·markdown 무시 정규화). 수백 개 held-out Q–A로 **학습 없이** 실행. 구현: [`src/wigtnocr_radp/evaluation/`](src/wigtnocr_radp/evaluation/).

### Coverage 진단 — 파서 vs 청커 (C2)

RCPS는 파서+청커+retriever를 함께 채점하므로 낮은 점수만으로 어느 layer를 먼저 살펴야 하는지 알기 어렵다. 파서 출력을 고정하고 청커만 바꿔, 정규화한 gold span을 **covered**, **split**(페이지 출력에는 있지만 chunk 사이에 나뉨 — overlap으로 회복 가능), **absent**(정규화한 파서 출력에 exact match가 없어 re-chunking만으로 같은 span을 복원할 수 없음)로 분류한다. absent는 실제 내용 누락일 수도, 표면형 차이일 수도 있으므로 case-level 검토로 구분해야 한다. 코드: [`scripts/evaluation/coverage_diagnostic.py`](scripts/evaluation/coverage_diagnostic.py).

### 파서측 학습 — 되는 것과 안 되는 것 (C4)

coverage 진단이 파서를 가리키면, 두 가지 자연스러운 방향으로 파서측 학습을 시험한다.

- **RADP-aux** *(hidden-state 보조손실 — sub-threshold).* `L_total = L_parse + λ·L_contrast` (파서의 답-span pooled hidden state와 frozen BGE-M3 임베딩 간 InfoNCE). 신호가 배포 markdown엔 diffuse gradient backflow로만 도달 — **threshold 미달**.
- **RADP-DPO** *(discrete-output retrieval-reward DPO).* 프로덕션 파서에서 K개 parse를 샘플 → page-local RCPS로 채점 → preference pair 구성 → **LoRA-toggle 레퍼런스**로 학습 (`π_θ`=LoRA on, `π_ref`=LoRA off — 가속기 하나, 모델 복제 없음). reward를 **R1 → R2 → R3** 마일스톤으로 sharpening.
- **RADP-Distill** *(fidelity-based control).* 후보를 page-local RCPS 대신 reference Markdown과의 edit-distance로 순위한다. 정렬된 per-QA artifact가 현재 없어 이 README에서는 Distill과 DPO의 정량 비교를 하지 않는다.
- **SimPO** *(reference-free control).* 평가된 point estimate는 음수지만, 어떤 최적화 차이가 원인인지는 이 실험만으로 분리하지 못한다.

---

## 🧪 Experiments

### Setup

- **KoGovDoc-RAG** — 294개 평가 페이지(**KoGov 229 + arXiv 65**) / 663 Q–A (`gpt-5.4` 생성, LLM-as-judge 94/100 accept). DPO/SimPO + 메커니즘은 통합 **242페이지 / 663-Q–A** fold; RADP-aux는 73페이지 held-out fold; +train Q–A 6,164개(2,667페이지 Prod train).
- **OHR-Bench** — 감사된 compatibility subset 두 개를 사용한다. C1은 **Law–Manual 1,043 Q–A**와 parser-output 15개 변종, C4는 legacy `notes` 오류 223건과 현 parser bundle에 evidence page가 없는 5건을 제외한 **6-domain 2,036 Q–A**다. 이는 full v2 rerun을 대체하지 않는다.
- **모델** — **Prod** = 한국 문서 파싱용 fine-tune된 Qwen3-VL-2B; LoRA (r=8, α=32). 모든 RCPS는 3 retriever × 3 cutoff; delta는 paired percentile bootstrap.

### C1 — disconnect (KoGovDoc-RAG 평가셋)

비교 가능한 full-set 파서 4종에서 BC와 RCPS는 **Pearson r = −0.74**다. 38페이지 subset의 Marker를 더하면 **r = −0.81 (n = 5)**이며, BC가 정의되지 않은 PaddleOCR은 제외한다. 둘 다 기술통계다.

| Parser | BC | CS | RCPS | Hit@1 |
|---|:---:|:---:|:---:|:---:|
| Qwen3-VL-30B (teacher) | 0.623 | 3.38 | **0.584** | 0.545 |
| **Prod (ours, 2B)** | 0.610 | 3.07 | 0.583 | 0.549 |
| Qwen3-VL-2B (base) | 0.520 | 3.74 | 0.532 | 0.500 |
| MinerU (tables-on, 별도 run) | — | — | 0.137 | 0.123 |
| MinerU (제출본 tables-off) | 0.716 | 2.81 | 0.212 | 0.197 |
| PaddleOCR | — | 3.46 | 0.140 | 0.125 |
| Marker (38p) | **0.717** | 3.41 | 0.073 | 0.068 |

*KoGov parser grid (논문 §4.3, Table 1). BC 상관은 제출본 tables-off grid를 사용한다. tables-on MinerU 행은 별도로 감사한 configuration이며 Marker는 full-set 순위 비교에서 제외한다.*

### C1 — 메커니즘 (cross-domain, OHR-Bench)

정렬된 Law–Manual subset에서 semantic noise는 검색을 낮추지만 BC는 일관되게 반응하지 않는다. MinerU RCPS는 **0.595 → 0.265(−55%)**로 떨어지는 동안 BC는 **0.657 → 0.631**로 비단조 변화하고, Qwen2.5-VL RCPS는 **0.545 → 0.497(−9%)**로 떨어지는 동안 BC는 약 **0.563**에 머문다. GOT은 RCPS가 **0.461 → 0.298**로 떨어지는 동안 BC가 **0.586 → 0.624**로 오른다. 15개 변종의 합산 상관 **r = −0.35**는 같은 family 안 변종들이 독립 파서가 아니므로 기술통계로만 본다. stale 7-domain 그림은 이 subset으로 다시 만들기 전까지 README에서 제거했다.

### C2 — coverage 진단이 출력 부재와 chunk 경계를 구분

Prod 출력(294페이지 = **KoGov 229 + arXiv 65**, 663 Q–A, **retriever 없음**)에서 정규화한 reference span의 **20.2%는 파서 출력에 exact match가 없고**, split은 최대 **2.3%**다. exact-span absent 비율은 **8개 chunker 전반에서 일정**하므로 re-chunking만으로 해당 case를 exact-span covered로 바꿀 수 없다. 따라서 chunker 튜닝보다 파서 출력을 먼저 점검해야 한다. 다만 이 수치만으로 답의 의미 자체가 완전히 누락됐는지, 다른 표면형으로 표현됐는지는 구분할 수 없다.

### C3 — RCPS는 청커를 구분하며, single-embedder MRR이 아니다

| Chunker | RCPS | Hit@1 | MRR@10 |
|---|:---:|:---:|:---:|
| md-h3 | **0.593** | 0.556 | 0.613 |
| parser_native | 0.583 | 0.549 | 0.602 |
| LumberChunker | 0.557 | 0.514 | 0.580 |
| fixed500 | 0.535 | 0.491 | 0.560 |

*KoGov 청킹 grid (663 Q–A, Prod 출력, 3-retriever RCPS 평균).* tracked aggregate 감사에서
MRR@{1,5,10} 평균 대신 3-retriever **MRR@10만 사용해도** 294페이지 파서 5개와 청커 4개의 전체
순위가 그대로 유지된다. 반면 retriever-평균을 빼고 BGE-M3 하나만 쓰면 **top 파서가 뒤집힌다**
(Prod 1위; full RCPS는 30B teacher 1위). 나머지 5-parser 순위는 일치해 Kendall $\tau=0.80$이다.
format-sensitive 비교에 필요한 ranked chunk 목록은 저장되지 않았으므로 해당 ablation은 보고하지 않는다.

### C4 — 파서측 학습: corrected compatibility-subset 결과

기존 OHR 결과는 benchmark release를 섞었다. 오류가 난 legacy `notes` 223건과 evidence page가 없는 5건을 제외한 strict 6-domain 감사 결과는 다음과 같다.

| Δ vs Prod (pp) | Hit@1 | Hit@5 | Hit@10 | MRR@10 | nDCG@5 |
|---|:---:|:---:|:---:|:---:|:---:|
| RADP-DPO R2 (retrieval reward) | +0.59 | +0.95 | +0.90 | +0.78 | +0.82 |
| RADP-DPO R3 (hard-negative) | +1.46 | +1.15 | +0.90 | +1.30 | +1.28 |

*corrected legacy compatibility subset, n=2,036, 3-retriever macro, paired bootstrap 1,000회(seed 42). Hit@5 95% CI는 R2 **[+0.33,+1.54]**, R3 **[+0.31,+2.05]**다. audit 후 정의한 subset이므로 기존 confirmatory analysis나 full OHR-Bench v2 평가로 취급하지 않는다.*

탐색적 KoGov fold(242페이지, n = 663)에서 RADP-DPO 마일스톤은 Hit@5 +1.96 ~ +2.11 pp(P[Δ>0] ≈ 0.90, 모든 양측 구간은 0을 포함)다. SimPO point estimate는 −1.7 ~ −0.7 pp다. RADP-Distill은 동일 subset per-QA artifact를 복구할 때까지 정량 결과를 제외한다.

### C4 — 메커니즘: 학습은 청킹이 아니라 텍스트 fidelity를 조인다

| Variant | BC ↑ | TextNED ↓ vs reference |
|---|:---:|:---:|
| Prod (ref) | 0.630 | 0.240 |
| RADP-DPO R2 | 0.647 | **0.163** |
| RADP-DPO R3 | — | 0.185 |
| RADP-aux λ=0.1 | 0.652 | 0.423 |

*현재 가능한 242페이지 mechanism 측정. DPO checkpoint들은 Prod보다 TextNED가 낮고 Hit@5 point estimate가 높지만, TextNED가 checkpoint 순서를 설명하지는 못한다. R3 BC와 불확실성 추정치가 없어 systematic boundary-change mechanism을 결론낼 수 없다.*

---

## 🚀 배포 플레이북

1. **파서는 내재적 지표만이 아니라 RCPS로 평가하라.** Boundary Clarity는 downstream retrieval과 다른 순서로 파서를 매길 수 있다. 수백 개 held-out Q–A를 학습 없이 채점하는 것이 별도 tables-on 비교에서 0.12 → 0.55 Hit@1 결정이다. *가장 레버리지 큰 교훈.*
2. **coverage 진단을 먼저 돌려라.** exact-span *absent*가 지배적이면 해당 파서 출력을 확인하고 실제 내용이 빠진 경우 파서를 바꾼다. *split*이 지배적이면 청커나 overlap을 조정한다.
3. **파서를 학습한다면 untouched subset에서 평가하고 fidelity baseline을 함께 둬라.** 감사된 DPO checkpoint의 Hit@5 point estimate는 Prod보다 약 1 pp 높지만, 현재 artifact로는 Distill 비교를 복구할 수 없다.
4. **가능한 근거 범위 안에서만 해석하라.** 현재 mechanism 결과는 DPO와 Prod 대비 낮은 TextNED의 동반을 보이지만, 인과 mechanism이나 evidence-type 우위를 확정하지 않는다.

---

## 📂 저장소 구조

```
.
├── configs/                  # 실험 config (YAML)
├── src/wigtnocr_radp/
│   ├── qa_generation/        # Q-A 생성
│   ├── evaluation/           # RCPS, chunker, retriever, coverage, Boundary Clarity, bootstrap CI
│   └── training/             # RADP-aux(contrastive) · RADP-DPO · RADP-Distill · SimPO (LoRA-toggle ref)
├── scripts/
│   ├── training/             # 후보 생성, preference / edit-distance pair, DPO/Distill/SimPO 파이프라인
│   ├── evaluation/           # baseline_grid, chunking_grid, coverage_diagnostic, rcps_protocol_ablation, OHR 체인
│   └── figures/              # 논문 그림 생성기 (disconnect, RCPS protocol, overview PPTX)
├── experiments/              # RADP-Distill 학습·평가 harness
├── paper/                    # EMNLP 2026 accepted 원고 + LaTeX + figures
├── data/KoGovDoc-RAG/        # frozen 663-Q–A 평가 파일과 page split
├── docs/                     # RESEARCH_DIRECTION · TIMELINE · ROADMAP · plans/ · literature_review/
├── output/                   # 선별된 결과 JSON; 아래 산출물 상태 참고
└── tests/
```

## ⚡ 로컬 코드 점검

```bash
uv sync --extra dev
uv run pytest
uv run python scripts/evaluation/coverage_diagnostic.py --out_dir /tmp/rcps-coverage-check
```

마지막 명령은 gitignore된 source-page mapping `data/KoGovDoc-Bench/val.jsonl`이 로컬에 있을 때
CPU 기반 294페이지 / 663-Q–A coverage 진단을 실행한다. Q–A와 parser 출력은 tracked이지만 이
mapping 파일은 아직 packaging되지 않아 현재 명령만으로는 fresh-clone 재현이 완결되지 않는다.
이 명령들은 논문 실험 전체의 **fresh-clone 재현**을 의미하지 않는다.
전체 파이프라인은 외부 parser 출력, cache, checkpoint에 아직 의존한다. portable end-to-end 실행법과
남은 공개 산출물은 아래의 camera-ready 작업 항목이다.

> **그림 로고 안내:** `make_fig_overview_pptx.py`(Figure 1)는 `scripts/figures/icons/logos/`의 타사 브랜드 로고
> (`qwen.png`, `mineru.png`, `marker_datalab.png`, `paddle.png`, `bge_baai.png`, `me5_ms.png`)를 사용한다.
> 라이선스 문제로 **repo에 포함하지 않음** — 재생성하려면 각 프로젝트 공식 사이트에서 받아 넣을 것. 그림 재생성은 camera-ready 마지막 시각 단계로 보류한다. 현재 일부 export와 generator에는 stale tables-off 또는 mixed-version OHR 수치가 있으므로 실행 원장을 먼저 확인한다.

---

## 👥 저자 (OpenReview 순서)

**WigtnOCR v1**(Qwen3-VL-2B 문서 파싱 fine-tuning)의 후속 연구.

1. Sang-Woo Son
2. Hyeong-seob Kim
3. Hyeonsang Kim
4. Hyun-woo Cho
5. Jinmo Kim

저자 명단과 순서는 제출 당시 그대로 유지한다. Hyeong-seob Kim의 교신저자 지정은 Industry Track
chairs의 서면 확인을 기다리는 중이므로 아직 교신저자 표시를 붙이지 않는다. 소속과 이메일도
확인된 metadata만 추후 반영한다.

---

## 📦 산출물 및 재현성 상태

### 현재 저장소에 있음

- **KoGovDoc-RAG 평가 파일** — 294페이지(**KoGov 229 + arXiv 65**) / 663 Q–A와 frozen page split,
  별도의 LLM-assisted 100-pair Q–A 품질 점검 표본 및 aggregate 94/100 결과. 이 표본의 빈
  `verification` 필드는 인간 라벨이 아니다.
- **RCPS 레퍼런스 구현** — [`src/wigtnocr_radp/evaluation/`](src/wigtnocr_radp/evaluation/).
- **선별된 평가 산출물** — tracked 결과 JSON과 현재 분석에 사용한 294페이지 MinerU table-ON 파서 출력.
- **정렬된 OHR 감사 artifact** — Law–Manual 1,043 Q–A C1 결과와 strict 2,036-Q–A legacy compatibility subset의 deterministic derivation. 구 7-domain 산출물은 provenance 용도로 남아 있지만 camera-ready 근거로는 유효하지 않다.

### Camera-ready pending — 현재는 제공되지 않음

- MinerU **table-OFF** 파서 출력과 정확한 rerun 명령.
- 전체 294페이지 parser/chunker grid의 per-Q–A 배열과 이에 대응하는 probe-resampling
  **ranking-stability** 산출물. tracked aggregate-grid audit와 end-to-end stability check는 다른
  분석이며 이미 저장소에 있다.
- 별도의 two-author 100-case absent-label 연구에서 나온 최종 per-case 라벨과 adjudication.
  현재 Git에는 없으며 공개 여부 결정과 packaging이 아직 남아 있다.
- full OHR-Bench v2 rerun과 새 current/quarantine manifest의 clean-machine 검증. legacy 7-domain/combined-CI/OHR-TextNED artifact는 이미 quarantine manifest로 분리했다.
- 동일 aligned subset의 RADP-Distill per-QA·CI artifact. 복구 전에는 Distill-vs-DPO 정량 비교를 지원하지 않는다.
- complete BC/CS mechanism data와 aligned 최신 값만 사용한 figure 재생성.
- RADP-Distill, RADP-aux, RADP-DPO, SimPO의 complete executed-config/log provenance와 모델 체크포인트.
- 외부 데이터, parser 출력, embedding cache, checkpoint 획득, 머신 종속 실행 가정을 포함한
  **portable fresh-clone end-to-end 재현 경로**.

## 📄 License & Citation

저장소 코드는 **MIT License**로 공개한다. 타사 데이터셋과 모델 자산에는 각각의 원 라이선스와
이용 조건이 적용된다.

```bibtex
@inproceedings{son2026rcps,
  title     = {Retrieval-Conditional Parsing Score (RCPS): Choosing Document Parsers by Retrieval, Not by Appearance},
  author    = {Son, Sang-Woo and Kim, Hyeong-seob and Kim, Hyeonsang and Cho, Hyun-woo and Kim, Jinmo},
  booktitle = {Proceedings of EMNLP 2026 (Industry Track)},
  year      = {2026},
  note      = {Accepted; camera-ready pending}
}
```
