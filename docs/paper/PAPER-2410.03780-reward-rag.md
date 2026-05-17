# Paper: Reward-RAG — Enhancing RAG with Reward Driven Supervision

**arxiv**: https://arxiv.org/abs/2410.03780
**Authors**: (RAG team)
**Date**: 2024-10
**Venue**: arxiv preprint

## Core Idea (3줄 이내)
RLHF에서 영감 받은 mechanism으로 **retrieval model을 fine-tune**.
Reward model로 query-document relevance 평가 → retrieval model을 reward model로 학습.

## Key Techniques
- Reward model: query-document relevance score
- Retrieval model fine-tuning with reward signal
- RLHF-like loop

## Relevance to RADP

- **Overlap (MEDIUM)**:
  - Retrieval reward 학습 컨셉
- **Difference**:
  - Reward-RAG: retrieval model (encoder) 학습
  - RADP-A: parser VLM 학습
  - 학습 대상 다름
- **Citation worthiness**: **MEDIUM-HIGH** — retrieval reward 학습 분야 representative

## Threat to our novelty
**Low-Moderate**

- 다른 layer 학습이라 직접 conflict 아님
- 다만 "retrieval reward로 어떤 모델을 학습한다"는 framework이 우리와 겹침

## Actionable Takeaways
1. RADP-A의 정신적 ancestor로 인용
2. "Reward-RAG trains the retriever; RADP-A trains the parser — both upstream of the generator."
3. 우리 reward function (Hit@1)이 단순한데 비해 RAG-Reward bench (2412.13746) 같은 정교한 reward model은 future work로
