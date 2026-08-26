# Camera-Ready 최종 핸드오프 — 잔여 작업 전량 (2026-08-25)

> **역할 확정**: 이 시점부터 camera-ready 실행은 **상우 전권**이다. Harrison은 실행에 관여하지
> 않고, 아래 §4의 **최종점검 1회**만 수행한다. 판단이 필요한 항목도 이 문서의 권고를 참고해
> 상우가 결정한다 (최종점검에서 결정 사유만 확인).
>
> 기준: `docs/CAMERA_READY_PLAN.md`(P1–P17 원장) + OpenReview 최종 게시본(SHA
> `654e6046…`, local-only). 이 문서는 2026-08-25 Harrison+클로드코드의 전수 감사 결과를
> 실행 목록으로 변환한 것이다. **데드라인: 2026-08-30 AoE = 08-31 20:59 KST.**

## 1. 감사 스냅샷 — 완료 확인된 것 (재작업 불필요)

`main_camera_ready.tex`(b563327 기준)·그림·아티팩트를 게시본 약속 전체와 대조했고, 이후
**8/24–25 머지된 PR #11–16(camera-ready 배치)까지 추가 검증했다.** PR #11–16에서 확인된 것:
C1의 MinerU-on 재베이스(초록·intro·L136–143·Limitations 일관), Table 1 BC 셀 `0.713` 기입,
n=5 상관 −0.81→**−0.83** 갱신(독립 재계산 −0.8292 일치 확인), `fig_disconnect` MinerU-on
재생성, Discussion의 MinerU-on absent 66.1%(=438/663, `FINDINGS_tableon_local_verification.md`
근거 확인). 전부 수치상 정확하다 — 남은 문제는 §2-E의 **근거 아티팩트 미커밋**뿐이다.

| 항목 | 판정 |
|---|---|
| P1·P2 Appendix C: 정의(`sec:parser-def`) + worked example(val_0155) + 3원인 수치 + 응답 원문 "Appendix C" 5곳 글자 일치 | ✅ |
| P3 Intro 재구성(발견 lead, scope 문장) | ✅ (미세갭 §3-b) |
| P4 밀도: 본문 p.6 종료(총 14p), noise·DPO 표 appendix, C4 압축 | ✅ |
| P5 인간 검증 수치 반영(κ=0.615, 84.0% CI, 90.3% n=93, 제외 사유 각주) | ✅ (라벨 공개는 §2-B3) |
| P6 E2E 표(`tab:e2e`), MinerU-on 페어링 원칙 | ✅ |
| P8 Table 1 3구획 분리, 42.6pp/4.47× 헤드라인, "lower bound" 제거 | ✅ (미세갭 §3-a) |
| P9 pseudo-GT 3곳 | ✅ |
| P11 4.9pp "scale only" 격하 + 229+65/527+136 | ✅ |
| P16 그림: overview `294=229+65`, disconnect r=−0.74/−0.81, stale 35.1/2.8× 제거, **Type3=0** | ✅ |
| P17 감사부: alignment audit 커밋, 1,043/2,036 분리, "not a full v2 rerun" 명시, Distill 정량 제외 | ✅ |
| MRR@10-only 약속(τ=1.0, `fullgrid_aggregate_audit`) 본문 반영 | ✅ |
| refs.bib 26키, 저자 순서 고정, PDF A4 | ✅ |

## 2. 남은 작업 (우선순위 순)

### A. P7 — full-grid probe-resampling 【최대 blocker, 유일한 실험+본문 동시 항목】

bXGg Q1에 **"The full-grid version goes into the revision"** 으로 약속했는데, 현재 본문은
반대로 "Missing aligned per-Q--A arrays prevent a probe-resampling test"(L183)라고 자인한다.

1. WSL에서 동일 294p·663 Q--A·동일 retriever/cutoff로 **9개 시스템 per-QA 수출**
   (30B/Prod/2B-base/MinerU-off/MinerU-on/Paddle × parser_native + Prod × 나머지 3청커).
   Marker 제외. 242p fold와 절대 혼합 금지 (PLAN P7의 풀 정의 그대로).
2. `scripts/analysis/rank_stability_bootstrap.py`(e005ad7) 실행 → 결과 JSON + MANIFEST 커밋.
3. 본문 L183 문장을 결과로 교체하고, rebuttal의 provisional 수치(100%/98.8%)는 full-grid
   결과로 **대체**한다(승격 금지 원칙 유지).
4. ⚠️ "format normalisation shifts scores by 0.02–0.03" 문장은 재계산 근거가 나오기 전까지
   논문에 넣지 않는다 (현 상태 유지가 정답).

### B. P12 — 아티팩트 3건

1. **MinerU tables-OFF predictions 커밋** — ZQv618에 "release both outputs"로 약속.
   git에 0건 (`results/kogovdoc/`에 tableon만 존재). WSL 원본 회수 → 커밋.
2. **체크포인트 릴리스 모순 해소 【감사 신규 발견 — PLAN에 없음】** — NAor1 답변은 현재형으로
   "the parser-training **checkpoints** are all released"라고 주장했는데, Appendix H(L491)는
   "does not yet contain … checkpoints"라고 자인한다. 게시 주장과 논문이 정면 충돌.
   → 권고: 최소 R2/R3 LoRA 어댑터 + 실행 config 공개(HF 또는 repo). 불가하면 App H 서술과
   별개로 공개 계획을 명시해야 하나, 공개가 정공법이다.
