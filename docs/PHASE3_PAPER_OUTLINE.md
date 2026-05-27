# PHASE_3 §3.3 — Paper Outline (pivot 반영본)

> 작성일: 2026-05-21
> EMNLP 2026 Industry Track, 4-page limit.
> PHASE_3_WEEK3.md §3.3 원안을 **RADP-B negative-result pivot**에 맞춰 갱신.
> pivot 근거: `docs/WEEK2_FINDINGS.md`, proposal §9.

## 0. pivot이 §3.3 원안에서 바꾼 것

| 원안 항목 | pivot 후 | 이유 |
|-----------|----------|------|
| Figure 4 InSeNT orthogonality bar | **삭제** | RADP-B 미동작 → H3(InSeNT 결합) 무의미 |
| Table 3 InSeNT orthogonality | **삭제** | 동일 |
| Figure 3 "λ trade-off" | **유지, 의미 전환** | RADP-B 성공 곡선 → **negative result** 곡선 (단조 하락) |
| Method = RADP-B 중심 | **RCPS 중심 + RADP-B는 시도/실패** | 메인 기여 C2로 이동 |
| Figure 6 / Table 4 cross-domain | **optional** | OHRBench(3.1)은 "시간 되면" — 미확정 |
| 신규 | **chunking-strategy grid 표 추가** | C2(RCPS가 전략을 변별) 증거 |

## 1. 제목 · 기여 framing

**제목(잠정)**: *Retrieval-Aware Document Parsing: Diagnosing and Measuring the
Parsing–Retrieval Gap* — 부제 `via Chunk-Boundary Contrastive Learning`은
RADP-B가 negative라 **삭제**, RCPS 중심으로 재명명.

**3-layer 기여**:
- **C1 (진단)** — 인간 가독성 기반 parsing 품질 지표는 downstream retrieval을
  약하게만 예측. 한국어 정부문서에서 Pearson r ≈ 0.18 — EnterpriseDocBench
  r=0.14 재현. (`output/baselines/correlation_v1.md`)
- **C2 (측정, 메인)** — RCPS (Retrieval-Conditional Parsing Score): task-oriented
  chunking/parsing 품질 지표. intrinsic 지표(MoC Boundary Clarity)가 못 잡는 것을
  잡음 (BC↔RCPS Pearson −0.81).
- **C3 (정직한 negative result)** — parser layer에 chunk-boundary contrastive aux
  loss를 직접 거는 자연스러운 해법(RADP-B)이 retrieval을 개선하지 못함을 λ sweep +
  matched control로 엄밀히 보임. "이 문제는 parser-layer 튜닝으로는 안 풀린다."

framing 한 줄: *진단하고(C1) — 측정 지표를 준다(C2) — 가장 자연스러운 해법이
왜 안 통하는지 보인다(C3).*

## 2. Section breakdown (4 page)

| § | 제목 | 분량 | 핵심 |
|---|------|:----:|------|
| 1 | Introduction | 0.5p | parsing↔retrieval mismatch, C1/C2/C3 요약 |
| 2 | Related Work | 0.5p | 6-layer RAG pipeline positioning — parser layer가 비어있음 |
| 3 | RCPS Metric | 0.75p | RCPS 정의, 정규화 매칭, intrinsic 지표와의 대비 |
| 4 | RADP-B and Why It Fails | 0.75p | decision-A 정식화, λ sweep negative |
| 5 | Experiments | 1.0p | baseline grid, H1 상관, chunking grid, MoC 상관 |
| 6 | Discussion & Deployment Lessons | 0.5p | 왜 parser-layer 튜닝이 안 되나, 실무자에게 RCPS의 가치 |

> §3+§4를 합쳐 "Method"로 봐도 됨. §4는 RADP-B를 *제안*이 아니라 *검증한 가설*로
> 서술 — negative result 논문 톤.

## 3. Figures (확정 5 + optional 1)

| # | 그림 | 뒷받침 데이터 | 상태 |
|---|------|---------------|:----:|
| F1 | 6-layer RAG pipeline — parser layer 공백 표시 | lit review | ✅ 그릴 수 있음 |
| F2 | Parsing 품질(BC) vs RCPS scatter (C1 진단) | `correlation_v1.md` | ✅ 데이터 있음 |
| F3 | λ sweep: λ↑ → RCPS↓ 단조 하락 (C3 negative) | `week2_lambda_sweep.json` | ✅ 데이터 있음 |
| F4 | Baseline grid heatmap (6 parser × 3 retriever) | `grid_v1_parser_native.md` | ✅ 데이터 있음 |
| F5 | RCPS vs MoC Boundary Clarity scatter (C2) | `moc_bc_correlation.md` | ✅ 데이터 있음 |
| F6 | Cross-domain bar (KoGov vs OHRBench) | — | ⏳ 3.1 미실행 (optional) |

→ **원안 Figure 4(InSeNT) 삭제.** 확정 5장이면 4-page 논문에 충분(보통 3~5장).

## 4. Tables (확정 3 + optional 1)

| # | 표 | 데이터 | 상태 |
|---|-----|--------|:----:|
| T1 | Main results — 6 parser baseline grid (RCPS/Hit@1/MRR@10) | `grid_v1_parser_native.md` | ✅ |
| T2 | Chunking-strategy grid (Fixed/MD-h3/ParserNative/Lumber) | `chunking_grid_v1.md` | ✅ |
| T3 | RADP-B λ sweep ablation (λ=0/0.1/0.3/0.5/1.0 + v1 ref) | `week2_lambda_sweep.json` | ✅ |
| T4 | Cross-domain | — | ⏳ optional (3.1) |

→ **원안 Table 3(InSeNT) 삭제.** 원안 Table 1의 NED 컬럼은 parsing 품질 지표라
유지 가능(부록).

## 5. §3.4 작성 순서 (다음 단계)

1. **Abstract** (150 words) — C1+C2+C3 압축
2. **§1 Intro** — motivation → "we confirm (C1) + we measure (C2) + we show the
   natural fix fails (C3)" → 기여 3줄
3. **§2 Related Work** — `LITERATURE_REVIEW_v1.md` 재포장 + 6-layer figure
4. **§3 RCPS** — 정의, property, intrinsic 지표 대비
5. **§4 RADP-B** — decision-A 정식화 명시, negative result

작성물 위치: `paper/` (LaTeX 골격은 PHASE_4 polish에서 ACL 템플릿 적용,
초안 prose는 우선 `paper/draft/` markdown).

## 6. 미결 — OHRBench cross-domain (3.1)

PHASE_3 §3.1은 원래 "RADP-B 모델로 cross-domain zero-shot". RADP-B가 negative라
이 형태로는 의미 없음. 살리려면 **"RCPS·baseline grid가 cross-domain에서도
성립"**으로 재정의해야 함 — 즉 OHRBench Manual/Law에 6-parser grid를 다시 돌리는
것. 단 WEEK2_FINDINGS는 이를 "(시간 되면)"으로 격하했고, Q-A 추출에 GPT 호출이
필요할 수 있어 [[api-budget-constraint]]와 충돌 가능. **실행 여부는 사용자 판단
대기** — 미실행 시 논문은 single-domain으로 가고 cross-domain은 limitation/future
work로 정직하게 명시.
