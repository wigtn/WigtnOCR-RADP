# Paper: ChunkRAG — A Novel LLM-Chunk Filtering Method for RAG Systems

**arxiv**: https://arxiv.org/abs/2410.19572
**Authors**: Singh, Aggarwal et al.
**Date**: 2024-10
**Venue**: arxiv preprint (highly cited)

## Core Idea (3줄 이내)
Retrieval **후** chunk-level relevance scoring + self-reflection + critic LLM으로 irrelevant chunks 필터링.
PopQA에서 baseline 대비 +10pp 정확도 (64.9%).
Document-level filtering의 한계 극복.

## Key Techniques
- Semantic chunking으로 분할
- 각 chunk에 대해 LLM relevance score (0~1)
- **Self-reflective scoring**: 초기 score → reflection → 조정
- **Critic LLM**: secondary LLM이 독립 평가, 평균

## Relevance to RADP

- **Overlap (LOW)**:
  - Chunk-level RAG 개선이라는 큰 그림
- **Difference**:
  - ChunkRAG: retrieval **후처리** filtering — chunks는 이미 결정됨
  - RADP: parsing **시점에** chunks를 retrieval에 align되도록 학습
  - 다른 stage, orthogonal
- **Citation worthiness**: **MEDIUM** — chunk-level RAG improvement 분야 representative

## Threat to our novelty
**Low**

- 다른 stage (post-retrieval filtering vs pre-retrieval parsing)
- 결합 가능 (RADP chunks + ChunkRAG filtering)

## Actionable Takeaways
1. **Related Work — "Post-retrieval chunk processing"** 카테고리로 인용
2. 차별화: "ChunkRAG operates after retrieval; RADP shapes what chunks exist in the first place."
3. Possible ablation: ChunkRAG filter를 RADP chunks 위에 적용 → 보완성 검증
