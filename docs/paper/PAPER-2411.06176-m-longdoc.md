# Paper: M-LongDoc — A Benchmark For Multimodal Super-Long Document Understanding And A Retrieval-Aware Tuning Framework

**arxiv**: https://arxiv.org/abs/2411.06176
**Authors**: (Singapore-based team)
**Date**: 2024-11 (v1)
**Venue**: **EMNLP 2025 Main**

## Core Idea (3줄 이내)
M-LongDoc 벤치마크 (851 multimodal long docs) + **Retrieval-Aware Tuning** framework 제안.
SFT + RAG를 통합하여, 학습 시 distracting content (다른 modality/page에서 retrieved)를 같이 noisy context로 넣어줌 → retrieval-time robustness 학습.
Correctness +4.6% 향상.

## Key Techniques
- **Benchmark**: 851 long multimodal documents, open-ended Q-A (extractive 아님)
- **Retrieval-Aware Tuning**:
  - training context = target page + distracting irrelevant pages from same document
  - model이 retrieved context의 noise 무시하는 법 학습
- **자동 evaluation framework**: LMM-based open-ended answer evaluation

## Relevance to RADP
이름이 너무 비슷해서 (Retrieval-Aware Tuning ↔ Retrieval-Aware Document Parsing) 위협적이지만, **층위가 다르다**.

- **Overlap (MEDIUM)**:
  - "Retrieval-Aware" 용어 사용 (naming conflict)
  - Multimodal long document에 RAG 결합 학습이라는 큰 그림 유사
- **Difference (CRITICAL)**:
  - 그들: **generation 단계 (answer reading) tuning** — retrieved context의 noise robustness
  - 우리: **parsing 단계 (chunking & encoding) tuning** — chunk boundary가 retrieval에 유리하도록
  - 그들 input = retrieved multimodal pages, 우리 input = raw document image → output markdown
  - 그들의 "retrieval-aware"는 retrieval 결과를 받는 reader 입장, 우리는 retrieval에 잘 retrieved되도록 parsing 모델 자체를 학습
- **Citation worthiness**: **HIGH** — naming clash가 있으니 반드시 인용하여 차별화 명시

## Threat to our novelty
**Moderate**

- 위협 정도: novelty 자체는 안 위협하나, **naming overlap**으로 reviewer가 혼동 가능
- 이유: "Retrieval-Aware Document Parsing" = "Retrieval-Aware Tuning Framework"로 잘못 읽힐 수 있음. 명시적 차별화 필수.

## Actionable Takeaways
1. **Naming 재고려**: "Retrieval-Aware Document Parsing"이 정확하지만, 부제목으로 차별화 강조 필요
   - 예: "RADP: Retrieval-Aware Document Parsing via Chunk-Boundary Contrastive Learning"
   - "Parsing-Time" 같은 modifier로 generation-time tuning과 구분
2. **Related Work에서 explicit 차별화**: "Unlike M-LongDoc, which makes the *reader* retrieval-aware, RADP makes the *parser* retrieval-aware — operating earlier in the pipeline."
3. **포지셔닝 표 추가**: M-LongDoc (reader-side) vs RADP (parser-side) vs InSeNT (embedding-side) vs Late Chunking (encoder-side)
4. EMNLP 2025에 publish된 paper라 EMNLP reviewer pool이 잘 알 가능성 높음 — 차별화 더 신경써야
