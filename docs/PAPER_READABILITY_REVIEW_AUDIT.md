# EMNLP 2026 camera-ready 문장·리뷰 요구사항 전수 감사

> 감사일: 2026-08-22
> 원고 정본: `paper/latex/main_camera_ready.tex`
> 동결본: `paper/latex/main.tex`는 편집하지 않음
> 판정 원칙: 근거가 현재 원고 또는 추적 가능한 산출물에 없으면 완료로 표시하지 않음
> rebuttal 정본: 2026-08-22 사용자 제공 OpenReview 최종 게시본(SHA-256 `654e60466b29d137af5aa527e3fd534e14d005378e5571e1775ae3728b0c5f6f`). 로컬 reviewer별 초안과 충돌하면 최종 게시본을 우선함.

## 1. 결론

- **문장·문단 감사:** 정본의 Abstract부터 Appendix H까지 모든 산문 문장, 절 제목, 표 머리글, 표 캡션, 그림 캡션을 순서대로 읽고 말투, 주어·대상, 선후 논리, 용어, 분모, parser configuration, claim–evidence 범위를 대조했다. 문장과 내러티브 수정은 반영했다.
- **리뷰 약속 감사:** R1/R2/R3 요구사항은 **전부 완료된 상태가 아니다.** 최종 게시본의 100-case absent-label human verification과 MRR@10-only aggregate audit은 원고에 반영됐지만, 동일 294페이지 full-grid probe bootstrap, format-normalisation 재검증, 일부 공개 아티팩트가 아직 없다.
- **시각물:** 사용자의 작업 순서에 따라 그림 파일과 아키텍처는 수정하지 않았다. 따라서 원고 캡션은 정정됐어도 기존 그림 내부의 구 수치·표현은 P16에서 따로 고쳐야 한다.
- **SHACL:** 별도 저장소 `/Users/sangwoo/Desktop/naacl2027-demo`에 분리돼 있다(파일럿 이관 `a2f0a6f`, 엔진 `7d94c98`). EMNLP 저장소의 현재 트리·도달 가능한 이력·원격에는 SHACL 파일이나 브랜치가 없으며, 이번 EMNLP 커밋에서는 수정하지 않았다. 단, 별도 SHACL 작업을 이번 턴에 추가 진행한 것은 아니다.

## 2. 리뷰어 번호 매핑

로컬 rebuttal 파일명과 OpenReview의 공식 리뷰 순서가 다르므로 아래 reviewer ID를 정본으로 사용한다.

| 공식 구분 | Reviewer ID | 로컬 파일에서 보이는 이름 |
|---|---|---|
| R1 | NAor1 | 일부 파일에서 R2로 표기 |
| R2 | ZQv618 | 일부 파일에서 R1로 표기 |
| R3 | bXGg | R3 |

## 3. 문장별·전체 흐름 감사 결과

### 반영한 주요 수정

