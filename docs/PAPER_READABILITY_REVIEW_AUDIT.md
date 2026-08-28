# EMNLP 2026 camera-ready 문장·리뷰 요구사항 전수 감사

> 최초 감사일: 2026-08-22 · 최신 갱신: 2026-08-29
> 원고 정본: `paper/latex/main_camera_ready.tex`
> 동결본: `paper/latex/main.tex`는 편집하지 않음
> 정합성 기준 커밋: PR #12 merge `a981bca`. 이 기준에서 C2=RCPS, C3=coverage,
> Marker 포함 보조 상관은 `r=-0.83`, E2E 결과표는 본문 C2이고 프로토콜·한계는 Appendix B, C4 상세는 Appendices E--G다.
> PR diff의 삭제 행과 동결본 `main.tex`는 현재 camera-ready 상태 판정에 사용하지 않는다.
> 판정 원칙: 근거가 현재 원고 또는 추적 가능한 산출물에 없으면 완료로 표시하지 않음
> rebuttal 정본: 2026-08-22 사용자 제공 OpenReview 최종 게시본(SHA-256 `654e60466b29d137af5aa527e3fd534e14d005378e5571e1775ae3728b0c5f6f`). 로컬 reviewer별 초안과 충돌하면 최종 게시본을 우선함.

> **2026-08-24 전면 후속 갱신:** Figure 1--4와 C1→C2 RCPS→C3 coverage→C4 순서를 모두 반영했다. 영·한 README 및 활성 재현 문서도 같은 번호와 MinerU-on BC 결과로 동기화했다. MinerU-off 기반 `r=-0.81`을 보존하는 초기 실험·계획 문서에는 현재 camera-ready 근거가 아니라는 역사적 기록 경고를 추가했다. 당시 `main_camera_ready.pdf`는 14쪽이었고, 아래 2026-08-27 갱신이 현재 15쪽 정본을 기록한다.

> **2026-08-27 P7 후속 갱신:** 동일 294페이지 full-grid 수치와 probe bootstrap 문단을 반영한 현재 `main_camera_ready.pdf`는 15쪽이다. 본문과 Limitations는 1--6쪽, References는 7--9쪽, Appendix는 10쪽부터이며, 15쪽 전부를 다시 렌더해 잘림·겹침·overflow와 Type3 font가 없음을 확인했다.

> **2026-08-29 본문 근거 보강:** 7쪽 본문 상한을 활용해 C2에 3-parser end-to-end 결과표를 이동하고, C3에 MinerU-on L4 matcher·human verification 핵심 수치와 coverage worked example을 보강했다. Full-set cross-family judge는 MinerU-off에서만 실행됐으므로 Appendix C에 설정을 명시해 유지했다. Discussion and Conclusion은 7쪽에서 끝나고, Limitations는 7--8쪽, References는 8--9쪽, Appendix는 10쪽부터다. 총 15쪽, 전 페이지 A4, Type3 font 0, embedded font, 잘림·겹침·overflow 없음과 CPU-only artifact gate 통과를 다시 확인했다.

> **2026-08-24 C2 중심 hierarchy pass:** Abstract에서 parser training을 secondary study로 낮추고, §4.5 C4를 RADP의 operational definition과 제한된 결과 두 단락으로 압축했다. RADP-aux는 answer-span hidden state--frozen BGE-M3 contrastive alignment, RADP-DPO는 page-local MRR로 후보 parse를 순위화한 DPO pair, RADP-Distill은 edit-distance fidelity control로 구분했다. 부록은 A OHR(C1) → B E2E(C2) → C absent robustness → D coverage(C3) → E--G training(C4) → H release로 재배열했다. 리버털이 약속한 Appendix C의 parser I/O, worked example, human verification는 그대로 유지된다.

## 1. 결론

