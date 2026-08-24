# RESEARCH DIRECTION — 연구 정의·가설·현재 위치

> 최종 갱신: 2026-05-27. 이 문서는 당시 연구 방향의 역사적 기록이다.

> **정본 변경 (2026-08-24):** camera-ready의 0순위 기준은 `paper/latex/main_camera_ready.tex`, `docs/CAMERA_READY_PLAN.md`, `docs/PAPER_REVISION_WORKMAP.md`, `docs/PAPER_READABILITY_REVIEW_AUDIT.md`다. 아래 `r=-0.81`은 MinerU-off 기반 초기 grid이며, 현재 동일-구성 근거는 MinerU-on 포함 `r=-0.74`(Marker 포함 보조 분석 `r=-0.83`)다. 기여 순서도 C1 disconnect → C2 RCPS → C3 coverage → C4 training으로 확정됐다.

---

## 1. 연구 질문 (정확히)

> **파서를 "사람이 보기 좋은 markdown"이 아니라 "검색이 잘 되는 chunk"를 만들도록 학습시킬 수 있는가? 그리고 그게 자체 지표가 아닌 통용 지표로도 증명되는가?**

---

## 2. 출발점 — C1이 찾아낸 역설

- **MoC Boundary Clarity(BC)** 같은 intrinsic 지표 = "사람이 보기에 경계가 명확한가". 파서를 보통 이걸로 평가.
- 그런데 KoGov 5-parser에서 **BC↔RCPS Pearson = −0.81**. BC 1위(MinerU)가 retrieval 꼴찌.
- 같은 방향을 OHR-Bench / EnterpriseDocBench(r≈0.14) / When Good OCR이 독립 확인.
- **결론: 사람 친화 경계 ≠ 검색(AI) 친화 경계.** 그럼 검색 친화 경계로 파서를 학습하면 검색이 오를 것이다 — 이게 가설의 출발.

---

## 3. 핵심 가설 — 증명해야 할 인과 사슬

```
① 파서를 검색 신호로 학습  →  ② 청크 경계가 사람친화→검색친화로 이동  →  ③ Hit@/MRR 상승
                                                                          ↑
                                            ③이 ②"때문"이고, 통용 지표로도 보여야 완결
```

| 사슬 | 무엇을 보여야 하나 |
|---|---|
| ① 파싱 변화 | 학습 후 파서 출력이 실제로 달라진다 |
| ② 경계 변화 | 청크 경계가 검색 친화 방향으로 바뀐다 (사람친화 지표 BC/CS는 ↑하지 않음) |
| ③ 검색 향상 | 그 경계의 조각이 검색에서 더 높은 점수 |
| ③⊂② (인과) | 향상이 "경계 변화" 때문이지, 단순 "내용을 더 받아씀" 때문이 아니다 |
| 통용 지표 | 자체 RCPS뿐 아니라 표준 retrieval 지표·BC/CS로도 일관 |

---

## 4. 현재 위치 — 어디까지 증명됐나 (2026-05-27)

| 사슬 | 상태 | 근거 |
|---|:---:|---|
| ① 파싱 변화 | ✅ | RADP-DPO 출력이 v1과 다름 (v1이 스킵한 표·내용 포함) |
| ② 경계 변화 | ❓ | **측정 안 됨** — 경계가 어떻게/얼마나 바뀌었는지 정량화 없음 |
| ③ 검색 향상 | 🟡 | RCPS +4pp (CI 하한 −0.37, marginal). **자체 지표 한정** |
| ③을 Hit@1로 분리 | ❌ | RCPS(MRR 평균)만 보고. 순수 Hit@1 미보고 |
| ③⊂② (인과) | ❌ | **경계 때문인지 "내용을 더 받아써서"인지 미분리 (confound)** |
| 통용 지표 | ❌ | 표준 retrieval(풀코퍼스 vectordb)·BC/CS 변화 미측정 |

### 가장 중요한 두 구멍
1. **자체 지표 한정.** +4pp는 우리가 설계한 RCPS(page-local + 자체 distractor pool) 안에서만. reviewer: *"메트릭을 유리하게 짠 것 아니냐"* → 표준 지표 검증 필요.
2. **경계 vs 내용 confound.** DPO가 "표·내용을 더 받아쓰게" 됐다는 정성 근거는, 향상이 *경계 개선*이 아니라 *받아쓰기 정확도 향상*(답이 비로소 조각에 들어감)일 수 있음을 시사. 사용자 가설의 핵심(②경계)이 아직 분리 입증 안 됨.

---

## 5. 증명 완결 조건 (다음 핵심 실험)

| # | 검증 | 도구 | 무엇을 닫나 |
|---|---|---|---|
| 1 | **표준 retrieval 평가** (풀코퍼스 vectordb, Hit@1/@5/@10·nDCG·MRR) v1 vs DPO | `PLAN-01` | 자체 지표 한정 해소 |
| 2 | **BC/CS 변화** DPO 전후 | `PLAN-02`, `boundary_clarity.py` | 사람친화 경계를 *희생*했는지 |
| 3 | **경계 분해** (covered/split/absent) v1 vs DPO | `PLAN-03`, `coverage.py` | 향상이 경계냐 내용이냐 |

### 이상적 결과 패턴 (= 논문 최강 클로징)
```
DPO 후:   BC/CS → flat or ↓   (사람친화 경계 포기)
          표준 Hit@1 → ↑      (검색은 더 잘됨)
          split → ↓           (경계가 답을 덜 자름 = ②가 원인)
```
이 셋이 같이 나오면 → **"파서가 사람 보기 좋은 경계를 버리고 검색 친화 경계로 스스로 이동했다"** 가 통용 지표로 증명 = C1(진단)을 training으로 직접 확증.
> 역설적으로 **BC/CS가 안 오르는 게 우리에게 유리**하다. BC/CS도 retrieval도 같이 오르면 "그냥 파싱이 전반적으로 좋아진 것"이라 "사람친화≠AI친화" 주장이 약해진다.

---

## 6. 용어 정리 (혼동 방지)

| 용어 | 정의 |
|---|---|
| **BC/CS** | MoC의 intrinsic 지표. "사람 보기에 경계가 명확/응집적인가". **높다고 검색 잘 되는 게 아님** (C1) |
| **RCPS** | 우리 extrinsic 지표. "이 파싱으로 검색하면 정답 조각이 몇 등?" (MRR@{1,5,10} × 3-retriever 평균) |
| **표준 retrieval 지표** | 풀코퍼스 인덱싱 기반 통용 Hit@k / nDCG / MRR (자체 distractor pool 아님) |
| **검색(AI) 친화 경계** | BC/CS를 높이는 게 *아니라*, BC/CS와 무관/역방향이어도 retrieval이 높은 경계 |

---

## 7. 방법론 두 갈래 (C3)

- **RADP-hidden** (C3a): 파서 hidden state를 retriever 공간에 맞추는 aux loss. **미분 가능하지만 간접** → negative(+1~3pp). `L_total = L_parse + λ·L_contrast`.
- **RADP-DPO** (C3b): 파서의 *discrete 출력*을 RCPS로 채점, preference pair로 DPO. **출력 직접 최적화** → +4pp (hidden의 2배). 미분 불가 구간을 "여러 개 뽑아 좋은 것 선택"으로 우회. (상세: `plans/PLAN-04`)

논문 framing: *"진단(C1) → 측정(C2) → 자연스러운 해법 두 가지를 시도, 출력 직접 학습(DPO)이 명확히 우월하나 통용 지표 검증이 완결 조건(C3)"*.