3. **인간 검수 per-case 라벨** — tex L365 `CAMERA-READY ARTIFACT BLOCKER` 주석 잔존.
   adjudicated 100건 라벨 + 93건 overlap manifest 공개 여부를 상우가 결정하고, 공개 시
   검수자는 "author A/B" 익명 표기. 결정 후 **blocker 주석 2건(L241 R2-β 포함) 제거**가
   최종 PDF 게이트다.

### C. 문안 미세갭 2건 (짧은 수정)

- **(a)** (PR #12 이후 선택으로 완화) Discussion에 MinerU-on 66.1%가 들어가 20.2%와의 차
  +45.9pp가 유도 가능해짐. rebuttal이 공표한 "+50.2 → +45.9, does not close" 명시 문장을
  넣을지는 상우 판단 — 넣으면 P15 매핑이 더 깔끔해진다.
- **(b)** NAor1에 약속한 ought-vs-is 문장("extrinsic evaluation should be standard practice,
  yet leaderboards rank by intrinsic fidelity")이 intro에서 완곡화됨. 한 문장 명시 권고.

### D. 메타데이터 (폼 8/23–30, 외부 의존)

5인 소속·이메일·ORCID 순서별 대조, presenter/등록/visa/preference와 대면 발표자의 Budapest
도착·출발일 및 선택적 scheduling constraints 입력, R2 β=0.1 vs 0.05 provenance 확인(트레이닝 로그).
교신저자는 chairs의 서면 승인에 따라 이름 별표 없이 `Correspondence: harrison@wigtn.com`으로 반영했다.
PLAN §0 게이트 그대로.

### E. BC 0.713 / r=−0.83의 근거 아티팩트 머지 【PR #12로 승격됨 — 이제 필수】

논문이 이미 BC `0.713`(Table 1·초록·L136·L222·Limitations)과 n=5 `r=−0.83`(L138·캡션·
Limitations)을 인용하는데, **이 수치를 생성한 아티팩트가 main에 없다.**

1. `origin/codex/mineru-on-bc`(524fd58)를 PR 생성 → merge. 8/24 Harrison 리뷰 완료
   **PASS(critical 0/major 0/minor 1)** — mean BC 0.7132·609 boundaries·r=−0.7445(→−0.74)를
   manifest 해시까지 로컬 재현, 테스트 40개 통과. 브랜치만 push돼 있고 PR은 미생성 상태.
2. **n=5(−0.83) 상관 아티팩트가 어디에도 없다** — 브랜치 JSON(`moc_bc_mineru_tableon.json`)의
   `derived_correlations`는 n=4(−0.7445)만 담는다. 수치 자체는 검증됨(BC 5종 + current-grid
   RCPS로 −0.8292): `compute_parser_bc.py`에 Marker 포함 n=5 블록을 추가해 재생성하거나,
   최소한 계산 스크립트+결과 JSON을 커밋해 P14 감사가 대조할 대상을 만들 것.
3. minor 1건(checkpoint의 manifest 미검증 재사용 풋건)은 camera-ready 무관 — 여유 있을 때만.

## 3. 게시 주장 대비 편차 원장 (P15 매핑표에 그대로 옮길 것)

방어 가능하지만 리뷰어가 응답과 대조할 수 있는 지점. 최종 게이트에서 "의도된 편차"로 기록한다.

1. NAor1 답변 "seven domains, 2,264 Q--A" → 수락 후 감사로 **2,036/6-domain** 교체 (App F에 사유 공개 ✅).
2. bXGg 답변 "does not beat a fidelity-distillation control" → Distill 아티팩트 제외로 논문의
   부정 결과 근거가 "파일럿 타깃 미달 + SimPO 음수"로 변경 (App B에 사유 공개 ✅).
3. NAor1 답변 "checkpoints are all released" → §2-B2로 해소 전까지 **미해소 모순**.
4. ZQv618·bXGg 답변의 "Boundary Clarity **r = −0.81**" → camera-ready는 MinerU-on 재베이스로
   **r = −0.83** (n=5, 방향 동일·더 강함, 독립 재계산 일치). 방어 가능하나 리뷰어가 응답과
   대조할 수 있는 수치 변경이므로 원장에 기록 + §2-E의 아티팩트로 뒷받침할 것.

## 4. Harrison 최종점검 프로토콜 (실행 아님 — 검증만)

§2 A·B가 닫히면 Harrison에게 신호. 최종점검 범위:

1. **P14**: 본문·표·캡션 수치 전수를 커밋된 아티팩트와 자동 대조 — MinerU-on 재베이스 신규
   수치(0.713 / −0.83 / 66.1%)와 P7 full-grid 결과 포함.
2. **P15**: 게시본 미래형 문장 전수 → 개정판 위치 매핑 + §3 편차 원장 확인. 미이행 잔존 시 보류.
3. **PDF 게이트**: 본문 ≤7p / Limitations ≤1p 실측, Type3=0 재확인, blocker 주석 0건,
   렌더링된 참고문헌 26건 수동 검수, 저자 블록 5인 순서·메타데이터 폼 대조.

— 작성: Harrison + 클로드코드 (감사 세션 2026-08-24/25). 실행 문의는 이 문서 기준으로.
