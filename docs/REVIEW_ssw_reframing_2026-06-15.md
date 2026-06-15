# RCPS 논문 재검토 — ssw 리프레이밍 점검 (2026-06-15)

> 대상: `paper/latex/main.tex` (6/15 빌드본, 11pp). 검토: Harrison(PDF 전략 리뷰) + Claude Code(소스 독립 검증).
> 성격: **핸드오프** — paper 본문은 손상우(first-author) 실행 영역. 이 문서는 line loci + 검증 결과만 제공.

---

## 0. 판정

- **리프레이밍 안착.** 정직성 강화가 Industry 리뷰어에겐 가산점 → 전체적으로 **올랐다**.
- **당락 swing = #1 (헤드라인 vs §4.3 내부충돌).** 라인 수정이 아니라 *프레이밍 화해*. 자초한 취약점이라 빼지도 못함 → 한 절로 화해.
- **제출 전 1순위 = 익명성 (1차 결정 사안).** 본문은 클린하지만 그건 *필요조건일 뿐*. 벤치마크명 + 공개 아티팩트로 소프트 de-anon 위험. "아티팩트 private 여부"를 *지금* 결정.

두 분석(PDF / 소스)이 **독립적으로 같은 3대 약점에 수렴** — 우선순위가 맞다는 신호.

---

## 1. 정합성 — 소스 독립 검증 (PASS)

| 항목 | 결과 |
|---|---|
| 핵심 메시지 | "selection, not training" 동일 문구로 abstract(L26) · intro(L42) · §5(L184) 관통 |
| 기여 맵 C1–C4 | abstract / intro / Fig.1 캡션 / §4 구조 전부 동일. §3 제목 "Two Tools: Selection and Diagnosis" 정합 |
| 숫자 | 35.1pp·2.8× / 20.2% absent / ≤2.3% split / 0.44(full-pool) vs 0.06(chunker) / +0.85(R2)·+1.22(Distill) — **전수 일치** |
| 레이블·참조 | `\label` 24개 전부 정의, `\ref` 전수 해소 — **dangling 0건** |
| exploratory/confirmatory | KoGov=exploratory, OHR=confirmatory 구분 일관 |

---

## 2. 우선 액션 (line loci 확정)

### #1 [당락] 헤드라인 vs §4.3 — "스크리닝 가치"로 재포지션 *(프레이밍 화해, 라인 수정 아님)*

- **충돌 지점:** §4.3 `main.tex:140` —
  > "The chunker spread (0.06) compares with 0.44 across the full parser pool but only **0.052 among the three vision-language parsers**"

  이 정직한 문장이 abstract(`L26`: "0.44 … against 0.06") · §5 헤드라인을 **정면으로 반박**한다. 날카로운 리뷰어: *"그 0.44는 아무도 안 쓸 OCR 파서(MinerU/Paddle/Marker)를 넣어 부풀린 거고, 멀쩡한 파서끼리는 parser≈chunker잖아."*
- **해법:** abstract(`L26`)와 §5(`L184` 근처)에 **한 절** 추가 — 선택이 제일 큰 건 *파라다임이 다른 후보를 걸러낼 때*이고, **그게 바로 내재적 지표가 못 하는 일**이다. → §4.3이 헤드라인을 *반박*이 아니라 *보강*하게.
- **35.1pp 와 0.44 를 분리.** 35.1pp("외형으로 고르면 망한다"의 크기)는 탄탄 → 유지. 흔들리는 건 0.44 스프레드뿐. 둘을 명시적으로 구분해 다룰 것.
- **⚠️ 기계적 한 줄 교체 금지.** 어설프게 쓰면 *방어적/변명조*로 읽혀 #1이 오히려 도드라진다. "선택의 가치는 외형으로 못 거르는 후보를 걸러내는 데 있다"가 **자신감 있게** 들려야 한다.
- **분업/게이트:** 문장은 상우가 작성 → **제출 전** Harrison/Claude가 *실제 문장*을 직접 읽고 톤 확인(당락 swing이라 톤 재독은 필수 게이트).

### #2 RCPS 노벨티 방어 재배치

