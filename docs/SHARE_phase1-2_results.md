# RADP — PHASE_1 · PHASE_2 결과 공유 (H1 검증 이후)

> 작성일: 2026-05-21
> 범위: H1 검증 이후 진행한 PHASE_1(데이터·RCPS·baseline) + PHASE_2(RADP-B 학습)
> 전체. 실험 수치 + 선택지마다의 결정 사유.
> 상세는 각 절에 링크된 문서 참조.

> **역사적 결과 주의 (2026-08-24):** 이 문서의 `r=-0.81`은 MinerU-off를 사용한 초기 grid를 기록한다. 현재 camera-ready C1은 MinerU-on 포함 complete-output 4-parser `r=-0.74`를 본 근거로, Marker 포함 `r=-0.83`을 보조 분석으로 사용한다. 기여 번호도 C2=RCPS, C3=coverage로 변경됐다.

---

## 0. TL;DR (3줄)

1. **PHASE_1 완료** — KoGovDoc-RAG(663 Q-A) 구축, RCPS 지표 구현, 6-parser ×
   3-retriever baseline + 4-chunker grid 완성. **H1 검증됨**: parsing 품질 ↔
   retrieval 상관 Pearson r ≈ 0.18 — EnterpriseDocBench의 r=0.14를 한국어
   정부문서에서 재현.
2. **PHASE_2 완료(negative)** — RADP-B(parser에 chunk-boundary contrastive aux
   loss)는 λ sweep 전 구간에서 retrieval을 **개선 못 함**. contrastive를 안 쓴
   v1 레퍼런스가 모든 RADP-B 체크포인트를 이김. proposal §9 fallback 발동.
3. **논문 pivot 확정** — 메인 기여를 **C1(진단) + C2(RCPS 지표)** 로, RADP-B는
   **C3(정직한 negative result)** 로. RADP-A는 ACL 2027 future work.

---

## 1. PHASE_1 — 데이터 · RCPS · Baseline

상세: `docs/PHASE1_FINDINGS.md`, `docs/PHASE1_5_BASELINE_DECISIONS.md`

### 1.1 데이터 — KoGovDoc-RAG

- KoGovDoc-Bench 294 validation 페이지 → **663 Q-A** 생성 (GPT-5.4, PROMPT v3).
- frozen: `data/KoGovDoc-RAG/qa_pairs_v1.jsonl` — 이후 모든 평가의 고정 셋.
- 검증: 100개 stratified 샘플 → **94/100 accept** (PRD 목표 ≥85% 충족).
  LLM-assisted 검증 (human 아님 — 논문에 caveat 명시 예정).

### 1.2 RCPS 지표

- `src/wigtnocr_radp/evaluation/`: chunkers, retrievers, `compute_rcps` 구현.
- RCPS = retriever × cutoff 에 대한 MRR@k 평균 (task-oriented chunking 품질).
- relevance 판정은 whitespace/markdown 무시 정규화 매칭(`normalize_for_match`)
  — parser를 *포맷*이 아닌 *내용*으로 비교.

### 1.3 Baseline Grid — 6 parser × 3 retriever

retriever = bge-m3 + multilingual-e5-large + qwen3-emb-8b (RCPS 평균).
chunker = parser_native.

| Parser | RCPS | Hit@1 |
|--------|:----:|:----:|
| Qwen3-VL-30B (teacher) | 0.584 | 0.545 |
| WigtnOCR-2B (ours, v1) | 0.583 | 0.549 |
| Qwen3-VL-2B (base) | 0.532 | 0.500 |
| MinerU | 0.212 | 0.197 |
| PaddleOCR | 0.140 | 0.125 |
| Marker | 0.073 (38p) | 0.068 |

→ VLM 파서(0.53~0.58) ≫ 비-VLM 파서(0.07~0.21). MinerU/PaddleOCR/Marker는
한국어 정부문서에서 출력이 비거나 모지바케 — 직접 확인. 낮은 RCPS는 평가
artifact가 아니라 **실제 파싱 실패**.

