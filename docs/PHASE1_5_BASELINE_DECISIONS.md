# PHASE_1 §1.5 — Baseline 결정 기록 및 사유

> 작성일: 2026-05-21
> Week 1 §1.5 "Additional Baselines"의 chunking / retriever baseline 결정과 그 근거.
> 모든 결정은 사용자 승인하에 확정.

> **역사적 baseline 기록 주의 (2026-08-24):** 아래 `r=-0.81`은 MinerU-off 기반 초기 grid다. 현재 camera-ready C1의 동일-구성 근거는 MinerU-on 포함 `r=-0.74`, Marker 포함 보조 분석은 `r=-0.83`이다.

## 요약

| 항목 | 결정 | 핵심 사유 |
|------|------|-----------|
| LumberChunker | ✅ 실측 (chunking grid 포함) | 구현·실행 완료 |
| MoC (chunker) | cite-only | MoE-chunker 통합 부담; PRD §11이 명시 허용. MoC Boundary Clarity 지표는 §3.2용으로 구현·실행 완료 |
| Late Chunking | cite-only | mean-pooling 장컨텍스트 모델 필수 — 표준 모델 jina-v3가 transformers 5.8 비호환. 논문 기여 C1–C4에 non-load-bearing |
| jina-v3 (retriever) | Qwen3-Embedding-8B로 교체 | jina-v3 remote 코드 ↔ transformers 5.8 비호환 → 간헐적 NaN 임베딩 |

최종 baseline 구성:
- **Chunking grid**: Fixed500 / MD-h3 / ParserNative / LumberChunker (4종)
- **Retrievers**: bge-m3 + multilingual-e5-large + qwen3-emb-8b (3종, 모두 검증됨)

---

## 1. LumberChunker — 실측 ✅

LLM narrative-boundary chunker (arXiv:2406.17526). 122B vLLM(qwen3.5-122b-gptq-vl)을
LLM 백엔드로 구현. chunking grid 결과: RCPS 3위(0.557) — MD-h3(0.593)·
ParserNative(0.583)에 못 미침. 타당한 결과 — LumberChunker는 장편 서사용 설계,
정부문서(표·양식·법조문)엔 transfer 약함. 논문 chunking baseline으로 그대로 사용.

## 2. MoC chunker — cite-only

- MoC(ACL 2025) 공식 release 존재: `github.com/IAAR-Shanghai/Meta-Chunking/tree/main/MoC`.
- 그러나 그들의 Mixture-of-Chunkers(MoE) 통합은 research-repo 의존성·환경 호환
  부담이 큼 (이번 세션에서 jina-v3 / ms-swift / 122B 등 동류 비호환을 반복 경험).
- **PRD §11이 명시 허용**: *"공식 release 우선 사용, 안 되면 paper 인용만 + 부분 재현."*
- MoC의 핵심 비교 자산 — **Boundary Clarity 지표** — 는 §3.2 (RCPS vs intrinsic
  metric) 분석용으로 이미 구현·실행 완료 (`boundary_clarity.py`; BC↔RCPS
  Pearson −0.81, n=5).
- → MoC *chunker 자체*는 cite-only. MoC와의 핵심 대비(intrinsic vs extrinsic 지표)는
  Boundary Clarity 비교로 살아있음.

## 3. Late Chunking — cite-only

근거를 PRD 논문 목표에 대조하여 판단:

**(a) 방법론적 제약** — Late Chunking(Jina, 2024)은 **mean-pooling** 장컨텍스트
임베딩 모델을 *필수*로 요구한다. 창시자(Jina)가 명시: *"requires mean pooling ...
doesn't use CLS pooling."* bge-m3는 CLS 풀링 → Late Chunking 방법론적으로 불가
(강행 실측 시 RCPS 0.24/0.08 — 백본 mismatch 아티팩트). 표준/최적 모델
jina-embeddings-v3는 transformers 5.8 비호환(→ §4). multilingual-e5-large는
mean-pooling이나 512 컨텍스트로 whole-page Late Chunking 불가.

**(b) 논문 기여에 non-load-bearing** —
- C1 (진단, parsing≠retrieval): 6-parser grid 기반. Late Chunking 무관.
- C2 (RCPS 지표): 청킹 전략 비교(Fixed/MD/ParserNative/LumberChunker)가 이미
  "RCPS가 전략을 변별"함을 보임. Late Chunking은 한 행 추가일 뿐, 지표 유효성을
  떠받치지 않음.
- C3 (RADP-B): 무관 (RADP-B는 negative result로 종결).
- C4 (layer-positioning 도식): Late Chunking은 *embedding layer* 칸에 배치 —
  **citation으로 완전히 충족**, 실측 불필요.

**(c) 분류상 chunking 전략이 아님** — Late Chunking은 청크 경계가 아니라
*임베딩 방식*을 바꾸는 embedding-layer 기법. PRD 자체 노트(`docs/paper/
PAPER-2409.04701-late-chunking.md`)도 *"different layer ... orthogonal"*로
분류 — chunking 전략 비교 그리드에 속하지도 않는다.

→ **결정**: Related Work 인용 + layer-positioning 도식 배치. 미실측은 논문에
*"Late Chunking은 mean-pooling 장컨텍스트 모델을 요구하나, 표준 모델 jina-v3가
본 연구의 pinned 환경(transformers 5.8)과 비호환 — head-to-head는 future work"*
로 정직하게 명시.

## 4. jina-v3 retriever → Qwen3-Embedding-8B 교체

jina-embeddings-v3를 RCPS 3번째 retriever로 쓰려 했으나, 그 커스텀 remote
코드가 transformers 5.8과 비호환 — 일부 가중치가 랜덤 초기화되어 **간헐적 NaN
임베딩**을 냄 (비결정적: 같은 입력에 run마다 RCPS가 0.26↔0.0015). fp32 강행도
실패. → `Qwen/Qwen3-Embedding-8B`(2025, 표준 Qwen3 아키텍처, remote 코드 없음)로
교체. 검증: 두 번 로드 비트 단위 동일(결정적), NaN 없음. 상세는
memory `jina-v3-retriever-broken`.
