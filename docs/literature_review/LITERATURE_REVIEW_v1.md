# RADP Literature Review v1

> 작성일: 2026-05-17
> 작성자: bc-arxiv agent (Claude Opus 4.7 1M)
> 대상: Harrison Kim (Braincrew AI), EMNLP 2026 Industry Track 투고 준비

---

## 1. Executive Summary

- **검토한 paper 수**: 14편 (직접 요약), 추가 30+편 abstract 스캔
- **검토 키워드**: retrieval-aware chunking, chunking optimization, ColPali, Late Chunking, LumberChunker, MetaChunking, OCR-RAG correlation, retrieval reward DPO/RLHF, contrastive chunk embedding, task-oriented OCR
- **Scooping risk verdict**: **CAUTION (DANGER on C1 alone)**

### 가장 위협적인 발견

| Paper | 위협 부분 | 위협 강도 |
|-------|-----------|----------|
| **EnterpriseDocBench (2604.26382)** | C1 (parsing↔retrieval weak correlation) — **이미 정량화됨 r=0.14** | **Critical** |
| **InSeNT / Context is Gold (2505.24782)** | RADP-B의 in-sequence contrastive negative 아이디어 선점 | **Critical** |
| **When Good OCR Is Not Enough (2605.00911)** | OCR↔RAG mismatch motivation 점유 (concurrent 2026-04) | **Critical** |
| **OCR Hinders RAG (2412.02592, ICCV 2025)** | OHRBench로 OCR-RAG cascade impact 정량화 (선행) | **High** |
| **M-LongDoc (2411.06176, EMNLP 2025)** | "Retrieval-Aware Tuning" 이름 점유 (다른 layer지만) | **Moderate (naming)** |
| **MoC (2503.09600, ACL 2025)** | Chunking quality metric (Boundary Clarity/Stickiness) 제안 — RCPS와 framing 충돌 | **Moderate** |
| **RPO (2501.13726)** | DPO + retrieval reward — RADP-A의 prior | **Moderate (A only)** |
| **LMAR (2508.05672)** | Joint chunking + embedding contrastive learning | **Moderate** |

### RADP의 novelty가 살아있는 영역

1. **VLM parser 자체에 retrieval-aware fine-tuning을 적용한 최초 사례** (모든 선행 연구는 embedding/retriever/reader/post-hoc chunker를 학습; parser는 frozen)
2. **Image input → retrieval-aligned chunk output** end-to-end 학습
3. **한국어 정부문서 도메인** (희소 데이터)
4. **RCPS = task-oriented, extrinsic chunking metric** (intrinsic MoC와 보완)
5. **Triple contribution stack** (diagnostic + metric + method) — 다른 paper는 하나~둘만

### 한 줄 결론

> RADP는 **C1만으로는 scooped at risk**. **C2 (RCPS) + C3 (RADP-B/A)와 함께 layered contribution으로 framing**하면 살아있다. 가장 위협적인 InSeNT와 EnterpriseDocBench를 **explicit 차별화 + 결합 실험**으로 방어해야 한다.

---

## 2. 관련 연구 카테고리

### 2.1 OCR/Parsing quality ↔ RAG performance correlation (우리 C1 영역)

이 카테고리가 **가장 hot**하고 **가장 위험**하다.

**Closest prior:**
- **OCR Hinders RAG (2412.02592, ICCV 2025)**: OHRBench로 OCR noise (semantic + formatting)가 RAG cascade에 미치는 영향 정량화. SOTA OCR도 GT 대비 ≥7.5% gap.
- **When Good OCR Is Not Enough (2605.00911, 2026-04)**: 11 challenging document types에서 WER/CER이 낮아도 retrieval/generation 실패 발생. "Downstream-aware OCR assessment" 주장.
- **EnterpriseDocBench (2604.26382, 2026)**: parsing→retrieval Pearson r=0.14. parsing variance가 retrieval의 2% 미만 설명. **우리 핵심 발견과 정확히 동일**.

