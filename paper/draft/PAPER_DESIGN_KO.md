# 논문 설계도 (한글 blueprint) — WigtnOCR-RADP / RCPS

> 목적: 영어 본문(`paper.md`)을 뜯어보지 않고도 **각 섹션·표·그림이 무엇을·왜 보여주는지** 한글로 검증하기 위한 source-of-truth. 본문은 이 설계에 맞춰 정리한다.
> 기준 시점: 2026-06-07, paper v0.7 (commit `50fc02e` 이후). 숫자는 전부 실험파일 검증본.

---

## 0. 메타

- **타깃**: EMNLP 2026 Industry Track, 본문 **6쪽**(refs·Limitations·Appendix 미포함), 마감 2026-06-16
- **제목**: *RCPS: Choosing Document Parsers by Retrieval, Not by Appearance — Diagnosing the Parsing–Retrieval Gap*
- **한 줄 요지**: **"제일 깨끗해 보이는 파서가 제일 잘 찾는 retriever는 아니다 (오히려 하위권)."** — BC 같은 사람 가독성 지표가 retrieval을 *예측 못 함*(반상관). → **retrieval로 파서/청커를 진단·선택(RCPS)**하라. 파서 학습은 작고 정직한 보조 lever.
  - ⚠️ **"cleanest = 꼴찌"는 과장 (쓰지 말 것)**: MinerU Hit@1 0.197 = 6개 중 4등(꼴찌는 38p Marker 0.068·PaddleOCR 0.125). 정확한 건 "cleanest = best 아님 = 하위권, VLM 파서보다 한참 아래". 현재 abstract/§1/§5가 "worst"로 과장 → 정정 대상.
- **명칭 확정**: 우리 프로덕션 파서 = **Prod** (구 "v1", fine-tuned 2B). base=Qwen3-VL-2B(원본), teacher=Qwen3-VL-30B. RADP-DPO 마일스톤=R1/R2/R3. 권장 학습 lever=**RADP-Distill**.

---

## 1. 기여 4개 (C1–C4)

| | 기여 | 핵심 증거 | 강도 |
|---|---|---|---|
| **C1** | parsing–retrieval **disconnect** + 메커니즘 | BC↔RCPS **r=−0.81**(n=5) · Hit@1 **2.8×**(0.197→0.549) · noise 시 BC 평탄/RCPS −51% | **헤드라인, 가장 셈** |
| **C2** | retriever-free **coverage diagnostic** | absent **20.2%**(파서 탓) vs split 0–2%(청커 탓), 8 chunker 일정 → 규칙 | 강함, 실행가능 |
| **C3** | **RCPS 프로토콜** (파서+청커 선택) | RCPS≠단순 MRR ablation(retriever 평균이 1위 뒤집음) | 제안의 핵심 |
| **C4** | 파서 학습 = bounded lever (정직한 negative 포함) | RADP-Distill OHR Hit@5 **+1.22**, RADP-DPO +0.85; reward 불필요 | 보조, bounded |

---

## 2. 섹션 구조 (본문 6쪽)

- **§1 Intro** — disconnect 훅 → C1–C4 bullet → 공개물
- **§2 Related Work** — 진단 선행연구 + layer별 학습연구 → "파서 자체를 학습한 연구 없음"(우리 자리)
- **§3 Method** — 3.1 RCPS(프로토콜) / 3.2 Coverage diagnostic / 3.3 파서학습(aux + DPO + Distill)
- **§4 Experiments** — 4.1 Setup / 4.2 C1+C2 / 4.3 C3 / 4.4 C4 / 4.5 메커니즘
- **§5 Discussion** — 헤드라인=selection, C1↔메커니즘 화해, 가설 수정, 실무 playbook
- Appendix A/B/C/D (6쪽 미포함)

---

## 3. 표·그림 설계 ★검증 핵심★

> 각 항목: **무엇을** 보여주나 / **왜** 필요 / **데이터 출처** / **핵심 숫자** / ⚠️**확인필요**

### 📊 Figure 1 — disconnect (C1 헤드라인) · 본문 §4.2
- **무엇**: (a) 6파서 BC↔RCPS scatter(반상관) + (b) Hit@1 2.8× swing 막대
- **왜**: 논문 한 방 — "깨끗한 파서(MinerU/Marker)가 retrieval 하위권, VLM보다 한참 아래". 시각적 gut-punch.
- **출처**: BC=`moc_bc_correlation.json`, RCPS/Hit@1=`grid_v1_parser_native.json`(3-retriever)
- **핵심숫자**: r=−0.81(n=5, PaddleOCR 제외=BC undefined), 0.197→0.549
- ⚠️ scalar r은 "illustrative"로 포지셔닝(데이터-mix 민감, [[ohrbench-7dom-flip]]). 진짜 C1 증거는 Fig2.

### 📈 Figure 2 — noise mechanism (C1) · 본문 §4.2
- **무엇**: noise 심해질수록(clean→severe) BC 평탄 / RCPS 붕괴, 3 파서family
- **왜**: disconnect의 *원인* — "지표가 포맷만 보고 내용을 못 봄". C1의 robust 증거.
- **출처**: `ohrbench_7dom_bc.json` (OHR-Bench **7 domain**, 2,264 Q-A)
- **핵심숫자**: MinerU BC 0.71–0.73 평탄 / RCPS 0.50→0.24(−51%), GOT→0.26, Qwen 0.47→0.43(robust)

