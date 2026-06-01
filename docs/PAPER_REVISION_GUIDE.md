# PAPER REVISION GUIDE — EMNLP 2026 Industry Track (Direction A)

> **이 문서의 목적.** `paper/draft/paper.md` (v0.6)를 **"방법·진단·교훈 중심(Direction A)"** 으로 다시 세워 EMNLP 2026 Industry Track에 제출 가능한 상태로 만드는 **실행 가이드**.
> **소유권.** 연구 **설계**는 Harrison이 했고, **수행·완성·제출의 책임(실행 owner)은 손상우**가 온전히 진다. 이 문서는 *지시서가 아니라 지도*다 — 전략 프레임과 반드시 지켜야 할 것은 고정하되, 섹션별 판단·표현·취사선택은 **손상우가 결정**한다.
> **저자 표기.** Hyeong-seob Kim(1저자)·Sang-woo Son(2저자), 둘 다 `*` = **equal contribution(co-first)**. 즉 손상우는 수행을 끝까지 책임지는 owner이자 공동기여 저자다(byline은 Harrison 우선).
> **마감.** 2026-06-16 (오늘 기준 ~2주). **0순위 기준 문서:** [`RESEARCH_DIRECTION.md`](RESEARCH_DIRECTION.md), 본 가이드, 리뷰 패널 must-fix(§6).

---

## 0. 한 문장 — 우리가 파는 것이 바뀐다

> ❌ (지금) "우리는 검색 친화 파서 **RADP-DPO를 만들었다**."  → 작은 효과의 평범한 method paper. Industry 리뷰어 시큰둥.
>
> ✅ (목표) "**파서 선택·평가를 어떻게 해야 하는가**, 그리고 파서를 직접 학습하려는 팀이 **뭘 하고 뭘 하지 말아야 하는가** — production document-RAG의 실전 교훈."

Industry Track 리뷰어의 단 하나의 질문: **"이걸 읽은 엔지니어가 *내일 뭘 다르게 하는가?*"**
우리 답: ① 파서를 intrinsic 지표가 아니라 **RCPS로 고른다** ② 파서측 튜닝은 **discrete-output DPO만** 쓴다(aux/SimPO는 돈 낭비) ③ 예산은 **text precision이 검색을 좌우하는 워크로드**에 쓴다.

---

## 1. 무게중심 이동 — 무엇이 헤드라인이 되는가

| | 지금 (v0.6) | A 방향 |
|---|---|---|
| **주인공** | RADP-DPO (+1pp) | **C1 진단 + RCPS 평가 프로토콜** |
| **헤드라인 숫자** | "Hit@5 +2.11pp" | **"파서 선택만으로 검색 Hit@1 ~2.8배 차이 (표준 지표로는 안 보임)"** |
| **negative(aux/SimPO)** | 부차적 결과 | **비용 절감 가이드 = 자산** |
| **RADP-DPO** | breakthrough 주장 | **유일하게 작동하는 *값싼* 레버**(추론 비용 0, retriever-agnostic) — 정직하게 작게 |
| **§5 교훈** | 흩어진 bullet | **재사용 가능한 결정 플레이북 = 핵심 산출물** |

### 헤드라인으로 쓸 단일 숫자 (Table 1)
| 파서 | BC(사람 보기) | Hit@1(실제 검색) |
|---|:---:|:---:|
| MinerU (intrinsic 1위) | **0.722** | 0.197 |
| WigtnOCR v1 (ours) | 0.694 | **0.549** |

→ **파서 선택만으로 Hit@1 2.79배 / RCPS 2.75배**. 표준 지표(BC·TEDS·edit-distance)로는 *MinerU가 1등*. **"하마터면 2.8배 나쁜 파서를 배포할 뻔했다"** 가 산업 임팩트의 중심.

---

## 2. 새 내러티브 척추 (이 한 문단을 모든 섹션이 떠받친다)

