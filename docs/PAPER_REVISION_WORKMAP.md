# main_camera_ready.tex 개정 워크맵 (P1–P17 → 실제 편집 위치)

> 상태: EMNLP 2026 Industry Track Submission **#384 Accepted**. 현재 Poster로 기록되어 있으나 provisional이며 oral 변경 가능.
> 대상·정본: `paper/latex/main_camera_ready.tex`. 심사 제출본 `paper/latex/main.tex`는 비교·감사용으로 동결하며 편집 금지.
> Camera-ready form: **2026-08-23–2026-08-30**. 마감: **2026-08-30 AoE = 2026-08-31 20:59 KST**.
> 재실행/외부 입력이 남아 있다. 특히 P7/P10/P12/P13/P14/P15/P16/P17을 완료로 간주하지 않는다.
> 줄번호는 편집 전 기준(편집하면 밀림).

## 제출·메타데이터 게이트

- 페이지: 본문 최대 **7쪽** + 필수 Limitations 최대 **1쪽** + 선택 Ethics 등 허용된 추가 페이지; References/Supplementary Material은 제한 없음.
- 저자 순서 고정: `Sang-Woo Son → Hyeong-seob Kim → Hyeonsang Kim → Hyun-woo Cho → Jinmo Kim`.
- PDF·OpenReview·camera-ready form의 5인 이름/이메일을 같은 순서로 대조하고, **5인 모두 ORCID**를 입력한다.
- presenter, registration, visa/travel, presentation preference를 Aug 23–30 form에 입력한다.
- Hyeong-seob Kim의 교신저자 주석은 Industry Track chairs 회신 대기. **서면 승인 전 별표·Correspondence 표기 금지**.
- `refs.bib` 26개 키는 2026-08-21 1차 출처 기준으로 축약 저자를 전체 목록으로 확장했다. 최종 PDF의 저자·제목·venue·연도·ID/링크를 수동 검증한다.

## 현재 구조 (편집 전)
- Abstract L25 · §1 Intro L29(+Fig1) · §2 Related L48
- §3.1 RCPS L56(Eq.1 L62, Fig2 L68) · §3.2 Coverage L77(Fig3 L82)
- §4.1 Setup L91 · §4.2 C1-C2 L98(Fig4 L103) · §4.3 C3 L116(Tab1 L119, Tab4 L144) · §4.4 C4 L161(Tab2 L166)
- §5 Discussion L182 · Limitations L190
- App A milestones · B dpo · C family-neutral/human · D mechanism · E coverage · **F OHR version audit/noise** · G E2E · H reproducibility

## 목표 부록 순서 (P2)
A milestones / B dpo / **C = 정의+worked-ex(P1)+family-neutral+human(P5)+stability(P7)** / D chunk-mechanism / E coverage / F noise / **G repro(P10)+data(P11)**

---

## 편집 항목