1. **Abstract:** 문제–근거–프로토콜–진단–훈련의 순서로 재구성하고, 과도하게 긴 문장을 분리했다. RCPS를 새 similarity metric이 아니라 표준 MRR 위의 parser-selection protocol로 한정했다.
2. **Introduction:** `parsers ought to be evaluated by retrieval`과 실제 intrinsic-metric 선택 관행의 차이를 먼저 제시했다. tables-on 근거, exact-span absent/split 결과, 약 1pp의 제한된 training 결과를 앞에 배치했다. retrieval 범위와 end-to-end 범위를 명시했다.
3. **Related Work:** reader-side M-LongDoc, embedding-side InSeNT, parser-side 본 연구의 위치를 분리했다. fidelity control의 aligned artifact가 없으므로 objective 간 우열 주장을 삭제했다.
4. **Methods:** parser, chunker, retriever, RCPS score/protocol, format-normalised relevance, covered/split/absent를 처음 나올 때 정의했다. `absent`가 곧 실제 semantic omission을 뜻하지 않는다고 제한했다.
5. **Experiments:** 294-page full corpus, 242-page evidence fold, 73-page pilot, 1,043-Q–A Law–Manual, 2,036-Q–A compatibility subset을 섞지 않았다. MinerU-off와 MinerU-on을 서로 다른 configuration으로 분리했다.
6. **Results:** 작은 표본의 BC correlation은 descriptive로 낮췄다. parser range와 VLM-only range를 함께 제시해 heterogeneous candidate-pool 효과를 숨기지 않았다. fixed retriever가 있으면 그 retriever를 쓰고, averaging은 미정·near-tie 상황의 hedge라고 명시했다.
7. **Training:** R1/R2/R3 구성과 R2 warm start를 설명하고 R3의 pool을 K=16(기존 두 후보+신규 14개)으로 정정했다. DPO·SimPO 표기와 입력을 정의했다. 실행 provenance가 확인되지 않은 R2 beta 값은 camera-ready 산문에서 제외하고 source comment의 blocker로 남겼다.
8. **Robustness:** parser I/O와 폐기 요소를 정의하고 pseudo-reference임을 명시했다. 원문–MinerU-on 출력 대비표를 추가했다. model-free matcher, cross-family judge, absent-label 인간 검증의 역할과 한계를 분리했다.
9. **Discussion/Limitations:** selection gap과 training delta를 직접 비교하지 않았다. boundary mechanism과 TextNED를 causal claim이 아닌 post hoc observation으로 낮췄다. Q–A lineage, matcher dependence, generator–judge self-evaluation, candidate-pool 범위를 명시했다.
10. **MinerU correction:** MinerU-off submitted-output 진단과 MinerU-on deployment 비교를 분리하고, tables-on의 42.6pp/4.47×, table-evidence 87.9→41.7%, overall absence-gap 50.2→45.9pp, mixed RCPS 0.212→0.137을 Limitations에 연결했다. 두 실행에서 software/retrieval 환경도 달라 35.1pp를 lower bound나 causal table ablation으로 재주장하지 않았다.

### 2026-08-22 2차 sentence-level pass

- Abstract부터 Appendix H까지 각 산문 문장·절 제목·표 머리글·캡션을 다시 읽고, 문장별 주어·비교 대상·분모·시제·claim strength를 확인했다.
- MinerU-off BC와 MinerU-on Hit@1, BGE-M3 top-five E2E retrieval과 3-retriever×3-cutoff RCPS, 73-page held-out pilot과 이후 242-page pooled analysis를 각각 분리했다.
- `improve`, `reduce`, `lower bound`, `equivalent`처럼 현재 설계가 인과·유의성·단조관계를 지지하지 않는 표현을 point estimate·descriptive association 표현으로 낮췄다.
- 100-case human study와 별도의 100-pair Q--A quality check를 명시적으로 분리하고, 1,017 judge 항목을 unique answer가 아닌 parser--answer case로 정의했다.
- Q--A-level bootstrap이 page clustering을 반영하지 않는다는 제한, evidence-type별 정확한 분자/분모(figure 5/7 포함), 세 seed가 Prod seed가 아니라 R1 recipe의 독립 seed라는 사실을 추가했다.

### 2026-08-22 3차 skim-reading narrative pass

- 제목→Abstract→절·소절 제목→각 절 첫 문장→표·그림 캡션 순으로 다시 읽어, 정독하지 않아도 `select with RCPS → diagnose with coverage → train only if needed`가 이어지도록 전체 서술 순서를 재구성했다.
- Abstract 둘째 문장에서 RCPS를 바로 정의하고, Introduction과 Discussion도 선택–진단–훈련 순서로 맞췄다. C1과 C2를 분리하고 결과 절·부록 제목과 캡션을 결론형 문구로 바꿨다.
- evaluation frame을 294-page selection, 242-page training/mechanism, 73-page pilot로 분리했다. selection만 Q--A-free distractor 52쪽을 포함한 294쪽을 index하며, training 분석이 294쪽 전체를 index한다는 기존 혼동을 정정했다. OHR 1,043/2,036 Q--A도 별도 frame으로 유지했다.
- 인과·일반화로 읽힐 수 있는 `loss`, `effect`, `gain`, `predict` 표현을 현재 근거 범위에 맞게 낮추고, E2E 결과는 세 parser의 top-choice check로만 명시했다.
- 그림 파일 자체는 이 pass에서 수정하지 않았다. Figure 1·4 내부의 구 수치와 Figure 2·3의 작은 글자는 P16 시각 단계에서 교체한다.

