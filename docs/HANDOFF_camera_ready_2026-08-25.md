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
| P4 밀도: 본문 p.6 종료(현재 총 15p), noise·DPO 표 appendix, C4 압축 | ✅ |
| P5 인간 검증 수치 반영(κ=0.615, 84.0% CI, 90.3% n=93, 제외 사유 각주) | ✅ (라벨 공개는 §2-B3) |
| P6 E2E 표(`tab:e2e`), MinerU-on 페어링 원칙 | ✅ |
| P8 Table 1 3구획 분리, 42.6pp/4.47× 헤드라인, "lower bound" 제거 | ✅ (미세갭 §3-a) |
| P9 pseudo-GT 3곳 | ✅ |
| P11 4.9pp "scale only" 격하 + 229+65/527+136 | ✅ |
| P16 그림: overview `294=229+65`, disconnect r=−0.74/−0.81, stale 35.1/2.8× 제거, **Type3=0** | ✅ |
| P17 감사부: alignment audit, 1,043/2,036 분리, "not a full v2 rerun" 명시, aligned Distill 직접 비교 복원 | ✅ |
| MRR@10-only 약속(τ=1.0, `fullgrid_aggregate_audit`) 본문 반영 | ✅ |
| refs.bib 26키, 저자 순서 고정, PDF A4 | ✅ |

## 2. 남은 작업 (우선순위 순)

### A. P7 — full-grid probe-resampling 【2026-08-27 완료】

bXGg Q1의 **"The full-grid version goes into the revision"** 약속은 동일 294페이지·663 Q--A·
9-system artifact와 parser/chunker bootstrap 결과로 닫았다. 과거의 missing-array 문장은 원고에서 교체했다.

1. 동일 294p·663 Q--A·동일 retriever/cutoff로 **9개 시스템 per-QA 수출 완료**.
   Marker와 242p fold는 제외했다.
2. `rank_stability_bootstrap.py` 실행과 결과 JSON·MANIFEST 반영 완료.
3. 본문의 missing-array 문장을 실제 full-grid 수치로 교체했다. Provisional 98.8%는
   md-h3 $>$ parser-native 96.5%로 정정했다.
4. Format normalisation은 raw 대비 0.024--0.041 상승하고 두 pool 순서를 바꾸지 않는다.
   기존 0.02--0.03 범위는 MinerU-on 0.041 때문에 정정했다.

### B. P12 — 아티팩트 3건

1. **MinerU tables-OFF predictions 커밋 완료** — 35번 서버의 원본 294건을 회수했다.
   `audit_mineru_output_release.py`가 229 KoGov+65 arXiv, tables-on과 동일 filename set,
   tree SHA-256, `grid_v1_parser_native.json`의 MinerU aggregate 연결을 검증한다.
   Portable `source_page_map_v1.json`도 294개 `val_####` ID를 4개 parser-output inventory와
   교차검증하며, 242 evidence + 52 distractor와 229/65 domain 구성을 확인한다.
2. **체크포인트 릴리스 모순 해소 완료(2026-08-27)** — RADP-aux 4종, RADP-DPO R1–R3,
   RADP-Distill, RADP-SimPO의 최종 LoRA adapter 9종을 public
   `wigtn/RCPS-RADP-Adapters` `v1.0.0`에 배포했다. 추적 manifest에 source/release hash,
   portable executed config, training/evaluation base를 기록했고, 익명 다운로드 본을
   clean checkout에서 검증했다. Appendix H의 “checkpoints missing” 문장은 공개 상태로 교체했다.
   이 감사에서 RADP-aux가 Qwen3-VL-2B-Instruct에서 학습되고 Prod에 적용된 cross-base
   실행임을 확인해 원고·README의 lineage도 정정했다.
3. **인간 검수 per-case 라벨** — 저자 전용 패키지의 두 평가 파일, sampling manifest,
   19건 adjudication 기록을 scorer로 재검증했다. κ=0.615, 81/100, parser별 비율,
   human--LLM 90.3%(n=93)가 모두 원고와 일치한다. 원본은 패키지 규칙에 따라 공개하지 않으며,
   tex의 관련 blocker 주석과 `final human labels missing` 표현은 제거했다.

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
2. bXGg 답변 "does not beat a fidelity-distillation control" → 동일 2,036-Q–A frame의 Distill 아티팩트를
   복원했다. Distill−R2/R3 직접 paired CI가 모두 0을 포함해 이 부정 결과를 다시 직접 뒷받침한다 ✅.
3. NAor1 답변 "checkpoints are all released" → 공개 `v1.0.0` 9-adapter release와 clean-checkout 검증으로 **해소 완료**.
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
