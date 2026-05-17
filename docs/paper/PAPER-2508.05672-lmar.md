# Paper: LMAR — Language Model Augmented Retriever for Domain-specific Knowledge Indexing

**arxiv**: https://arxiv.org/abs/2508.05672
**Authors**: Yao Zhao, Yantian Ding, Zhiyue Zhang, Dapeng Yao, Yan Xu
**Date**: 2025-08
**Venue**: arxiv preprint

## Core Idea (3줄 이내)
Domain-specific RAG에서 embedding adaptation과 semantic chunking의 상호의존성을 풀기 위한 2-stage pipeline.
LLM이 (1) triplet sampling + synthetic data augmentation, (2) contrastive learning + clustering의 supervisor 역할.
Model-agnostic — 어떤 embedding과도 결합 가능.

## Key Techniques
- **Stage 1**: LLM이 labeler + validator로 triplet 합성 (anchor/positive/negative)
- **Stage 2**: contrastive embedding adaptation + semantic chunking 결합
- Joint optimization of embedding refinement AND chunking

## Relevance to RADP

- **Overlap (MEDIUM-HIGH)**:
  - "Embedding과 chunking을 joint optimization" 아이디어
  - Contrastive learning 사용
- **Difference**:
  - LMAR: text input, **embedding model** + chunking 학습 (parser는 외부)
  - RADP: image input, **parsing model** 학습 (embedding은 frozen)
  - 학습 대상 layer 다름
- **Citation worthiness**: **HIGH** — "joint embedding + chunking" prior work로 차별화 필요

## Threat to our novelty
**Moderate**

- "joint optimization" 프레임을 이미 점유함
- 우리는 "joint **parsing + retrieval objective**"로 차별화

## Actionable Takeaways
1. **Related Work에서 명시 차별화**: "LMAR jointly adapts embeddings and chunking on text; RADP operates upstream, training the *parser* to produce retrieval-aligned chunks from raw document images."
2. LMAR도 baseline 가능 (텍스트 input 기준)
3. 가능하면 LMAR + RADP 결합 ablation (orthogonal stack)
