# Camera-Ready 개정 계획 — 채택 시 (2026-07-27)

> 근거: `REBUTTAL_FINAL_EN.md`(게시본) 전수 추출 — 응답에서 한 모든 약속을 개정 작업으로 변환.
> 실행: 상우(1저자). 감사·수치 대조: Harrison + 클로드코드.
> 채택 불발 시에도 P7·P12·P14는 재제출 대비 유효.
> **레포 배치 주석**: 본 계획이 참조하는 `output/rebuttal_pack/`(게시본·번들·런북)은 블라인드/local-only 정책으로 gitignore 상태다 — 공동저자 전달은 공유 번들(zip) 경유. 이 문서 자체는 `docs/PAPER_REVISION_GUIDE.md`의 후속 개정 가이드로 커밋한다.

## 0. 게시본 스냅샷 (2026-07-27 실측)

| Comment | 자수 | 여유 |
|---|---|---|
| General Response | 4,797 | 203 |
| NAor1 (공식 R1) | 2,876 | 2,124 |
| ZQv618 (공식 R2) | **4,994** | **6 ⚠️** |
| bXGg (공식 R3) | **4,987** | **13 ⚠️** |

전 수치가 검증된 아티팩트와 일치 확인. ZQv618·bXGg는 게시 전 1글자도 추가 수정 불가(수정 시 check_len.py 재계수 필수).

---

## 1. 약속 전수 목록 → 개정 작업 (P1–P15)

### P1. 신설 Appendix C = 파서 문제 정의 + worked example 【GR-4, ZQv618 Point 1, NAor1】

- **현상태 (80% 존재)**: `main.tex` app:familyneutral(현 Appendix E) 상단에 정의 문단 압축판 이미 존재(`sec:parser-def` 라벨 포함, pseudo-GT 명시). 풀버전 LaTeX는 `docs/DRAFT_problem_definition.md`.
- **할 일**: ① 정의 확장 — 입력 서술(정부문서, born-digital+스캔, 다단·직인·병합셀) + absent 3원인 taxonomy + 근거 수치(Prod tabular 13.9% / figural 71.4% / factoid·procedural ~21%; MinerU tabular **41.7% tables-on 병기 필수** — 초안의 87.9% 단독 인용 금지, tables-off 구값). ② **worked example 1건** (GR이 "with a worked example"로 약속 — 초안에 없음): 후보 = val_0096 표 붕괴 사례(원문 표 "전통적설계법|강도설계법|RC용벽등" → MinerU 출력 `RC号甲号` 한자 잔해) 또는 FINDINGS의 셀 손상(`13,316→13.316`, `$1.5\mathrm{m}$` LaTeX 파편). 원본 발췌 + 파서 출력 대비 박스.

### P2. Appendix 재배열 — "Appendix C" 글자 정합 【응답 5회 지칭】

- 현재: A DPO-milestones / B DPO-progression / **C Chunk-mechanism** / D Coverage / **E Family-neutral** / F Noise.
- 목표: A / B(+압축된 C4 수용, P4) / **C = 정의+worked example+family-neutral+인간검증(P5)+stability(P7)** / D Chunk-mechanism / E Coverage / F Noise.
- LaTeX `\ref` 자동 갱신이라 블록 이동이면 됨. **완료 후 응답 원문의 "Appendix C" 5곳과 최종 레터 대조** (리뷰어가 응답 읽고 개정판 열었을 때 일치해야 함 — 구번호 사고의 재발 방지).

### P3. Intro 재구성 【GR-2, NAor1, bXGg】

- 발견 3개가 lead: ① intrinsic 반상관(r=−0.81, 선택 반전 2.8~4.5×) ② parser-vs-chunker 진단 ③ 훈련 부정적 결과.
- "ought-vs-is delta" 명시(NAor1: "We will state this delta explicitly in the intro").
- **명시적 scope 문장**: "retrieval, not end-to-end generation" (bXGg: "we will state it as an explicit scope").

### P4. 밀도 개선 【ZQv618 Point 4】