### 아직 문장만으로 닫을 수 없는 항목

- R2 executed checkpoint의 `beta`가 0.1인지 0.05인지 원 로그/checkpoint config 확인이 필요하다. 현재 Git의 0.05는 논문 서술이고 0.1은 실행 코드/default이므로 어느 쪽도 단독 provenance가 아니다.
- MRR@10-only aggregate ranking은 완료됐다. 동일 294-page full-grid probe-resampling stability와 format-normalisation sensitivity는 여전히 재실행이 필요하다.
- full OHR-Bench v2 rerun과 RADP-Distill same-subset artifact가 없다. 현재 원고는 호환성 subset으로 범위를 낮추고 Distill 비교를 제외했다.
- 저자 affiliation/email/ORCID, 교신저자 chairs 회신, 공개 URL/checkpoint/fresh-clone 명령 검증이 남아 있다.
- 그림 내부 구 수치와 문구는 최종 시각 단계에서 수정해야 한다.

## 4. Reviewer NAor1 요구사항

| 요구사항 | 상태 | 현재 처리 / 남은 일 |
|---|---|---|
| 외부 benchmark 검증 | **부분 완료** | Law–Manual 1,043과 strict six-domain compatibility 2,036은 source-aligned. full official v2 rerun은 미완이며 원고가 이를 명시함. |
| implementation, evaluation code, frozen KoGov set | **완료** | repository와 원고에 범위를 명시. |
| parser-training checkpoints 공개 | **대기** | checkpoint/config/HF release 및 executed provenance 필요. |
| 동일 Q–A와 paired bootstrap | **완료** | paired evaluation 및 CI 명시. |
| exact run commands / reproducibility checklist | **대기** | release tag와 산출물 확정 후 clean checkout에서 실행 검증 필요. |
| ought-vs-is gap을 Intro에 명시 | **완료** | Introduction 첫 문단에 반영. |
| 어려운 문장 분리, 핵심 용어 정의 | **완료(텍스트)** | Abstract·Methods·Appendix 정의 정리. 그림 가독성은 P16 대기. |
| parser problem definition | **완료** | Appendix C에 I/O, 문서 유형, 보존·폐기 요소, worked example 추가. |

## 5. Reviewer ZQv618 요구사항

| 요구사항 | 상태 | 현재 처리 / 남은 일 |
|---|---|---|
| parser input/output와 문서 유형 정의 | **완료** | born-digital/scanned, multi-column, merged cells, stamps/seals, figure text 포함. |
| Markdown 보존·폐기 요소 | **완료** | body/headings/tables와 coordinates/fonts/imagery/page furniture를 구분. |
| absent 원인 taxonomy와 수치 | **완료** | table cells, in-image text, numerals/units 및 parser별 수치 반영. |
| pseudo-ground-truth와 Qwen lineage 공개 | **완료** | Setup, parser definition, Limitations에서 반복 확인. |
| source/reference ↔ parser output worked example | **완료** | `val_0155`의 m²→m 손실을 대비표로 추가. |
| model-free L0–L4 matcher ladder | **완료** | matcher 정의·분모·해석 반영. |
| cross-family recoverability judge | **완료** | GPT-family QA 생성과 완전히 독립적이지 않다는 제한까지 명시. |
| blind human absent-case subsample | **완료(분석)** | 100 cases, κ=0.615, 81/100 raw agreement, Wilson CI, 93-case overlap 반영. |
| adjudicated human labels 공개 | **대기** | per-case artifact와 manifest 필요. |
| MinerU tables-on correction | **완료(원고)** | 본문·표·Limitations 정정. MinerU-off 공개는 P12 대기. |
| RCPS를 새 similarity metric으로 주장하지 않기 | **완료** | standard MRR 기반 protocol로 명시. |
| Findings/diagnostics를 foreground | **완료** | Abstract와 Intro에 absent/split 및 bounded training 결과 반영. |
| dense training material을 appendix로 이동 | **완료** | 본문 C4 압축, 상세표·robustness 부록 이동. |
| end-to-end table | **완료** | accuracy와 RCPS 모두 MinerU-on으로 same-configuration 유지. MinerU-off 0.212는 인접 문장에 별도 공개. |

