# Findings — Prod per-domain 분해 + 숫자 정합성 확정 (rebuttal R1.1 지원)

> 2026-07-25, 로컬(macOS) 작업. 브랜치 `rebuttal/family-neutral-absent`.
> 신규 스크립트: `scripts/analysis/absent_per_domain.py`, `scripts/analysis/perqa_source_rcps.py` (미커밋).
> 기준값: 663 Q-A = 527 KoGov + 136 arXiv / 294p = 229 + 65 / Prod absent L1 20.2% · L4 16.9% /
> Table 1: Prod 0.549/0.583, 2B-base 0.500/0.532, MinerU(table-OFF) 0.197/0.212.

---

## 작업 1 — Prod per-domain absent (L1/L4)

**상태: 로컬 산출 불가 — [근거 없음(로컬)]. 구현은 완성·검증됨, 입력 데이터만 WSL에 있음.**

- 사용 파일: `data/KoGovDoc-RAG/qa_pairs_v1.jsonl`, `data/KoGovDoc-Bench/val.jsonl`,
  `src/wigtnocr_radp/evaluation/absent_matchers.py`(LADDER 그대로 재사용),
  `evaluation/parser_outputs.py`, `evaluation/rcps.load_qa_pairs`.
- 차단 원인: 로컬 클론(3/20)의 `wigtnOCR-v1/results/kogovdoc/v1_val/predictions/` 294개 파일이
  **전부 0바이트 스텁**. mineru_val(table-OFF)·paddleocr_val·v2-best_val도 0/294,
  30b_val은 211/294만 실콘텐츠(83개 빈 파일 → 산출 시 absent 과대계상되므로 계산 금지).
  실콘텐츠 완전본: 2b_base_val(294), marker_val(38), RADP repo의 mineru_val_tableon(294).
- **구현 검증 [통과]**: 동일 스크립트를 MinerU table-ON에 적용 →
  `FINDINGS_mineru_tableon_rerun.md`의 공식 수치 10개 전부 자릿수까지 재현.

| MinerU table-ON | arxiv (n=136) | kogov (n=527) | overall (n=663) |
|---|---|---|---|
| L1_normalized | 48/136 = 0.352941 (35.3%) | 390/527 = 0.740038 (74.0%) | 438/663 = 0.660633 (66.1%) |
| L4_fuzzy_lcs | 34/136 = 0.250000 (25.0%) | 378/527 = 0.717268 (71.7%) | 412/663 = 0.621418 (62.1%) |

- Prod 실행 커맨드 (WSL, 수 초 소요 — 텍스트 매칭만):

```bash
uv run python scripts/analysis/absent_per_domain.py \
    --parser-dir /mnt/data1/work/wigtnOCR-v1/results/kogovdoc/v1_val/predictions \
    --label Prod
# 게이트: overall L1이 20.2%±0.2pp, L4가 16.9%±0.2pp 재현되어야 per-domain 수치 채택
```

- 보충(참고용, 검증 기준치 없음): 2B-base per-domain —
  L1 kogov 133/527 = 0.252372 (25.2%), arxiv 34/136 = 0.250000 (25.0%), overall 167/663 = 0.251885 (25.2%);
  L4 kogov 109/527 = 0.206831 (20.7%), arxiv 31/136 = 0.227941 (22.8%), overall 140/663 = 0.211161 (21.1%).
  같은 Qwen3 계열 2B-base조차 kogov/arxiv absent가 균형(25.2 vs 25.0)이라는 점은
  MinerU의 kogov 편중(74.0 vs 35.3)이 family 효과가 아니라는 보조 근거로 쓸 수 있다.

## 작업 2 — per-domain RCPS / Hit@1

**Prod: 산출 완료 [통과 — fold 기준]. 30B/2B-base/MinerU: [근거 없음(로컬)].**

- 사용 파일: `output/results/FULL_HF_perqa_242p.json`("v1 (ref)" = Prod, 242p 코퍼스),
  `qa_pairs_v1.jsonl`, `val.jsonl`. 파서 그리드 per-QA(`output/baselines/grid_v1_*.json`)는
  로컬 부재 — perqa 계열 전 파일(FULL_HF/v5/v4/simpo/radp_b/ohr*) 전수 스캔 결과
  시스템 키가 학습 변형(λ·DPO·SimPO·v1(ref))뿐임을 확인.
