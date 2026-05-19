# Q-A Generation Prompt — v3

> **버전**: v3 (2026-05-18)
> **목적**: difficulty 분포 강제. v2 prototype + full run 결과의 easy 편향 해소.
> **위치**: `src/wigtnocr_radp/qa_generation/schema.py` (SYSTEM_PROMPT, USER_TEMPLATE)

## 배경 — v2 → v3 motivation

### v2 full run 결과 (294p, GPT-4o, 2026-05-18)

| Difficulty | actual | PHASE_1.1 target | 편차 |
|---|---:|---:|---:|
| easy | **68.7%** (454/661) | 40% | +29pp |
| medium | 31.0% (205/661) | 40% | -9pp |
| hard | **0.3%** (2/661) | 20% | **-20pp** |

**원인 분석**:
- v2 `# DIFFICULTY DISTRIBUTION` 섹션은 **정의만** 적혀 있고 **분포 강제 instruction이 없음**
- 모델이 보수적으로 판단 → easy fallback
- "limit to 20%" 문구를 *"hard를 최대 20%까지만"*으로 잘못 해석한 가능성도 있음

### 변경점 (v3)

| 영역 | v2 | v3 |
|---|---|---|
| 섹션 이름 | `# DIFFICULTY DISTRIBUTION` (정의) | `# DIFFICULTY MIX — STRICT REQUIREMENT (highest priority)` (강제) |
| Per-page mandate | 없음 | "3 Q-A → 최소 1 medium + 1 hard / 2 Q-A → 최소 1 medium-or-hard" |
| Anti-fallback | 없음 | *"All-easy output is a task failure."* / *"NEVER substitute with easy."* |
| Hard 정의 | 1줄 ("cross-referencing multiple sections...") | 5개 구체 카테고리 (a~e) |
| GOOD / BAD 예시 | 없음 | 한국어 + 영어 각 3~4개 |
| USER_TEMPLATE reminder | 없음 | *"enforce the DIFFICULTY MIX mandate"* 추가 |

## v3의 핵심 instruction 발췌

```
You MUST produce a *mix* of difficulties on each page.
**All-easy output is a task failure.**

Per-page mandate:
- If you generate 3 Q-A → at least 1 medium AND 1 hard (when feasible). At most 1 may be easy.
- If you generate 2 Q-A → at least 1 must be medium or hard. Two easies is NOT acceptable.
- If a page genuinely cannot support a hard question, you may substitute with medium —
  BUT NEVER substitute with easy.
```

## 의도된 효과

1. **easy 비율 ↓**: 페이지당 easy 1개 cap 강제 (3 Q-A 페이지에서)
2. **hard 비율 ↑**: 페이지당 hard 1개 권장 + GOOD 예시로 모델의 "hard 발상" 능력 끌어올리기
3. **medium 활성화**: hard 불가 시 substitute target을 easy → medium으로 redirection

## 검증 방법 (ablation)

| Config | Model | Prompt | 페이지 수 | 목적 |
|---|---|---|---:|---|
| `ablation_v3_4o.yaml` | gpt-4o-2024-08-06 | v3 | 20 | v3 prompt 단독 효과 측정 |
| `ablation_v3_5_4.yaml` | gpt-5.4-2026-03-05 | v3 | 20 | 모델 업그레이드 추가 효과 |

같은 20p random sample (seed 고정)로 두 조건 비교. 분포 + Q-A 품질 (sample 손검수) 보고 full run 모델 결정.

## 향후 — v4 후보 (필요 시)

- **Multi-page Q-A** (PHASE_1.1 §1.1.2): 코드 변경 필요 (페이지 그룹화)
- **Per-page difficulty target 명시 할당**: 코드에서 페이지별 target ("이 페이지는 hard 1개") 할당해서 prompt에 전달
- **Question-type 비율 강제**: 현재 type 분포는 비슷 (factoid 43 / tabular 29 / procedural 27 / figural 1)이라 후순위

## Lessons (paper appendix 후보)

- Prompt-only difficulty control이 가능하다는 증거 (v3 결과 OK 시)
- vs Per-page assignment 통제 방식의 비용/효과 비교 데이터 (필요 시 추후)
