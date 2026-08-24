# EMNLP 2026 Industry Track Camera-Ready 실행 원장 — Accepted (2026-08-21 갱신)

> 근거: OpenReview 최종 게시본 `REBUTTAL_FINAL_EN.md` 전수 추출 — 응답에서 한 모든 약속을 개정 작업으로 변환. 2026-08-22 사용자 제공 최종본 SHA-256: `654e60466b29d137af5aa527e3fd534e14d005378e5571e1775ae3728b0c5f6f`.
> 실행: 상우(1저자). 감사·수치 대조: Harrison + 클로드코드.
> **레포 배치 주석**: 본 계획이 참조하는 `output/rebuttal_pack/`(게시본·번들·런북)은 블라인드/local-only 정책으로 gitignore 상태다 — 공동저자 전달은 공유 번들(zip) 경유. 이 문서 자체는 `docs/PAPER_REVISION_GUIDE.md`의 후속 개정 가이드로 커밋한다.
> **정본 규칙**: camera-ready 편집·빌드 정본은 `paper/latex/main_camera_ready.tex`이다. 심사 제출본 `paper/latex/main.tex`는 비교·감사용으로 동결하며 편집하지 않는다.
> **rebuttal 정본 규칙**: `docs/REBUTTAL_R3_bXGg.md` 등 로컬 reviewer별 파일은 게시 전 초안이다. 최종 게시본과 충돌하면 위 SHA의 최종본이 우선한다.
> 일정·페이지·폼·발표 형식 조건은 acceptance email 원문을 기준으로 기록했다.

## 0. 수락 상태·공식 제출 조건

| 항목 | 확정 상태 / 게이트 |
|---|---|
| Submission | **#384 — Accepted** |
| 발표 형식 | 현재 시스템에는 **Poster**로 기록되어 있으나 provisional 상태이며, 프로그램 편성에 따라 oral로 변경될 수 있음 |
| Camera-ready form | **2026-08-23–2026-08-30** |
| Camera-ready deadline | **2026-08-30 AoE = 2026-08-31 20:59 KST** |
| 내부 제출 목표 | 마감일의 마지막 시간대를 피하도록 **2026-08-30 KST 안에 제출 완료** |
| 페이지 | 본문 최대 **7쪽** + 필수 Limitations와 선택 Ethical Considerations를 합쳐 추가 최대 **1쪽**; References와 Supplementary Material은 제한 없음 |
| 저자 순서 | `Sang-Woo Son → Hyeong-seob Kim → Hyeonsang Kim → Hyun-woo Cho → Jinmo Kim`으로 고정 |
| 저자 메타데이터 | PDF의 저자 이름 순서와 camera-ready form의 **5인 이름·이메일 순서**를 대조; **5인 전원의 OpenReview 프로필에 ORCID 등록 필수** |
| 교신저자 | Hyeong-seob Kim 표기 가능 여부를 Industry Track chairs에 문의했고 **회신 대기 중**. 회신 전에는 이름 별표·Correspondence 문구를 넣지 않음 |
| 폼 운영 정보 | 등록 담당자 이름·이메일, 발표자 이메일·거주 국가/지역·visa/초청장 여부, 대면/온라인 및 Oral/Poster 선호, 대면 발표자의 예상 여행일을 확인해 Aug 23–30 폼에 입력 |
| 참고문헌 | `refs.bib`의 26개 키를 1차 출처로 수동 대조하고 축약 저자를 전체 목록으로 확장함(2026-08-21). 최종 PDF에서 저자·제목·venue·연도·ID/링크를 다시 눈으로 확인 |

제출 전 메타데이터 게이트:

- [ ] OpenReview의 5인 이름·이메일을 export/화면 캡처해 PDF author block의 이름 순서 및 camera-ready form의 이름·이메일 순서와 대조
- [ ] 5인 모두 OpenReview 프로필에 ORCID를 등록하고 각 ORCID 프로필의 이름과 저자 정보를 대조
- [ ] 논문 등록 담당자의 이름·이메일과 presenter 1인을 확정
- [ ] 발표자의 이메일·거주 국가/지역·visa 상태·Visa Invitation Letter 필요 여부를 확인
- [ ] 대면/온라인 발표 방식과 Oral/Poster 선호를 확정하고, 대면 발표이면 발표자의 예상 conference travel dates를 확인
- [ ] chairs의 교신저자 회신 반영 여부 결정; 회신이 없거나 불허면 별표·Correspondence 없이 제출
- [ ] 7쪽 이하 본문 / Limitations와 선택 Ethics를 합친 추가 1쪽 이하 / References·Supplement 구획을 최종 PDF 페이지 단위로 확인
- [ ] AI 도구의 결과만으로 종결하지 않고, 렌더링된 참고문헌 26건을 저자가 실제 논문·공식 출판 페이지와 수동 대조
- [ ] 공식 마감보다 앞선 내부 목표인 2026-08-30 KST 안에 form과 PDF 제출 완료