- **문장·문단 감사:** 정본의 Abstract부터 Appendix H까지 모든 산문 문장, 절 제목, 표 머리글, 표 캡션, 그림 캡션을 순서대로 읽고 말투, 주어·대상, 선후 논리, 용어, 분모, parser configuration, claim–evidence 범위를 대조했다. 문장과 내러티브 수정은 반영했다.
- **리뷰 약속 감사:** 논문·artifact 범위의 R1/R2/R3 요구사항은 완료했다. 100-case absent-label human verification, MRR@10-only aggregate audit, 동일 294페이지 full-grid probe bootstrap, format-normalisation 재검증, aligned Distill comparison, MinerU-off, source map, public 9-adapter release, clean-checkout gate를 반영했다. Human per-case 라벨은 명시적 author-only 예외이고, full OHR-Bench v2 결과는 주장하지 않는다. 제출 폼 메타데이터와 저자 수동 참고문헌 확인은 별도 외부 게이트다.
- **시각물:** Figure 1--4를 camera-ready 수치·정의와 새 기여 순서에 맞춰 반영했다. 벡터 PDF 삽입, 실제 2단 PDF 렌더, 흑백 구분, Type 3 font 0개를 확인했다.
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
7. **Training:** R1/R2/R3 구성과 R2 warm start를 설명하고 R3의 pool을 K=16(기존 두 후보+신규 14개)으로 정정했다. DPO·SimPO 표기와 입력을 정의했다. 원본 R2 실행 로그와 명령에서 beta=0.1을 확인해 camera-ready 산문과 portable provenance record에 반영했다.
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

### 2026-08-22 P16 시각 pass: Figure 2--4

- Figure 2는 번호를 제거하고 evaluation pages/candidate → parse·chunk·index → fixed probe retrieval → relevance → RCPS → rank의 단일 세로 실행 흐름으로 정리했다. `RCPS(P,C)`, reference-page + normalised-span relevance, retriever/cutoff 평균을 표시하고 구 `Hit@1 0.20→0.55` headline을 제거했다. 고정 deployment retriever의 singleton-set 정책은 캡션으로 옮겼다.
- Figure 3은 70--100% 축을 자른 stacked bar를 폐기했다. pre-chunking normalised exact-span no-match `134/663=20.2%`와 chunk-boundary split `0.0--2.3%`를 분리해, semantic omission을 증명하지 않는 operational diagnostic으로 한정했다.
- Figure 4는 MinerU-on을 포함한 complete-output BC diagnostic(`r=-0.74`, Marker 38p 포함 `r=-0.83`)과 MinerU-on--Prod deployment gap(`0.123→0.549`, `42.6` points, `4.47×`)을 같은 audited configuration 기준으로 맞췄다. MinerU-off는 별도 submitted-output diagnostic으로만 유지했다.
- Figure 2/3은 `0.96\columnwidth`, Figure 4는 `0.90\textwidth`의 벡터 PDF로 삽입했다. 세 PDF와 합본 모두 embedded CID TrueType이며 Type 3 font는 0개다. 200dpi page render와 grayscale render에서 잘림·겹침·색상 의존을 발견하지 않았다.

### 2026-08-24 Figure 1--4 최종 균형·수식 pass

- Figure 1은 승인된 기존 디자인·색·크기·문구를 유지하고, RCPS 배지의 C3를 C2로, coverage 배지의 C2를 C3로 교체했다. 그 밖의 시각 요소는 변경하지 않았다.
- Figure 2는 박스 폭을 통일하고 모든 세로 화살표가 인접 박스 경계까지 닿게 했다. RCPS 정의도 일반 문장 대신 수식으로 표시했다.
- Figure 3은 lollipop guide가 endpoint marker 뒤까지 이어지도록 연장하고 상단의 pre-chunking no-match callout을 제거했다. Figure 4는 MinerU-on 기준 $r=-0.74/-0.83$과 Hit@1 0.123/0.549를 재확인하고, 파생값 callout은 제거했으며 두 막대 값을 동일하게 막대 위에 배치했다. BC 패널은 Marker 다이아몬드를 MinerU-on 원과 같은 시각 폭으로 줄이고 두 라벨에 같은 오프셋을 적용했다.
- `paper/figures/fig_overview_camera_ready.pptx`가 최종 편집 정본이며, 여기서 export한 `paper/figures/fig_overview.pdf`가 삽입 정본이다.

