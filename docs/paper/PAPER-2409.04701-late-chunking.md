# Paper: Late Chunking — Contextual Chunk Embeddings Using Long-Context Embedding Models

**arxiv**: https://arxiv.org/abs/2409.04701
**Authors**: Michael Günther et al. (Jina AI)
**Date**: 2024-09 (v1), v3 2025-07
**Venue**: arxiv (Jina AI technical paper, widely adopted)

## Core Idea (3줄 이내)
Naive chunking은 chunk를 먼저 자르고 각각 embed → context loss.
**Late chunking**: long-context embedding model로 전체 document를 먼저 토큰 임베딩한 후 마지막에 chunk-wise mean pool.
Training 불필요, 어떤 long-context embedding model에도 적용 가능.

## Key Techniques
- **Late pooling**: full document 통과 후 chunk boundary에 따라 token vector mean pool
- **Long-context embedding** (Jina v2 8192 token)
- No training required — 단순 inference-time technique
- Chunk embedding이 "previous chunks에 conditioned"

## Relevance to RADP

- **Overlap (LOW-MEDIUM)**:
  - Chunk embedding 품질 개선이 목표 — 같은 RAG 영역
  - Chunk boundary는 여전히 외부 chunker가 결정 (orthogonal)
- **Difference**:
  - Late Chunking: embedding 시점에 context 보존 (inference technique)
  - RADP: parsing 시점에 chunk boundary 자체를 retrieval에 align (training method)
  - 두 layer 다름 → orthogonal
- **Citation worthiness**: **HIGH** — RAG chunking 분야 must-cite. 핵심 baseline.

## Threat to our novelty
**Low**

- 다른 layer를 다룸 (embedding pooling vs parsing fine-tune)
- 결합 가능성: RADP-B 출력 chunks를 Late Chunking으로 embedding하면 추가 gain 가능

## Actionable Takeaways
1. **필수 baseline**: 우리 experiment에서 BGE-M3 + Late Chunking을 baseline pipeline에 포함
2. **Orthogonality 분석**: RADP + Late Chunking 결합 vs 각각 단독 — 두 기법이 stack 가능한지 보여주면 강력
3. Related Work "Chunking strategies" 섹션에서 인용
4. InSeNT paper와 같이 묶어서 "post-hoc retrieval-aware techniques" 카테고리로 정리
