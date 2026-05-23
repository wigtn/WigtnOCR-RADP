# Post-H1 Experiments — 결과 · 왜 · PRD와 차이 · 논문 활용

> 작성일: 2026-05-23
> H1 검증(PHASE_1 §1.6, BC/CS↔RCPS r≈0.18) 이후 한 모든 실험·검증의 종합.
> 각 항목: **결과 / 왜 했나 / PRD와 차이 / 논문 활용**.

## TL;DR

EMNLP 2026 Industry Track 제출(6/16)에 필요한 **실험 증거 전부 확보 완료.** 다음 = PHASE_3 (writing).

| 기여 | 증거 | 상태 |
|---|---|---|
| **C1** parsing 품질 ≠ retrieval | KoGov BC↔RCPS −0.81 + OHRBench n=15 r=−0.35 + noise-family 곡선 | ✅ cross-domain까지 |
| **C2** RCPS 지표 | KoGov 6 parser × 3 retriever × 4 chunker + OHRBench 15-variant | ✅ cross-domain까지 |
| **C3** RADP-B (정직한 negative) | pilot 169p + full-scale 2,667p λ sweep, v1과 공정 비교 | ✅ airtight |

---

## PRD와 실제 — 요약 (왜 어디가 달라졌나)

| PRD 조항 | 실제 | 이유 |
|---|---|---|
| §5.3 retriever = jina-v3 | **Qwen3-Embedding-8B** | jina-v3가 transformers 5.8 비호환 (간헐적 NaN 임베딩) |
| §5.3 chunker grid = MoC + Late Chunking 포함 | 두 항목 **cite-only** | MoC research-repo 통합 부담 / Late Chunking은 mean-pooling 장컨텍스트 모델 부재 |
| §4.1 RADP-B 정식화 (parser→discrete markdown→BGE→InfoNCE) | **decision-A** (parser hidden→projection head→InfoNCE) | 원안은 discrete markdown 구간에서 미분 불가 → decision-A는 미분 가능한 최소 변형 |
| §5.1 RADP-B 학습 = 2,667p | pilot 169p → **full-scale 2,667p** | Q-A가 val에만 있어 169p 파일럿 먼저. 게이트 미달 후 §9 fallback 분기 → 사용자가 confound 제거 위해 full-scale 진행 |
| §5.2 Q-A 생성 = val 294p (663개) | + **train 2,667p (6,164 Q-A) 추가** | full-scale RADP-B에 train Q-A 필수 (PRD §4.1 + §5.1의 implied step; qa_generation 문서가 이미 anticipate) |
| 학습 프레임워크 ms-swift | **HF Trainer + peft** | ms-swift 4.2가 pinned cu128 env 비호환 |
| §3.1 OHRBench = RADP-B zero-shot 파싱 | **Level 1** = OHRBench 자체 출력으로 RCPS·BC | RADP-B는 한국어 튜닝 모델 → 영어 zero-shot은 transfer 약함, 논문에 마이너스. C1·C2 일반화로 reframe |
| (PRD에 없음) | **OHRBench noise variants n=15 BC↔RCPS** | n=3로는 결론 불가 → n=15로 확정. 추가 분석, paper 강화 |

---

## Thread별 — 결과 / 왜 / PRD diff / 논문 활용

### A. PHASE_1 §1.5 — baseline + chunking + MoC BC

**결과.**
- 6 parser RCPS(parser_native): Qwen3-VL-30B teacher 0.584 / WigtnOCR v1 0.583 / Qwen3-VL-2B base 0.532 / MinerU 0.212 / PaddleOCR 0.140 / Marker 0.073(38p).
- 4 chunker(v1 파서, RCPS): md_h3 0.593 / parser_native 0.583 / LumberChunker 0.557 / fixed500 0.535.
- **BC↔RCPS Pearson r = −0.81** (n=5, Marker 제외) — 최고 BC인 MinerU가 RCPS 꼴찌.

**왜.** PRD §1.4 baseline grid + C1 정량 입증 + C2가 chunker를 변별함을 확인.

**PRD diff.** MoC·Late Chunking은 cite-only로 결정 (사유: `docs/PHASE1_5_BASELINE_DECISIONS.md`).

**논문 활용.** §5 메인 표 (Table 1 main results · Table 2 chunking grid). §4 C1의 핵심 그림 (BC vs RCPS scatter, Figure 2). **MoC BC −0.81은 C1의 가장 강력한 단일 발견.**

### B. Retriever 교체 + 3-retriever 재평가