### 아직 문장만으로 닫을 수 없는 항목

- R2 executed checkpoint의 `beta=0.1`은 원본 `v4_train.log`의 시작 기록과 exact command에서 확인했다. Portable config와 원본 로그 SHA-256을 `docs/provenance/RADP_DPO_R2_EXECUTED_CONFIG.md`에 기록했다.
- 동일 294-page full-grid의 9개 unique system per-Q--A 재색인, probe-resampling stability, format-normalisation sensitivity를 완료했다. Prod는 Base와 세 OCR configuration보다 1,000/1,000 draws에서 높다. 전체 chunker 순서는 96.1% 유지됐고 normalised-vs-raw score 차이는 0.024--0.041이며 두 pool 모두 순서가 유지됐다.
- full OHR-Bench v2 rerun은 수행하지 않고 호환성 subset으로 범위를 고정했다. RADP-Distill same-subset artifact는 복구했으며 직접 DPO 비교 구간이 모두 0을 포함한다.
- 교신저자 표기는 chairs의 서면 승인에 따라 `Correspondence: harrison@wigtn.com`으로 반영했다. 공통 소속 `WIGTN, Seoul, Republic of Korea`도 저자명 아래에 추가했다. Public checkpoint URL과 CPU-only fresh-clone artifact 명령은 검증했다. 나머지 email/ORCID·form 입력은 아직 남아 있다.
- Figure 1--4 시각 수정은 완료했다. 이후 그림 파일이 다시 바뀌면 합본 렌더·흑백·폰트 검사를 재실행해야 한다.

## 4. Reviewer NAor1 요구사항

| 요구사항 | 상태 | 현재 처리 / 남은 일 |
|---|---|---|
| 외부 benchmark 검증 | **부분 완료** | Law–Manual 1,043과 strict six-domain compatibility 2,036은 source-aligned. full official v2 rerun은 미완이며 원고가 이를 명시함. |
| implementation, evaluation code, frozen KoGov set | **완료** | repository와 원고에 범위를 명시. |
| parser-training checkpoints 공개 | **완료** | Public GitHub Release `v1.0.0`에 9개 adapter, portable config, manifest/hash, 가용 trainer state를 공개하고 익명 다운로드를 검증. |
| 동일 Q–A와 paired bootstrap | **완료** | paired evaluation 및 CI 명시. |
| exact run commands / reproducibility checklist | **완료(artifact gate)** | README의 public download→extract→CPU audit command를 clean checkout에서 검증. 전체 end-to-end rerun의 외부 입력 한계는 별도 명시. |
| ought-vs-is gap을 Intro에 명시 | **완료** | Introduction 첫 문단에 반영. |
| 어려운 문장 분리, 핵심 용어 정의 | **완료(원고·시각)** | Abstract·Methods·Appendix와 Figure 1--4의 정의·가독성을 정리. |
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
| adjudicated human labels | **완료(비공개 감사)** | 저자 전용 패키지의 100×2 판정, sampling manifest, 19건 adjudication을 scorer로 재검증. 공개본에는 aggregate만 보고. |
| MinerU tables-on correction | **완료** | 본문·표·Limitations 정정과 MinerU-off 294-page 공개·tree-hash 감사 완료. |
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
| human labels 감사 | **완료(비공개)** | adjudicated labels와 sampling manifest를 내부 정본으로 확인했으며 원본은 author-only protocol에 따라 공개하지 않음. |
| parser-training section 압축 | **완료** | 본문은 RADP 정의와 제한된 결과 두 단락, 상세 setup·표·mechanism은 Appendix E--G. |
| MRR@10-only에서도 ranking 유지 | **완료** | tracked 294-page aggregate를 `fullgrid_aggregate_audit.py`로 재구성. 5개 full-page parser와 Prod×4 chunker 모두 RCPS 대비 순위 동일($\tau_a=1.0$). Marker는 38-page 행으로 별도 표시. |
| format normalisation 영향과 reorder 여부 | **완료(수치 정정)** | 동일 ranked lists의 raw matching 대비 normalised RCPS 차이는 0.024--0.041이다. MinerU-on이 0.041이므로 provisional 0.02--0.03을 정정했다. Parser/chunker order는 모두 유지된다. |
| probe-subset bootstrap stability | **완료** | 동일 294 pages / 663 Q–A / 9 unique systems에서 500-Q–A 무복원 추출을 1,000회 실행했다. Parser mean $\tau_a=0.902$, chunker full-order 96.1%, Prod-vs-Base/OCR 100%다. 242-page fold는 혼합하지 않았다. |
| end-to-end table과 top choice 확인 | **완료** | Prod top choice만 확인. near-tied lower pair reversal을 공개하고 full-ranking claim을 하지 않음. |
| generator/judge self-evaluation 제한 | **완료** | 같은 checkpoint임을 밝히고 top-choice check로만 해석. |
| retrieval vs generated-answer scope | **완료** | Intro, Discussion, Limitations에 명시. |
| candidate-pool / generalisation bound | **완료** | score가 pool/probe 상대적이고 broader pool을 future work로 제한. |
| fixed deployment retriever vs averaging 지침 | **완료** | fixed이면 그 retriever, 미정/near-tie면 averaging이라고 조건화. |
| Distill matched comparison | **완료** | aligned per-Q–A artifact와 strict 2,036 mask를 복원. Distill−R2/R3 paired CI가 모두 0을 포함함을 원고에 반영. |