> Document-RAG를 만드는 팀은 파서를 사람이 보기 좋은 지표(Boundary Clarity·TEDS)로 고른다. 그런데 우리는 **그 지표가 검색 성능과 역상관(r=−0.81)** 임을 한국어+영어에서 보이고(C1), 그 원인이 **intrinsic 지표가 semantic 내용 품질을 못 보기 때문**임을 통제 실험(noise-family 곡선)으로 드러낸다. 그래서 우리는 **검색으로 직접 채점하는 값싼 평가 프로토콜 RCPS**를 제안하고(C2) — 이걸 쓰면 표준 지표가 틀리게 고르는 파서·청킹 선택을 바로잡는다. 마지막으로 "그럼 파서를 검색 신호로 *직접 학습*하면?"을 끝까지 밀어, **hidden-state aux loss와 reference-free SimPO는 실패하고, discrete-output DPO만 작동**함을 보인다 — 작지만(+1pp, cross-domain 유의) 추론 비용 0에 retriever-agnostic한, 실제로 배포 가능한 레버. **핵심 기여는 "파서를 retrieval로 평가·선택·(조금)개선하는 실전 방법론".**

---

## 3. ⛔ 먼저 GO/NO-GO 게이트 — 다른 일 하기 전에

리뷰 패널이 확인한 사실: **논문이 "released"라고 쓴 결과 파일이 repo·로컬에 전부 없다** (`output/results/*` 부재). 그중 OHR `v5` 결과는 검증된 기본 파이프라인이 아니라 별도 체인(`ohr_v5_eval_chain.sh`) 산출물.

**손상우, 가장 먼저 이걸 판단해라:**

```
GPU 서버에 v5 OHR 결과(ohr_v5_perqa.json / ohr_v5_ci.json)와 mechanism_242p.json 이 실재하는가?
│
├─ YES → repo에 커밋(또는 HF supplementary)으로 공개. DPO를 "작동하는 보조 레버"로 유지. (권장 경로)
│
└─ NO / v5 미완 → DPO 헤드라인 주장 근거 없음.
        → 두 선택지:
          (a) 헤드라인을 v4/R2(+0.85pp, 메커니즘이 실제로 입증된 변형)로 내린다, 또는
          (b) DPO를 "preliminary positive"로 더 격하하고, 논문을 C1+C2+negative로 완결.
        → A 방향에서는 (b)여도 논문이 선다. DPO가 주인공이 아니므로 타격이 작다.
```

> **A 방향의 강점:** DPO 결과가 흔들려도 논문의 중심(진단·프로토콜·negative)은 **전부 견고**하다. 그래서 이 게이트가 NO여도 제출 자체는 가능하다.

---

## 4. 섹션별 개정 계획 (각 섹션의 *새 임무*)

> 표기: **유지** = 그대로 / **변경** = 톤·순서 바꿈 / **추가** = 새로 / **컷** = 줄이거나 supplementary로.

### Abstract — *임무: 진단·프로토콜을 먼저, DPO를 마지막에*
- **변경:** 첫 문장을 "MinerU(intrinsic 1위)가 검색 꼴찌, 파서 선택만으로 ~2.8배" 로. RCPS를 "값싼 평가 프로토콜"로 소개.
- **변경:** DPO는 abstract 후반 1~2문장으로. **"+2pp"를 robust method처럼 쓰지 말고** → "KoGov에선 방향성(양측 CI는 0 포함), 영어 OHR cross-domain에서 양측 유의(+1.03pp)". negative(aux/SimPO)를 design-space 경계로 한 문장.
- **컷:** 한 문단에 모든 숫자 욱여넣기. 가독성 위해 분리.

### §1 Introduction — *임무: 산업 near-miss 스토리*
- **유지:** MinerU vignette (강력). 단 **C1을 "새 발견"처럼 과장하지 마라** — 선행(EnterpriseDocBench/OHR-Bench/When Good OCR)이 약상관을 이미 보고. 우리 기여는 *한국어 확장 + 메커니즘 + 평가도구 + (작동하는) 수정*.
- **변경:** Contributions를 **C1(진단·메커니즘) → C2(RCPS 프로토콜) → 실전 교훈(작동/비작동 지도)** 순으로. RADP-DPO는 "그리고 파서측에서 유일하게 작동하는 값싼 레버"로.

