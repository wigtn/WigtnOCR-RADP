# Paper: ColPali — Efficient Document Retrieval with Vision Language Models

**arxiv**: https://arxiv.org/abs/2407.01449
**Authors**: Manuel Faysse, Hugues Sibille, Tony Wu, Bilel Omrani, Gautier Viaud, Céline Hudelot, Pierre Colombo (Illuin Technology)
**Date**: 2024-06 (v1)
**Venue**: **ICLR 2025**

## Core Idea (3줄 이내)
OCR/parsing을 skip하고 **document page image 자체를 VLM으로 직접 embed**하여 retrieval.
PaliGemma backbone + late interaction (ColBERT 스타일).
ViDoRe benchmark에서 OCR-based pipeline 대비 큰 폭 outperform.

## Key Techniques
- **VLM-based visual document encoder**: PaliGemma → patch-level embeddings
- **Late interaction matching**: ColBERT 스타일 MaxSim
- **ViDoRe benchmark**: page-level visual document retrieval
- End-to-end trainable

## Relevance to RADP

- **Overlap (MEDIUM)**:
  - VLM을 retrieval에 활용
  - 한국어/다국어 document retrieval에 영향력
- **Difference (FUNDAMENTAL)**:
  - **ColPali: parsing을 skip — image를 직접 retrieval에 사용**
  - **RADP: parsing은 유지 — generation을 위해 text/markdown이 필요한 RAG에 적용**
  - ColPali는 retrieval만, RADP는 retrieval + generation까지 full RAG pipeline
  - ColPali는 LLM이 retrieval된 image를 직접 처리 (multimodal generation), RADP는 text generation 기반 RAG
- **Citation worthiness**: **HIGH** — visual document retrieval의 SOTA, "alternative paradigm"으로 인용

## Threat to our novelty
**Low (RADP scope에서) / Moderate (RAG 일반 scope에서)**

- 위협 정도: ColPali는 우리 task (parsing for text-based RAG)와 다른 paradigm
- 그러나 reviewer가 "why not just use ColPali?" 질문할 가능성 → 답변 필요
- **방어**: 한국 정부문서처럼 **generation 단계에서 정확한 text가 필요한 경우** (e.g., 인용, 수치, 표 데이터), image-based retrieval은 generation에 직접 도움이 안 됨. Text parsing이 여전히 필요.

## Actionable Takeaways
1. **Related Work — "Alternative paradigms" 섹션**에서 인용, 차별화 명시
2. **Limitations / Discussion 섹션**: "We focus on text-based RAG (post-parsing); visual retrieval (ColPali) is complementary."
3. **Future work**: RADP의 contrastive signal을 visual retrieval과 결합하는 방향
4. 우리 baseline pipeline에 ColPali 비교를 포함할지 결정 — 비교 framework가 다르긴 함 (page retrieval vs chunk retrieval)