- Abstract 다절 문장 분리. parser/chunker/retriever 용어 선행 정의.
- 본문 표 이동: 현 본문 표 3개(main.tex L119/144/166) 중 **tab:noise·tab:c4 계열 → appendix** (라벨 실행 시 확인). 본문 6페이지 유지.
- **C4(§4.4) 섹션 압축 → appendix** (bXGg: "we will compress the section into the appendix") — 본문엔 결론 1문단+포인터.

### P5. 인간 검증 수치 논문 반영 【GR, ZQv618, bXGg】

Appendix C 소절로: 프로토콜(파서 마스킹 시트, LLM-판정 absent frame 층화 100 = MinerU 50/Prod 30/Paddle 20, 저자 2인 독립 판정 → 불일치 19건 공동 합의) + 수치: **κ=0.615 (raw 81/100)** / genuine: **MinerU 84.0% [71.5, 91.7]**, Paddle 95.0% [76.4, 99.1], **Prod artefact 60.0% [42.3, 75.4]** / cross-family judge와 동일분모 대응(84.2/84.1/44.0% — 전부 CI 내) / human–LLM binary **90.3% (n=93**, MinerU 프레임 세대 교집합 사유 각주**)**. 표기는 "the two authors".

### P6. E2E 표 신설 【bXGg Q2: "We will add the end-to-end table"】

- 열: parser / answer accuracy(72.5/23.8/20.5) / EM / answered rate + RCPS dual-config(0.583 / 0.212 off·0.137 on / 0.140).
- 각주: 하위 2개 근소차(ΔRCPS≈0.003) — rank-2/3 순서만 MinerU 설정 의존, 배포 선택 불변. "3–3.5×"는 vs MinerU/Paddle 각각.
- 소스: `output/results/e2e_rag.json`(dual-ref 커밋본).

### P7. Probe-resampling stability — full-grid 【bXGg Q1: "The full-grid version goes into the revision"】

- **선행 실행(WSL, 채택 전이라도)**: 6파서×parser_native + Prod×4청커 per-QA 수출 → `rank_stability_bootstrap.py`(커밋됨 e005ad7) → 결과 JSON 커밋+MANIFEST. 런북: `share_to_ssw/WSL_RUNBOOK_rank_stability.md`.
- 논문 소절(Appendix C): 가용 풀 실측(파서쌍 100%/청커 근소쌍 98.8%/E2E 100%) + full-grid 결과.
- ⚠️ **소스 미확인 문장 2개** — bXGg Q1의 "unchanged with MRR@10 alone (vs averaged cutoffs)"와 "format normalisation shifts scores by 0.02–0.03": 근거 아티팩트 소재 확인(후보: `scripts/analysis/robustness_boost.py` 계열) → 없으면 재계산 후 논문 인용. 조기 처리.

### P8. MinerU tables-on 정식 반영 【GR, ZQv618 self-audit】

- Table 1: MinerU(tables-on) 행 추가 또는 dual 표기. 헤드라인 정책 = GR 문구 정합: published 35.1pp는 **lower bound**, corrected **42.6pp** 병기. 4.47× 병기.
- Limitations에 config 교정 서술("we correct it in Limitations"): tabular absent 87.9→41.7%(still ~3× Prod 13.9%), 전체 L1 gap +50.2→+45.9pp, retrieval은 mixed 0.212→0.137(KoGov-only 0.046 붕괴, arxiv 0.486이 완충) — FINDINGS_tableon caveat 오류 문장은 인용 금지(fefa808로 정정됨).

### P9. pseudo-ground-truth 정정 3곳 【ZQv618 Point 1 "(see Limitations)"】

- `paper/draft/paper.md` L76(§4.1)/L183(Limitations)/L237(App C Table 7 캡션)의 "human-curated ground-truth" → pseudo-GT 서술로. main.tex은 351행 정용법 외 무결 확인됨 — md/tex 어느 쪽이 camera-ready 정본인지 확정 후 일괄. Limitations의 pseudo 서술 존재 확인·보강.

### P10. 재현성 체크리스트 + exact run commands appendix 【NAor1 조건부 제안 — 이행 권장】

