# Paper: M3-Embedding (BGE-M3) — Multi-Linguality, Multi-Functionality, Multi-Granularity Text Embeddings

**arxiv**: https://arxiv.org/abs/2402.03216
**Authors**: Jianlv Chen, Shitao Xiao, Peitian Zhang, Kun Luo, Defu Lian, Zheng Liu (BAAI)
**Date**: 2024-02
**Venue**: arxiv (widely cited, SOTA multilingual embedding)

## Core Idea (3줄 이내)
**100+ languages, 3 retrieval functionalities (dense/sparse/multi-vector), short~8192 token 범위** 모두 지원하는 통합 임베딩.
Self-knowledge distillation으로 3 functionalities의 relevance score를 teacher signal로 통합.

## Key Techniques
- Multi-functional output (dense, sparse lexical, ColBERT-like multi-vector)
- Self-knowledge distillation
- Massive multilingual training

## Relevance to RADP

- **Overlap**: 없음. Tool/foundation 역할.
- **사용 위치**: RADP-B의 contrastive signal source (frozen embedding) + 우리 baseline retriever
- **Citation worthiness**: **HIGH** — 우리 system의 핵심 component

## Threat to our novelty
**None**

## Actionable Takeaways
1. Method section에서 "BGE-M3 as frozen embedding teacher in RADP-B contrastive loss" 명시
2. Baseline retriever 비교에 포함 (multilingual-e5-large, jina-v3와 함께)
3. 한국어 지원이 검증된 점이 KoGovDoc 적용에 중요
