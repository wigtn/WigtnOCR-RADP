# Phase 0 — Foundation

> **기간**: ~2026-05-17
> **상태**: ✅ COMPLETED
> **목표**: 연구 방향 확정, 자산 정리, prototype 검증

## Tasks

### 0.1 — 사전 분석 및 방향 설정 ✅

- [x] V2 (Gemma 4 backbone) 실험 결과 분석
  - 결과: `docs/V2_FINDINGS_REPORT.md`
  - 결론: backbone 교체는 dead-end → 방법론으로 pivot
- [x] EMNLP 2026 일정 확인
  - Main: 5/25 (8일, 불가능)
  - **Industry: 6/16** (선택)
- [x] Research direction 결정
  - 4개 후보 평가 → ① Retrieval-Aware Document Parsing 선택
  - 동기: BC/CS 1위 ≠ retrieval 1위 발견을 발전
- [x] Publication strategy 2-shot 확정
  - Shot 1: EMNLP 2026 Industry (6/16) — RADP-B
  - Shot 2: ACL 2027 Main (Asia/Pacific) — RADP-A 확장
- [x] Research proposal 작성 v0.1 → v0.2
  - 파일: `docs/RADP_RESEARCH_PROPOSAL.md`

### 0.2 — Literature Review ✅

- [x] bc-arxiv skill로 14편 paper 요약
  - 폴더: `docs/paper/PAPER-*.md`
  - 검토 키워드: retrieval-aware chunking, ColPali, Late Chunking, LumberChunker,
    MetaChunking, OCR-RAG correlation, retrieval reward DPO, contrastive chunk embedding
- [x] 종합 보고서 작성
  - 파일: `docs/literature_review/LITERATURE_REVIEW_v1.md`
  - Verdict: **CAUTION** (C1 alone = DANGER)
- [x] Scooping risk 분석 + 방어 angle 정리
  - EnterpriseDocBench (Critical): 우리 = 한국어 + method 해결책
  - InSeNT (Critical): 우리 = parser layer (그들 embedding) + orthogonality
  - M-LongDoc (Moderate): naming clash → 부제목 차별화
- [x] 권장 변경사항 proposal v0.2에 반영
  - Title: `RADP via Chunk-Boundary Contrastive Learning`
  - Framing: "we discover" → "we confirm + first parser-layer solution"
  - Scope: RADP-A를 ACL 2027로 이전
  - Baseline 추가: InSeNT, MoC, LumberChunker

### 0.3 — Repo Scaffolding ✅

- [x] uv 프로젝트 초기화 (pyproject.toml, uv.lock)
- [x] Folder structure 설계 (configs/, src/, scripts/, docs/, data/, output/, tests/)
- [x] `src/wigtnocr_radp/` 라이브러리 skeleton
  - `qa_generation/` (generator, schema)
  - `evaluation/` (Week 1 placeholder)
  - `utils/` (config loader, language heuristics)
- [x] Configs 셋업
  - `configs/data/kogovdoc_bench.yaml`
  - `configs/qa_generation/{default,gpt4o_mini,diverse_5}.yaml`
  - `configs/training/radp_b_base.yaml` (placeholder)
  - `configs/evaluation/rcps_default.yaml` (placeholder)
- [x] CLI script (`scripts/qa_generation/generate_qa.py`)
- [x] `.env.example`, `.gitignore`, `README.md`
- [x] python-dotenv 자동 로드 통합

### 0.4 — Data Pipeline ✅

- [x] KoGovDoc-Bench 다운로드 (`data/KoGovDoc-Bench/`, 109MB)
- [x] 데이터 구조 분석
  - 294 validation pages
  - Domain: 229 KoGov + 65 arXiv
  - Language: 209 ko + 78 en + 7 mixed
  - Length: median 1083 chars, max 11178
- [x] 다양한 5 sample 페이지 추출
  - `docs/qa_generation/samples/sample_*.json` (idx 0, 8, 9, 62, 259)
- [x] 데이터 품질 이슈 식별
  - idx=8: teacher reasoning leak (filter 필요)
  - idx=9: bibliography only (filter 필요)
  - idx=62: <100 chars (filter 필요)

### 0.5 — Q-A Generation Prototype ✅

- [x] Q-A schema 정의 (`docs/qa_generation/SCHEMA.md`)
- [x] Prompt v1 설계 (`docs/qa_generation/PROMPT_v1.md`)
- [x] Generator 구현 (`src/wigtnocr_radp/qa_generation/`)
- [x] **v1 실행 결과**: 5p → 1 valid Q-A (5/6 fail)
  - 원인: answer_chunk이 너무 짧음 (5~50자)
- [x] **v2 iteration**: chunk auto-expansion (코드에서 계산)
  - GPT는 question + answer_span만 반환
  - 코드가 answer_span 위치 찾고 200~800자로 자동 확장
- [x] **v2 실행 결과**: 5p → 6 valid Q-A, 3 SKIP (filter 작동)
  - 모두 자연스러운 한국어
  - chunk len 226~339자 (적절)
  - 출력: `docs/qa_generation/sample_output_v2.jsonl`

## Deliverables

- ✅ `docs/RADP_RESEARCH_PROPOSAL.md` v0.2
- ✅ `docs/literature_review/LITERATURE_REVIEW_v1.md`
- ✅ `docs/paper/` (14 paper summaries)
- ✅ `docs/V2_FINDINGS_REPORT.md`
- ✅ `docs/qa_generation/` (schema, prompt, samples, prototype output)
- ✅ 작동하는 repo (uv sync + dry-run + real run 모두 통과)
- ✅ KoGovDoc-Bench 다운로드 완료
- ✅ Q-A generation prototype 검증 (5p, $0.06, 10초)

## Lessons Learned

1. **Q-A generation에서 LLM에게 chunk를 요청하면 안 됨**
   - 표 페이지에서 cell 한 줄만 반환 → validation fail
   - **해결**: span만 받고 chunk는 코드에서 결정적으로 계산
2. **Literature review가 핵심 변수**
   - Scooping risk 발견 후 framing 전면 수정
   - 만약 안 했으면 EnterpriseDocBench와 동일 framing으로 reject 가능성
3. **Page quality filter는 명시적 prompt instruction으로 가능**
   - GPT-4o가 reasoning-leak/bibliography/empty 페이지 100% 정확히 skip
