# main_camera_ready.tex 개정 워크맵 (P1–P19 → 실제 편집 위치)

> 상태: EMNLP 2026 Industry Track Submission **#384 Accepted**. 현재 Poster로 기록되어 있으나 provisional이며 oral 변경 가능.
> 대상·정본: `paper/latex/main_camera_ready.tex`. 심사 제출본 `paper/latex/main.tex`는 비교·감사용으로 동결하며 편집 금지.
> Camera-ready form: **2026-08-23–2026-08-30**. 마감: **2026-08-30 AoE = 2026-08-31 20:59 KST**. 내부 제출 목표는 마지막 시간대를 피한 **2026-08-30 KST 안**이다.
> 재실행/외부 입력이 남아 있다. P7은 2026-08-27 완료했다. P10/P12/P13/P15/P17과 P18 artifact 정리·병합은 아직 완료로 간주하지 않는다. P14는 현재 공개 근거 범위의 재감사를 마쳤지만 외부 artifact 반영 후 다시 실행한다. P18/P19의 원고·README·활성 문서 반영과 PDF 정합 검수는 2026-08-24 완료했다.
> 줄번호는 편집 전 기준(편집하면 밀림).

## 제출·메타데이터 게이트

- 페이지: 본문 최대 **7쪽** + 필수 Limitations와 선택 Ethical Considerations를 합쳐 추가 최대 **1쪽**; References/Supplementary Material은 제한 없음.
- 저자 순서 고정: `Sang-Woo Son → Hyeong-seob Kim → Hyeonsang Kim → Hyun-woo Cho → Jinmo Kim`.
- PDF 저자 이름 순서와 camera-ready form의 5인 이름·이메일 순서를 대조하고, **5인 모두 각자의 OpenReview 프로필에 ORCID를 등록**한다. Acceptance email은 PDF의 이메일·ORCID 표기를 요구하지 않는다.
- 등록 담당자의 이름·이메일, 발표자의 이메일·거주 국가/지역·visa/초청장 여부와 대면/온라인 여부를 Aug 23–30 form에 입력한다. 선호는 Oral / Poster / No preference 중 선택하고, 대면 발표자는 Budapest 도착·출발일을 `YYYY-MM-DD`로 입력하며 선택적 scheduling constraints를 정리한다.
- Industry Track chairs가 저자 순서를 유지한 Hyeong-seob Kim의 교신저자 지정과 PDF 각주 표기를 서면 승인했다. 이름 별표 없이 ACL 템플릿의 `Correspondence: harrison@wigtn.com` 줄을 반영한다.
- `refs.bib` 26개 키는 2026-08-26 공식 출판·venue·arXiv 기록 기준으로 재검증해 출판 버전·전체 저자·DOI·페이지를 정정했다. 최종 PDF의 저자·제목·venue·연도·ID/링크를 저자가 수동 검증한다.

## 현재 구조 (P18/P19 반영 후)
- Abstract · §1 Introduction(+Fig1) · §2 Related Work
- §3.1 RCPS(Eq.1, Fig2) · §3.2 Coverage(Fig3)
- §4.1 Evaluation Frames/Setup · §4.2 C1(Fig4) · §4.3 C2 RCPS(Tab1/ablation) · §4.4 C3 Coverage · §4.5 C4 RADP training
- §5 Discussion/Conclusion · Limitations
- App A OHR version audit/noise · B E2E top-choice check · C family-neutral/parser definition/human verification · D coverage · E RADP preferences · F training results · G training mechanism · H reproducibility

## 확정 부록 순서 (P2/P19)
A OHR alignment/noise(C1) / B E2E top-choice check(C2) / **C = 정의+worked-ex(P1)+family-neutral+human(P5)+stability(P7)** / D coverage(C3) / E RADP preferences(C4) / F training results(C4) / G training mechanism(C4) / **H repro(P10)+data(P11)**

---

## 편집 항목