## 1. 게시본 스냅샷 (2026-07-27 실측)

| Comment | 자수 | 여유 |
|---|---|---|
| General Response | 4,797 | 203 |
| NAor1 (공식 R1) | 2,876 | 2,124 |
| ZQv618 (공식 R2) | **4,994** | **6 ⚠️** |
| bXGg (공식 R3) | **4,987** | **13 ⚠️** |

KoGov 수치는 재대조했지만 OHR의 구 7-domain 산출물은 legacy parquet와 v2 parser bundle을 섞은 것으로 사후 확인됐다. 해당 수치와 Distill 비교는 camera-ready 근거에서 제외했으며, 아래 P17을 통과해야 한다. ZQv618·bXGg 게시본은 이력으로 동결한다.

---

## 2. 약속 전수 목록 → 개정 작업 (P1–P16)

### P1. 신설 Appendix C = 파서 문제 정의 + worked example 【GR-4, ZQv618 Point 1, NAor1】

- **완료**: `main_camera_ready.tex`의 `app:familyneutral`은 최종 Appendix C다. `sec:parser-def`에서 parser I/O, 보존·폐기 요소, 문서 유형, pseudo-reference를 정의했고, absent 원인 taxonomy와 근거 수치를 연결했다.
- **worked example**: KoGov `val_0155`의 pseudo-reference `$A=180\,\mathrm{m}^{2}$`와 MinerU-on 출력 `A = 180m`을 대비해 단위 지수 손실이 exact-span absent가 되는 과정을 보였다.

### P2. Appendix 재배열 — "Appendix C" 글자 정합 【응답 5회 지칭】

- **최종 순서:** A OHR alignment/noise(C1) / B E2E top-choice check(C2) / **C parser definition + worked example + family-neutral + 인간검증(P5) + stability(P7)** / D coverage(C3) / E RADP preferences(C4) / F training results(C4) / G training mechanism(C4) / H release scope.
- C2를 논문의 중심으로 읽히게 하려고 C1--C3 검증을 A--D에 먼저 배치하고, 선택 이후의 보조 parser-training 세부를 E--G로 미뤘다.
- LaTeX `\ref` 자동 갱신 뒤 응답 원문의 "Appendix C" 5곳과 최종 레터를 대조했다. Parser I/O, worked example, human verification는 여전히 Appendix C라서 게시본 약속이 유지된다.

### P3. Intro 재구성 【GR-2, NAor1, bXGg】

- 발견 3개가 lead: ① intrinsic 지표와 retrieval의 기술적 불일치(MinerU-on 포함 complete-output r=−0.74; Marker 포함 r=−0.83, tables-on 선택 차이 4.47×) ② parser-vs-chunker 진단 ③ 정렬 subset에서 약 1pp인 DPO 차이와 objective 비교 보류.
- "ought-vs-is delta" 명시(NAor1: "We will state this delta explicitly in the intro").
- **명시적 scope 문장**: "retrieval, not end-to-end generation" (bXGg: "we will state it as an explicit scope").

### P4. 밀도 개선 【ZQv618 Point 4】

- Abstract 다절 문장 분리. parser/chunker/retriever 용어 선행 정의.
- 본문 표 이동: `main_camera_ready.tex`의 현 본문 표 3개 중 **tab:noise·tab:c4 계열 → appendix** (라벨 실행 시 확인). 본문 6페이지 목표를 유지하되 공식 상한 7페이지를 넘지 않는다.
- **C4(§4.5) 섹션 압축 → appendix** (bXGg: "we will compress the section into the appendix") — 본문은 RADP의 operational definition과 제한된 결과 두 단락으로 두고, LoRA/decoding/샘플링·상세표·mechanism은 Appendix E--G로 보낸다.

