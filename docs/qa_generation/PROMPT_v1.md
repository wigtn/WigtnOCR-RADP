# Q-A Generation Prompt v1 (GPT-4o)

> 작성일: 2026-05-17
> Target: GPT-4o-2024-08-06 (structured outputs)
> 입력: KoGovDoc-Bench validation page의 ground truth markdown
> 출력: JSON array of Q-A pairs (SCHEMA.md 따름)

## System Prompt

```text
You are a precise question-answer pair generator for evaluating RAG (Retrieval-Augmented Generation) systems on Korean government documents and academic papers.

Your task is to generate retrieval-evaluation Q-A pairs from a given document page's markdown content. Each Q-A pair must satisfy:

# CRITICAL CONSTRAINTS
1. The answer MUST be a contiguous substring of the document (exact text match).
2. The question MUST be answerable ONLY from the document — no external knowledge.
3. Avoid leading phrases like "according to the document", "in this text", "본 문서에 따르면" — questions must read naturally.
4. Match the document's language: Korean document → Korean question, English document → English question.
5. Do NOT generate yes/no questions or questions asking for opinions.
6. Avoid trivial questions (e.g., "What is the title?") — focus on substantive content.

# QUESTION TYPES (target distribution within 2~3 Q-A per page)
- factoid: a specific fact ("X의 시행일은 언제인가?", "What is the publication year of the paper?")
- procedural: a procedure or condition ("Y를 신청하려면 어떤 서류가 필요한가?")
- tabular: a value in a table ("표 3에서 Φ1200 흘관의 합계는?", "What is the value in row 5 column 3?")
- figural: a chart/figure interpretation (only if figures present; usually skip if not)

# DIFFICULTY DISTRIBUTION
- easy: direct lookup from one sentence/cell
- medium: requires combining 2-3 facts within page
- hard: requires cross-referencing multiple sections or implicit reasoning (limit to 20%)

# PAGE QUALITY FILTER (PRE-CHECK)
Before generating, check if the page is suitable. SKIP generation (return empty array) if:
- The markdown contains visible LLM reasoning artifacts (e.g., "Then, the next rows are...", "Let me think...", "Under section X..." that describes structure rather than content)
- The page is purely a reference list / bibliography (only citations, no substantive content)
- The page has less than 100 characters of meaningful content
- The page contains repetitive boilerplate only (e.g., footers, page numbers)

# OUTPUT FORMAT
Return ONLY a valid JSON array. Each element follows this schema:
{
  "question": "string",
  "answer_span": "string (EXACT substring of document)",
  "answer_chunk": "string (200-500 char surrounding context that contains answer_span)",
  "question_type": "factoid | procedural | tabular | figural",
  "difficulty": "easy | medium | hard",
  "rationale": "string (1 sentence: why this Q-A is good for retrieval evaluation)"
}

If the page should be skipped, return: {"skip": true, "reason": "string"}
```

## User Prompt Template

```text
# Document Page

**Metadata**:
- Page ID: {page_id}
- Domain: {domain}  # "kogov" or "arxiv"
- Language: {language}  # "ko" / "en" / "mixed"

**Markdown content**:
---
{ground_truth_markdown}
---

# Task

Generate 2~3 high-quality Q-A pairs for retrieval evaluation, following the constraints above.

If the page is unsuitable (per PAGE QUALITY FILTER), return `{"skip": true, "reason": "..."}`.

Otherwise, return a JSON array of 2~3 Q-A objects.
```

## Structured Output Schema (for OpenAI Responses API)

```json
{
  "type": "json_schema",
  "json_schema": {
    "name": "qa_pairs",
    "strict": true,
    "schema": {
      "type": "object",
      "properties": {
        "skip": {
          "type": "boolean"
        },
        "reason": {
          "type": "string"
        },
        "qa_pairs": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "question": {"type": "string"},
              "answer_span": {"type": "string"},
              "answer_chunk": {"type": "string"},
              "question_type": {
                "type": "string",
                "enum": ["factoid", "procedural", "tabular", "figural"]
              },
              "difficulty": {
                "type": "string",
                "enum": ["easy", "medium", "hard"]
              },
              "rationale": {"type": "string"}
            },
            "required": ["question", "answer_span", "answer_chunk", "question_type", "difficulty", "rationale"],
            "additionalProperties": false
          }
        }
      },
      "required": ["skip", "reason", "qa_pairs"],
      "additionalProperties": false
    }
  }
}
```

## Validation Pipeline (post-generation)

생성 직후 즉시 자동 검증:

```python
def validate_qa(qa, gt_markdown):
    # 1. answer_span 이 document에 존재
    if qa['answer_span'] not in gt_markdown:
        return False, "answer_span not in document"

    # 2. answer_chunk 이 document에 존재
    if qa['answer_chunk'] not in gt_markdown:
        return False, "answer_chunk not in document"

    # 3. answer_span 이 answer_chunk에 포함
    if qa['answer_span'] not in qa['answer_chunk']:
        return False, "answer_span not in answer_chunk"

    # 4. 길이 제약
    if not (5 <= len(qa['question']) <= 200):
        return False, "question length out of range"
    if not (1 <= len(qa['answer_span']) <= 100):
        return False, "answer_span length out of range"
    if not (50 <= len(qa['answer_chunk']) <= 1000):
        return False, "answer_chunk length out of range"

    return True, "ok"
```

실패 → 폐기, 동일 페이지 1회 재시도. 2회 실패하면 페이지 자체를 skip.

## 비용 추정

- GPT-4o input ~ $2.50 / 1M tokens, output ~ $10 / 1M tokens
- 평균 페이지: input 2000 token (markdown) + system 500 token = 2500 token
- 출력 (2~3 Q-A): ~600 token
- 페이지당 비용: (2500 × 2.5 + 600 × 10) / 1M = $0.0123 ≈ **$0.012**
- 294 페이지 × $0.012 = **~$3.6** for full validation set
- 학습용 추가 생성 (2,667 train pages × 1 Q-A each = 2,667 Q-A): ~$32
- **총 예상: ~$35**

## 모델 선호 옵션

기본은 `gpt-4o-2024-08-06` (structured output 지원, 안정적).
실험: 
- `gpt-4o-mini-2024-07-18`로 cost 1/10로 줄여서 비교 가능
- Quality 차이 small sample (50 페이지)으로 사전 측정 후 결정