## 6. Reviewer bXGg 요구사항

| 요구사항 | 상태 | 현재 처리 / 남은 일 |
|---|---|---|
| findings와 diagnostic를 Intro에서 foreground | **완료** | selection gap, absent/split, bounded training 결과를 Intro에 제시. |
| RCPS를 deployable selection protocol로 정직하게 framing | **완료** | new metric/causal/general ranking 주장을 제거. |
| fixed Q–A와 paired evaluation | **완료** | 동일 probe와 paired CI 명시. |
| Qwen same-family 우려 완화 | **완료(원고)** | matcher ladder, cross-family judge, 최종 게시본의 100-case absent-label human study를 함께 반영. |
| **최종 게시본의 100-case blind human verification** | **완료(원고)** | 최종 답변은 `LLM-judged absent sets`에서 층화한 100건을 명시한다. κ=0.615, raw 81/100, 19건 공동 adjudication, human–LLM 90.3%(n=93)를 반영. 로컬 R3 초안의 “same 100 Q–A”는 비정본 문구. |
| human labels 공개 | **대기** | adjudicated labels와 protocol/manifest 필요. |
| parser-training section 압축 | **완료** | 본문은 결론과 범위, 상세는 Appendix A/B. |
| MRR@10-only에서도 ranking 유지 | **완료** | tracked 294-page aggregate를 `fullgrid_aggregate_audit.py`로 재구성. 5개 full-page parser와 Prod×4 chunker 모두 RCPS 대비 순위 동일($\tau_a=1.0$). Marker는 38-page 행으로 별도 표시. |
| format normalisation 영향 0.02–0.03, reorder 없음 | **대기** | 근거 artifact 없음. 재계산 전 원고에 넣지 않음. |
| probe-subset bootstrap stability | **대기** | aggregate는 있으나 aligned per-QA가 MinerU-on 한 configuration뿐이다. 동일 294 pages / 663 Q–A / 9 unique systems 실행과 JSON·CI 필요. 242-page fold와 혼합 금지. |
| end-to-end table과 top choice 확인 | **완료** | Prod top choice만 확인. near-tied lower pair reversal을 공개하고 full-ranking claim을 하지 않음. |
| generator/judge self-evaluation 제한 | **완료** | 같은 checkpoint임을 밝히고 top-choice check로만 해석. |
| retrieval vs generated-answer scope | **완료** | Intro, Discussion, Limitations에 명시. |
| candidate-pool / generalisation bound | **완료** | score가 pool/probe 상대적이고 broader pool을 future work로 제한. |
| fixed deployment retriever vs averaging 지침 | **완료** | fixed이면 그 retriever, 미정/near-tie면 averaging이라고 조건화. |
| Distill matched comparison | **대기/제외** | aligned per-Q–A artifact 복원 전 objective comparison을 원고에서 제외. |

## 7. P1–P17 실행 상태