## 7. P1–P19 실행 상태

| 항목 | 상태 | 판정 |
|---|---|---|
| P1 parser definition + worked example | **완료** | 정의, taxonomy, 수치, pseudo-reference↔output 대비표 반영. |
| P2 Appendix 재배치 | **완료** | A--D가 C1--C3 검증, E--G가 C4 상세이며 Appendix C 약속과 모든 참조가 일치. |
| P3 Intro 재구성 | **완료** | 핵심 발견과 scope를 전면 배치. |
| P4 Abstract/본문 압축 | **완료** | C4를 두 단락으로 유지하면서 C2/C3 핵심 근거를 본문에 복원했다. 15쪽 최종 렌더에서 본문·결론은 7쪽 마지막에 끝나고 Limitations는 8쪽에서 시작한다. |
| P5 human verification | **완료(원고)** | 본문 C3에 MinerU-on/Prod/PaddleOCR의 adjudicated count, rate, Wilson CI를 모두 제시하고 표본 검증이라는 한계를 명시. per-case human label 공개는 P12에서 별도 추적. |
| P6 E2E table | **완료** | same-configuration을 지키고 off 값은 별도 서술. |
| P7 294-page full-grid stability | **완료** | aligned 9-system per-Q--A JSON, parser/chunker bootstrap JSON, exporter와 input tree hash를 저장했다. |
| P8 MinerU tables-on 정정 | **완료** | MinerU-on 원고 정정과 submitted-output MinerU-off 공개 감사를 모두 완료. |
| P9 pseudo-ground-truth 정정 | **완료** | camera-ready 정본 전역에서 과장 표현 제거. |
| P10 exact commands/fresh clone | **완료(artifact gate)** | Public `v1.0.0` 다운로드와 CPU-only audit를 clean checkout에서 검증. |
| P11 composition/contamination | **부분 완료** | 구성·page-disjoint는 완료. 4.9pp는 엄밀한 contamination upper bound가 아니므로 scale로만 보고; 약속 수정 필요. |
| P12 artifact release | **완료(명시한 예외 제외)** | MinerU-off, source map, strict manifests, full-grid JSON, public 9-adapter release 완료. Human per-case labels은 author-only 정책. |
| P13 metadata | **부분 완료** | 5인 순서·공통 affiliation·교신 표기는 완료. 나머지 email/ORCID/form 입력 필요. |
| P14 numeric/lineage final audit | **완료** | Public checkpoint hash/base lineage까지 재감사. RADP-aux cross-base 실행을 원고·README에 정정. |
| P15 promises-to-paper gate | **논문·artifact 범위 완료** | 남은 외부 게이트는 저자 ORCID/form 메타데이터와 수동 참고문헌 대조. |
| P16 figures/architecture | **완료** | Figure 1--4 재생성·합본 렌더·흑백·Type3=0 검증 완료. |
| P17 OHR version correction | **완료** | mixed-version 근거 격리, strict 2,036 replacement, aligned Distill direct comparison 완료. full-v2 claim은 하지 않는 것으로 범위 고정. |
| P18 MinerU-on BC | **완료** | clean rerun BC 0.713123, four-parser $r=-0.7443$을 감사했고 원고·README에는 0.713/$-0.74$, Marker 포함 $-0.83$을 반영. PR #21 병합 완료. |
| P19 C2/C3 순서 | **완료** | 원고·활성 계획/감사 문서를 C1→C2 RCPS→C3 coverage→C4로 통일하고, 부록도 C1--C3 검증을 C4보다 먼저 배치. |

