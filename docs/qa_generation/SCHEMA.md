# Q-A Pair Schema for KoGovDoc-RAG

> 작성일: 2026-05-17
> 용도: RADP retrieval evaluation을 위한 Q-A pair 데이터 표준

## JSON Schema

```json
{
  "qa_id": "string (uuid4)",
  "page_id": "string (KoGovDoc-Bench validation idx, e.g., 'val_0042')",
  "doc_id": "string (원문 문서 식별자, e.g., 'kogov_envir_2023_07')",
  "language": "ko | en",
  "domain": "kogov | arxiv",

  "question": "string (한 문장 의문문)",
  "answer_span": "string (문서에서 정확한 substring)",
  "answer_chunk": "string (answer_span을 포함하는 충분한 맥락, 200~500자)",

  "question_type": "factoid | procedural | tabular | figural",
  "difficulty": "easy | medium | hard",

  "multi_page": false,
  "referenced_pages": ["string"],

  "metadata": {
    "generator_model": "gpt-4o-2024-08-06",
    "generation_timestamp": "ISO-8601",
    "human_verified": false,
    "verification_notes": "string | null"
  }
}
```

## 필드 정의

### `qa_id`
- UUID v4. 전역 유니크.

### `page_id`
- KoGovDoc-Bench validation split의 인덱스. 형식: `val_{idx:04d}`
- 다중 페이지 질문이면 첫 번째 페이지 ID를 primary로

### `doc_id`
- 원문 문서를 그룹핑하기 위한 식별자
- KoGov 문서면 `kogov_{topic}_{year}_{seq}`
- arXiv면 `arxiv_{paper_id}`

### `question`
- 한 문장 의문문
- "according to the document" 같은 leading phrase 금지
- 한국어 페이지면 한국어, 영어 페이지면 영어
- yes/no question 지양 (factoid이지만 span retrieval 어려움)

### `answer_span`
- 문서의 **정확한 substring** (대소문자, 공백 보존)
- 검증: `answer_span in document_text` 가 `True`
- 길이: 1~100자 (보통은 10~30자)

### `answer_chunk`
- `answer_span`을 포함하는 충분한 맥락
- 검색 시 hit 판정에 사용 (chunk 단위 매칭)
- 200~500자 권장

### `question_type` (분포 목표: 50/30/15/5)
- **factoid**: 사실 질문 ("X의 시행일은 언제인가?") — 50%
- **procedural**: 절차/조건 질문 ("Y를 신청하려면 어떤 서류가 필요한가?") — 30%
- **tabular**: 표 셀 참조 ("표 3의 2024년 예산 항목 중 가장 큰 것은?") — 15%
- **figural**: 그림/차트 참조 ("그래프에서 가장 높은 막대의 값은?") — 5%

### `difficulty` (분포 목표: 40/40/20)
- **easy**: 한 문장/한 셀에서 바로 추출 — 40%
- **medium**: 여러 문장 조합 또는 표 cross-reference — 40%
- **hard**: 다중 페이지 또는 implicit reasoning — 20%

### `multi_page`
- `true`이면 `referenced_pages`에 모든 관련 페이지 ID 나열
- 전체 비율 목표: 30%

### `metadata.human_verified`
- 자동 생성 직후 `false`
- 100개 샘플 human-in-the-loop 검증 후 `true`로 갱신

## Validation Rules

생성 후 즉시 검증할 것:

1. ✅ `answer_span` 이 `answer_chunk` 의 substring인가?
2. ✅ `answer_chunk` 이 ground truth markdown 안에 존재하는가?
3. ✅ `question` 길이 5~200자
4. ✅ `answer_span` 길이 1~100자
5. ✅ 같은 페이지에서 중복 Q-A 없음 (cosine similarity < 0.85)
6. ✅ Language detection: 페이지 언어와 question 언어 일치
7. ✅ 단일 페이지인데 `multi_page=true`인 경우 없음

검증 실패 → 즉시 폐기, 재생성.
