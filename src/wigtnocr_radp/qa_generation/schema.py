"""Q-A pair schema, prompt, validator, and chunk auto-expansion.

Schema: docs/qa_generation/SCHEMA.md
Prompt: docs/qa_generation/PROMPT_v2.md

Design rationale (v2):
    - GPT-4o returns question + answer_span + question_type + difficulty + rationale only.
    - answer_chunk is auto-computed in Python by locating answer_span in the source
      markdown and expanding to natural boundaries (newlines, ~300 char window).
    - This decouples Q-A generation from chunking strategy and removes a major
      source of validation failures observed in v1 (model returning 5-15 char chunks).
"""

from __future__ import annotations

from typing import Any


SYSTEM_PROMPT = """You are a precise question-answer pair generator for evaluating RAG (Retrieval-Augmented Generation) systems on Korean government documents and academic papers.

Your task is to generate retrieval-evaluation Q-A pairs from a given document page's markdown content. Each Q-A pair must satisfy:

# CRITICAL CONSTRAINTS
1. The answer (answer_span) MUST be a contiguous substring of the document — exact text match including whitespace and punctuation.
2. The question MUST be answerable ONLY from the document — no external knowledge.
3. Avoid leading phrases like "according to the document", "in this text", "본 문서에 따르면" — questions must read naturally.
4. Match the document's language: Korean document → Korean question, English document → English question.
5. Do NOT generate yes/no questions or questions asking for opinions.
6. Avoid trivial questions (e.g., "What is the title?") — focus on substantive content.
7. answer_span must be 1-100 characters. For table cells, copy the cell value EXACTLY as it appears (including commas, units, etc.).

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
Before generating, check if the page is suitable. SKIP generation (set skip=true, qa_pairs=[]) if:
- The markdown contains visible LLM reasoning artifacts (e.g., "Then, the next rows are...", "Let me think...", "Under section X..." that describes structure rather than content)
- The page is purely a reference list / bibliography (only citations, no substantive content)
- The page has less than 100 characters of meaningful content
- The page contains repetitive boilerplate only (e.g., footers, page numbers)

If suitable, set skip=false and return 2~3 Q-A objects in qa_pairs.

# IMPORTANT — DO NOT return answer_chunk
The surrounding context will be computed automatically by the pipeline. Your job is only to provide a precise question and an exact answer_span."""


USER_TEMPLATE = """# Document Page

**Metadata**:
- Page ID: {page_id}
- Domain: {domain}
- Language: {language}

**Markdown content**:
---
{ground_truth_markdown}
---

# Task

Generate 2~3 high-quality Q-A pairs for retrieval evaluation, following the constraints above.

If the page is unsuitable (per PAGE QUALITY FILTER), set skip=true with reason and empty qa_pairs."""


QA_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "json_schema",
    "json_schema": {
        "name": "qa_pairs_response",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "skip": {"type": "boolean"},
                "reason": {"type": "string"},
                "qa_pairs": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question": {"type": "string"},
                            "answer_span": {"type": "string"},
                            "question_type": {
                                "type": "string",
                                "enum": ["factoid", "procedural", "tabular", "figural"],
                            },
                            "difficulty": {
                                "type": "string",
                                "enum": ["easy", "medium", "hard"],
                            },
                            "rationale": {"type": "string"},
                        },
                        "required": [
                            "question",
                            "answer_span",
                            "question_type",
                            "difficulty",
                            "rationale",
                        ],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["skip", "reason", "qa_pairs"],
            "additionalProperties": False,
        },
    },
}


def expand_to_chunk(
    answer_span: str,
    gt_markdown: str,
    target_min: int = 200,
    target_max: int = 800,
) -> str | None:
    """Locate answer_span in gt_markdown and expand to a retrieval-friendly chunk.

    Algorithm:
        1. Find first occurrence of answer_span in gt_markdown.
        2. Expand symmetrically around it until natural boundaries (newline) are hit
           and total length lies within [target_min, target_max].

    Returns:
        The chunk string, or None if answer_span not found.
    """
    pos = gt_markdown.find(answer_span)
    if pos < 0:
        return None

    half = max(target_min // 2, len(answer_span))
    start = max(0, pos - half)
    end = min(len(gt_markdown), pos + len(answer_span) + half)

    # Snap to nearest newline (outward)
    while start > 0 and gt_markdown[start - 1] != "\n":
        start -= 1
    while end < len(gt_markdown) and gt_markdown[end] != "\n":
        end += 1

    chunk = gt_markdown[start:end].strip()

    # If chunk grew beyond max, recenter and clip
    if len(chunk) > target_max:
        center = pos + len(answer_span) // 2
        half_max = target_max // 2
        c_start = max(0, center - half_max)
        c_end = min(len(gt_markdown), center + half_max)
        chunk = gt_markdown[c_start:c_end].strip()

    return chunk if chunk else None


def validate_qa(qa: dict[str, Any], gt_markdown: str, rules: dict[str, Any]) -> tuple[bool, str]:
    """Validate a Q-A pair. answer_chunk is auto-computed (v2 design).

    Args:
        qa: dict with question + answer_span (chunk auto-added by caller).
        gt_markdown: source document markdown.
        rules: validation rules from config.

    Returns:
        (is_valid, message)
    """
    if rules.get("answer_span_must_be_substring", True):
        if qa["answer_span"] not in gt_markdown:
            return False, "answer_span not in document"

    q_min, q_max = rules.get("question_length_range", [5, 200])
    if not (q_min <= len(qa["question"]) <= q_max):
        return False, f"question length out of range ({len(qa['question'])})"

    s_min, s_max = rules.get("answer_span_length_range", [1, 100])
    if not (s_min <= len(qa["answer_span"]) <= s_max):
        return False, f"answer_span length out of range ({len(qa['answer_span'])})"

    # answer_chunk is added by generator after this validation passes;
    # we still sanity-check if caller already attached one.
    if "answer_chunk" in qa:
        if qa["answer_chunk"] is None or qa["answer_span"] not in qa["answer_chunk"]:
            return False, "answer_chunk auto-expansion failed"

    return True, "ok"
