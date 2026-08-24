# PLAN-02 — BC/CS 변화 측정 (DPO 전후)

> 상태: ❌ 미착수 (P0-3) · 의존: RADP-DPO 출력(PLAN-04) · 담당: TBD

> **역사적 계획 주의 (2026-08-24):** 아래 `r=-0.81`은 MinerU-off 기반 초기 grid를 전제로 한다. 현재 camera-ready C1은 MinerU-on 포함 `r=-0.74`(Marker 포함 보조 분석 `r=-0.83`)를 사용하며, 이 미착수 계획은 현재 실행 원장이 아니다.

## 목적
DPO 학습이 파서의 **사람 친화 경계 지표(BC/CS)를 *올리지 않으면서*** 검색을 올렸는지 확인. 이게 "검색 친화 경계로 이동"의 직접 증거.

## 왜 (배경)
C1: BC↑가 retrieval↑를 뜻하지 않는다(−0.81). 그러므로 우리가 원하는 "AI 친화 경계"는 **BC를 높이는 게 아니다.** 오히려:
- DPO 후 **BC flat-or-↓ + retrieval ↑** → "사람친화 경계를 버리고 검색친화로 이동" = C1을 training으로 확증 (논문 최강 클로징)
- DPO 후 **BC↑ + retrieval↑** → "그냥 파싱이 전반적으로 좋아진 것" → "사람친화≠AI친화" 주장 약화

즉 **BC가 안 오르는 게 우리에게 유리**한 역설. (`docs/RESEARCH_DIRECTION.md §5`)

## 방법
1. `src/wigtnocr_radp/evaluation/boundary_clarity.py`로 BC(가능하면 CS도) 계산
2. 대상: v1 출력 vs RADP-DPO 출력 (chunker별)
3. 같은 페이지셋에서 BC 분포 비교 (평균 + 페이지별 Δ)
4. **RCPS·표준 Hit@(PLAN-01)와 나란히 표로**: BC 변화 vs retrieval 변화의 방향 대비

## 입력 / 출력
- 입력: `output/parses_full/{v1, radp_dpo_eval}/`
- 출력: `output/eval/bccs_shift.{json,md}` — 파서별 BC(+CS) + retrieval Δ 동시 표

## 판정 기준 (이상적)
```
DPO BC  ≤  v1 BC      (flat or ↓)
DPO RCPS / 표준 Hit@1  >  v1   (↑)
```
→ "검색 친화 경계로 이동" 입증. 이 대비가 §4 또는 §4.2-4.4 브리지의 핵심 그림.

## 구현 노트
- BC 계산은 WIG-165/172에서 이미 사용한 코드 경로 재활용
- Figure 후보: x=BC, y=retrieval, v1→DPO 화살표로 "이동 방향" 시각화