### P5. 인간 검증 수치 논문 반영 【GR, ZQv618, bXGg】

Appendix C 소절로: 프로토콜(파서 마스킹 시트, LLM-판정 absent frame 층화 100 = MinerU 50/Prod 30/Paddle 20, 저자 2인 독립 판정 → 불일치 19건 공동 합의) + 수치: **κ=0.615 (raw 81/100)** / genuine: **MinerU 84.0% [71.5, 91.7]**, Paddle 95.0% [76.4, 99.1], **Prod artefact 60.0% [42.3, 75.4]** / cross-family judge와 동일분모 대응(84.2/84.1/44.0% — 전부 CI 내) / human–LLM binary **90.3% (n=93**, MinerU 프레임 세대 교집합 사유 각주**)**. 표기는 "the two authors".

- **최종 게시본 대조 완료(2026-08-22)**: bXGg 최종 답변은 “100 cases stratified from the LLM-judged absent sets”의 two-grader human verification을 보고한다. 위 결과가 바로 그 검증이며, 원고 반영 기준 P5는 **완료**다.
- `docs/REBUTTAL_R3_bXGg.md`의 “same 100-Q--A sample the LLM graded” 문장은 게시 전 초안에만 남은 미래형 문구로, 최종 게시본에서 absent-set 검증으로 교체됐다. 이 초안을 최종 약속으로 사용하지 않는다.
- 별도의 100 Q--A quality sample은 LLM-assisted 94/100 평가이며 인간검증으로 주장하지 않는다. 다만 최종 human adjudication per-case 파일은 현재 Git에서 확인되지 않으므로 공개 아티팩트 게이트는 P12에 계속 둔다.

### P6. E2E 표 신설 【bXGg Q2: "We will add the end-to-end table"】

- 열: parser / answer accuracy(72.5/23.8/20.5) / EM / answered rate + RCPS dual-config(0.583 / 0.212 off·0.137 on / 0.140).
- 각주: 하위 2개 근소차(ΔRCPS≈0.003) — rank-2/3 순서만 MinerU 설정 의존, 배포 선택 불변. "3–3.5×"는 vs MinerU/Paddle 각각.
- 소스: `output/results/e2e_rag.json`(dual-ref 커밋본).
- **최종 표기 원칙**: answer generation이 MinerU-on으로 실행됐으므로 표의 answer accuracy에는 MinerU-on RCPS `0.137`만 짝지어 표시한다. MinerU-off `0.212`는 같은 문단에서 별도로 공개하되 answer accuracy와 한 행의 same-configuration 결과처럼 묶지 않는다.

### P7. Probe-resampling stability — full-grid 【bXGg Q1: "The full-grid version goes into the revision"】

- **Git aggregate 감사 완료(2026-08-22)**: `output/baselines/grid_v1_parser_native.json`에는 30B/Prod/2B-base/MinerU-off/Paddle의 294페이지 집계와 Marker의 38페이지 집계가 있고, `output/baselines/chunking_grid_v1.json`에는 동일 294페이지의 Prod×4청커 집계가 있다. 즉 과거의 “6-parser grid” 전체를 동일 294페이지라고 부르면 안 된다.
- **MRR@10-only 검증 완료(CPU)**: `scripts/analysis/fullgrid_aggregate_audit.py`와 `output/results/fullgrid_aggregate_audit.json`이 저장 aggregate를 재구성해 RCPS와 3-retriever 평균 MRR@10-only의 순위가 5개 294페이지 parser, 모든 저장 parser 행, Prod×4청커에서 모두 동일함을 확인한다(Kendall $\tau_a=1.0$). 이는 MRR@10-only 약속만 닫으며 probe-resampling을 대신하지 않는다.
- **동일 294페이지 per-QA full-grid는 여전히 대기**: 현재 유효한 294페이지 per-QA는 MinerU-on×parser_native 한 configuration뿐이다. 최종 안정성 분석은 30B/Prod/2B-base/MinerU-off/MinerU-on/Paddle×parser_native와 Prod의 나머지 3청커를 같은 294페이지 코퍼스·동일 663 Q--A·동일 retriever/cutoff로 수출한 9개 고유 system에서 실행한다. Marker는 294페이지 출력이 새로 확보되지 않는 한 제외한다. 그 뒤 `rank_stability_bootstrap.py`(e005ad7) → 결과 JSON+MANIFEST를 만든다.
- 기존 242페이지 fold 결과는 훈련 분석용 보조 결과일 뿐이다. **242페이지와 294페이지 결과를 한 stability 표·문장·bootstrap 풀에서 혼합하지 않는다.** Appendix C에는 동일 294페이지 full-grid가 완료된 뒤 그 결과만 넣는다.
- 현재 가용 풀의 파서쌍 100%/청커 근소쌍 98.8%/E2E 100% 수치는 provisional 진단으로만 보관하며, 294페이지 full-grid와 동일성이 확인되기 전 camera-ready 근거로 승격하지 않는다.
- ⚠️ **format-normalisation 문장만 미해결** — "format normalisation shifts scores by 0.02–0.03"은 저장 aggregate가 이미 format-normalised relevance로 축약돼 있어 복원할 수 없다. ranked chunk 목록을 회수하거나 재색인한 뒤 검증하며, 그 전에는 논문에 넣지 않는다.