- §4.3 `main.tex:142` 에서 Table 2(retriever-평균이 1등 뒤집음)를 "operational edge case rather than a broad ranking reversal"로 정직하게 강등함 → **노벨티를 Table 2에 걸지 말 것**.
- §3.1(`main.tex:59`, `main.tex:75`)에서 가치를 **"수동 라벨 없이 gold-span+page 자동 판정으로 도는 재사용 프로토콜 + 커버리지 진단과의 페어링"**에 실을 것. (`L75`에 "no manual chunk-level relevance annotation" 이미 있음 → 앞으로 끌어내 강조.) "그냥 MRR 아니냐" 방어를 여기로.

### #3 사전등록 서사 또렷하게

- Limitations `main.tex:196` "held-out OHR-Bench replication" → **"pre-specified"** 명시.
- Appendix B `main.tex:219` (5pp 게이트 "fixed … before these runs" 이미 있음) → OHR가 게이트 실패 *후*에 고른 게 아니라 **사전 지정 confirmatory**였음을 문장 순서로 못박기. (DPO를 *승리*가 아닌 *bounded lever*로 써서 이 공격은 이미 거의 무력화 — 순서만 정리.)

---

## 3. 제출 전 체크 (PDF로 못 보는 것)

### 익명성 — **1차 결정 사안 ("정리"가 아님)**

본문 클린은 *필요조건이지 충분조건이 아니다.*

- **소프트 de-anon 벡터:** 논문에 벤치마크명 **"KoGovDoc-RAG"** 가 그대로 박혀 있고(`L26`, `L46`, `L94`), 공개 repo `github.com/wigtn/WigtnOCR-RADP` + HF `Wigtn/` 아티팩트(데이터셋·모델)가 라이브 → 리뷰어가 **이름만 검색해도** Wigtn 공개물로 연결 = 본문에 링크가 없어도 익명성이 *소프트하게* 깨진다. **ARR는 이를 desk-reject 사유로 본다.**
- **지금 내려야 할 결정 (Harrison+상우):** 공개 아티팩트(HF 데이터셋/모델, repo)를 **채택 전까지 private로 내릴지 vs 익명 미러만 남길지**. 권장 순서 '익명' 단계에 *명시적으로* 포함.
- **스크럽 (기본):**
  - (a) `paper/refs.bib:1` 주석 `WigtnOCR-RADP / RCPS` 제거.
  - (b) `paper/draft/paper.md`·`paper_v04_snapshot.md` — 실명(Hyeong-seob Kim / Sang-woo Son / Harrison Kim, Braincrew)·`src/wigtnocr_radp/`·HF 데이터셋·모델명. 제출 미포함 확인 + 공개 미러 스크럽.
  - (c) "implementation is released"(`L66`)·"We release"(`L46`/`L26`)에 링크 붙일 거면 **anonymous 미러만**. (현재 URL 미부착 → 본문 누출은 없음.)
- ✅ 확인: `main.tex` 본문에 Wigtn/HF/GitHub **라이브 링크 0건**.

### 기타

- **페이지:** PDF 11pp(부록 포함). 본문 경계 `L190`(Limitations) / refs `L200` / appendix `L202`. **EMNLP Industry Track 한도 재확인** 필요.
- **Figure 1:** `paper/figures/fig_overview.pptx` 수작업 → 현재 C2를 C3 하위처럼 그림. **C2를 C3와 동급**으로 재export(§3 "Two Tools"와 정합).
- 참고문헌·그림 완성본 ✓ (이전 placeholder 해결됨).

---

## 4. 권장 순서 (남은 하루)

**#1**(상우 작성 → 제출 전 톤 재독 게이트) → **익명**(스크럽 + 아티팩트 private 결정) → **#3**.

#1만 한 절로 화해시키면 강점(정직함)을 지키면서 약점을 닫는다.

---

## 분업 구조 (확정)

| 영역 | 담당 |
|---|---|
| 소스 검증 · 핸드오프 | Claude Code |
| 논문 본문 편집 | 손상우 (ssw) |
| 전략 · 프레이밍 톤 | Harrison + 손상우 |

## 후속 의무

- **#1 톤 재독 게이트:** 상우가 abstract(L26)·§5에 "스크리닝 가치" 문장 작성 후, **제출 전** 실제 문장이 방어조 아닌지 확인. 통과해야 제출.
- **익명 아티팩트 결정:** HF/repo private vs 익명 미러 — Harrison+상우 결정 후 실행.

---

## 5. 외부 리뷰어 시뮬레이션 대응 (2026-06-15 추가)