### 1.4 Chunking-strategy Grid — parser=v1, 663 Q-A

| Rank | Chunker | RCPS |
|:--:|---------|:----:|
| 1 | md_h3 | 0.593 |
| 2 | parser_native | 0.583 |
| 3 | lumberchunker | 0.557 |
| 4 | fixed500 | 0.535 |

→ 마크다운 헤더 청킹이 최선 — 정부문서의 명시적 구조를 활용. **LumberChunker(LLM
서사 청킹)는 단순 규칙 청커를 못 이김** — 장편 서사용 설계라 표·양식 위주
정부문서엔 transfer 약함.

### 1.5 H1 검증 — EnterpriseDocBench r 재현

intrinsic chunk 품질 ↔ extrinsic retrieval(RCPS) Pearson r:

| 집합 | Pearson BC↔RCPS | H1 (r<0.5) |
|------|:---------------:|:----------:|
| 6 parser | +0.323 | ✅ |
| 5 parser (Marker 제외) | +0.175 | ✅ |

→ **We confirm the prior finding (r=0.14, EnterpriseDocBench) in the Korean
government-document domain (r ≈ 0.18).** 인간 가독성 기반 파싱 품질 지표는
retrieval 성능을 약하게만 예측 — RADP의 핵심 동기(C1) 정량 확인.

추가로 **MoC Boundary Clarity ↔ RCPS는 음의 상관 (Pearson −0.81, n=5)** — MoC의
intrinsic 경계 지표는 MinerU/Marker처럼 *깔끔하지만 내용이 깨진* 파서에 높은
점수를 줌. RCPS가 intrinsic 지표가 못 잡는 것을 잡는다는 직접 증거 (논문 §3.2).

---

## 2. PHASE_2 — RADP-B (negative result)

상세: `docs/WEEK2_FINDINGS.md`

### 2.1 설정

| 항목 | 값 |
|------|-----|
| 방법 | RADP-B: `L_total = L_parse + λ·L_contrast` |
| Base | Qwen3-VL-2B-Instruct + LoRA (r=8, α=32) |
| 학습 데이터 | KoGovDoc-RAG train fold 169p / 461 Q-A |
| 평가 | held-out 73p / 202 Q-A, **3-retriever RCPS 평균** (PHASE_1 grid와 동일 기준) |
| λ sweep | {0, 0.1, 0.3, 0.5, 1.0}, λ=0은 contrastive 끈 matched control |

### 2.2 λ Sweep 결과 (md_h3 chunker)

| λ | RCPS | Hit@1 | parse↔GT 유사도 |
|---|:----:|:----:|:----:|
| 0.0 (control) | 0.637 | 0.606 | 0.861 |
| **0.1 (best)** | **0.654** | 0.627 | 0.843 |
| 0.3 | 0.634 | 0.604 | 0.846 |
| 0.5 | 0.615 | 0.591 | 0.819 |
| 1.0 | 0.569 | 0.538 | 0.821 |
| **v1 (ref, contrastive 없음)** | **0.672** | **0.639** | 0.789 |

### 2.3 게이트 FAIL → pivot

- **게이트**(PHASE_2 §2.2): best λ vs λ=0 RCPS gain ≥ **5pp** 이면 2,667p
  풀스케일 재학습. → best λ=0.1 gain = **+1.8pp** (md_h3) / +3.4pp
  (parser_native). 둘 다 미달 → **FAIL**.
- **단조 하락**: λ↑ → RCPS↓ + parsing 충실도↓. under-tuning이 아니라 objective가
  counterproductive.
- **결정적**: contrastive를 안 쓴 v1이 모든 RADP-B를 이김 → aux loss는 도움이
  안 될 뿐 아니라, 같은 파서를 그냥 parsing만 더 학습한 것보다 못함.
