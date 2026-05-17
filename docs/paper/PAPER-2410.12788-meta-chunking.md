# Paper: Meta-Chunking — Learning Text Segmentation and Semantic Completion via Logical Perception

**arxiv**: https://arxiv.org/abs/2410.12788
**Authors**: (Chinese team)
**Date**: 2024-10 (v1), v3 2025-05
**Venue**: arxiv (widely cited)

## Core Idea (3줄 이내)
Meta-Chunking: 문장과 문단 사이 granularity, "deep linguistic logical connections" 단위.
2 techniques: **Perplexity Chunking** (PPL distribution 분석) + **Margin Sampling Chunking** (uncertainty 기반).
+ dynamic merging, global information compensation (hierarchical summary).

## Key Techniques
- **PPL Chunking**: context perplexity 분포로 boundary 결정 (training-free, LLM forward 사용)
- **Margin Sampling**: LLM에 binary "여기 자를까?" 질문하여 confidence margin으로 결정
- **Dynamic merging**: 너무 짧은 chunk 합치기
- **Hierarchical summary + 3-stage chunk rewriting**: context 보충

## Relevance to RADP

- **Overlap (MEDIUM)**:
  - Logical/semantic chunk boundary 결정 method
  - LLM-based chunking 계열
- **Difference**:
  - Meta-Chunking: text input, training-free, LLM inference로 PPL/uncertainty 측정
  - RADP: image input, training-based, VLM parameter update
  - Meta-Chunking은 retrieval objective와 직접 align 안 됨 (intrinsic semantic만)
- **Citation worthiness**: **HIGH** — chunking 분야 must-cite

## Threat to our novelty
**Low**

- training-free vs training-based, modality 차이
- 우리 RADP는 학습 기반이라 generalization과 cost 다른 trade-off

## Actionable Takeaways
1. **Related Work** 필수 인용 — "Semantic/LLM-based chunking" 카테고리
2. **Baseline**: KoGovDoc에 Meta-Chunking PPL Chunking 적용해서 RADP와 비교
3. 우리 method 차별화: "Training-based vs training-free trade-off" 논의 — RADP는 retrieval signal 직접 학습, Meta-Chunking은 intrinsic logical proxy