| P | 위치 | 작업 | 상태 |
|---|---|---|---|
| **P2** | App 블록 | 현 E(familyneutral)를 C 자리로 이동 → 현 C(mechanism)→D, D(coverage)→E, F유지. `\label` 유지·`\ref` 자동. 완료 후 응답 "Appendix C" 5곳 대조 | ✅ 완료 |
| **P1** | 새 App C 상단 | ① parser-def 확장: 입력(정부문서, born-digital+스캔, 다단·직인·병합셀) + absent 3원인 taxonomy + 수치(Prod tabular 13.9%/figural 71.4%/factoid~21%; MinerU **41.7% tables-on** 병기) ② worked example 1건(val_0096 표붕괴 `RC号甲号` 또는 `13,316→13.316`·`$1.5\mathrm{m}$`) 원문↔출력 대비 박스 | ✅ 완료 |
| **P3** | §1 Intro L29-46 | 발견 3개 lead(full-set r=−0.74, Marker subset 포함 r=−0.81 / tables-on 42.6pp·4.47× / parser-vs-chunker 진단 / 정렬 subset DPO 약 1pp) + scope 한계 | ✅ 완료 |
| **P4** | Abstract L25 / Tab2 / §4.4 | Abstract 다절 문장 분리 + 용어 선행정의 / **tab:c4(Tab2) → appendix** / §4.4 C4 본문 압축(결론 1문단+포인터), 상세 App B로. 본문 6pp 목표(공식 상한 7pp) | ✅ 완료 |
| **P5** | 새 App C 소절 | 최종 게시본이 보고한 `LLM-judged absent sets` 층화 100건(MinerU50/Prod30/Paddle20)의 parser-masked two-author 검증, κ=0.615/raw81, 19건 adjudication, human–judge 90.3%(n=93)를 반영. 로컬 R3 초안의 “same 100 Q--A” 문구는 최종 게시본에서 교체된 비정본 문구임. per-case human label 공개는 P12 게이트 | ✅ **완료(원고)** |
| **P6** | §4 또는 App | E2E 표 신설: parser/answer-acc(72.5/23.8/20.5)/EM/answered. 같은 MinerU-on 구성의 RCPS 0.137을 accuracy와 짝지었고, MinerU-off 0.212는 본문에서 별도 공개해 config 혼합을 차단. src `output/results/e2e_rag.json` | ✅ 완료 |
| **P7** | 새 App C 소절 | **동일 294p**(229 KoGov+65 arXiv), 동일 663 Q--A/config의 full-grid만 최종 근거로 사용. 242p 훈련 fold와 294p 결과를 표·문장·bootstrap에서 혼합 금지. 기존 파서쌍100%/청커98.8%/E2E100%는 provisional로 격리. full-grid JSON은 WSL run 필요; MRR@10-only·normalisation 0.02–0.03도 재검증 | ⏳ **동일 294p WSL 대기** |
| **P8** | Tab1 / Limitations L194 | Tab1에 MinerU(tables-on) 행/dual. 헤드라인: 35.1pp=lower bound, corrected **42.6pp**(4.47×) 병기. Limitations 수치 갱신(tabular87.9→41.7%, gap+50.2→+45.9pp, retrieval0.212→0.137) | ✅ 완료 |
| **P9** | `main_camera_ready.tex` 전역 | "human-curated ground-truth"→pseudo-GT 잔여 표현 점검. 동결본 `main.tex`은 수정하지 않음 | ✅ 완료 |
| **P10** | 새 App G | 재현성 체크리스트/명령어 골격은 존재. P7의 294p 결과, P12 공개 경로·릴리스 태그, 최종 URL 수령 후 clean checkout에서 exact commands 실행 검증. 검증 전 “exact/released” 완료 표기 금지 | ⏳ **외부 입력 대기** |
| **P11** | App G 또는 Limitations | 데이터 구성(294=229KoGov+65arXiv, Q–A527+136, 페이지분할)은 반영. 4.9pp는 오염의 엄밀한 상한이 아니므로 원고에서 규모 참고값으로만 표기. 상한 논리 입증 또는 약속 철회, CR-1/CR-2 최종 검증 필요 | ⚠️ **부분 완료** |
| **P12** | 레포 | OHR mixed-version manifest 격리·strict audit hash 교체는 완료. MinerU tables-OFF 원본 회수(WSL), 동일 294p full-grid JSON, 인간라벨 공개 결정은 대기. 닫히기 전 “Everything is released” 금지 | ⏳ **외부 입력/WSL 대기** |
| **P13** | 전역 | 5인 고정 순서로 de-anon하고 소속·이메일·ORCID·acks·라이브링크를 확정. OpenReview/form/PDF 순서 일치. Hyeong-seob 교신 별표/Correspondence는 chairs 서면 회신 전 금지 | ⏳ **저자 메타데이터·chairs 회신 대기** |
| **P14** | 자동 | 응답↔본문 수치 라운딩 + dataset SHA/version + QA→page coverage 100% + 제외 223+5 + n=1,043/2,036 + seed42 CI + 표/캡션/figure source 전수 대조 | ⏳ **최종 figure/full v2 후 감사** |
| **P15** | 자동 | P7/P10/P12/P13/**P17**, 공개 URL/릴리스, chairs 회신이 닫힌 최종판에서 REBUTTAL_FINAL 미래형 문장 전수→개정판 매핑 체크 | ⏳ **외부 입력 후 최종 감사** |
| **P16** | Fig1–4/아키텍처·캡션 | 이미지 작업은 마지막 단계. canonical generator 충돌 해소; Fig1 Distill/35.1 제거·294/663 구성, Fig2 stale headline/agnostic 제거, Fig3 exact-span 한정·폰트, Fig4 tables-on 42.6pp/4.47×. 흑백·100%·Type3=0 | ⏳ **본문 확정 후 최종 시각 단계** |
| **P17** | OHR 전역 | legacy 4,330p/v2 8,561p 혼용 차단. C1=Law–Manual 1,043; C4=notes223+missing5 제외 strict 2,036. deterministic audit+coverage gate 및 current/quarantine manifest 분리 완료. full v2 rerun과 Distill same-subset artifact 복원/삭제 결정은 대기 | 🚧 **P0: 부분 완료, WSL/외부 입력 대기** |

## 실행 순서
1. **P17 strict audit** → 2. **P2**(뼈대 이동) → 3. **P1·P5·P6**(새 App C) → 4. **P8·P9**(수치정정) → 5. **P3·P4**(본문) → 6. **P11**(App G) → 7. **P16**(최종 그림)
- WSL/외부 입력: P7 동일 294p full-grid, P12 tables-OFF·JSON·인간라벨, P17 full v2·Distill artifact/삭제 결정.
- Aug 23–30 form: P13의 5인 이메일/ORCID와 presenter/registration/visa·travel/preference를 먼저 확정하고, chairs 답변에 따라 교신 표기 여부를 결정.
- 외부 입력 수령 후: P10 exact-command clean-run → P17 full v2/Distill 결정 → P14 수치·lineage 감사 → P16 그림 → P15 약속-이행 최종 게이트.
- 제출 직전: 본문 7p/Limitations 1p/추가 페이지 구획, 참고문헌 26건, 저자순서, 링크, 최종 렌더를 수동 확인.