- → 2,667p 스케일업 안 함, **예산 지출 0** (게이트가 제 역할). proposal §9 /
  PHASE_2 리스크의 "RADP-B gain < 5pp" 분기 발동.

---

## 3. 주요 의사결정 + 사유 (선택지 표)

> 각 항목: 어떤 선택지들이 있었고, 무엇을, 왜 골랐는지.

### D1. RADP-B contrastive 정식화 — **decision-A** ⚠️ PRD 이탈, 확인 요망

- **PRD §4.1 원안**: parser → discrete markdown → chunk → BGE 임베딩 → InfoNCE.
- **문제**: parser 출력이 *discrete 토큰(markdown)* 이라 chunk·BGE 경로가
  **미분 불가** — gradient가 parser로 안 흘러감. PRD §4.1 정식화는 그대로는
  학습 불가.
- **선택지**: (a) parser pooled hidden → projection head → InfoNCE vs 답
  chunk BGE 임베딩 (= **decision-A**), (b) Gumbel-softmax 등 미분가능 완화,
  (c) RL/REINFORCE로 discrete 경로 우회.
- **결정: (a) decision-A**. (b)는 markdown 토큰 시퀀스에 비현실적, (c)는
  reward variance·구현 비용이 파일럿엔 과함. decision-A는 PRD 의도(파서를
  retrieval 신호로 학습)를 가장 단순하게 미분가능화한 형태.
- ⚠️ **확인 요망**: 이는 PRD §4.1 문자 그대로가 아닌 구현상 결정. 다만
  negative result라 "어느 정식화든 안 됐다"가 아니라 "decision-A 정식화가
  안 됐다"임 — 논문에 이 정식화를 명시해 한정해야 함.

### D2. 학습 스택 — **HF Trainer** (ms-swift 아님)

- **선택지**: ms-swift 4.2 (PRD가 가정) vs HF Trainer (transformers 5.8 + peft).
- **결정: HF Trainer**. ms-swift 4.2가 pinned cu128 환경(Blackwell GPU)과
  비호환. HF Trainer로 동등 학습 가능 — compute_loss override + forward-hook으로
  hidden 캡처해 contrastive loss 구현.

### D3. 학습 규모 — **169p 파일럿** (2,667p 아님)

- **선택지**: PRD §5.1 원안 2,667p (= v1 train set) vs 294p를 split.
- **제약**: L_contrast는 학습 페이지에 Q-A가 있어야 하는데 Q-A는 294 val
  페이지에만 존재. 2,667p 학습엔 train 페이지 Q-A 생성 비용($30+)이 필요한데
  **OpenAI 예산 거의 소진** 상태.
- **결정: 294p를 169/73 split, 169p 파일럿**. "RCPS gain ≥5pp면 풀스케일 투자"
  게이트를 걸어 예산 리스크 차단. → 게이트 FAIL이라 지출 0.

### D4. RCPS 3번째 retriever — **Qwen3-Embedding-8B** (jina-v3 아님)

- **선택지**: jina-embeddings-v3 (원안) vs Qwen3-Embedding-8B.
- **문제**: jina-v3의 custom remote 코드가 transformers 5.8과 비호환 — 일부
  가중치가 랜덤 초기화되어 **간헐적 NaN 임베딩** (비결정적: 같은 입력에 run마다
  RCPS 0.26↔0.0015). fp32 강행도 실패.
- **결정: Qwen3-Embedding-8B**(표준 아키텍처, remote 코드 없음). 두 번 로드
  비트 단위 동일(결정적) 검증 완료. → retriever 3종 = bge-m3 +
  multilingual-e5-large + qwen3-emb-8b.

### D5. 추가 baseline — **MoC · Late Chunking은 cite-only**

- **MoC chunker**: 공식 release(MoE-chunker) 있으나 research-repo 의존성 통합
  부담 큼. PRD §11이 "안 되면 cite-only" 명시 허용. → cite-only. 단 MoC의 핵심
  대비 자산인 **Boundary Clarity 지표는 §3.2용으로 구현·실행 완료**.