### P8. MinerU tables-on 정식 반영 【GR, ZQv618 self-audit】

- Table 1: MinerU-on deployment 행과 MinerU-off submitted-output 진단 행을 분리한다. 공정 비교의 헤드라인은 tables-on `42.6pp / 4.47×`로 둔다.
- 최종 rebuttal은 tables-off `35.1pp`를 lower bound라고 불렀지만, 두 실행은 MinerU 소프트웨어와 retrieval 환경도 달라 단조관계가 보장되지 않는다. Camera-ready 원고에서는 이 표현을 반복하지 않고 submitted-output diagnostic과 audited deployment comparison으로만 구분한다.
- Limitations에 config 교정 서술: tabular absent 87.9→41.7%(still ~3× Prod 13.9%), 전체 L1 gap +50.2→+45.9pp, retrieval은 mixed 0.212→0.137(KoGov-only 0.046, arXiv 0.486). 이 차이를 table-recognition의 causal effect로 해석하지 않는다.

### P9. pseudo-ground-truth 정정 3곳 【ZQv618 Point 1 "(see Limitations)"】

- `paper/draft/paper.md`의 "human-curated ground-truth" 잔여 표현을 참고해 **정본 `main_camera_ready.tex`만** pseudo-GT 서술로 점검·보강한다. 동결본 `main.tex`은 수정하지 않는다.

### P10. 재현성 체크리스트 + exact run commands appendix 【NAor1 조건부 제안 — 이행 권장】

- 문안·명령어 골격은 준비했지만 **외부 입력 대기**: P7의 동일 294페이지 full-grid 산출물, P12의 공개 경로/릴리스 태그, 최종 공개 URL이 확정돼야 exact command를 실제 clean checkout에서 실행 검증할 수 있다. 검증 전에는 “exact/released” 완료로 표시하지 않는다.

### P11. 데이터 구성·오염 상한 문장 【GR】

- "294 = 229 KoGov + 65 arXiv / Q–A 527+136 / 페이지 단위 분할 / 오염 기여 상한 **4.9pp**(=파인튜닝 delta: Prod−2B-base Hit@1 0.5485−0.4997=4.88pp) vs 파서 갭 42.6pp" — Appendix H 또는 Limitations에 명문화.
- **CR-1**: 공개 데이터 도메인 행 오류(arXiv 613→864). **CR-2**: HF 카드 277→283+24. (기존 큐, `docs/PAPER_REVISION_GUIDE.md` §8b)
- **정합성 정정(2026-08-22)**: Prod−2B-base의 4.9pp 차이는 fine-tuning과 데이터 중복의 효과를 분리하지 않으므로 엄밀한 "오염 기여 상한"이 아니다. 현재 원고는 이를 42.6pp와 비교하는 **규모 참고값**으로만 보고한다. P11을 완료하려면 상한 논리를 별도로 입증하거나, 계획·응답의 "upper bound" 약속을 철회하고 제한된 비교로 명시해야 한다. CR-1/CR-2도 최종 공개 산출물에서 재확인한다.

### P12. 아티팩트 공개 정합 — "Everything is released" 실체화 【GR】