| P | 위치 | 작업 | 상태 |
|---|---|---|---|
| **P2** | App 블록 | 독자 순서를 C1--C3 검증(A--D) → 보조 C4 학습(E--G) → 공개 범위(H)로 재배열했다. 최종 게시본이 약속한 parser definition/worked example/human verification는 Appendix C에 그대로 유지하고 `\label`/`\ref`를 재검증했다 | ✅ 완료 |
| **P1** | App C 상단 | parser I/O(정부문서, born-digital+스캔, 다단·직인·병합셀), 보존·폐기 요소, absent taxonomy와 수치를 정의했다. Worked example은 `val_0155`의 pseudo-reference `$A=180\,\mathrm{m}^{2}$`와 MinerU-on `A = 180m`을 대비한다 | ✅ 완료 |
| **P3** | §1 Intro | 발견 3개 lead(complete-output r=−0.74, Marker 포함 r=−0.83 / tables-on 42.6pp·4.47× / parser-vs-chunker 진단 / 정렬 subset DPO 약 1pp) + scope 한계 | ✅ 완료 |
| **P4** | Abstract / §4.5 / App E--G | Abstract에서 training을 secondary study로 명시하고, C4를 RADP 정의·변형 설명과 제한된 결과의 두 단락으로 압축했다. LoRA/decoding/샘플링·상세 결과·mechanism은 App E--G로 이동. 본문 6pp 목표(공식 상한 7pp) | ✅ 완료 |
| **P5** | 새 App C 소절 | 최종 게시본이 보고한 `LLM-judged absent sets` 층화 100건(MinerU50/Prod30/Paddle20)의 parser-masked two-author 검증, κ=0.615/raw81, 19건 adjudication, human–judge 90.3%(n=93)를 반영. 로컬 R3 초안의 “same 100 Q--A” 문구는 최종 게시본에서 교체된 비정본 문구임. per-case human label 공개는 P12 게이트 | ✅ **완료(원고)** |
| **P6** | §4 또는 App | E2E 표 신설: parser/answer-acc(72.5/23.8/20.5)/EM/answered. 같은 MinerU-on 구성의 RCPS 0.137을 accuracy와 짝지었고, MinerU-off 0.212는 본문에서 별도 공개해 config 혼합을 차단. src `output/results/e2e_rag.json` | ✅ 완료 |
| **P7** | §4.2 robustness + 공개 artifact | 동일 294p(229 KoGov+65 arXiv), 663 Q--A, 9 unique systems를 재색인했다. 500-Q--A×1,000 bootstrap에서 parser mean $\tau_a=0.902$, Prod-vs-Base/OCR 100%, chunker full-order 96.1%다. Raw 대비 normalised 차이는 0.024--0.041이고 두 pool order가 유지된다. Marker와 242p fold는 제외 | ✅ **완료** |
| **P8** | Tab1 / Limitations L194 | MinerU-on deployment 행과 MinerU-off submitted-output 진단 행을 분리. 헤드라인은 **42.6pp/4.47×**. 두 실행은 software/retrieval 환경도 달라 35.1pp를 lower bound나 causal table ablation으로 재주장하지 않음. Limitations 수치 갱신(tabular87.9→41.7%, gap+50.2→+45.9pp, retrieval0.212→0.137) | ✅ 완료 |
| **P9** | `main_camera_ready.tex` 전역 | "human-curated ground-truth"→pseudo-GT 잔여 표현 점검. 동결본 `main.tex`은 수정하지 않음 | ✅ 완료 |
| **P10** | App H | 재현성 체크리스트/명령어 골격과 P7의 294p 결과는 존재. P12 공개 경로·릴리스 태그, 최종 URL 수령 후 clean checkout에서 exact commands 실행 검증. 검증 전 “exact/released” 완료 표기 금지 | ⏳ **외부 입력 대기** |
| **P11** | App H 또는 Limitations | 데이터 구성(294=229KoGov+65arXiv, Q–A527+136, 페이지분할)은 반영. 4.9pp는 오염의 엄밀한 상한이 아니므로 원고에서 규모 참고값으로만 표기. 상한 논리 입증 또는 약속 철회, CR-1/CR-2 최종 검증 필요 | ⚠️ **부분 완료** |
| **P12** | 레포 | OHR mixed-version manifest 격리·strict audit hash 교체와 동일 294p full-grid JSON은 완료. MinerU tables-OFF 원본 회수, 인간라벨 공개 결정, checkpoints는 대기. 닫히기 전 “Everything is released” 금지 | ⏳ **외부 입력 대기** |
| **P13** | 전역 | 5인 고정 순서로 de-anon하고 소속·이메일·ORCID·acks·라이브링크를 확정. OpenReview/form/PDF 순서 일치. Chairs의 서면 승인에 따라 PDF에 `Correspondence: harrison@wigtn.com` 반영 완료 | 🚧 **교신저자 완료, 나머지 저자 메타데이터 대기** |
| **P14** | 자동 | 응답↔본문 수치 라운딩 + dataset SHA/version + QA→page coverage + 제외 223+5 + n=1,043/2,036 + seed42 CI + 표/캡션/figure source 전수 대조. 현재 공개 artifact 범위는 2026-08-24 재감사했고, full v2/외부 artifact 반영 뒤 최종 재실행 | 🚧 **현재 범위 완료, 최종 외부 입력 대기** |
| **P15** | 자동 | P10/P12/P13/**P17**과 공개 URL/릴리스를 닫은 최종판에서 REBUTTAL_FINAL 미래형 문장 전수→개정판 매핑 체크. P7과 chairs 회신, P18/P19 원고 반영은 완료 | ⏳ **외부 입력 후 최종 감사** |
| **P16** | Fig1–4/아키텍처·캡션 | Fig1은 승인된 원래 디자인을 원복하고 RCPS 배지만 C2, coverage 배지만 C3로 교체했다. 편집 정본은 `paper/figures/fig_overview_camera_ready.pptx`, 삽입 정본은 `paper/figures/fig_overview.pdf`다. Fig2는 수식과 box-to-box 화살표를 정리했고 Fig3 guide endpoint를 연장했다. Fig4는 MinerU-on -0.74/-0.83과 42.6pp/4.47×를 반영했다. 현재 15쪽 합본·Type3=0 확인 | ✅ **최종 시각·수치 재검수 완료** |
| **P17** | OHR 전역 | legacy 4,330p/v2 8,561p 혼용 차단. C1=Law–Manual 1,043; C4=notes223+missing5 제외 strict 2,036. deterministic audit+coverage gate 및 current/quarantine manifest 분리 완료. full v2 rerun과 Distill same-subset artifact 복원/삭제 결정은 대기 | 🚧 **P0: 부분 완료, WSL/외부 입력 대기** |
| **P18** | C1 / Tab1 / Fig4 / artifact | MinerU-on BC=0.713211(294p, 903 chunks, 609/609 boundaries), new 4-parser Pearson=-0.7445를 검증했다. 원고·Table 1·Figure 4에는 BC 0.713, 4-parser -0.74, on+Marker/current RCPS n=5 -0.83을 반영했다. `codex/mineru-on-bc`는 문구 3건(statistical claim, PaddleOCR BC, 4.47x)과 dirty provenance/checkpoint fingerprint를 보정한 뒤 병합한다 | 🚧 **원고·Fig4 완료, artifact 정리·병합 대기** |
| **P19** | Intro contributions / §3–4 / Fig1 / App A--H / 전역 C-label | 원고 흐름을 C1 disconnect → **C2 RCPS selection** → **C3 coverage diagnosis** → C4 training으로 통일했다. C4를 secondary/optional로 명시하고 RADP-aux·DPO·Distill의 역할을 정의했다. 부록도 C1--C3 검증(A--D)을 C4 상세(E--G)보다 먼저 배치했으며 Appendix C 약속은 보존했다. `Ref. page + span`은 사용자 결정대로 유지했다 | ✅ **완료** |

## 실행 순서
1. **P18 MinerU-on BC artifact 정리·병합** → 2. **P17 full-v2/Distill 결정** → 3. **P12 외부 artifact** → 4. **P10 exact commands** → 5. **P14·P15 최종 재감사**. P7은 완료.
- 외부 입력: P12 tables-OFF·인간라벨·checkpoints, P17 full v2·Distill artifact/삭제 결정. P7 동일 294p full-grid는 완료했다.
- Aug 23–30 form: P13의 5인 이름·이메일 순서와 OpenReview ORCID, 등록 담당자, 발표자 visa·travel, 발표 방식·선호를 먼저 확정하고, chairs 답변에 따라 교신 표기 여부를 결정.
- 외부 입력 수령 후: P10 exact-command clean-run → P17 full v2/Distill 결정 → P14 수치·lineage 감사 → P18/P19 반영 후 figure·번호 정합 재검증 → P15 약속-이행 최종 게이트.
- 제출 직전: 본문 7p 이하/Limitations와 선택 Ethics를 합친 추가 1p 이하/References·Supplement 구획, 참고문헌 26건, 저자순서, 링크, 최종 렌더를 수동 확인하고 2026-08-30 KST 안에 제출.