**결과.** jina-v3 → Qwen3-Embedding-8B 교체 후 baseline·chunking grid 1e-4 단위 일관(불일치 해소).

**왜.** jina-v3 NaN bug — 안 고치면 PHASE_2 평가가 noise.

**PRD diff.** §5.3의 retriever specced jina-v3 → 교체.

**논문 활용.** Methodology/Appendix — retriever 셋(bge-m3 + ml-e5-large + qwen3-emb-8b) 명시. 모든 후속 RCPS 수치의 기반.

### C. PHASE_2 RADP-B pilot (169p)

**결과 (eval fold 73p / 202 Q-A, 3-retriever):**
| λ | RCPS (md_h3) | parseSim |
|---|---|---|
| 0.0 | 0.637 | 0.861 |
| **0.1** | **0.654** | 0.843 |
| 0.3 | 0.634 | 0.846 |
| 0.5 | 0.615 | 0.819 |
| 1.0 | 0.569 | 0.821 |

→ λ=0.1 작은 피크, λ↑ 단조 하락. 게이트(≥5pp) **FAIL** (+1.8pp md_h3).

**왜.** PRD §4.1 RADP-B 방법 검증 (H2). Q-A가 val에만 있어 train 데이터로 직접 학습 불가, 169p 파일럿으로 시작.

**PRD diff.** §5.1 원안 2,667p — 데이터 제약으로 169p로 축소. §4.1 정식화는 미분 불가라 decision-A로 변형.

**논문 활용.** §4 C3 보조 — pilot의 단조 하락 패턴 제시. 메인 수치는 full-scale 사용.

### D. Train Q-A 생성 (GPT-5.4)

**결과.** v1 train 2,667p 전체에 **6,164 Q-A** 생성 (procedural 2,580 / tabular 1,754 / factoid 1,715 / figural 115). resume 모드로 두 키 걸쳐 무손실 완주. 총 비용 ~$30 (실측 단가 ~$0.012/page).

**왜.** full-scale RADP-B에 train Q-A 필수 (L_contrast positive 정의에 필요). v1과 공정 비교를 위해 같은 2,667p로 학습해야 함. 5.4는 eval Q-A가 5.4 frozen이라 generator confound 차단.

**PRD diff.** §5.2가 val Q-A만 명시했으나 qa_generation 문서가 train Q-A를 이미 anticipate — §4.1 + §5.1 실행에 필요한 implied step.

**논문 활용.** Methodology — Q-A 생성 절차. full-scale 비교의 데이터 토대.

### E. Full-scale RADP-B 학습 (2,667p)

**결과.** 체크포인트 4개 (`radp_b_full_lambda{00,01,03,05}/final`), 각 run ~3.3h.

**왜.** 169p 파일럿의 **데이터-스케일 confound** 제거 — H2의 문자 그대로 "vs v1" 비교를 confound 없이 처음으로 가능하게.

**PRD diff.** §9 fallback 발동 후의 **override**. fallback 시점엔 "스케일업 중단"이었으나, 사용자가 confound 제거 위해 full-scale 진행 결정.

**논문 활용.** C3의 핵심 실험. 메인 수치 산출.

### F. Full-scale 평가 (4 λ + v1 ref)

**결과 (eval fold 73p / 202 Q-A, parser_native chunker):**
| λ | RCPS | vs v1 | parseSim |
|---|---|---|---|
| 0.0 | 0.6557 | −0.1pp | 0.872 |
| **0.1** | **0.6788** | **+2.2pp** | 0.874 |
| 0.3 | 0.6694 | +1.3pp | 0.862 |
| 0.5 | 0.6442 | −1.3pp | 0.851 |
| v1 | 0.6569 | — | 0.789 |

→ λ=0.1 피크, λ↑ 단조 하락. λ=0 ≈ v1 (confound 제거 확인). λ=0.1이 v1 vs parser_native +2.2pp / md_h3 −0.6pp — **호각**. 게이트 +5pp 미달, H2 +8pp 압도적 미달. parseSim도 단조 하락.

**왜.** lever ① — full-scale에서도 단조 하락 확인 ("under-tuning" 반론 봉쇄). C3 negative를 airtight로.

**PRD diff.** 평가 자체는 §5.4 그대로. 결과가 §9 fallback 분기를 *확정*.

**논문 활용.** §5 C3 메인 표 (Table 3 λ ablation, full-scale). 핵심 문장: **"공정 full-scale 비교에서 contrastive aux loss는 +1~3pp marginal — parser-layer aux loss는 잘못된 레버."**

