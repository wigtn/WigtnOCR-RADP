# RADP 진행 보고 — H1 검증 이후 (공유용)

> 대상: 형섭 (프로젝트 리드)
> 작성일: 2026-05-21
> 범위: H1 검증(parsing↔retrieval 상관) 이후 ~ PHASE_1·2 완료까지.

---

## ⚠️ TL;DR — 먼저 알아야 할 것

**RADP-B (C3, 우리가 제안한 메서드)는 검증 결과 작동하지 않습니다.** λ sweep 전
구간에서 retrieval을 개선하지 못했고, λ가 커질수록 오히려 RCPS·parsing이 같이
하락했습니다. → **proposal §9의 fallback대로, 논문을 C1(진단) + C2(RCPS metric)
중심으로 pivot 확정.** RADP-B는 정직한 negative result로 보고. RADP-A는 ACL 2027.

PHASE_1(baseline·RCPS) 작업은 이번에 제대로 완성했습니다 (이전엔 일부 스킵된 채
Week 2로 건너뛰어 있었음).

---

## 1. RADP-B 학습 + 평가 결과 (핵심)

PRD §4.1 기반 구현. 단 **세 가지 deviation** — 특히 ①은 형섭님 검토 필요:

**① contrastive 정식화 (`decision-A` — 가장 중요)**: PRD §4.1의 contrastive를
문자 그대로 구현하면 **미분 불가**다. gradient 경로가 `parser → 이산 markdown →
chunk → BGE-M3` 인데 "이산 markdown 생성" 단계가 미분되지 않음. 그래서 이전
세션이 `decision-A`로 대체 — parser의 hidden state를 mean-pool 후 projection
head로 BGE-M3 공간에 정렬 (`contrastive.py` docstring에 기록). **따라서 아래의
"RADP-B 실패"는 정확히는 "decision-A 변형의 실패"이며, PRD §4.1의 원래 정식화를
literal하게 테스트한 것이 아니다** (literal 구현은 불가능). 다른 정식화(예:
retrieval reward RL = RADP-A 계열)는 미검증.

**② 프레임워크**: ms-swift 4.2가 pinned 환경(transformers 5.8, cu128)과 비호환 →
HF Trainer 스택으로 구현 (LoRA 하이퍼파라미터·결과엔 영향 없음).

**③ 학습 데이터**: §5.1은 2,667p를 명시하나 L_contrast엔 Q-A가 필수이고 Q-A는
294 val 페이지에만 존재 ([[api-budget-constraint]]로 train-page Q-A 생성 불가).
→ 294p를 169/73으로 split, 169p 파일럿으로 학습.

**λ sweep 결과** (held-out 73p, RCPS@md_h3):

| λ | 0.0 | 0.1 | 0.3 | 0.5 | 1.0 |
|---|----|----|----|----|----|
| RCPS | 0.624 | 0.629 | 0.608 | 0.592 | 0.546 |

- best(λ=0.1)가 λ=0 대비 **+0.005** — 게이트 기준 +0.05(5pp)의 1/10.
- λ↑ → RCPS·parsing 충실도 **단조 하락**. 튜닝 문제가 아니라 contrastive
  objective(decision-A 정식화)가 counterproductive.
- → **게이트 FAIL.** 169p→2,667p 풀스케일 확장 안 함 (예산 절약).

상세: `docs/WEEK2_FINDINGS.md`, `output/results/week2_lambda_sweep.json`.

## 2. Pivot 결정

proposal §9 / PHASE_2 리스크의 *"gain<5pp → method 격하, RCPS로 pivot"* 발동.

**개정된 논문 구성**:
- **C1** 진단 — parsing 품질 ≠ retrieval (한국어 도메인, H1 검증).
- **C2** RCPS metric — task-oriented chunking 품질 지표 (**메인 기여**).
- **C3** RADP-B — 파서를 retrieval 신호로 직접 학습 시도 → **정직한 negative
  result** ("자연스러운 해법이 안 통함, 문제는 더 어렵다").
- RADP-A는 future work (ACL 2027).

## 3. PHASE_1 완성 (baseline·RCPS — 이전에 스킵돼 있던 것 마무리)

| 항목 | 결과 |
|------|------|
| Q-A 검증 | 100개 stratified 샘플 94% accept (LLM-assisted) |
| Baseline grid (6 parser × 3 retriever) | Qwen3-VL-30B 0.584 / **v1 0.583** / Qwen2B-base 0.532 / MinerU 0.212 / PaddleOCR 0.140 / Marker 0.073 |
| Chunking grid (v1, 4 chunker) | md_h3 0.593 > parser_native 0.583 > **LumberChunker 0.557** > fixed500 0.535 |
| EnterpriseDocBench r 재현 | parsing↔retrieval Pearson **r = 0.18~0.32** (<0.5) — H1 확정, r=0.14 한국어 재현 |

발견:
- **MinerU/PaddleOCR/Marker는 한국어 정부문서에서 출력이 비거나 깨짐**(모지바케) —
  직접 검증 확인. 낮은 RCPS는 metric artifact가 아니라 실제 파싱 실패.
- **LumberChunker(LLM 청커)는 단순 규칙 청커(md_h3)를 못 이김** — 장편 서사용
  설계라 정부문서엔 transfer 약함. (위기 아님 — baseline의 정상적 비교 결과.)

## 4. 주요 기술 결정 (사유는 각 문서에)

- **retriever jina-v3 → Qwen3-Embedding-8B 교체** — jina-v3 remote 코드가
  transformers 5.8과 비호환, 간헐적 NaN 임베딩 (`docs/PHASE1_5_BASELINE_DECISIONS.md`).
- **MoC chunker / Late Chunking → cite-only** — PRD §11 허용. Late Chunking은
  mean-pooling 장컨텍스트 모델 필수인데 표준 모델(jina-v3) 비호환, C1~C4에
  non-load-bearing. MoC Boundary Clarity 지표(§3.2)는 구현·실행 완료 (BC↔RCPS −0.81).
- **RCPS relevance 매칭** — 정규화(공백·markdown 무시)로 parser를 포맷 아닌 내용으로 비교.

## 5. 현재 상태 / 다음

- **Phase 0·1·2 완료.** 코드·결정·결과 전부 `ssw` 브랜치에 커밋·푸시.
- 다음 = **Phase 3: 논문 writing** — C1 진단 + C2 RCPS 메인, C3 negative result.
- 검토 요청 포인트:
  1. **§4.1 contrastive가 literal하게는 미분 불가** — `decision-A` 대체가 적절했는지,
     다른 정식화(미검증)를 시도할 가치가 있는지. (위 §1-① 참조)
  2. pivot 방향(C1+C2 메인) 동의 여부.
  3. RADP-B negative result를 논문에 어떻게 배치할지 (별도 섹션 vs ablation).
  4. RADP-B의 169p 파일럿 한계 — proposal §5.1(2,667p)과의 간극을 논문에 어떻게 명시할지.

## 참조 문서

- `docs/WEEK2_FINDINGS.md` — RADP-B negative result 상세
- `docs/PHASE1_FINDINGS.md` — Week 1 baseline 종합
- `docs/PHASE1_5_BASELINE_DECISIONS.md` — baseline 선택 결정·사유
- `output/baselines/`, `output/results/` — 원자료