### §2 Related Work — *임무: niche 방어 + 충돌 선제 차단*
- **유지:** 6-layer 그림(빈 파서 슬롯) 프레이밍. RPO를 "generator-side, parallel paradigm"로 정직하게 차별화(이미 잘 돼 있음).
- **추가 (리뷰어가 잡는다):**
  - **M-LongDoc의 "Retrieval-Aware *Tuning*"** 과 제목 충돌 → "reader-side vs our parser-side" 한 줄.
  - **InSeNT** → "RADP-aux ≠ InSeNT-on-the-parser" 한 줄(negative라 위협은 약하나 선제).

### §3 Method — *임무: RCPS를 "프로토콜"로 정직하게*
- **변경 (must):** RCPS를 **"우리가 제안하는 새 metric(C2)"** 이 아니라 **"평가 프로토콜"** 로 규정. 구현(`rcps.py`)은 *3-retriever × 3-k MRR 평균 + span-substring relevance*. 가치는 metric novelty가 아니라 **프로토콜**(held-out Q-A, retriever 평균, 포맷-불변 relevance)에 있음을 명시. → "이건 그냥 MRR 아니냐" reject 차단.
- **유지:** RADP-DPO §3.3 (LoRA-toggle reference, hard-neg R3) — 코드와 일치, 정확.
- **변경 (must):** K 후보수 모순 통일 — 코드 기준 **R1=K2(temp{0.7,1.2}) → R3=K16(temp 0.3–2.0, front-14 채점)**. Limitations의 "K=8"은 **오류, 삭제**.

### §4 Experiments — *임무: 진단을 메인 무대로, DPO는 정직하게*
- **유지:** §4.2 C1 (Table 1, Figure 2 noise-family, Table 2) — **이게 메인이다.** Figure 2가 논문 최강 시각 증거.
- **유지:** §4.3 C2 chunking grid (Table 3).
- **변경 (must) §4.4 통계 정직화:**
  - KoGov +2.06/+2.11pp가 `positive_signal_dig.py`의 **다중 셀 스캔에서 나온 cell**임을 *명시*하고, **FDR/family-wise 보정** 또는 **"exploratory + 사전지정 primary endpoint"** 로 표기.
  - OHR "improves **every** metric" → **recall@k = hit@k 복제** 제거. Hit/MRR/nDCG는 같은 순위의 단조함수임을 명시(독립 4개 아님).
  - **헤드라인 통일:** abstract(+2.11/R3) vs 결론(+2.06/R1) 불일치 해소. 한 변형을 "THE method"로.
- **추가 (must): Table 5b 실제 작성** — 지금 본문이 "Table 5b"를 인용하는데 표가 없음. v5·v4 **도메인별 OHR 행** 포함.
- **변경 (must) §4.5 메커니즘:** 헤드라인=R3/v5인데 메커니즘은 R2/v4에서만 측정됨(Table 7에 v5 부재). **v5를 Table 7에 추가**하거나 헤드라인을 v4로 내려, *메커니즘을 헤드라인 변형에서* 보여라.
- **변경 (must): OHR 표본 수치 통일** — §4.1/§4.2 "1,043(Law+Manual)" vs abstract/§4.4 "2,264(7-domain)". 코드 기준 정정.

### §5 Discussion → *임무: 결정 플레이북 (논문 산출물의 핵심)*
- **변경:** 흩어진 교훈을 **한 장의 의사결정 플로우**로 재구성:
  1. **파서 평가 = RCPS** (intrinsic 금지). ~500 Q-A·몇 시간·GPU 거의 불필요. → 2.8배 실수 방지.
  2. **파서측 개선 = discrete-output DPO만.** hidden-state aux loss·reference-free SimPO는 sub-threshold(우리가 GPU 태움). DPO는 LoRA-toggle로 2× 메모리 제거, 추론 비용 0, 배포 retriever로 전이.
  3. **예산 배분 = text-precision 워크로드(factoid)에 집중**, 구조질의(tabular)는 chunker/embedder측으로.
