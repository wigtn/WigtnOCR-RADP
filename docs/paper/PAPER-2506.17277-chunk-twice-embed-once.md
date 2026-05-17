# Paper: Chunk Twice, Embed Once — A Systematic Study of Segmentation and Representation Trade-offs in Chemistry-Aware RAG

**arxiv**: https://arxiv.org/abs/2506.17277
**Authors**: chemistry-RAG team
**Date**: 2025-06
**Venue**: arxiv preprint

## Core Idea (3줄 이내)
화학 도메인 RAG에서 25 chunking configurations × 48 embedding models를 systematic 평가.
**Key claim: chunking configuration이 retrieval에 미치는 영향이 embedding model 선택과 같거나 더 큼.**
Contrastive retrieval objective로 학습된 embedding이 domain pretraining만보다 강력.

## Key Techniques
- 25 chunking configs across 5 method families (recursive, semantic, structural 등)
- 48 embedding models 평가
- 새 benchmark: FSUChemRxivQuest
- Mean IoU, Precision/Recall 기준 평가

## Relevance to RADP

- **Overlap (MEDIUM)**:
  - "Chunking이 retrieval 성능의 주요 요인" 주장이 우리 motivation 일부와 일치
  - Contrastive retrieval tuning > domain pretraining alone → RADP-B의 contrastive 접근 지지
- **Difference**:
  - 그들: chemistry 도메인, **기존 chunking 방법들 평가만**
  - 우리: 학습 가능한 새로운 chunking-via-parsing 방법
- **Citation worthiness**: **MEDIUM** — "chunking이 중요하다" evidence로 인용

## Threat to our novelty
**Low**

- benchmark/evaluation paper, method proposal 없음
- 우리 RADP-B/A와 직접 competing 안 함

## Actionable Takeaways
1. Motivation 섹션에서 "chunking matters more than embedding choice" 주장의 supporting citation
2. 그들이 사용한 chunking method families를 우리 baseline에 reuse (recursive, semantic 등)
3. "Contrastive retrieval tuning beats domain pretraining" 주장은 우리 RADP-B 논리 보강