**우리 차별점**:
- 한국어 정부문서 (다른 언어/도메인)
- 6 parser × 3 retriever grid (구체적 SOTA parser 비교)
- 발견에서 끝나지 않고 **training method (RADP-B/A)로 해결**
- 새 metric (RCPS) 제공

### 2.2 Chunking optimization for retrieval

**Method 계열**:
- **Late Chunking (2409.04701, Jina)**: long-context embedding으로 inference-time chunk pooling
- **LumberChunker (2406.17526, EMNLP 2024 Findings)**: LLM이 narrative boundary 직접 predict
- **Meta-Chunking (2410.12788)**: PPL/uncertainty 기반 logical boundary
- **MoC (2503.09600, ACL 2025)**: MoE chunker + Boundary Clarity/Stickiness metric
- **Vision-Guided Chunking (2506.16035)**: LMM으로 PDF batch 처리하여 chunk
- **ChunkRAG (2410.19572)**: retrieval 후 LLM-based chunk filtering

**Survey/Eval**:
- **Beyond Chunk-Then-Embed (2602.16974)**: chunking taxonomy
- **Chunk Twice Embed Once (2506.17277)**: chunking이 embedding choice만큼 중요
- **Rethinking Chunk Size (2505.21700)**: long-doc retrieval에서 chunk size 영향
- **Reconstructing Context (2504.19754)**: contextual vs late chunking trade-off

**우리 차별점**: 위 모든 method는 **post-parsing text input**을 chunking. 우리 RADP는 **parsing 시점에 chunk 경계를 retrieval에 align**되게 학습 → image → retrieval-ready chunks가 한 forward에서.

### 2.3 Contrastive learning for retrieval embeddings (우리 RADP-B의 가장 가까운 prior)

- **InSeNT / Context is Gold (2505.24782)**: in-sequence negative + late chunking으로 contextual chunk embedding
- **LMAR (2508.05672)**: LLM-supervised contrastive embedding + chunking joint
- **BGE-M3 (2402.03216)**: multilingual contrastive embedding (foundation)

**가장 위협적인 게 InSeNT다**. 우리 RADP-B의 "같은 페이지 내 hard negative" 아이디어와 거의 동일. **방어 핵심: 그들은 embedding model, 우리는 parsing VLM을 학습.**

### 2.4 Retrieval reward / preference optimization for RAG (RADP-A 영역)

- **DPO (2305.18290)**: foundation
- **Reward-RAG (2410.03780)**: reward model로 retriever fine-tune
- **RAG-Reward (2501.13264)**: reward + RLHF로 RAG LLM 학습
- **RPO (2501.13726)**: retrieval relevance signal로 DPO 변형 (generator 학습)
- **RAG-RewardBench (2412.13746)**: RAG reward model 평가

**우리 RADP-A 차별점**: 모든 선행 연구는 **retriever 또는 generator**를 학습. **Parser를 retrieval reward로 학습하는 것은 우리가 처음**.

### 2.5 Document parsing / OCR foundation

- **OmniDocBench (2412.07626, CVPR 2025)**: parsing benchmark (우리 baseline 평가)
- **ColPali (2407.01449, ICLR 2025)**: VLM 기반 visual document retrieval (parsing skip alternative)
- **MinerU 2.5 (2509.22186)**: SOTA parsing VLM (우리 baseline)
- **PaddleOCR-VL (2510.14528)**: 0.9B compact VLM parsing
- **Logics-Parsing (2509.19760)**: SFT-then-RL parsing
- **Doc-Researcher (2510.21603)**: parsing + deep research 통합

### 2.6 Multimodal RAG / long-document understanding

- **M-LongDoc (2411.06176, EMNLP 2025)**: **"Retrieval-Aware Tuning"** — reader-side
- **MMDocIR (2025 EMNLP)**: multimodal retrieval benchmark
- **REAL-MM-RAG (2502.12342)**: real-world multimodal RAG benchmark
- **MHier-RAG (2508.00579)**: visual-rich document QA

---

