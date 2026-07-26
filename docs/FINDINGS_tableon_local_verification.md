# Findings — table-ON 결과 로컬 이중검증 (sanity 3종 + 수치 재도출 2종)

> 2026-07-26, 로컬(macOS) 검증. 대상: ml37/ml35 실행 결과
> `docs/FINDINGS_tableon_rcps_and_prod_absent.md` (main, 8dd5104 기준)의 §1
> table-ON MinerU 수치가 아티팩트(스텁·chunker 병리·전송 오류) 없이 성립하는가.
> 결론 먼저: **5개 검증 전부 통과. C1 헤드라인("공정 설정으로도 MinerU는 구제되지
> 않는다")은 로컬에서 독립 재현됨.** 단, 커밋된 per-QA JSON 1개가 손상돼 있어
> 재커밋이 필요(§4 — 검증 결론에는 영향 없음, 경계 계산으로 봉인).

사용 데이터(전부 repo 내): `results/kogovdoc/mineru_val_tableon/predictions/`(294 .md),
`data/KoGovDoc-RAG/qa_pairs_v1.jsonl`(663 Q-A), `data/KoGovDoc-Bench/val.jsonl`(294p),
main 커밋 산출물 `output/results/{grid,perqa}_MinerU-tableON_parser_native.json`.

---

## 1. 스텁 사고 재발 검사 — [통과]

0바이트 스텁 전례(3/20 로컬 클론 사고)와 같은 유형인지 전수 확인.

```bash
python3 - <<'EOF'
import os, glob, statistics as st
files = sorted(glob.glob('results/kogovdoc/mineru_val_tableon/predictions/*.md'))
sizes = {f: os.path.getsize(f) for f in files}
print(len(files), 'files |', sum(1 for s in sizes.values() if s == 0), 'empty')
EOF
```

| 항목 | 값 |
|---|---|
| 파일 수 | 294 (kogov 229 + arxiv 65) |
| **0바이트** | **0건** |
| 50B 미만 초박형 | 9건 (전부 kogov; kogov_001_page_0001, kogov_003_page_{0001,0011,0423,0774} 등 — 표지/간지류) |
| 페이지 크기 | kogov 중앙값 **413B** (평균 622B, min 1, max 4,039) / arxiv 중앙값 **3,449B** (평균 3,381B) |

스텁 아님. 대신 **kogov 추출량이 arxiv의 1/8**이라는 실질 신호 확보 — RCPS 붕괴의
1차 원인은 "추출된 텍스트 자체가 얇다"이다.

## 2. KoGov 표 페이지 육안 확인 — 손상 양상 실재 [통과]

FINDINGS가 주장한 손상 유형(쉼표→마침표, 자릿수 소실, LaTeX 파편화)이 실제 출력에
있는지 확인. 대표 페이지 `kogov_008_page_0544.md`(관경별 단가표, E2E·검수 시트와
동일 파일) 발췌:

```
172,467  131,735  13.316  27,416     ← 13,316 → 13.316 (쉼표→마침표)
61.,424                              ← 이중 구두점
D350m / 300mm / 180                  ← D400mm류 라벨 훼손, 1800 → 180
百 四 空 上                           ← 한글·기호를 한자로 오인
NO  百 … (행 구조 없는 단일행 수프)    ← 표 구조 소실, 값-헤더 연결 파괴
```

다른 페이지: `kogov_001_page_0011.md`의 `$\mathbf{\xi}/\mathbf{\Xi}$` — 한글을
그리스 수식으로 오인. 정량: **kogov 229장 중 98장(42.8%)에 `$…$`/`\mathrm`/`\text`
LaTeX 잔해** (`grep -l 'mathrm\|\\\\text\|\$' kogov_*.md | wc -l`).

→ "내용이 있어도 검색 불가능한 형태"(D, degraded)의 실물 확인. 사람 검수 50건에서
A 다수 판정이 나온 것과 같은 자산이며, WSL 문서의 해석(OCR 손상 셀이 노이즈로
작용)이 실측과 부합한다.

## 3. Chunker 병리 배제 — [통과]

LaTeX 잔해로 인한 비정상 분할(초거대 chunk 1개 or 수천 파편) 가능성 검사.
repo의 `ParserNativeChunker(min_chars=30)` 그대로 사용.

| | kogov (229p) | arxiv (65p) |
|---|---|---|
| chunks | 440 | 463 |
| chunks/page 중앙값 (최대) | **1** (12) | 7 (16) |
| chunk 길이 중앙값 / 평균 / 최대 | **80자** / 228 / 3,935 | 349자 / 468 / 5,530 |
| 2,000자 초과 | 3 | 7 |
| 0-chunk 페이지 | 0 | 0 |

**로컬 총 chunk 903 = WSL grid JSON `num_chunks` 903 정확 일치** — 입력 동일성과
chunker 재현성 동시 확인. 병리 없음: kogov가 페이지당 1개·80자로 얇은 것은 분할
오류가 아니라 §1의 추출량 부족의 직접 귀결.

## 4. 수치 재도출 A — per-domain RCPS/Hit@1 [통과 / 데이터 결함 1건 발견]

main 커밋된 per-QA JSON(`perqa_MinerU-tableON_parser_native.json`)에서 kogov/arxiv
분해를 로컬 산술로 재도출.

**발견된 결함**: 커밋된 파일이 **invalid JSON** — char 38,416 지점에서 약 60바이트
소실, `ml-e5-large__mrr@1` 배열이 663이 아닌 651개(인덱스 252부터 12개 값 소실,
해당 qa 구성 kogov 11 + arxiv 1). WSL 원본→커밋 과정의 전송 손상으로 추정.
**조치 필요: WSL 원본에서 재커밋** (아래 검증 결론 자체에는 영향 없음).

**경계 검증**: 소실 토큰이 `0.`으로 시작하므로 참값 ∈ [0,1). 소실 12개를 v=0과
v=1로 채운 두 경우를 모두 계산:

| 채움 | kogov (RCPS, Hit@1) | arxiv | overall |
|---|---|---|---|
| **v=0** | **(0.0463, 0.0380)** | (0.4861, 0.4510) | (0.1365, 0.1227) |
| v=1 | (0.0486, 0.0449) | (0.4869, 0.4534) | (0.1385, 0.1287) |
| **WSL 보고치** | (0.046, 0.038) | (0.486, 0.451) | (0.1365, 0.1227) |

**v=0 채움이 WSL 보고치와 일치** — overall은 grid JSON과 float 전체 자리 일치
(0.1365278210049452 / 0.12267471091000504), per-domain 4셀은 WSL 문서가 3자리로
보고하므로 3자리 일치(재도출 원값: kogov 0.0463205/0.0379507, arxiv
0.4860813/0.4509804). → 소실 12개 값은 전부 0.0이었고(정확히 57바이트 소실),
보고된 per-domain 분해는 어느 경계를 가정해도 유효.
**KoGov 0.046 / arxiv 0.486 재도출 완료.** 부수 확인: qa `domain` 필드,
val.jsonl 유래 소스, perqa qa_id 순서가 상호 정합(불일치 0/663) — 도메인 오배정
리스크도 닫힘.

## 5. 수치 재도출 B — absent 사다리 정합 (기존 검증 요약)

- MinerU table-ON L1-absent **438/663 = 66.06%**: 로컬 사다리 재계산이
  `FINDINGS_mineru_tableon_rerun.md`의 공식 수치 10개(L0–L4 overall + per-domain)를
  자릿수까지 재현 (도구: `scripts/analysis/absent_per_domain.py`).
- Prod 게이트: WSL 실행이 overall L1 20.2% / L4 16.9%를 ±0.2pp 내 정확 재현
  (`FINDINGS_tableon_rcps_and_prod_absent.md` §2). **[WSL stdout 인용 — Prod
  predictions가 레포에 없어 로컬 재현 불가]**
- fold seal: train 2,667 / val 294 (동 문서 §3) — 유령 숫자(2,664/2,994) 최종 사망.
  **[val 294는 로컬 실측 확인; train 2,667은 WSL stdout 인용]**

## 종합 판정

| # | 검증 | 판정 |
|---|---|---|
| 1 | 294 predictions 스텁/공백 | **통과** (0 empty) |
| 2 | 손상 양상 육안 + LaTeX 오염 정량 | **통과** (42.8% 페이지 오염, 패턴 실재) |
| 3 | chunker 병리 | **통과** (903=903, 분포 정상) |
| 4 | per-domain 수치 재도출 | **통과** (v=0 경계에서 4자리 일치) + perqa 재커밋 필요 |
| 5 | absent 사다리 정합 | **통과** (기왕 검증분) |

**Rebuttal에 실을 논리 (table-ON 쪽 절반은 로컬 검증 완료; 0.212/0.197은 논문
Table 1 인용값 — 레포 내 아티팩트 없음, 아래 Action 3):**
표를 켜도(공정 설정) MinerU의 KoGov 검색은 복구되지 않는다(RCPS 0.212→0.046,
Hit@1 0.197→0.038; arxiv는 0.486으로 준수 → 한국 정부문서 특이적 실패). 원인은
(a) 추출량 자체가 arxiv 대비 1/8(중앙값 413B vs 3,449B), (b) 살아남은 표 텍스트도
숫자·라벨이 훼손된 무구조 수프(42.8% 페이지에 LaTeX 오염, `13,316→13.316`류),
(c) chunk 통계는 정상 범위여서 분할 아티팩트가 아니다. 즉 스텁·chunker·config
세 반론 경로가 모두 데이터로 닫혔다.

**정직성 caveat (반드시 유지):** table-OFF 0.212는 원 환경, table-ON 0.046은
재구축 환경(magic-pdf 1.3.12, 2026 모델, transformers 4.49)의 값 — 버전 충실도
한계는 `FINDINGS_mineru_tableon_rerun.md` caveat 그대로 병기. 따라서 "표를 켜니
더 나빠졌다"가 아니라 "**공정 설정으로도 구제되지 않는다**"로 서술할 것.

## 독립 감사 (2026-07-26, 별도 에이전트 재도출)

본 문서의 모든 수치를 제3의 에이전트가 원시 데이터에서 독립 재도출 —
**로컬 재계산 가능한 전 항목 CONFIRMED, 불일치 0건** (초박형 9장의 미기재 4장
파일명까지 특정: kogov_004_page_{0165,0251}, kogov_008_page_{0149,0198}).
감사가 지적한 약점은 산술이 아니라 **출처 계보**: 0.212/0.197(table-OFF),
train 2,667, Prod 게이트, 사람 검수 50건은 레포 내 아티팩트가 없는 인용값이다
(→ Action items 3–5). `MANIFEST.sha256`가 tableON JSON 2종을 미포함해
전송 손상 시점의 사전 해시 대조도 불가했다(→ Action 1에 병합).

## Action items

1. [상우] `output/results/perqa_MinerU-tableON_parser_native.json` WSL 원본에서
   재커밋 (현재 커밋본 invalid JSON — 파싱하는 모든 후속 작업이 실패함).
   재커밋 시 grid/perqa 2종을 `MANIFEST.sha256`에 등재.
2. (선택) grid_v1(table-OFF) per-QA도 같은 방식으로 커밋되면 per-domain 비교표가
   table-OFF까지 확장 가능.
3. [상우] table-OFF 기준선(0.212/0.197)의 grid JSON 커밋 — rebuttal 비교 문장의
   좌변을 인용값에서 검증값으로 승격.
4. [상우] Prod 게이트·fold seal의 산출 로그(또는 JSON)를 output/에 커밋 —
   현재는 WSL stdout 인용.
5. [검수 완료 후] 사람 검수 결과 JSON(2인분 + 조정)을 커밋 — "사람 검수 50건"
   주장의 아티팩트화. (상우 독립 검수 전에는 커밋 금지 — 블라인드 보호.)
