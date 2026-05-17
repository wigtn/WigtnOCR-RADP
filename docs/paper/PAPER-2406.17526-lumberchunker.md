# Paper: LumberChunker — Long-Form Narrative Document Segmentation

**arxiv**: https://arxiv.org/abs/2406.17526
**Authors**: André V. Duarte, João Marques, Miguel Graça, Miguel Freire, Lei Li, Arlindo L. Oliveira
**Date**: 2024-06
**Venue**: **EMNLP 2024 Findings**

## Core Idea (3줄 이내)
LLM (Gemini)이 sequential passages를 입력받아 **content shift 지점**을 찾아 chunk boundary 결정.
Narrative document에서 사용. GutenQA dataset 공개.
EMNLP 2024에 publish됨.

## Key Techniques
- **LLM-as-chunker**: 문단 그룹을 LLM에 입력 → topic shift point를 직접 prediction
- Iterative segmentation
- **GutenQA benchmark**: long-form narrative Q-A

## Relevance to RADP

- **Overlap (LOW-MEDIUM)**:
  - LLM-based chunking 분야의 시초
  - retrieval-oriented chunking 시도
- **Difference**:
  - 그들: text input → text chunking, LLM inference-time
  - 우리: image input → VLM parsing + chunk boundary 학습
  - 그들 narrative novel, 우리 정부문서/표/그림 포함 multimodal
  - 그들 inference cost 높음 (LLM call), 우리 single VLM forward
- **Citation worthiness**: **HIGH** — chunking 분야 must-cite, EMNLP 직속 venue

## Threat to our novelty
**Low**

- 다른 modality (text-only narrative), 다른 method (inference vs training)
- 우리 baseline으로 비교 가능

## Actionable Takeaways
1. **Related Work — "LLM-based chunking" 섹션** 필수 인용
2. **Baseline 후보**: 우리 KoGovDoc에 LumberChunker 적용해서 RADP와 비교 (LumberChunker로 자른 chunks vs RADP가 자른 chunks의 retrieval 성능)
3. **EMNLP 직속 venue 인용으로 reviewer awareness 활용**
4. Inference cost 비교 (LumberChunker = LLM calls per document, RADP = single forward) → efficiency 차별화