## 3. Closest Threats (RADP novelty 위협 정도 순)

### 1. **EnterpriseDocBench (2604.26382)** — 위협 Critical (C1)
**우리 angle**: 한국어 도메인 재현 + **method로 문제 해결** (그들은 진단만). Concurrent independent confirmation으로 framing.

### 2. **InSeNT / Context is Gold (2505.24782)** — 위협 Critical (B)
**우리 angle**: Embedding을 학습하는 그들과 달리 **parser VLM을 학습**. 두 layer는 orthogonal하며 결합 가능. Ablation으로 증명.

### 3. **When Good OCR Is Not Enough (2605.00911)** — 위협 Critical (C1)
**우리 angle**: 그들이 "need downstream-aware assessment"를 외쳤다면, 우리는 **RCPS라는 concrete metric + RADP라는 training solution**을 제공.

### 4. **OCR Hinders RAG / OHRBench (2412.02592)** — 위협 High (C1)
**우리 angle**: 그들 perturbation analysis는 합성 noise, 우리는 real SOTA parser 6개 직접 비교. Method까지 제공.

### 5. **M-LongDoc (2411.06176)** — 위협 Moderate (naming)
**우리 angle**: Naming clash 명시 차별화. "Reader-side retrieval-aware tuning" vs "Parser-side retrieval-aware document parsing". 부제목 추가 검토 (e.g., "via Chunk-Boundary Contrastive Learning").

### 6. **MoC (2503.09600, ACL 2025)** — 위협 Moderate (C2)
**우리 angle**: MoC의 Boundary Clarity/Stickiness = intrinsic, RCPS = extrinsic task-oriented. 두 metric 상관도 실험해서 intrinsic의 한계 보이기.

### 7. **RPO (2501.13726)** — 위협 Moderate (A only)
**우리 angle**: RPO=generator DPO, RADP-A=parser DPO. Layer 차이. **EMNLP 2026에는 RADP-B만 + A는 future work**로 미루는 옵션 강력 추천 (timeline risk + scooping risk 둘 다 완화).

### 8. **LumberChunker (2406.17526, EMNLP 2024 Findings)** — 위협 Low (그러나 EMNLP venue 동일)
**우리 angle**: Text narrative vs image multimodal, inference vs training.

### 9. **LMAR (2508.05672)** — 위협 Moderate
**우리 angle**: Embedding + chunking joint vs parsing. Layer 차이.

### 10. **ColPali (2407.01449, ICLR 2025)** — 위협 Low (다른 paradigm)
**우리 angle**: Parsing skip vs parsing improvement. Text-based RAG에서 parsing은 여전히 필요.

---

## 4. Recommended Citations (20개)

### Introduction & Motivation (5)
- **OCR Hinders RAG (2412.02592)** — OCR-RAG mismatch 핵심 evidence
- **When Good OCR Is Not Enough (2605.00911)** — concurrent confirmation
- **EnterpriseDocBench (2604.26382)** — parsing→retrieval r=0.14
- **OmniDocBench (2412.07626)** — existing parsing eval limitation
- **Chunk Twice Embed Once (2506.17277)** — chunking matters as much as embedding

### Related Work — Chunking (5)
- **Late Chunking (2409.04701, Jina)**
- **LumberChunker (2406.17526, EMNLP 2024)**
- **Meta-Chunking (2410.12788)**
- **MoC (2503.09600, ACL 2025)** — intrinsic metric proposer
- **Vision-Guided Chunking (2506.16035)** — multimodal chunking

### Related Work — Contrastive embeddings (3)
- **InSeNT / Context is Gold (2505.24782)** — closest prior, MUST cite
- **LMAR (2508.05672)** — joint embedding + chunking
- **BGE-M3 (2402.03216)** — foundation for our contrastive signal

### Related Work — Retrieval reward (3)
- **DPO (2305.18290)** — foundation
- **RPO (2501.13726)** — closest to RADP-A
- **Reward-RAG (2410.03780)** — retrieval reward training