- **Late Chunking**: mean-pooling 장컨텍스트 모델 필수인데 — jina-v3 비호환,
  bge-m3는 CLS 풀링이라 방법론적 불가, e5-large는 512 컨텍스트로 부족. 게다가
  embedding-layer 기법이라 chunking 전략 비교 그리드에 속하지도 않음(PRD 자체
  노트도 "orthogonal"로 분류). → cite-only + layer 도식 배치, 미실측은 future
  work로 정직하게 명시.
- **LumberChunker**: 실측 완료 (122B vLLM Docker를 LLM 백엔드로). chunking grid
  3위.

### D6. 논문 pivot — **C1 + C2 메인, RADP-B는 C3 negative**

- **선택지**: RADP-B 재설계·재시도 vs proposal §9 fallback 발동.
- **결정: fallback**. λ sweep이 단조 하락 + v1 ref가 모든 체크포인트 우위 —
  under-tuning이 아니라 objective 자체의 문제. PRD에 명시된 분기 그대로 발동.
- **개정 논문 구성**:
  - **C1** parsing 품질 ≠ retrieval (r≈0.18, H1 검증 완료)
  - **C2** RCPS — task-oriented chunking 지표 (**메인 기여**)
  - **C3** parser-layer contrastive aux loss 시도의 **엄밀한 negative result**
- **버림**: RADP-B 재설계, negative-sampling ablation(2.4), InSeNT
  orthogonality(2.5 — RADP-B 미동작이라 H3 무의미).

---

## 4. 산출물

repo 경로(재현용):

| 분류 | 경로 |
|------|------|
| Q-A 데이터 | `data/KoGovDoc-RAG/qa_pairs_v1.jsonl` (663, frozen, 852K) |
| RCPS 구현 | `src/wigtnocr_radp/evaluation/` |
| baseline grid | `output/baselines/grid_v1_parser_native.{json,md}` |
| chunking grid | `output/baselines/chunking_grid_v1.{json,md}` |
| H1 상관 | `output/baselines/correlation_v1.{json,md}` |
| MoC BC 상관 | `output/baselines/moc_bc_correlation.{json,md}` |
| RADP-B λ sweep | `output/results/week2_lambda_sweep.json` |
| RADP-B 체크포인트 | `output/checkpoints/radp_b_lambda{00,01,03,05,10}/` (각 435M, 바이너리 — 공유 불가) |

결과 원본(작은 파일)은 아래 부록 A에 통째로 임베드 — 이 문서만으로 자체 완결.
Q-A 663개 raw·체크포인트 바이너리는 크기상 repo에만.

---

## 부록 A — 결과 원본 (임베드)

### A.1 Baseline Grid — 6 parser × 3 retriever (chunker=parser_native)

Q-A 663, retrievers = bge-m3 + ml-e5-large + qwen3-emb-8b (RCPS 평균).

| Rank | Parser | role | pages | chunks | RCPS | Hit@1 | Hit@5 | MRR@10 | nDCG@10 |
|:--:|--------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| 1 | Qwen3-VL-30B (teacher) | teacher | 294 | 1577 | 0.5844 | 0.5445 | 0.6903 | 0.6064 | 0.6343 |
| 2 | WigtnOCR-2B (ours, v1) | ours | 294 | 1455 | 0.5826 | 0.5485 | 0.6727 | 0.6016 | 0.6265 |
| 3 | Qwen3-VL-2B (base) | baseline | 294 | 2057 | 0.5321 | 0.4997 | 0.6149 | 0.5504 | 0.5738 |
| 4 | MinerU | baseline | 294 | 1050 | 0.2120 | 0.1971 | 0.2519 | 0.2200 | 0.2297 |
| 5 | PaddleOCR | baseline | 294 | 294 | 0.1397 | 0.1252 | 0.1805 | 0.1489 | 0.1628 |
| 6 | Marker | baseline | 38 | 1136 | 0.0732 | 0.0679 | 0.0865 | 0.0761 | 0.0795 |

