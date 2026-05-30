# Stage 4 — Parser vs Chunker 분해 + Best-of-N 파일럿 계획

> 작성일: 2026-05-26
> 목적: 현재 논문(C1 진단 / C2 RCPS / C3 RADP negative)의 아쉬운 결론을 보강하기 위한
> **추가 가설 + 검증** 설계. EMNLP 2026 Industry Track 마감(6/16) 전 미니 파일럿으로 진행.
> 코드: `src/wigtnocr_radp/evaluation/coverage.py`, `scripts/evaluation/coverage_diagnostic.py`,
> `tests/test_coverage.py` (branch `feat/radp-coverage-diagnostic`, ssw 기반).

---

## TL;DR

C3(RADP)는 "파서에 contrastive aux loss를 붙여도 +1~3pp뿐"이라는 **negative**로 끝난다.
문제는 *왜* 안 됐는지를 못 말한다는 것. 검색이 안 되는 게 **파서가 구조화를 잘못해서**인지,
**청커가 답의 맥락을 경계에서 갈라놔서**인지 분리가 안 돼 있다(confound).

Stage 4는 이 confound를 가른다:

1. **0단계 — 커버리지 진단** (검색기·GPU 불필요, 수 초): 파서를 고정하고 청커만 바꿔,
   각 Q-A의 정답이 단일 청크에 담기는지(`covered`) / 경계에 잘리는지(`split`, 청킹탓) /
   파서 출력에 아예 없는지(`absent`·`no_parse`, 파서탓)를 분류한다. → **범인이 파서냐 청킹이냐 판별.**
2. **1단계 — Best-of-N 파일럿** (GPU 2~3일): 0단계가 파서를 범인으로 지목하면, 파서가 만든
   여러 파싱 후보를 RCPS로 채점해 **우등생 답안만 골라 다시 학습**한다(=출력을 검색 신호로 직접 최적화).

결과가 어느 쪽이든 Industry용 **처방**이 남는다: *"파서를 고쳐라"* 또는 *"파서 말고 청킹을 고쳐라."*

---

## 1. 배경 — 현재 논문의 3 스테이지

| | 스테이지 | 결과 |
|---|---|---|
| **S1 (가설)** | 구조화 잘하면 → 맥락 청킹 잘 됨 → 검색 잘 될 것이다 | **틀림.** 구조화 잘한 파서(MinerU, BC=0.72)가 검색 꼴찌(RCPS=0.21). BC↔RCPS = −0.81 |
| **S2 (측정)** | "검색 잘 되는 파싱"을 잴 지표가 필요 | **RCPS** 수립 (retriever-agnostic, task-oriented) |
| **S3 (처치)** | 사람용이 아닌 *AI용* 구조화로 파서를 학습 (RADP) | **+1~3pp, 게이트 5pp 미달 → 정직한 negative** |

**왜 아쉬운가**: S3가 "안 된다"로 끝나는데, *왜* 안 되는지 — 파서 출력 문제인지, 그 뒤
청킹 문제인지 — 를 설명하지 못한다. RCPS는 `파서 × 청커 × 검색기`의 합작이라, S1~S3 전체가
이 둘을 한 번도 분리하지 않았다.

---

## 2. Stage 4 — 핵심 가설

> **검색 실패의 원인을 파서(구조화)와 청커(경계)로 분해한다. 파서가 범인일 때만 파서-side
> 학습(best-of-N/DPO)이 정당하며, 학습 시 파서가 "사람용 구조화 → AI용 구조화"로 이동하는지
> (BC↓ & RCPS↑)를 측정한다.**

분해의 결정적 단서는 **RCPS의 relevance 규칙** 자체에 있다 (`metrics.py` / `types.py`):

```
chunk가 relevant  ⟺  chunk.page_id == qa.page_id  AND  normalize(answer_span) ⊂ normalize(chunk.text)
```

즉 **정답이 단일 청크 안에 통째로 들어와야** 검색에 잡힌다. 답이 두 청크에 걸쳐 잘리면
어느 청크도 답 전체를 못 담아 → 전부 0점. 이건 파서가 잘못 옮긴 게 아니라 **청크 경계가
답을 가른** 것이다. 바로 이 지점을 측정한다.

---

## 3. 0단계 — 커버리지 진단

### 3.1 정의 — 답 위치 4분류

파서 출력을 고정하고, 각 Q-A의 정답이 청킹 후 어디에 떨어지는지 분류한다:

| 분류 | 정의 | 귀책 | 회수 가능? |
|---|---|---|---|
| **covered** | 답이 단일 청크 안에 통째로 있음 | — (정상) | — |
| **split** | 답이 페이지엔 있는데 어떤 단일 청크에도 통째로는 없음 (경계가 가름) | **청커** | ✅ overlap·큰 윈도우로 회수 |
| **absent** | 답이 페이지 markdown에 아예 없음 | **파서** | ❌ 어떤 청킹으로도 불가 |
| **no_parse** | 파서가 그 페이지를 통째로 출력 안 함 | **파서** | ❌ |

- `coverage = covered / total` = **검색 성능의 천장**. split·absent는 retriever가 아무리 좋아도 0점.
- `parser-fault = absent + no_parse` = 청커와 **무관**해야 함(경계와 독립). → 자가 sanity check.
- `split`만 청커마다 변한다. 이 변화가 곧 "청킹이 답을 가른 정도".

### 3.2 방법

- 파서 = WigtnOCR v1 출력 고정.
- 청커 8종을 fine→coarse로 정렬 (split이 줄어드는 추세를 봄):
  `md_h3 → md_h2 → md_h1 → parser_native → fixed500 → fixed500_ov200 → fixed1000 → fixed1000_ov200`
- relevance 매칭은 RCPS와 동일한 `normalize_for_match`(공백·markdown 무시) 사용 → 진단과 본평가의 기준 일치.
- **검색기·GPU 불필요.** 순수 텍스트 substring 매칭이라 CPU에서 수 초.

### 3.3 해석 분기 (→ 1단계 진행 여부 결정)

- **`split`이 md_h3에서 높다가 overlap/큰 윈도우에서 확 줄어든다** → 범인은 **청킹**.
  best-of-N/DPO(파서 학습)는 잘못된 레버. 파일럿을 *청킹 개선*으로 전환.
  (그 자체로 논문 C1 강화: "disconnect의 절반은 청킹이 답 맥락을 가르는 것")
- **`parser-fault`가 청커 무관하게 높게 깔려 있다** → 범인은 **파서**. best-of-N/DPO 정당 → 1단계로.
- **covered는 높은데 RCPS가 낮다**(0단계+기존 RCPS 비교) → 답은 청크에 있는데 retriever가 못 찾음
  = 파서의 표현/내용 문제 → 1단계로.

### 3.4 실행

```bash
uv run python scripts/evaluation/coverage_diagnostic.py
# 산출: output/diagnostics/coverage_diagnostic_v1.{md,json}
#   - md:  청커별 covered / split / parser-fault 표
#   - json: 분류 카운트 + question_type·difficulty 분해 + split/absent 실제 예시 8개씩
```

기본 경로는 `chunking_grid.py`와 동일(`data/KoGovDoc-RAG/qa_pairs_v1.jsonl`,
`/mnt/data1/work/wigtnOCR-v1/results/kogovdoc/v1_val/predictions`).

### 3.5 검증 상태

`tests/test_coverage.py` 11개 통과 (데이터·GPU 불필요). 핵심 2개:
- `test_diagnose_overlap_recovers_split`: 500자 경계에 걸린 답이 `split` → overlap에서 `covered`로 회수.
- `test_diagnose_absent_is_chunker_independent`: 파서가 안 뱉은 답은 모든 청커에서 `absent`.

---

## 4. 1단계 — Best-of-N 파일럿 (파서가 범인일 때)

### 4.1 개념

가장 단순한 강화학습 형태(rejection sampling / RAFT). **"모델한테 같은 문서를 N가지로 파싱하게
하고, RCPS로 채점해 1등 답안만 골라, 그걸 정답지 삼아 다시 SFT."**

```
1. Sample  — v1 파서로 한 페이지를 N개 버전 생성 (temperature↑로 다양성)
2. Score   — 각 버전을 청킹+검색해 RCPS로 채점 (채점기 = 기존 compute_rcps 재활용)
3. Select  — 점수 1등 버전만 채택 (rejection)
4. Distill — 그 버전을 target으로 표준 SFT (기존 학습 파이프라인 재활용)
            (1~4 반복 = iterative)
```

### 4.2 왜 이게 C3(RADP) 실패를 피하나

C3 decision-A는 파서의 **hidden state**를 retriever 공간에 맞추는 *곁다리* 손실이라, 실제 출력은
간접적으로만 바뀌고 "사람 보기 좋게 써라"는 1차 목표(`L_parse`)를 못 이겼다.
best-of-N은 파서의 **실제 출력(markdown)**을 RCPS로 직접 채점해 좋은 출력을 모방한다 →
**배포되는 산출물 그 자체를 최적화** → 실패 원인(간접성) 정면 회피.

### 4.3 보상 설계