### Related Work — Multimodal RAG (2)
- **ColPali (2407.01449, ICLR 2025)** — alternative paradigm
- **M-LongDoc (2411.06176, EMNLP 2025)** — naming clash, MUST cite

### Method / Baselines (2)
- **MinerU 2.5 (2509.22186)** — SOTA parsing baseline
- **ChunkRAG (2410.19572)** — post-retrieval filtering baseline

---

## 5. Refined Novelty Positioning

### 기존 framing (위험)
> "We discover that human-readability metrics don't predict retrieval performance, and propose retrieval-aware document parsing."

이 framing은 **EnterpriseDocBench, When Good OCR Is Not Enough에 의해 scooped 위험**.

### 권장 framing (방어 가능)

> "Recent benchmarks (OHRBench, EnterpriseDocBench, ConTEB) demonstrate that parsing quality and retrieval performance correlate weakly across enterprise and multilingual settings. **We propose RADP — the first method to fine-tune the parsing VLM itself with a retrieval objective, treating chunk boundaries and visual structure as a joint signal.** Unlike prior work that optimizes embeddings (InSeNT, LMAR), post-retrieval filtering (ChunkRAG), or readers (M-LongDoc, RPO), RADP operates earliest in the RAG pipeline. We also introduce RCPS, a task-grounded extrinsic metric complementary to intrinsic chunking metrics (MoC's Boundary Clarity)."

### 핵심 distinguishing claims

1. **"First parser fine-tuning with retrieval signal"** — 모든 선행 연구는 다른 layer
2. **"From visual input to retrieval-ready chunks in one forward"** — efficiency + integration
3. **"Korean government domain, KoGovDoc-RAG"** — empirical scope
4. **"RCPS: extrinsic, task-grounded chunking metric"** — MoC와 complementary

### Pipeline layer 표 (paper에 figure로)

| Layer | Component | Prior work that adapts this layer |
|-------|-----------|-----------------------------------|
| L1: Parsing (image→text) | VLM parser | **RADP (ours)** |
| L2: Chunking (text→chunks) | Chunker | LumberChunker, MoC, Meta-Chunking, Late Chunking |
| L3: Embedding (chunks→vectors) | Encoder | InSeNT, LMAR, BGE-M3 |
| L4: Retrieval (query→top-k) | Retriever | Reward-RAG |
| L5: Filtering (top-k→relevant) | Filter | ChunkRAG |
| L6: Generation (chunks→answer) | Reader/Gen | M-LongDoc (Retrieval-Aware Tuning), RPO, RAG-Reward |

→ **RADP는 L1을 처음 retrieval-aware로 학습**. 다른 layer와 모두 orthogonal하게 결합 가능.

---

## 6. Open Questions for Harrison

### Q1. EnterpriseDocBench (2604.26382)와 직접 비교 실험을 추가할까?
- **Pro**: 동일 framework로 r 측정, "we confirm and extend" framing 강력
- **Con**: 영어 enterprise data 추가 evaluation 부담
- **추천**: Section 5.5 ablation에 짧게 — 그들 결과 인용 + 우리 KoGovDoc r 값 비교 (실측만, 그들 데이터 재실행 X)

### Q2. InSeNT를 baseline에 포함하고 RADP-B + InSeNT 결합 실험을 할까?
- **Pro**: orthogonality 증명하면 가장 강력한 차별화
- **Con**: BGE-M3에 InSeNT 적용 별도 학습 필요 (~1일 GPU)
- **추천**: **반드시 포함**. Week 2 마지막 1일에 squeeze. 결합 시 추가 gain 보이면 critical reviewer 방어.

### Q3. "Retrieval-Aware Document Parsing"이라는 이름을 유지할까, 변경할까?
- M-LongDoc의 "Retrieval-Aware Tuning Framework"와 clash
- 옵션:
  - (A) 유지 + 부제목 차별화: "RADP: Retrieval-Aware Document Parsing via Chunk-Boundary Contrastive Learning"
  - (B) 변경: "PaRC: Parser with Retrieval-aware Contrastive learning" 등