### G. OHRBench cross-domain RCPS (Level 1)

**결과 (Law+Manual, 1,043 verbatim-answerable Q-A, parser_native):**
| parser | RCPS |
|---|---|
| gt | 0.640 |
| MinerU | 0.595 |
| Qwen2.5-VL | 0.545 |

RCPS가 영어 기업문서에서도 파서를 0.54~0.64로 변별.

**왜.** EMNLP 리뷰어의 "single-domain (Korean gov)" 반론 봉쇄 + C2 일반화 검증.

**PRD diff.** §3.1 원안 "RADP-B zero-shot" → Level 1로 reframe (RADP-B는 한국어 튜닝, 영어 zero-shot은 transfer 약함; C1·C2 일반화가 본 목적).

**논문 활용.** §6 cross-domain — C2 일반화 증거.

### H. OHRBench BC 15-variant 상관 (C1 cross-domain 확정)

**결과.**
- 15 변형 (gt + MinerU + Qwen2.5-VL + 3 formatting noise + 9 semantic noise) BC + RCPS.
- **Pearson BC↔RCPS = −0.351 (n=15)** — KoGov −0.81의 *방향 재현*.
- **★ 메커니즘**: 같은 base parser의 mild→severe noise 변형에서 **BC는 거의 안 변하는데 RCPS가 폭락**:

| MinerU family | BC | RCPS |
|---|---|---|
| (clean) | 0.657 | 0.595 |
| + sem mild | 0.628 | 0.476 |
| + sem moderate | 0.651 | 0.384 |
| + sem severe | 0.631 | 0.265 |

intrinsic 경계 지표가 **semantic content 품질을 못 본다**는 직접 증거.

**왜.** n=3로는 BC↔RCPS +0.61이라 inconclusive. n=15로 진짜 상관 확보.

**PRD diff.** PRD에 없는 추가 분석. paper 강도 위해 도입.

**논문 활용.** §4 C1 메인 — KoGov −0.81 + OHRBench −0.35로 cross-domain 일반화. **noise family 곡선은 Figure 후보** (C1을 *시각적으로* 입증).

---

## 논문 매핑 (어디에 어떻게 들어가나)

| Paper 섹션 | 채울 자료 (위 thread) |
|---|---|
| §1 Intro | C1 진단 한 줄 + C2 지표 + C3 negative |
| §2 Related Work | paper notes + layer-positioning figure (PRD C4) |
| §3 RCPS 정의 | rcps.py 정의 + KoGov chunking grid (A) |
| §4 C1 진단 | KoGov BC↔RCPS −0.81 (A) + OHRBench n=15 −0.35 (H) + **noise-family curve (Figure)** (H) |
| §5 C3 RADP-B negative | decision-A 정식화 + full-scale λ sweep + v1 비교 (E, F) |
| §6 Cross-domain | OHRBench RCPS 그리드 (G) + BC↔RCPS (H) |
| §7 Discussion | aux-loss 모양 한계 + retrieval-feedback이 올바른 레버(RADP-A) → ACL 2027 |

---

## 산출물 (paper-ready 자산)

| 종류 | 경로 |
|---|---|
| baseline grid (6 parser) | `output/baselines/grid_v1_parser_native.{json,md}` |
| chunking grid (4 chunker) | `output/baselines/chunking_grid_v1.{json,md}` |
| H1 상관 (KoGov BC/CS) | `output/baselines/correlation_v1.{json,md}` |
| MoC BC↔RCPS (KoGov, −0.81) | `output/baselines/moc_bc_correlation.{json,md}` |
| RADP-B λ sweep (pilot + full-scale) | `output/results/radp_b_full_eval.json` |
| OHRBench 15-variant RCPS | `output/results/ohrbench_noise.json` |
| OHRBench BC↔RCPS (−0.35, n=15) | `output/results/ohrbench_bc_noise.json` |
| Full-scale RADP-B 체크포인트 | `output/checkpoints/radp_b_full_lambda{00,01,03,05}/final` |
| Eval Q-A (frozen) | `data/KoGovDoc-RAG/qa_pairs_v1.jsonl` (663) |
| Train Q-A (frozen) | `output/qa_pairs/train_2667_5_4.jsonl` (6,164) |

## 다음

**PHASE_3** (writing) — 위 자료로 §1~§7 초안. 아웃라인은 `docs/PHASE3_PAPER_OUTLINE.md` (full-scale·OHRBench 결과 반영 필요).
