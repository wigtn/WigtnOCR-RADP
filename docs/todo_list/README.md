# Todo List — Progress Tracker

> 프로젝트 전체 진행 상황을 한눈에 볼 수 있는 인덱스.
> 상세 task는 각 Phase 파일 참조.

## 📊 Overall Progress

| Phase | 기간 | 상태 | 진행률 |
|:-----:|------|:----:|:------:|
| **Phase 0**: Foundation | ~5/17 | ✅ DONE | `[██████████] 100%` |
| **Phase 1**: Week 1 — Data + RCPS | 5/18 ~ 5/24 | ✅ DONE | `[██████████] 100%` |
| **Phase 2**: Week 2 — RADP-B | 5/25 ~ 5/31 | ✅ DONE (negative → pivot) | `[██████████] 100%` |
| **Phase 3**: Week 3 — Cross-domain + Writing | 6/1 ~ 6/7 | ⏳ PLANNED | `[░░░░░░░░░░] 0%` |
| **Phase 4**: Week 4 — Polish & Submit | 6/8 ~ 6/14 | ⏳ PLANNED | `[░░░░░░░░░░] 0%` |
| **Submission** | 2026-06-16 | 🎯 TARGET | — |
| **Phase 5**: ACL 2027 Extension | TBD | 🔮 FUTURE | — |

## 📁 Phase Files

- [`PHASE_0_FOUNDATION.md`](PHASE_0_FOUNDATION.md) — 기초 (lit review, prototype) ✅
- [`PHASE_1_WEEK1.md`](PHASE_1_WEEK1.md) — Data + RCPS Metric ✅ (→ `docs/PHASE1_FINDINGS.md`)
- [`PHASE_2_WEEK2.md`](PHASE_2_WEEK2.md) — RADP-B Training ✅ (negative → `docs/WEEK2_FINDINGS.md`)
- [`PHASE_3_WEEK3.md`](PHASE_3_WEEK3.md) — Cross-domain + Writing ⏳
- [`PHASE_4_WEEK4.md`](PHASE_4_WEEK4.md) — Polish & Submit ⏳
- [`PHASE_5_FUTURE.md`](PHASE_5_FUTURE.md) — ACL 2027 Main 🔮

## 🎯 Critical Path

EMNLP submission까지 무조건 필요한 것:

1. ✅ Q-A pair prototype (5p)
2. ✅ Full Q-A generation (294p) + 검증
3. ✅ RCPS metric + 6 parser × 3 retriever baseline grid + chunking grid
4. ✅ RADP-B 구현 + λ sweep → **negative result** (`docs/WEEK2_FINDINGS.md`)
5. ❌ InSeNT 결합 ablation — RADP-B negative로 무의미, drop
6. ⏳ Paper writing (4 page) — **C1(진단) + C2(RCPS) 중심으로 pivot**
7. 🎯 Submit (6/16)

## ⚠️ Risk Watch

| Risk | 영향 | 상태 |
|------|:----:|:----:|
| 유사 idea publish (EnterpriseDocBench scooping) | Critical | ✅ Mitigated by reframing |
| InSeNT가 method 위협 | High | ⏳ Week 2 ablation 필요 |
| Q-A 자동 생성 품질 | Medium | ✅ v2 prompt로 해결 |
| 시간 부족 | High | ⏳ Week 4 buffer 확보 |
| RADP-B gain 부족 | Medium | ⏳ Week 2 결과 시점 판단 |

상세: `docs/RADP_RESEARCH_PROPOSAL.md §9`

## 🔄 Update 규칙

- 매일 작업 끝나면 해당 Phase 파일 체크박스 갱신
- Phase 완료 시 이 README의 진행률 업데이트
- 새 task 발생 시 해당 Phase 파일에 추가하고 origin 기록
- 차단 사항(blocker)은 즉시 README의 Risk Watch에 등재

---

**마지막 업데이트**: 2026-05-21 (Phase 1 완료 — `docs/PHASE1_FINDINGS.md`; Phase 2 완료 — RADP-B negative result로 pivot, `docs/WEEK2_FINDINGS.md`)