- **추천**: A. 이름이 직관적이고 retrieval-aware 키워드 점유 중요.

### Q4. RADP-A (DPO)를 EMNLP 2026에 포함할까, ACL 2027로 미룰까?
- **포함 시 위험**: RPO와 가까워 보임 (parser DPO 차별화 필요), timeline 빠듯 (6/1~6/7), 학습 불안정 risk
- **미루는 시**: EMNLP 더 focused, RADP-B + RCPS + diagnostic으로 3-tier contribution 충분
- **추천**: **EMNLP는 RADP-B만, A는 short "preliminary results" 또는 future work**. ACL 2027 main에 정식. 이게 scooping risk와 timeline risk 동시 완화.

### Q5. KoGovDoc-RAG Q-A 생성 시 OHRBench 프로토콜 일부 차용?
- 그들 Q-A 생성 pattern (factoid + structural)을 reuse하면 비교 가능성 증가
- 단, 영어/중국어 → 한국어 transfer 필요
- **추천**: Yes — proposal Section 5.2의 50/30/20 비율을 그들 prior와 align되게 조정

### Q6. 우리도 OHRBench 일부 도메인 (Manual, Law)에 RADP cross-evaluation?
- **Pro**: generalization 증명, EMNLP reviewer 설득력
- **Con**: 영어 data, parser 학습 데이터 한국어 편중
- **추천**: zero-shot evaluation만 (RADP-B 한국어 학습 → OHRBench Manual에 zero-shot apply). 1일 작업.

### Q7. RCPS의 mathematical novelty를 더 강화할 필요?
- 현재 RCPS = mean(MRR@k over retrievers × k)는 단순 aggregate
- MoC의 Boundary Clarity와 비교 시 simple하게 보일 risk
- **추천**: RCPS에 **statistical significance test와 retriever-agnostic property 증명**을 추가. "RCPS is invariant to specific retriever choice within reasonable bounds" 같은 property.

---

## 7. 추가 검토 권장 (v2에서)

다음은 시간 부족으로 표면만 봄. v2 lit review에서 깊이 검토 필요:

- **TopoChunker (2603.18409)** — topology-aware chunking
- **FreeChunker (2510.20356)** — cross-granularity chunking
- **Beyond Chunk-Then-Embed (2602.16974)** — chunking taxonomy
- **Passage Segmentation (2501.09940)** — extractive QA chunking
- **MultiDocFusion (2604.12352)** — hierarchical industrial chunking
- **MMDocIR / REAL-MM-RAG / MHier-RAG** — multimodal RAG benchmarks
- **GLM-OCR / DocFusion / Doc-Researcher** — recent parsing technical reports

---

## 8. 결정 사항 권장 정리 (Harrison 회의용)

1. **Title 변경**: "RADP: Retrieval-Aware Document Parsing **via Chunk-Boundary Contrastive Learning**" (M-LongDoc과 차별화)
2. **Framing 변경**: "We discover" → "We confirm prior diagnostic findings (OHRBench, EnterpriseDocBench, ConTEB) and **provide the first training-time solution at the parser layer**"
3. **EMNLP 2026 scope 축소**: C1 (diagnostic + r 값 측정) + C2 (RCPS) + C3-B (RADP-B with InSeNT comparison). C3-A는 future work mention만.
4. **필수 추가 실험**:
   - InSeNT baseline + RADP-B 결합 ablation
   - MoC Boundary Clarity와 RCPS correlation 분석
   - LumberChunker / Meta-Chunking baseline
5. **Related Work 4-layer figure** 작성 (Section 5 layer 표를 figure로)
6. **OHRBench cross-domain zero-shot** 평가 (1일 작업, generalization 증명)
7. **RADP-A는 ACL 2027 main으로** — timeline + scooping risk 동시 완화

---

**문서 버전**: v1 (2026-05-17 초안)
**다음 업데이트**: Week 2 RADP-B 첫 학습 결과 + InSeNT ablation 결과 반영 v2