- 재현 커맨드:

```bash
.venv/bin/python scripts/analysis/perqa_source_rcps.py \
    --perqa output/results/FULL_HF_perqa_242p.json --system 'v1 (ref)'
```

| chunker | metric | kogov (527) | arxiv (136) | overall (663) |
|---|---|---|---|---|
| md_h3 | macro Hit@1 | 0.569892 | 0.534314 | 0.562594 |
| md_h3 | RCPS | 0.603749 | 0.579268 | 0.598727 |
| parser_native | macro Hit@1 | 0.548387 | 0.563725 | 0.551533 |
| parser_native | RCPS | 0.583550 | 0.594030 | 0.585700 |

- 검증: overall은 동일 per-QA 배열에서 재계산(가중평균 항등 성립).
  parser_native overall RCPS **0.585700** vs 논문 §4.4a fold 고정치 **0.586** → 차 0.03pp **[통과]**.
  Table 1(0.549/0.583)은 **294p 그리드 코퍼스**(52 distractor 포함) 기준이라 이 파일로는
  직접 재현 불가 — 논문 자체가 0.583(그리드) vs 0.586(fold)을 구분 명시. 그리드 per-QA는 WSL에서
  `baseline_grid.py` 재실행 시 `--out_dir`에 생성됨.
- 읽기: Prod는 두 도메인에서 균형(parser_native RCPS 0.5836 vs 0.5940; arxiv가 오히려 소폭 높음).
  MinerU의 도메인 격차(absent 74.0 vs 35.3)와 대조적 — "absent 격차는 한국어 정부문서 현상"
  서사를 retrieval 축에서도 지지.

## 작업 3 — MinerU table-ON retrieval: **미실행 확정**

- 탐색 경로: `output/` 전체에서 tableon 참조 grep 0건, `output/baselines/` 부재,
  FINDINGS_mineru_tableon_rerun.md 아티팩트 목록에 predictions + absent ladder만 명시,
  RUNBOOK Step 4가 "optional, needs GPU" 상태로 종결.
- 실행 절차 (WSL, GPU; 승인 후):
  1. RADP repo pull (predictions는 `results/kogovdoc/mineru_val_tableon/predictions/`로 이미 커밋됨).
  2. `scripts/evaluation/baseline_grid.py`의 `PARSER_DEFS`에 1행 추가:
     `("MinerU-tableON", "…/WigtnOCR-RADP/results/kogovdoc/mineru_val_tableon", "ocr")` —
     `V1_RESULTS_ROOT` 밖 절대경로 허용 여부 확인(현 구현은 root 기준 join이므로 절대경로 처리 1줄 필요).
  3. `uv run python scripts/evaluation/baseline_grid.py --qa data/KoGovDoc-RAG/qa_pairs_v1.jsonl`
- 예상 소요: 임베딩 3종 × (chunks ~1.4k + 663 queries). BGE-M3·e5-large는 수 분,
  Qwen3-Embedding-8B가 지배적 — RTX 5070 기준 **총 15–40분** 추정(원 그리드 실행 로그 부재로 보수 추정).
- 산출 후 비교표 골격: table-OFF(RCPS 0.212 / Hit@1 0.197) vs table-ON(신규), per-domain 분해는
  `--out_dir` 산출물에 per-QA가 남으면 `perqa_source_rcps.py` 재사용.

## 작업 4 — 숫자 정합성 3건

### 4a. "2,994 → 2,664+294=2,958, 36장 행방" — **전제 자체가 성립하지 않음 [근거 없음]**

2,994 / 2,664 / 2,958 세 숫자 모두 로컬 어디에도 없다. 탐색 경로: RADP 전 브랜치
(main·rebuttal·review·ssw·docs/readme-v06)의 docs/configs/scripts/output JSON, 훈련 레포
스크립트·로그 20종(regenerate_failed.log 602줄 포함)·docs/paper 부록 전체, HF 카드 2종
(모델·데이터셋), data_stats.json 신·구본, train/val jsonl 실측.