- 사용자 초안: "검색된 첫 청크에 정답이 없으면 0점"(= Hit@1).
- 보강: 0/1은 신호가 희박(대부분 0 또는 1이라 우열이 안 갈림) → **등수로 부드럽게**(MRR:
  1등 1.0 / 2등 0.5 / 3등 0.33…). RCPS가 이미 이 방식.
- DPO 변형으로 갈 경우: 같은 문서의 N개 파싱을 점수로 정렬 → 상위 = `chosen`, 하위 = `rejected` 쌍.
  best-of-N(우등생 모방)이 더 가벼우므로 파일럿은 best-of-N 우선.

### 4.4 안전장치 — Reward hacking 방지

- 보상을 **단일 청커(md_h3)로만** 주면 그 청커에만 유리한 꼼수로 변질(과적합).
  → 보상은 **여러 청커 평균**으로, 그리고 **학습에 안 쓴 청커**(예: fixed1000)에서도 오르는지 별도 검증.
- **학습 전후 BC/CS 추적** → 파서가 "사람용 구조화"를 희생하는지 정량화:
  - RCPS↑ & **BC↓** → "사람용 → AI용 구조화 이동" = S1이 틀린 이유가 손에 잡힘 (논문 C1·C3 연결).
  - RCPS↑ & BC 유지 → 구조화 안 깨고 검색 친화 표현 발견.
  - RCPS 미미 → 파서 출력을 바꿔도 안 오름 = 범인은 상류(청킹/검색).

### 4.5 게이트 (느슨 — 신호 확인용)

본게임의 5pp 게이트가 아니라 *"v1 대비 RCPS가 의미있게 +방향이면서 parseSim 안 깨짐"*.
이 신호가 보이면 → **ACL 2027 본 연구(retrieval-reward DPO/RL) go**. 안 보이면 → 청킹/상류로 방향 전환.

---

## 5. 의사결정 트리

```
0단계 커버리지 진단
├─ split 높고 overlap/큰창에서 급감      → 범인=청킹  → 파일럿 보류, 청킹 개선 (C1 강화 소재)
├─ parser-fault 높고 청커 무관하게 평탄   → 범인=파서  → 1단계 best-of-N
└─ covered 높은데 RCPS 낮음              → 표현/검색 → 1단계 best-of-N
        │
        └─ 1단계 best-of-N (멀티청커 보상 + BC/CS 추적)
           ├─ RCPS↑ & BC↓/유지 + held-out 청커도 ↑  → 신호 O → ACL 2027 본 연구 go
           └─ 미미                                   → 신호 X → 상류(청킹/embedding)로 전환
```

---

## 6. 일정 (6/16 마감 전, GPU 2~3일 가용)

| 단계 | 작업 | 소요 | GPU |
|---|---|---|---|
| 0 | 커버리지 진단 실행 + 해석 | ~반나절 | 불필요 |
| 1a | N-best 파싱 샘플링 + RCPS 채점으로 학습셋 구성 | ~1일 | 추론 |
| 1b | best-of-N SFT + BC/RCPS 전후 비교 | ~1일 | 학습 |

---

## 7. 논문 활용

- **0단계 결과**: 어느 쪽이든 C1을 보강.
  - 청킹탓이면 → "parsing–retrieval disconnect의 상당 부분은 청크 경계가 답을 가르는 것"이라는
    새 분해 — 기존 C1(BC↔RCPS 음의 상관)에 메커니즘을 한 겹 더함.
  - 파서탓이면 → C3 negative의 "왜"에 대한 정량 근거.
- **1단계 결과**: Industry 처방.
  - 신호 O → "출력을 검색 신호로 직접 학습하면 파서가 AI용 구조화로 이동한다"(positive 단서, ACL 2027 예고).
  - 신호 X → "파서-side 학습은 (aux loss든 best-of-N이든) 약하다 → 청킹/상류부터 고쳐라"(강한 deployment lesson).
- **ACL 2027 Main**: retrieval-reward training on parser's discrete output (DPO/RL) 본 연구.

---

## 8. 관련 파일

| 종류 | 경로 |
|---|---|
| 진단 핵심 로직 | `src/wigtnocr_radp/evaluation/coverage.py` |
| 진단 CLI | `scripts/evaluation/coverage_diagnostic.py` |
| 진단 테스트 | `tests/test_coverage.py` |
| RCPS 본평가 (채점기 재활용) | `src/wigtnocr_radp/evaluation/rcps.py` |
| 기존 청킹 그리드 (경로 컨벤션 참고) | `scripts/evaluation/chunking_grid.py` |
| C3 negative 보고 | `docs/WEEK2_FINDINGS.md` |
| 실험 종합 | `docs/EXPERIMENTS_post-H1.md` |
