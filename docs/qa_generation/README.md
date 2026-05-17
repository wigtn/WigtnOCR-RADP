# Q-A Pair Generation for KoGovDoc-RAG

> KoGovDoc-Bench validation 페이지에 retrieval evaluation용 Q-A pair를 생성하는 prototype.

## 디렉토리

```
docs/qa_generation/
├── README.md            # 이 파일
├── SCHEMA.md            # Q-A pair JSON schema 정의
├── PROMPT_v1.md         # GPT-4o prompt template (system + user)
├── samples/             # KoGovDoc-Bench 다양한 5개 샘플 페이지 (sanity check용)
└── sample_output.jsonl  # 실행 후 생성됨

scripts/qa_generation/
└── generate_qa.py       # 생성 스크립트
```

## 실행 방법

### 1. 환경 셋업 (이미 완료됨)

```bash
cd /Users/harrisonkim/Documents/WIGTN/EMNLP
# pyproject.toml 이미 생성됨, openai 설치됨
uv sync
```

### 2. API key 설정

```bash
export OPENAI_API_KEY=sk-...
# 영구 저장하려면 ~/.zshrc에 추가
```

### 3. Prototype 실행 (5 페이지)

```bash
uv run python scripts/qa_generation/generate_qa.py \
    --input data/KoGovDoc-Bench/val.jsonl \
    --output docs/qa_generation/sample_output.jsonl \
    --num-pages 5 \
    --model gpt-4o-2024-08-06
```

### 4. 특정 다양 샘플로 sanity check

```bash
# kogov(0), arxiv(9), mixed-quality(8), longest(259), shortest(62)
uv run python scripts/qa_generation/generate_qa.py \
    --page-indices 0,8,9,62,259 \
    --output docs/qa_generation/sample_output_diverse.jsonl
```

## 기대 출력

각 행:

```json
{
  "qa_id": "uuid",
  "page_id": "val_0000",
  "doc_id": "kogov_008",
  "language": "ko",
  "domain": "kogov",
  "question": "단가산출서에서 흘관 Φ1200의 종배 수관부설 합계는 얼마인가?",
  "answer_span": "196,645",
  "answer_chunk": "| 290 | 종배 수관부설 (흘관 Φ1200) | 소켓관 부설및점할 | M | 196,645 | 150,297 | 15,131 | 31,217 | |",
  "question_type": "tabular",
  "difficulty": "easy",
  "multi_page": false,
  "referenced_pages": ["val_0000"],
  "metadata": {
    "generator_model": "gpt-4o-2024-08-06",
    "generation_timestamp": "2026-05-17T...",
    "human_verified": false,
    "rationale": "Direct tabular lookup, good for testing retrieval of price table rows"
  }
}
```

## 비용

- 5 페이지 prototype: ~$0.06
- 294 페이지 전체 (validation): ~$3.5
- 2,667 학습 페이지 추가: ~$32
- **총 예상: ~$35**

## Next Steps

1. ✅ Schema 정의 (SCHEMA.md)
2. ✅ Prompt 설계 (PROMPT_v1.md)
3. ✅ 생성 스크립트 (scripts/qa_generation/generate_qa.py)
4. ⏳ Prototype 실행 (API key 입력 대기 중)
5. ⏳ 출력 품질 검토 → prompt v2 iteration
6. ⏳ Full validation set 생성 (294 페이지)
7. ⏳ Human verification (100개 sample)
8. ⏳ Train set Q-A 생성 (~2,667 페이지)

## Quality Iteration

Prototype 실행 후 다음을 검증:
- 각 질문이 자연스러운가? (leading phrase 없음, 한국어 자연스러움)
- `answer_span` 검증 통과율 (목표: ≥80%)
- 질문 유형 분포가 목표(50/30/15/5)와 가까운가
- 페이지 quality filter가 idx=8 같은 reasoning-leaked 페이지를 잘 skip하는가
- 동일 페이지 내 Q-A의 다양성

문제 있으면 PROMPT_v1.md → PROMPT_v2.md로 iterate.