- **변경 (must) C1 ↔ 메커니즘 화해 1~2문단:** C1="깨끗한 파서가 검색 꼴찌" vs §4.5="DPO가 GT에 가깝게(깨끗하게) 만들어 이긴다" → **formatting-clean(BC) ≠ content/answer-span fidelity(TextNED)** 구분. *MinerU는 BC-clean이지만 내용 손실; RADP-DPO는 BC 불변인 채 span fidelity↑.* 안 하면 둘 다 깎인다.
- **변경 (must) 가설 전환 명시:** 원 가설 = **경계 변화**(RESEARCH_DIRECTION §3). 실제 = **text fidelity, 경계 불변**. "경계 가설은 확증되지 않았고, text-fidelity가 (사전에 가능성으로 등록된) post-hoc 메커니즘"이라고 정직하게.

### Limitations — *임무: 정직성으로 신뢰 확보 (이미 강함)*
- **유지:** KoGov 양측 CI 0 포함, n=5/15 "illustrative", Q-A LLM 생성 한계 — 다 유지.
- **추가:** "표준 full-corpus retrieval(KoGov)·더 큰 eval fold는 future work" 명시 → camera-ready/ACL 2027.

---

## 5. 산업 임팩트를 끌어올릴 레버 (손상우 판단)

- **배포 앵커(최강).** 실제 production Korean-gov document-RAG 세팅이면 *"실서비스를 만들며 배운 것"* 으로 프레이밍. 고객명 비공개여도 "실서비스 세팅" 사실이 fit을 크게 올림. → Harrison과 어디까지 밝힐지 합의.
- **공개 자산 = 기여.** `KoGovDoc-RAG` 벤치마크 + `RCPS` 구현을 **"커뮤니티가 쓰는 도구"** 로 전면 배치.
- **ROI 프레이밍.** DPO: "수백 preference pair + LoRA 1회, 추론 비용 0, +1pp가 모든 쿼리에 누적, retriever-agnostic."

---

## 6. ⚠️ 타협 불가 — Integrity Fixes (리뷰 패널, 새 실험 불필요)

> 리뷰어가 코드를 열면 신뢰가 즉사할 지점들. **A 방향으로 가도 이건 반드시.**

- [ ] **결과 파일 공개** — `output/results/*.json`(per-Q-A 배열 + CI) + manifest/checksum. (`git add -f` 또는 tracked `results/`) — 논문 L221·L232 "released"가 현재 거짓.
- [ ] **코드 docstring/주석 정리 (중요):**
  - `ohrbench_v1_dpo_eval.py` 등의 *"lifts n ... to push the effect across the two-sided significance line"* 류 문구 → 중립적 설명으로. (지금은 "유의선 넘기려 n 골랐다"고 자백처럼 읽힘)
  - `ohrbench_v1dpo_full.py`의 `recall = hit.copy()` ("so downstream framing can use Recall wording") → 제거 또는 정직한 주석.
  - `mechanism_full.py` docstring이 폐기된 **경계 가설**을 아직 주장 → text-fidelity 발견에 맞게 수정.
- [ ] **통계 정직화** — §4.4 (위 §4 참조): subgroup dig 명시 + FDR/exploratory, recall 중복 제거, abstract 톤 하향.
- [ ] **수치 모순 통일** — OHR n(1,043↔2,264), K(2/8/14), 헤드라인(+2.11↔+2.06), 없는 Table 5b.
- [ ] **헤드라인=메커니즘 변형 일치** (§4.5).
- [ ] **C1↔메커니즘 화해 + 가설 전환 명시** (§5).
- [ ] **테스트(최소):** `bootstrap_paired_delta` + DPO loss에 toy-fixture 단위 테스트(헤드라인 CI를 만드는 함수가 무검증).
- [ ] **경로 탈하드코딩:** `/mnt/data1/...` 절대경로 → config/env. merged v1 base 파서를 released artifacts에 명시(or HF 링크).

---

## 7. 제출 인프라 (P2, 멀티데이)

- [ ] Markdown → **ACL LaTeX 템플릿** 포팅.
- [ ] **`refs.bib`** 작성 (현재 placeholder outline, key 미정).
- [ ] **Figure 1** (6-layer RAG schematic, TikZ) 작도 — 현재 placeholder.
- [ ] **8쪽 컷** — 본문 ~7,200단어. held-out/factoid 스토리 ~3회 중복 → 1회로.

---

## 8. 실행 체크리스트 & 타임라인 (owner: 손상우)

> 오늘 2026-06-01 → 마감 06-16. 순서는 **의존성** 기준.