- 완료 ✅: judge cache 1,017(d4a41bb) · e2e dual-ref · 분석 스크립트(rank_stability 포함) · MinerU tables-on predictions · MANIFEST.
- **외부 입력 대기 / 미완**: ① **MinerU tables-OFF predictions** 원본 회수·커밋("release both outputs" 약속의 나머지 절반 — 현재 WSL에만) ② 동일 294페이지 full-grid stability JSON(P7) ③ 인간 검수 per-case 라벨 공개에 대한 저자 결정. 권장: 최종 adjudicated 100건 라벨 + 프로토콜 문서 공개(검수자 익명 "author A/B"), answer key 구조상 blind 재현 가능하게. 이 셋이 없으면 “Everything is released” 문구를 사용하지 않는다.
- **OHR manifest 교정 완료 ✅**: mixed-version 7-domain/OHR TextNED/구 CI를 `MANIFEST.legacy-invalid.sha256`로 격리하고, current `MANIFEST.sha256`에는 raw per-QA의 용도 경고와 `ohrbench_alignment_audit.json`·생성 스크립트 hash를 넣었다. 두 manifest 모두 checksum 검증을 통과했다. full v2 rerun 전에는 strict 2,036 compatibility audit만 current evidence로 표시한다.

### P13. De-anonymization 【camera-ready 관례】

- **외부 입력 대기**: 저자 순서는 `Sang-Woo Son → Hyeong-seob Kim → Hyeonsang Kim → Hyun-woo Cho → Jinmo Kim`으로 고정한다. PDF 저자 이름 순서와 camera-ready form의 5인 이름·이메일 순서를 대조하고, 5인 전원의 OpenReview 프로필에 ORCID를 등록한다. Acceptance email은 PDF의 이메일·ORCID 표기를 요구하지 않으므로 이를 메일 요구사항으로 간주하지 않는다. 소속·acks·라이브 링크(HF/GitHub)는 최종 템플릿과 저자 결정에 따라 복원하되, Hyeong-seob Kim의 교신저자 별표·Correspondence는 Industry chairs의 서면 회신 전 추가 금지.
- 벤치마크 명명 일관성(논문 "KoGov" 표기 vs HF "KoGovDoc-RAG") 정책 확정 후 통일. HF 카드 정정은 CR-2와 함께.

### P14. 수치·lineage 정합 감사 (자동)

- 응답과 아티팩트 간 미세 라운딩 통일 — 예: 응답 "−1.3 to +5.0pp"(같은 가족 gap)의 −1.3은 아티팩트 표(−1.4, 1.36의 반올림) 기준으로 논문에선 −1.4 계열 사용.
- 기존 검증 스크립트(scratchpad verify_pack.py) 확장 → camera-ready 본문 수치 전수 자동 대조 1회.
- OHR dataset SHA/version, `QA target page IDs ⊆ parser page IDs`(누락 0 hard gate), 제외 223+5, n=1,043/2,036, seed42 CI, 표·캡션·figure source를 함께 검사한다. **최종 figure와 full v2 결과 전까지 pending**이다.

### P15. 약속-이행 최종 게이트

- **외부 입력 대기**: P7·P10·P12·P13·**P17**이 닫히고 P18·P19가 원고에 반영된 최종 개정판에서만 실행한다. chairs 회신과 공개 URL/릴리스도 확정한 뒤 `REBUTTAL_FINAL_EN.md`의 모든 미래형 문장("will …", "goes into the revision", "we add …") 추출 → 개정판 대응 위치 매핑 체크리스트를 실행한다. 하나라도 미이행이면 camera-ready 제출 보류.

### P16. 아키텍처·개요 그림 개정 【camera-ready 시각·수치 정합】