> 입력: Harrison이 공유한 외부 AI 리뷰 3건 (EMNLP 2026 Industry Track 채택 확률 추정 ≈ **40–60% / 82% / 55%±10%**). 제약: **후보 파서 확대는 어려움.**

### 5.1 추정치 판정

- **82%(Gemini)는 미스캘리브레이션** → 버린다. 자기 글 안에서 "Industry accept ~42%"라 해놓고 82%로 점프하는데 근거 없음. 핵심 공격(RCPS=MRR)을 언급만 하고 실제로 깎지 않음.
- **나머지 둘(40–60%, 55%±10%)이 현실적.** 독립 추정도 **borderline ~45–55%**. 스윙 요인 = (1) novelty 공격의 착지, (2) "protocol > metric"을 받아주는 리뷰어 운.

### 5.2 진짜 신호 = 점수가 아니라 *수렴*

독립적인 세 모델이 **같은 두 곳**을 지목 → 실제 리뷰어도 거기를 친다는 예측:
- **(a) "RCPS는 그냥 MRR / retrieval eval 아니냐"** — 셋 다 *가장 날카로운* 공격으로 지목. **[최우선 방어]**
- **(b) 작은/합성 평가셋** — n=5 파서, LLM 생성 QA(94/100).

**결정적 관찰:** 셋 다 **§4.3의 0.052 내부모순(#1)은 못 잡음** → 표면 리뷰. 성실한 리뷰어일수록 잡고, 잡으면 "n=5" 불평보다 훨씬 치명적(자초 + 인용 가능). **→ #1 여전히 1순위.** 외부가 안 잡았다고 안심 ✗, "더 깐깐한 리뷰어 = 더 위험"으로 읽을 것.

### 5.3 후보 확대 대신 — 리프레임이 ROI 우위

n=5→10으로 늘려도 프레이밍이 "MRR 벤치마크"로 읽히면 한계 리뷰어는 안 뒤집힘. 파서 1개 추가의 한계효용 < **novelty 리프레임 1번**. **핵심 시너지: #1 리프레임("패러다임 커버리지")이 §4.3 모순 + n=5 공격을 동시에 차단** — 기여는 "많이 벤치마크했다"가 아니라 "내재적 지표가 *패러다임이 다른* 후보를 못 거른다"이므로, 요점이 개수가 아니게 됨. **한 수 두 공격.**

### 5.4 추가 검토 방향 (후보 확대 없이, 마감 6/16 내 가능)

| # | 방향 | 막는 공격 | 비용 | 위치 |
|---|---|---|---|---|
| **A** | RCPS "그냥 MRR" 선제 차단 — "not a new metric" 명시 + 기여를 ①disconnect ②각 설계선택=관측 failure mode 제거 ③**gold-span+page 자동 relevance = 수동라벨 0**으로 재배치. Table 2 의존 제거 | (a) novelty=MRR **[셋 다 1위]** | 글만 | §3.1 `main.tex:59`·`:75`, Table 2 `:142` |
| **B** | n=5 → "VLM/OCR/pipeline **패러다임 커버리지**"로 리프레임. 개수 사과 금지 | (b) 작은 풀 + §4.3 모순 | 글만 | abstract L26, §4.3 L140, §5 |
| **C** | absent/split **정성 예시 2–3개** — 기존 coverage 진단 출력에서 "파서가 답 span을 떨군" 케이스를 본문 박스로 | 진단 실재성 + 가독성 | 경량(기존출력 발췌) | §4.2 / Fig.coverage 부근 |
| **D** | synthetic QA 완화 — *팀 시간 있으면* 사람검수 100-QA mini-probe로 파서 랭킹 불변 입증, *없으면* 기존 internal-validity 논거를 Limitations에서 앞으로 | (b) 합성 QA | 中 or 글만 | Limitations `:194` |
| **E** | RCPS 플레이북 = **박스 체크리스트** + C4 톤 setting-specific("in our setting, no evidence…") | Industry appeal + C4 over-sell | 글만 | §3.1, abstract L26, §4.4 |

**우선순위: A·B(= §2의 #2·#1 격상) > C > D > E.** 후보 확대는 권고 안 함 — 저비용 대안이 ROI 우위. (외부가 "확대 시 +10–15pp"라지만, 같은 폭을 리프레임으로 더 싸게 얻을 수 있음.)