- "happy to add … if that would help"로 남겼지만 저비용·신의성실 — 체크리스트 + 명령어 부록 추가. `scripts/analysis/` 커밋 스크립트들이 재료.

### P11. 데이터 구성·오염 상한 문장 【GR】

- "294 = 229 KoGov + 65 arXiv / Q–A 527+136 / 페이지 단위 분할 / 오염 기여 상한 **4.9pp**(=파인튜닝 delta: Prod−2B-base Hit@1 0.5485−0.4997=4.88pp) vs 파서 갭 42.6pp" — Appendix G 또는 Limitations에 명문화.
- **CR-1**: Appendix G.2.1 도메인 행 오류(arXiv 613→864). **CR-2**: HF 카드 277→283+24. (기존 큐, `docs/PAPER_REVISION_GUIDE.md` §8b)

### P12. 아티팩트 공개 정합 — "Everything is released" 실체화 【GR】

- 완료 ✅: judge cache 1,017(d4a41bb) · e2e dual-ref · 분석 스크립트(rank_stability 포함) · MinerU tables-on predictions · MANIFEST.
- **미완**: ① **MinerU tables-OFF predictions 커밋**("release both outputs" 약속의 나머지 절반 — 현재 WSL에만) ② full-grid stability JSON(P7) ③ 인간 검수 per-case 라벨 공개 여부 결정 — 권장: 최종 adjudicated 100건 라벨 + 프로토콜 문서 공개(검수자 익명 "author A/B"), answer key 구조상 blind 재현 가능하게.

### P13. De-anonymization 【camera-ready 관례】

- 저자·소속·acks 복원, 라이브 링크(HF/GitHub) 삽입 — rebuttal 기간 익명 규칙 해제.
- 벤치마크 명명 일관성(논문 "KoGov" 표기 vs HF "KoGovDoc-RAG") 정책 확정 후 통일. HF 카드 정정은 CR-2와 함께.

### P14. 수치 라운딩·정합 감사 (자동)

- 응답과 아티팩트 간 미세 라운딩 통일 — 예: 응답 "−1.3 to +5.0pp"(같은 가족 gap)의 −1.3은 아티팩트 표(−1.4, 1.36의 반올림) 기준으로 논문에선 −1.4 계열 사용.
- 기존 검증 스크립트(scratchpad verify_pack.py) 확장 → camera-ready 본문 수치 전수 자동 대조 1회.

### P15. 약속-이행 최종 게이트

- 개정판 완성 후 `REBUTTAL_FINAL_EN.md`의 모든 미래형 문장("will …", "goes into the revision", "we add …") 추출 → 개정판 대응 위치 매핑 체크리스트 실행. 하나라도 미이행이면 camera-ready 제출 보류.

---

## 2. 실행 순서 (의존성)

```
[지금, 채택 무관]   P7 선행 실행(WSL) · P12-① tables-OFF 커밋 · P7-⚠️ 소스 확인
[채택 직후, 1주]    P2(재배열 뼈대) → P1·P5·P6·P8(내용 삽입) → P3·P4(본문 개편)
[마감 전]           P9·P10·P11 → P13(de-anon) → P14·P15(감사 게이트)
```

## 3. 리스크

1. **Appendix C 글자 재불일치** — P2 완료 후 응답 원문 5곳 대조 필수 (구번호 사고 재발 방지 항목).
2. **P7 미확인 문장 2개** — 근거 없으면 응답이 이미 주장한 사실이라 재계산으로 반드시 채워야 함. 조기 확인.
3. **6페이지 제한** — P1 worked example + P5 + P6 + P7 전부 appendix行이므로 본문 증가 없음. 단 P3·P4 개편 시 넘침 주의.
4. Marker 38페이지 각주 유지(코퍼스 불일치).

## 4. 역할

- **상우**: P1–P13 실행(1저자 전권), WSL 런(P7·P12-①).
- **Harrison + 클로드코드**: P14·P15 감사 자동화, 개편 리뷰, 수치 대조.