- **stale MinerU table-off 제거/격리**: 아키텍처·overview 그림의 headline `35.1pp / 2.8×`, MinerU Hit@1/RCPS/absent 수치가 table-off 값인지 전수 확인한다. 공정 비교의 주 표시는 같은 table-on 설정의 `42.6pp / 4.47×`로 맞추고, table-off 값은 필요할 때만 “submitted-output diagnostic”으로 분리한다. 환경이 함께 바뀌었으므로 “lower bound”나 table-recognition causal effect로 표기하지 않는다.
- **코퍼스 단위 명시**: camera-ready 평가 코퍼스는 `294 = 229 KoGov + 65 arXiv`임을 그림에 표시한다. 훈련 분석용 242페이지 fold와 294페이지 full corpus를 하나의 박스·화살표·분모로 합치지 않는다.
- **same-configuration E2E**: Top-1 선택 보존만 제시한다. 3-system `ρ=0.5`는 표본이 너무 작으므로 headline/그림에서 제거하고, table-off RCPS와 table-on answer accuracy를 섞지 않는다.
- **가독성 QA**: 최종 2-column PDF에서 100% 확대 및 흑백 인쇄 기준으로 최소 글자 크기, 선 굵기, 범례, 색각 대비, 잘림, 약어 정의를 점검하고 캡션만 읽어도 흐름이 복원되게 한다.
- **generator source collision 점검**: Q--A 생성기, E2E answer generator, LLM judge의 모델 ID·prompt·cache·source-page key를 구분해 도식과 manifest에서 대조한다. 동일 모델을 재사용했다면 역할을 명시하고, source-page/QA ID 충돌·캐시 오염·gold leakage가 없는지 자동/수동으로 확인한다.
- **canonical source 충돌 제거(2026-08-24 최종 결정)**: camera-ready 삽입 정본은 `paper/figures/fig_overview.pdf`, 편집 정본은 `paper/figures/fig_overview_camera_ready.pptx`다. 원래 디자인은 유지하고 RCPS 배지만 C2, coverage 배지만 C3로 교체했다. `scripts/figures/make_fig_overview.py`와 중간 `fig_overview_vector.*`는 비정본 시안이며 정본을 덮어쓰지 않는다.
- **그림별 수정 명세**: Fig1은 Distill/구 OHR 수치와 `35.1pp/2.8×`를 제거하고 294=229+65 및 527+136 Q--A를 표기한다. Fig2의 `Hit@1 0.20→0.55`와 `retriever-agnostic`을 제거한다. Fig3의 인과 문구를 exact-span 한정으로 낮추고 글자/폰트를 키운다. Fig4는 tables-on `0.123→0.549`, `42.6pp/4.47×`로 맞춘다. OHR visual은 Law--Manual 1,043만 사용하며 full v2 전 7-domain 그림을 금지한다.
- **출력 QA**: Fig1 0.9–1.0 textwidth, Fig2/3 0.9–1.0 column, Fig4 0.75–0.9 textwidth를 목표로 하고 100% 화면·흑백·Type3=0을 확인한다.
- **진행 기록(2026-08-24)**: Fig1--4를 최신 수치로 재생성·합본 삽입하고 실제 PDF 렌더를 검수했다. Fig1은 원래 색을 유지하면서 C2=RCPS/C3=coverage 배지, 수식 표기, 균형 잡힌 박스 비율, 선택 체크 포인트를 반영했다. Fig2의 수식·박스 연결 화살표와 Fig3의 endpoint guide를 연장했고, Fig4에는 42.6pp/4.47×를 같은 MinerU-on 구성으로 표시했다. 전체 14쪽 빌드에서 overflow·깨진 참조가 없고 Type3 font는 0개다.

### P17. OHR-Bench 버전·source-page 정합 게이트 【post-acceptance P0 audit】

- legacy parquet(4,330p)와 v2 parser/PDF bundle(8,561p)을 섞은 7-domain artifact를 camera-ready 근거에서 제외한다.
- C1은 source-aligned Law--Manual **1,043 Q–A**만 사용한다. C4는 stored-zero `notes` 223건과 missing-page 5건을 제외한 strict 6-domain **2,036 Q–A**만 사용한다.
- 완료 ✅: `scripts/analysis/audit_ohrbench_legacy_alignment.py`와 `output/results/ohrbench_alignment_audit.json`이 strict mask, 5개 QA ID, domain count, 1k paired bootstrap(seed 42)을 deterministic하게 재현한다. OHR scorer에는 전역 basename resolver와 evidence-page coverage hard gate를 추가했다.
- 미완 ⏳: official v2 parquet+`qas_v2.json` 전체 재실행, clean-machine audit, Distill per-QA 동일 2,036 subset 복원 및 직접 paired contrast. Distill을 복원하지 못하면 정량 행과 우월성 문구를 완전히 제외한다.
- `ohrbench_7dom_*`, 구 CI/combined CI, administration per-domain, OHR TextNED는 validity 상태를 manifest/README에 명시한다. `fig_noise_family`는 aligned Law--Manual로 재생성하기 전 사용 금지다.

### P18. MinerU-on Boundary Clarity 완결 【독해 중 발견한 correctness/evidence 보강】