정본 체인은 **세 독립 출처가 정합**:

| 단계 | 값 | 출처 |
|---|---|---|
| pre-filter | 4,501 (KoGov 3,637 + arXiv 864) | Appendix G.2 = HF 데이터셋 카드 |
| score≥3 + non-sampled | 3,977 | Appendix G.2 |
| max_doc_ratio=0.25 | 2,961 (+정제 283 / 탈락 24 반영 후) | G.2 = data_stats.json (2,985 준비 → −24) |
| split (seed 42, 90/10) | **train 2,667 / val 294** | data_stats.json = G.2 = HF 카드 |

검산: 2,961 − 294 = 2,667 ✓. **판정: 논문 "2,667-page" 표기가 맞다. "36장"은 존재하지 않는
두 숫자의 차이이므로 규명 대상이 아님.** (2,664·2,994의 최초 출처는 로컬 아티팩트가 아니라
구두/타 머신 전달 과정의 변형으로 추정 — WSL 실측 재확인 1회만 권장:
`wc -l /mnt/data1/work/wigtnOCR-v1/datasets/training/{train,val}.jsonl`)

부수 발견(교정 필요):
1. **Appendix G.2.1 도메인별 행 오류**: arXiv post-filter 613 → post-downsample 864로
   *증가* (불가능). 디스크 실측(정제 전 렌더 이미지)은 documents 2,339 / papers 646
   (78.4 : 21.6)로 G의 2,097/864 (70.9 : 29.1)와 불일치. 총계 행(2,961)만 정합. G.2.1 표 재작성 필요.
2. **HF 데이터셋 카드**: "cleaned 277 samples" vs data_stats/G.2의 "283 cleaned + 24 dropped" — 카드 갱신 필요.
3. 로컬 사본 위생: `datasets/training/train.jsonl`(745줄, 704×4096B 절단)과
   `v1_val` 등 예측 스텁 — 이 머신에서 카운트·매칭 금지 대상.

### 4b. 질문 언어 분해 — **가설 "527 ko / 136 en" [불일치]**

- 재현: `scripts/analysis/source_groupby.py --qa data/KoGovDoc-RAG/qa_pairs_v1.jsonl` (한글 정규식 판별)
- 실측: **질문 언어 ko 521 / en 142.** 출처 기준(527/136)과 6건 어긋남 — kogov_003(측량 좌표·계산
  페이지, 숫자/기호 위주)에서 GPT-5.4가 영어 질문 6건 생성. jsonl `language` 필드(511/146/6 mixed)는
  GT 마크다운 기준 감지라 질문 언어와 또 다름.
- 앵커 육안 확인: 무작위 10건 + 예외 6건 전수 출력 — 판별 오류 0건.
- 문안 지침: 구성 문장은 "**출처 기준** 527 KoGov / 136 arXiv"로 쓰고, 질문 언어를 언급할 땐
  521/142로 별도 표기 (두 축을 섞으면 리뷰어가 재계산 시 불일치 발견).

### 4c. 52 distractor 페이지 소스 — **전부 KoGov 아님**

- 실측: **kogov 40 + arxiv 12** (294 − 242 Q-A-bearing). Q-A 없는 페이지를 "retrieval distractors"로
  서술할 때 소스 혼합임을 명시할 것.

---

## 잔여 액션 (2026-07-26 전건 승인 — Harrison)

1. [WSL, 최우선] Prod per-domain 실행 — 절차: `docs/HANDOFF_wsl_rebuttal_runs.md` Run 1.
2. [WSL, 오늘 착수] table-ON retrieval — 전용 러너 `scripts/analysis/grid_single_parser.py`
   신설로 baseline_grid.py 수정 불필요해짐. 절차: HANDOFF Run 2. E2E table-ON 재실행(상우)과
   동일 predictions 사용 확인 필수.
3. [camera-ready 큐 등재 완료] G.2.1 표·HF 카드 교정 — `PAPER_REVISION_GUIDE.md` §8b (CR-1, CR-2).
   Rebuttal에서는 비언급(provenance는 G.2 총계 체인만 인용).