### 📋 Table 2b — coverage diagnostic (C2) · 본문 §4.2
- **무엇**: 파서 고정(Prod), 청커 8개 변화 → covered/split/absent 분류
- **왜**: gap이 **파서 탓인지 청커 탓인지** retriever 없이 판별 → 실무 규칙
- **출처**: `coverage_diagnostic_v1.json`(진짜 Prod parse, 294p)
- **핵심숫자**: absent **20.2%**(8 chunker 일정), split ≤2%
- ⚠️ coverage는 **294p**(Prod 전체 parse), C4 학습평가는 **242p fold** — page set 다름(의도적, 별개 측정). 헷갈릴 수 있어 캡션에 명시함.

### 📋 Table 3 — chunking 선택 (C3) · 본문 §4.3
- **무엇**: Prod 출력 고정, 청커 전략별 RCPS (md_h3 > parser_native > LumberChunker > fixed)
- **왜**: RCPS가 **파서뿐 아니라 청커도** 고른다(C3의 "두 knob") 입증
- **출처**: `chunking_grid_v1.json` (663 Q-A, 3-retriever)
- ⚠️ 이 표 캡션이 너무 짧음(한 줄) — 내용 충분한지 확인 필요

### 📋 Table 3b — RCPS ≠ 단순 MRR (C3 핵심) · 본문 §4.3
- **무엇**: 프로토콜 선택 ablation — retriever-평균/format-invariance 켜고 끄며 파서 랭킹 변화
- **왜**: "RCPS는 새 metric이 아니라 protocol" 입증 — retriever 평균이 1위를 뒤집음
- **출처**: `rcps_protocol_ablation.json`
- **핵심**: row A(naive MRR) vs D(full): 1위 역전

### 📋 Table 5b — C4 cross-domain 결과 (헤드라인 C4) · 본문 §4.4
- **무엇**: OHR-Bench 7-domain에서 RADP-Distill·RADP-DPO(R2/R3)의 Δ vs Prod
- **왜**: C4 confirmatory 결과(powered, n=2,264). RADP-Distill ≥ RADP-DPO → reward 불필요
- **출처**: `arm_b_ohr_ci.json`, `arm_b_textned_results.json`
- **핵심숫자**: RADP-Distill Hit@5 **+1.22 [.35,2.15]**, RADP-DPO +0.85 [.35,1.43]
- ⚠️ Hit@k/MRR/nDCG는 같은 랭킹의 monotone 변환(독립 아님) — 캡션에 명시(reviewer 방어)

### — Appendix (6쪽 미포함) —
- **Table 5** (Appx B): RADP-DPO R1→R2→R3 진행 + SimPO control (KoGov, exploratory). C4 detail.
- **Table 7** (Appx C): 12-variant chunk-level 통계(BC/CS/TextNED/shape). §4.5 메커니즘 근거. TextNED: Prod 0.240 → R2 0.163 → **RADP-Distill 0.158(최저)**.
- **Table D1** (Appx D): Fig1의 6파서 정확 수치(BC/RCPS/Hit@1). Fig1 백업.
- **fig_rcps_protocol** (보관, 본문 미사용): RCPS 프로토콜 흐름도. appendix 후보(선택).

---

## 4. 내러티브 흐름 (왜 이 순서)

1. **문제**: 깨끗한 파서가 최악 retrieval (Fig1) → 지표가 거짓말
2. **원인**: 지표는 포맷만 봄, 내용 못 봄 (Fig2 noise)
3. **어디가 문제?**: 파서냐 청커냐 → coverage가 파서로 지목 (Table 2b)
4. **그럼 어떻게 고르나?**: RCPS 프로토콜 (Table 3, 3b)
5. **학습으로 더?**: 가능하지만 bounded, reward 불필요 (Table 5b) → fidelity distillation
6. **결론**: selection이 메인, 학습은 보조

---

## 5. 확정 숫자 (외우기)

- C1: BC↔RCPS **r=−0.81**(n=5) · Hit@1 **2.8×**(0.197→0.549) · noise RCPS **−51%**
- C2: absent **20.2%** / split 0–2% (8 chunker 일정, 294p Prod)
- C4: RADP-Distill OHR **+1.22** / KoGov **+2.61** · RADP-DPO **+0.85** / **+1.96** · TextNED **0.158**(최저)

---

## 6. 알려진 정리 대상 (디자인과 별개)

- **번호 갭**: 본문에 Table 2b는 있는데 Table 2 없음(제거됨) → LaTeX 포팅 시 auto-number로 1,2,3 재정렬
- **익명화**: WigtnOCR/WIGTN(byline·인용·artifact ID) → 중립명 (double-blind)
- **register(말투)**: "headline/buys nothing/get backwards" 등 구어 → 학술어 교정
- **볼드 strip**: 본문 인라인 숫자/용어 볼드 → LaTeX 포팅 시 제거(run-in 헤더·표 best-cell만 유지)