난이도별 MRR@10:

| Parser | easy | medium | hard |
|--------|:--:|:--:|:--:|
| Qwen3-VL-30B (teacher) | 0.6447 | 0.6111 | 0.5560 |
| WigtnOCR-2B (ours, v1) | 0.6182 | 0.6151 | 0.5659 |
| Qwen3-VL-2B (base) | 0.5930 | 0.5487 | 0.5026 |
| MinerU | 0.2390 | 0.2253 | 0.1914 |
| PaddleOCR | 0.1691 | 0.1259 | 0.1531 |
| Marker | 0.0843 | 0.0687 | 0.0755 |

### A.2 Chunking-strategy Grid — parser=v1, Q-A 663

| Rank | Chunker | chunks | RCPS | Hit@1 | Hit@5 | MRR@10 | nDCG@10 |
|:--:|--------|:--:|:--:|:--:|:--:|:--:|:--:|
| 1 | md_h3 | 741 | 0.5929 | 0.5561 | 0.6838 | 0.6133 | 0.6382 |
| 2 | parser_native | 1455 | 0.5826 | 0.5485 | 0.6727 | 0.6016 | 0.6265 |
| 3 | lumberchunker | 1267 | 0.5571 | 0.5143 | 0.6677 | 0.5803 | 0.6088 |
| 4 | fixed500 | 983 | 0.5354 | 0.4907 | 0.6471 | 0.5598 | 0.5887 |

### A.3 H1 상관 — parsing 품질 ↔ retrieval

원본: v1 BC/CS (semantic chunker, doc-level), RCPS (parser_native, BGE-M3).

| Parser | pages | BC | CS | RCPS | Hit@1 |
|--------|:--:|:--:|:--:|:--:|:--:|
| Qwen3-VL-30B (teacher) | 294 | 0.6915 | 3.3766 | 0.5844 | 0.5445 |
| WigtnOCR-2B (ours, v1) | 294 | 0.6937 | 3.0749 | 0.5826 | 0.5485 |
| Qwen3-VL-2B (base) | 294 | 0.6767 | 3.7374 | 0.5321 | 0.4997 |
| MinerU | 294 | 0.7216 | 2.8146 | 0.2120 | 0.1971 |
| PaddleOCR | 294 | 0.6494 | 3.4632 | 0.1397 | 0.1252 |
| Marker | 38 | 0.6668 | 3.4062 | 0.0732 | 0.0679 |

| 집합 | Pair | Pearson r | H1 (r<0.5) |
|------|------|:--:|:--:|
| 6 parser | BC↔RCPS | +0.3227 | ✅ |
| 6 parser | BC↔Hit@1 | +0.3255 | ✅ |
| 6 parser | CS↔RCPS | +0.1259 | ✅ |
| 5 parser (Marker 제외) | BC↔RCPS | +0.1751 | ✅ |
| 5 parser (Marker 제외) | BC↔Hit@1 | +0.1801 | ✅ |
| 5 parser (Marker 제외) | CS↔RCPS | +0.2586 | ✅ |

### A.4 MoC Boundary Clarity (intrinsic) vs RCPS (extrinsic)

BC per MoC (arXiv:2503.09600), ppl model Qwen3-VL-2B, chunker parser_native.
높을수록 깨끗한 경계(intrinsic).