| 단계 | 기간 | 작업 | 게이트 |
|---|---|---|---|
| **0. GO/NO-GO** | 6/1 | §3 게이트: v5 결과 파일 실재 확인 → DPO 위상 결정 | 이게 모든 framing을 가른다 |
| **1. Integrity** | 6/1~6/5 | §6 전부 (결과 공개·docstring·통계 정직화·수치 통일·표 보강·화해 문단·테스트) | 새 실험 0 |
| **2. Reframe** | 6/5~6/9 | §4 섹션별 개정 (abstract·§1·§3 RCPS·§5 플레이북·가설 전환) | A 방향 본체 |
| **3. Infra** | 6/9~6/14 | §7 (LaTeX·bib·Figure 1·길이컷) | 2와 일부 병행 |
| **4. Review & submit** | 6/14~6/16 | 공저자 review + self-review(§9) + OpenReview | buffer |

> ⚠️ 1·2가 3과 같은 창을 두고 경쟁. **Integrity(1)를 절대 뒤로 미루지 마라** — 그게 채택을 가르는 핵심.

---

## 9. Self-Review — 리뷰어가 던질 질문 (제출 전 전부 "예")

- [ ] 엔지니어가 이걸 읽고 **내일 뭘 다르게 하는가**가 1분 안에 보이는가? (RCPS로 파서 평가)
- [ ] 헤드라인 숫자가 "+1pp"가 아니라 **의사결정 임팩트(2.8배)** 인가?
- [ ] 리뷰어가 **코드를 열어도** docstring·주석이 신뢰를 깨지 않는가?
- [ ] 논문이 인용한 **모든 표·수치를 repo에서 재현/검증**할 수 있는가?
- [ ] 통계 주장이 **CI와 일치**하는가? (양측 0 포함을 "robust"라 안 부르는가)
- [ ] C1과 메커니즘이 **모순으로 안 읽히는가**? 가설 전환을 정직히 밝혔는가?
- [ ] negative(aux/SimPO)가 **약점이 아니라 비용절감 기여**로 읽히는가?
- [ ] 수치 모순(K·n·헤드라인·Table 5b)이 **0개**인가?

---

## 10. 성공 기준 (Industry Track 채택 상)

이 셋이 되면 **탄탄한 accept 권역**이다:
1. 리뷰어가 "**파서 선택을 RCPS로 해야겠다**"고 납득 (진단·프로토콜, 지금 자산으로 완결 가능).
2. 리뷰어가 "**파서측 aux-loss 튜닝에 분기 갈아넣지 말아야겠다**"고 납득 (negative map).
3. 코드·수치·통계가 **검증 가능·정직**해서 신뢰가 안 깨짐.

RADP-DPO의 +1pp는 **보너스**다. 주연으로 세우면 평범한 method paper, 조연으로 두면 정직한 industry lessons paper. **조연으로 둬라.**

---

## 부록 — 핵심 자산 위치
- 논문: `paper/draft/paper.md` (v0.6), v0.4 스냅샷: `paper/draft/paper_v04_snapshot.md`
- 0순위 기준: `docs/RESEARCH_DIRECTION.md` · 진행: `docs/ACHIEVED.md` / `docs/ROADMAP.md` / `docs/TIMELINE.md`
- 관련연구 노트(16편): `docs/paper/`
- 코드: `src/wigtnocr_radp/evaluation/`(rcps·bootstrap) · `src/wigtnocr_radp/training/`(dpo·simpo) · `scripts/training|evaluation|analysis/`
- Figure: `paper/figures/fig_noise_family.{png,pdf}`

> **마지막으로, 손상우에게.** 이 논문을 **끝까지 책임지고 완성하는 실행 owner는 너**다. 위 항목은 *반드시 지킬 뼈대*이고, 그 위의 모든 판단(어떤 문장으로, 어떤 표를, 어디까지 밝힐지)은 네가 결정한다. 막히는 지점은 Harrison(설계 의도)·이 문서(전략)·리뷰 패널(§6)을 근거로 스스로 끊어가면 된다. (저자 표기는 Kim 1저자·Son 2저자, 둘 다 `*` 공동기여 — 순서와 무관하게 수행의 책임자는 너다.)