## 8. 제출 전 우선순위

1. P7 full-grid per-Q--A, probe bootstrap, normalisation sensitivity는 완료했다. 최종 원고와 manifest hash를 다시 대조한다.
2. R2 beta의 executed provenance와 9-adapter public release·hash/base lineage 검증을 완료했다.
3. MinerU-off 294-page predictions, portable source-page manifest, exact clean-clone artifact commands를 공개·검증했다. Human adjudication 원본은 author-only audit package에 유지한다.
4. 공통 affiliation과 corresponding-author chairs 회신은 반영했다. 나머지 email/ORCID/form을 최종 확인한다.
5. P14 수치·lineage와 P15 reviewer-promise 매핑은 완료했다. 제출 직전에는 P13 메타데이터와 참고문헌 수동 대조만 다시 확인한다.

## 9. 현재 PDF 빌드·렌더 검증

- `latexmk -pdf -g -interaction=nonstopmode -halt-on-error main_camera_ready.tex` 빌드 성공.
- 최종 작업 PDF는 15쪽이다. 본문과 Discussion/Conclusion은 7쪽 마지막에서 끝나고, Limitations는 8쪽에서 시작한다. References는 8--10쪽이며 Appendix는 참고문헌 마지막 항목 아래인 10쪽 왼쪽 열에서 이어진다.
- undefined citation/reference, multiply-defined label, overfull box는 없다. 2단 편집에서 생기는 underfull box 경고만 남는다. Type~3 폰트는 0개이며 모든 폰트가 임베드됐다.
- 2026-08-29 C2의 네 chunker 점수, single-retriever/depth/probe/matcher 강건성, near-tie 운영 규칙을 본문에 복원했다. C3에는 covered/split/absent별 후속 조치와 세 parser의 인간 검증 count/rate/CI를 추가했다. Release record, MinerU-on 도메인 민감도, selection-vs-tuning scale도 감사된 수치로 본문에 제시했다. 불필요한 참고문헌 뒤 강제 페이지 나눔을 제거했다. 앞서 검증한 1--9쪽의 조판이 유지됨을 확인하고 재배치된 10--15쪽을 다시 렌더해 육안 확인했다. C4와 결론을 포함한 본문은 7쪽 안에 끝나며 텍스트·표·그림의 잘림·겹침·페이지 밖 유출은 발견되지 않았다.
- P16의 Figure 1--4 blocker는 해소됐다. 최신 수치·정의, 실제 삽입 크기, 흑백 구분, Type3=0을 확인했다. 현재 남은 blocker는 시각물이 아니라 외부 artifact·metadata·clean-checkout 재현이다.
- 마지막 Appendix 쪽 하단 여백은 내용 손실이 아니라 문서 종료에 따른 비치명적 조판 여백이다.
- current `MANIFEST.sha256`의 모든 항목이 일치했다. OHR 2,036-Q--A alignment audit의 `--check`와 294-page aggregate grid 재구성도 통과했다. `src/`, `scripts/`, `tests/` 전체 Python 문법 컴파일도 임시 캐시 경로에서 통과했다. 이 Mac에는 `uv`와 `pytest`가 없어 unit test suite 자체는 실행하지 못했으며, 이는 clean-checkout 환경 게이트로 남긴다.