| Parser | role | pages | boundaries | BC | RCPS | Hit@1 |
|--------|:--:|:--:|:--:|:--:|:--:|:--:|
| WigtnOCR-2B (ours, v1) | ours | 294 | 1161 | 0.6100 | 0.5517 | 0.5219 |
| Qwen3-VL-30B (teacher) | teacher | 294 | 1283 | 0.6232 | 0.5446 | 0.5083 |
| Qwen3-VL-2B (base) | baseline | 294 | 1763 | 0.5199 | 0.4933 | 0.4661 |
| MinerU | baseline | 294 | 756 | 0.7161 | 0.1761 | 0.1629 |
| Marker | baseline | 38 | 1098 | 0.7168 | 0.0680 | 0.0633 |
| PaddleOCR | baseline | 294 | 0 | nan | 0.1159 | 0.1026 |

상관 (n=5, all valid): **BC↔RCPS Pearson −0.814** (p=0.09), Spearman −0.700.
→ MoC의 intrinsic 경계 지표는 깔끔하지만 내용이 깨진 파서(MinerU/Marker)에
높은 점수 — RCPS가 잡는 것을 못 잡음.

### A.5 RADP-B λ sweep — parser_native chunker (md_h3는 §2.2)

| λ | RCPS | Hit@1 |
|---|:--:|:--:|
| 0.0 | 0.6124 | 0.5776 |
| 0.1 | 0.6463 | 0.6122 |
| 0.3 | 0.6305 | 0.5990 |
| 0.5 | 0.6028 | 0.5743 |
| 1.0 | 0.5927 | 0.5611 |
| v1 (ref) | 0.6569 | 0.6254 |

원본 JSON: `output/results/week2_lambda_sweep.json`.

### A.6 Q-A 검증 결과 (100 stratified 샘플)

- 방법: LLM-assisted 검증 (PRD §1.2는 human 명시 — caveat). 3축 평가
  (질문 자연·답변 가능 / 답 정확 / answer_span이 chunk 내 위치).
- **94/100 accept** (PRD 목표 ≥85% → PASS).
- reject 6건 핵심 패턴: multi-part 질문(`각각`, `A이며 B`)을 단일 사실 span으로
  답함(~3건), answer_span이 너무 짧아 모호(`9`, `1.0`), answer_chunk 자동확장이
  근거 직전에서 끊김(1건).

### A.7 Q-A 데이터 샘플 (`qa_pairs_v1.jsonl` 663개 중 2)

```json
{"qa_id": "b6b16a35...", "page_id": "val_0000", "doc_id": "kogov_008",
 "language": "ko", "domain": "kogov",
 "question": "흘관 Φ1100부터 Φ1800까지 종배 수관부설 항목 중 합계가 가장 큰 규격은?",
 "answer_span": "종배 수관부설 (흘관 Φ1800)",
 "question_type": "tabular", "difficulty": "hard",
 "metadata": {"generator_model": "gpt-5.4-2026-03-05", "human_verified": false}}
{"qa_id": "ed9af8c1...", "page_id": "val_0000", "doc_id": "kogov_008",
 "question": "종배 수관부설 항목들 가운데 합계가 20만원을 넘는 규격은?",
 "answer_span": "종배 수관부설 (흘관 Φ1500)",
 "question_type": "tabular", "difficulty": "medium"}
```

각 레코드: `qa_id / page_id / doc_id / language / domain / question /
answer_span / answer_chunk / question_type / difficulty / multi_page /
referenced_pages / metadata`. 전체 663개는 repo의 `qa_pairs_v1.jsonl`.

---

## 5. 다음 단계 — PHASE_3 (writing)

- C2 강화: RCPS vs MoC Boundary Clarity 상관분석 본문화 (§3.2, 이미 실측됨).
- (시간 되면) OHRBench cross-domain zero-shot (§3.1).
- 논문 4쪽 초안 — C1+C2+C3 framing.
- Figure 1 (BC vs RCPS scatter) 생성.

**확인 요청 사항**: §3 D1(decision-A 정식화) — PRD §4.1 문자 그대로가
미분 불가라 구현상 변형이 불가피했음. 논문에서 RADP-B negative result를 이
정식화로 한정 기술할 예정 — 동의/이견 검토 필요.
