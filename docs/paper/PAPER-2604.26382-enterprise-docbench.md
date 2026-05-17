# Paper: Benchmarking Complex Multimodal Document Processing Pipelines: A Unified Evaluation Framework for Enterprise AI

**arxiv**: https://arxiv.org/abs/2604.26382
**Authors**: Saurabh K. Singh et al.
**Date**: 2026 (very recent, ~3 weeks before our submission)
**Venue**: arxiv preprint

## Core Idea (3줄 이내)
EnterpriseDocBench를 통해 parsing → indexing → retrieval → generation 4단계 pipeline의 stage 간 correlation을 측정.
핵심 발견: **parsing quality가 retrieval variance의 2% 미만, generation variance의 3% 미만만 설명** (parsing→retrieval r=0.14).
즉, parsing 품질과 downstream retrieval 성능은 거의 무관함을 정량적으로 보임.

## Key Techniques
- **EnterpriseDocBench**: parsing fidelity, indexing efficiency, retrieval relevance, generation groundedness를 같은 corpus에서 동시 평가
- **Cross-stage correlation 분석**: stage 간 Pearson r 측정 (parsing↔retrieval, retrieval↔generation)
- Hybrid retrieval (BM25+dense), dense embedding, BM25 비교
- Hallucination이 document length와 monotonic하지 않다는 발견 (short/long > medium)

## Relevance to RADP
**THIS IS THE MOST CRITICAL THREAT.** 우리 C1 (diagnostic contribution)과 본질적으로 같은 결론.

- **Overlap (HIGH)**:
  - 우리: "BC/CS 1위 MinerU가 retrieval 5위" → 동일한 비상관성 주장
  - 그들: parsing→retrieval r=0.14 (KoGovDoc에서 우리가 측정한 것과 같은 framing)
  - 그들이 이미 "weak correlation between sequential stages"를 정량적으로 증명함
- **Difference**:
  - 그들: enterprise corpus, 영어, parsing→retrieval r=0.14 (관찰만)
  - 우리: 한국 정부문서, 6 parser × 3 retriever × KoGovDoc, **+ RADP 학습 방법론(B/A) + RCPS metric**
  - 그들은 진단만, 우리는 진단 + 처방 + metric
- **Citation worthiness**: **HIGH (필수 인용)** — 우리 motivation의 evidence base로 인용. "concurrent independent confirmation"으로 framing 가능.

## Threat to our novelty
**Critical (C1만 보면), Moderate (C1+C2+C3 종합)**

- 위협 정도: C1 (diagnostic) novelty가 **이미 publish됨**. "We discover weak correlation"이라는 framing은 이제 불가능.
- 이유: 2026년에 같은 결론이 영어 enterprise data로 정량화됨. 우리는 "Korean government document에서 재현하고 + method로 해결" 포지션이 필요.

## Actionable Takeaways
1. **C1 framing 변경 필수**: "We discover" → "We confirm and extend to multilingual Korean setting, and crucially, we *solve* this gap with RADP"
2. **Introduction에서 이 paper를 prominent하게 인용** (concurrent work, independent confirmation)
3. **r=0.14 같은 수치를 우리도 동일 framework로 측정하여 비교** (KoGovDoc-RAG에서 parsing↔retrieval Pearson r 보고)
4. **차별점 강조**: 그들 = benchmark only, 우리 = benchmark + training method + new metric (RCPS)
5. EnterpriseDocBench와 KoGovDoc-RAG를 cross-validate 시도 가능하면 더 강력