| 항목 | 상태 | 판정 |
|---|---|---|
| P1 parser definition + worked example | **완료** | 정의, taxonomy, 수치, pseudo-reference↔output 대비표 반영. |
| P2 Appendix 재배치 | **완료** | 현재 Appendix A–H 구조와 참조 일치. |
| P3 Intro 재구성 | **완료** | 핵심 발견과 scope를 전면 배치. |
| P4 Abstract/본문 압축 | **완료(텍스트)** | 최종 그림 뒤 페이지 한도 재검증 필요. |
| P5 human verification | **완료(원고)** | 최종 게시본의 absent-label 100-case study와 수치를 반영. per-case human label 공개는 P12에서 별도 추적. |
| P6 E2E table | **완료** | same-configuration을 지키고 off 값은 별도 서술. |
| P7 294-page full-grid stability | **대기** | WSL/full-grid artifact 필요. |
| P8 MinerU tables-on 정정 | **완료(원고)** | 공개 artifact의 off half는 P12 대기. |
| P9 pseudo-ground-truth 정정 | **완료** | camera-ready 정본 전역에서 과장 표현 제거. |
| P10 exact commands/fresh clone | **대기** | 최종 release tag와 외부 artifact 필요. |
| P11 composition/contamination | **부분 완료** | 구성·page-disjoint는 완료. 4.9pp는 엄밀한 contamination upper bound가 아니므로 scale로만 보고; 약속 수정 필요. |
| P12 artifact release | **부분 완료** | strict audit/current-vs-legacy manifest는 완료. MinerU-off, full-grid, human labels, checkpoints 등 대기. |
| P13 metadata | **대기** | 5인 순서는 고정. affiliation/email/ORCID/form/교신 회신 필요. |
| P14 numeric/lineage final audit | **대기** | final figures/full v2/manifest 확정 뒤 수행. |
| P15 promises-to-paper gate | **대기** | 모든 외부 blocker 종료 뒤 최종 실행. |
| P16 figures/architecture | **의도적 연기** | 사용자의 지시에 따라 텍스트 확정 뒤 마지막 단계에서 수행. |
| P17 OHR version correction | **부분 완료** | mixed-version 근거 격리 및 aligned replacement 완료. full v2와 Distill same-subset은 대기. |

## 8. 제출 전 우선순위

1. 동일 294-page full grid의 per-Q--A를 확보해 probe-resampling stability와 normalisation sensitivity를 재실행한다. MRR@10-only aggregate 순위 검증은 이미 완료됐다.
2. R2 beta의 executed provenance와 checkpoints/config 공개 범위를 확정한다.
3. MinerU-off predictions, human adjudication labels, full-grid JSON, manifest, exact clean-clone commands를 공개·검증한다.
4. affiliation/email/ORCID/form과 corresponding-author chairs 회신을 반영한다.
5. 그림·아키텍처의 구 수치/표현을 고친 뒤 전체 PDF 페이지·폰트·흑백·100% 가독성을 다시 검증한다.
6. P14 수치·lineage와 P15 reviewer-promise 매핑을 마지막으로 재실행한다.

## 9. 현재 PDF 빌드·렌더 검증

- `latexmk -pdf -g -interaction=nonstopmode -halt-on-error main_camera_ready.tex` 빌드 성공.
- 최종 작업 PDF는 14쪽이다. 본문과 Limitations는 1–6쪽에 들어가며, References는 6쪽에서 시작하고 Appendix는 9쪽에서 시작한다.
- undefined citation/reference, multiply-defined label, overfull box는 없다. 2단 편집에서 생기는 underfull box 경고만 남는다.
- 14쪽 전부를 144dpi PNG로 렌더해 육안 확인했다. 텍스트·표의 잘림, 겹침, 페이지 밖 유출은 발견되지 않았다.
- P16의 알려진 시각 blocker는 그대로다. Figure 1과 4 내부에 tables-off 구 수치가 남아 있고, Figure 2와 3의 내부 글자가 작다. `fig_coverage.pdf`에서 유래한 Type 3 font도 남아 있다. 이 세 항목은 그림 재생성 뒤 다시 검사해야 한다.
- 참고문헌 마지막 쪽과 마지막 Appendix 쪽의 여백은 내용 손실이 아니라 section/page break에 따른 비치명적 조판 여백이다.