- **측정 완료, 정리·병합 대기**: 원격 `codex/mineru-on-bc`의 `524fd58`이 MinerU-on 294페이지·903청크·609경계에서 BC **0.713211**(유효 609/609, 누락 0)을 산출했다. 입력 manifest와 참조 artifact hash, 경계 수 가중 평균은 2026-08-23 로컬 감사에서 일치했다. MinerU-off BC 0.7161과 수치상 가깝고 Prod 0.610보다 0.1032 높으며, MinerU-on을 사용한 complete-output 4-parser BC--RCPS Pearson은 **-0.7445**로 두 자리 표기 **-0.74**를 유지한다.
- **병합 전 게이트**: 결과 문서의 `statistically indistinguishable`를 `numerically nearly identical`로 낮추고, PaddleOCR에도 BC가 없으므로 “every other complete-output parser has BC”를 “the other three vision--language parsers have BC”로 고친다. `4.7x worse`는 “Prod Hit@1 is **4.47x** MinerU-on's”로 바로잡는다.
- **provenance 게이트**: 현재 JSON은 새 runner를 포함하지 않은 `b563327`과 `git_dirty=true`를 기록한다. runner/tests 수정본을 먼저 커밋한 뒤 clean code commit에서 재실행하고, checkpoint에는 input manifest·model revision·max_tokens·min_chars fingerprint를 넣어 설정 불일치 resume를 거부한다. 최종 pytest/ruff의 실제 통과 개수도 실행 기록에 남긴다.
- **원고·Figure 4 반영 완료(2026-08-24)**: Table 1의 MinerU-on BC를 `0.713`으로 채우고 C1의 complete-output 4-parser 상관을 MinerU-on 기반 **-0.74**로 통일했다. Marker까지 추가한 n=5도 MinerU-on/current RCPS로 재기준화해 **-0.83**으로 갱신했다. Figure 4는 동일한 on 구성과 42.6pp/4.47x를 사용한다. MinerU-off는 submitted-output diagnostic으로만 분리하고 on/off 차이를 table recognition의 인과효과로 해석하지 않는다.

### P19. 기여 번호와 결과 절을 실제 workflow 순서로 재배열 【사용자 확정 editorial 변경】

- **목표 기여 순서**: C1 = intrinsic metric--retrieval disconnect, **C2 = RCPS로 parser--chunker 선택**, **C3 = coverage로 parser-side absence와 chunker-side split 진단**, C4 = 필요할 때 parser training.
- 편집 전 §3 Methods는 이미 `RCPS -> Coverage` 순서였으므로 정의 순서는 유지했다. 편집 전 §4 Experiments의 `C1 -> Coverage(C2) -> RCPS(C3) -> C4`는 **C1 -> RCPS(new C2) -> Coverage(new C3) -> C4**로 subsection 본문 자체를 이동했다. 단순 문자열 치환으로 끝내지 않았다.
- 전역 동기화 대상: Abstract의 workflow, Introduction contributions, Related Work의 `C1--C3`, Figure 1 내부 C1--C4와 caption, §4 subsection 제목·도입·표/그림 caption, Discussion/Conclusion, Limitations, Appendix의 contribution 참조, README/README.ko 및 재현 문서. 이동 뒤 `\label`/`\ref`와 첫 등장 정의를 다시 검사한다.
- RADP는 C4 첫 등장에 **Retrieval-Aware Document Parsing (RADP)**로 풀고 parser-training umbrella임을 한 문장으로 한정한다. C4 이전에는 일반적인 parser-side training 예고만 남긴다. RCPS는 training-free 선택 protocol, coverage는 retriever-free 진단, RADP는 선택·진단 뒤 필요한 경우의 학습으로 구분한다. §4.1의 LoRA/λ/decoding/preference-sampling 같은 학습 전용 setup은 C4 또는 Appendix로 옮기고 main C4는 결과 중심으로 압축한다.
- 데이터 문구는 294=229 government+65 arXiv, 663=527+136, 242 evidence pages+52 distractors를 섞지 않고, 663 Q--A가 RCPS·coverage·E2E에 쓰인다는 점과 전체 human-written answer key가 아니라 pseudo-reference+LLM-generated Q--A라는 점을 유지한다. C4는 audited compatibility subset에서 관측된 약 1pp 차이로만 제한하며, unavailable aligned Distill artifact로 matched-objective/causal claim을 만들지 않는다.
- **명시적 제외**: Figure 1의 `Ref. page + span`을 `Reference page + answer span`으로 풀어 쓰는 제안은 사용자 결정에 따라 수정 목록에서 제외한다.
- **전역 반영 완료(2026-08-24)**: Abstract/Introduction/§4/Discussion/Limitations와 Figure 1 badge를 새 C1→C2 RCPS→C3 coverage→C4 순서로 동기화했다. §4의 RCPS와 coverage subsection은 본문 블록 자체를 이동했다. 후속 hierarchy pass에서 C4를 optional secondary study로 명시하고 RADP-aux/DPO/Distill을 operational하게 정의했으며, Appendix A--D는 C1--C3 검증, E--G는 C4 상세로 재배열했다. Appendix C 약속과 `Ref. page + span` 문구는 보존했다.

