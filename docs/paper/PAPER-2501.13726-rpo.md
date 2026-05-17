# Paper: RPO — Retrieval Preference Optimization for Robust Retrieval-Augmented Generation

**arxiv**: https://arxiv.org/abs/2501.13726
**Authors**: (RAG team)
**Date**: 2025-01
**Venue**: arxiv preprint

## Core Idea (3줄 이내)
DPO를 RAG에 맞게 변형: **retrieval relevance representation을 reward에 통합**하여 retrieval quality에 따라 LLM을 adaptive하게 학습.
DPO의 RL objective와 RAG 요구사항 사이의 discrepancy 해결.

## Key Techniques
- DPO variant with retrieval relevance signal
- Adaptive reward based on retrieval quality
- Policy optimization for RAG-specific scenarios

## Relevance to RADP

- **Overlap (MEDIUM)**:
  - **RADP-A (Method A)** = retrieval reward DPO와 직접 비교 대상
- **Difference (CRUCIAL)**:
  - RPO: **generator LLM** (answer reading)을 DPO로 학습
  - RADP-A: **parser VLM**을 retrieval reward DPO로 학습
  - 학습 layer 다름 (reader vs parser)
- **Citation worthiness**: **HIGH** — RADP-A의 가장 직접적 prior

## Threat to our novelty
**Moderate-High (RADP-A only)**

- 위협 정도: RADP-A의 DPO + retrieval reward formula가 RPO의 변형으로 보일 가능성
- 이유: 둘 다 DPO + retrieval signal 결합
- **방어**:
  - RPO는 generation LLM 학습, RADP-A는 parsing VLM 학습 (모달리티/layer 다름)
  - Reward function이 다름: RPO = retrieval relevance score, RADP-A = Hit@1 of downstream retrieval

## Actionable Takeaways
1. **RADP-A 정당화**: "Inspired by RPO for generation, we apply preference optimization to the parsing stage for the first time."
2. Method 차별화 표: RPO (reader DPO) vs RADP-A (parser DPO)
3. **RADP-A를 EMNLP 2026에 포함할지 재고**: timeline 빠듯하면 ACL 2027로 미루는 옵션 (proposal Section 11.4)이 합리적. EMNLP에는 RADP-B만 + RADP-A는 future work로 mention.
4. RPO와 결합 가능성: RADP-A로 학습된 parser + RPO로 학습된 generator → full retrieval-aware stack