---

## 3. 실행 순서 (의존성)

```
[완료]               P2 → P1·P5·P6·P8 → P3·P4 → P9·P11 → P16 Figure 1--4 시각 정합
[지금–폼 오픈 전]   P18 MinerU-on BC artifact 정리·병합 · P17 OHR strict audit 완료분 고정·full v2 준비 · P7 동일 294p full-grid(WSL) · P12 tables-OFF 회수
[Aug 23–30]          form 메타데이터(5인 이름·email, OpenReview ORCID, 등록 담당자, 발표자 visa·travel, 발표 방식·선호) 입력 · P13 de-anon 확정
[외부 입력 수령 후] P7·P12·P17 full v2/Distill 결정 → P10 exact-command 검증 → P14 수치·lineage 감사 → P18·P19 반영 후 figure/번호 정합 재검증 → P15 약속-이행 최종 게이트
[제출 직전]          페이지 규칙·수동 참고문헌·저자순서·PDF 렌더·링크 최종 확인 → 내부 목표인 Aug 30 KST 안에 업로드
```

## 4. 리스크

1. **Appendix C 글자 재불일치** — P2 완료 후 응답 원문 5곳 대조 필수 (구번호 사고 재발 방지 항목).
2. **P7 미확인 문장 2개** — 근거 없으면 응답이 이미 주장한 사실이라 재계산으로 반드시 채워야 함. 조기 확인.
3. **페이지 제한 오해** — 공식 게이트는 본문 최대 7쪽, 필수 Limitations와 선택 Ethical Considerations를 합쳐 추가 최대 1쪽, References/Supplement 무제한이다. Ethics에 별도 추가 페이지가 더 허용된다고 해석하지 말고 최종 PDF에서 구획별 페이지를 직접 센다.
4. Marker 38페이지 각주 유지(코퍼스 불일치).
5. **구성 혼합** — 242p 훈련 fold와 294p 평가 full-grid, MinerU table-off/on, E2E generator/judge cache를 한 결과처럼 섞지 않는다.
6. **메타데이터 지연** — 5인 이름·이메일 순서, 전원 OpenReview ORCID, 등록 담당자, 발표자 거주지·visa·초청장·대면 시 여행일, 발표 방식·선호 및 chairs 회신이 P13/P15의 외부 의존성이다. Aug 23 폼 오픈 즉시 누락자 추적.
7. **OHR 버전 혼용 재발** — 구 manifest에 hash가 있다는 사실은 validity 증거가 아니다. dataset/version SHA, evidence-page coverage 100%, exclusion/CI derivation이 함께 맞지 않으면 수치·표·그림을 사용하지 않는다.
8. **폰트** — 최종 Figure 1--4와 합본 PDF를 `pdffonts`로 검사해 Type3=0을 확인했다. 이후 그림을 재수출하면 같은 검사를 다시 수행한다.

## 5. 역할

- **상우**: P1–P19 실행(1저자 전권), WSL 런(P7·P12-①·P17 full v2·P18 BC), form owner.
- **Harrison + 클로드코드**: P14·P15 감사 자동화, 개편·아키텍처 리뷰, 수치·참고문헌 대조.
- **전 저자 5인**: 이름·이메일 순서 확인, 각자 OpenReview 프로필에 ORCID 등록.
- **등록 담당자·발표자**: 등록 담당자 이름·이메일, 발표자 이메일·거주 국가/지역·visa/초청장 여부, 대면 시 예상 여행일 제공; 저자진은 대면/온라인 및 Oral/Poster 선호 확정.
