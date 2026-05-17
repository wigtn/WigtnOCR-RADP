# Paper: When Good OCR Is Not Enough: Benchmarking OCR Robustness for Retrieval-Augmented Generation

**arxiv**: https://arxiv.org/abs/2605.00911
**Authors**: (TBD — 2026 paper, mixedbread.ai 관련 추정 — "The Hidden Ceiling" 블로그와 동시)
**Date**: 2026-04-29 (very recent)
**Venue**: arxiv preprint, OpenReview submission

## Core Idea (3줄 이내)
11 challenging document types (extreme layouts, watermarks, historical, tables, formulas)에서 SOTA OCR 모델들을 OCR-first RAG pipeline에서 평가.
**핵심 주장: WER/CER이 낮아도 structural/semantic error가 retrieval 실패를 유발한다.**
Character-level metric (WER/CER)이 downstream RAG 효과를 측정 못함 → downstream-aware OCR assessment 필요.

## Key Techniques
- **Industrial RAG benchmark**: 11 document categories (extreme layouts, high-res, watermarked, historical, tables, math 등)
- **OCR-first pipeline**: 통일된 retrieval + generation backend에서 OCR만 swap
- **Failure mode 분석**: retrieval-side vs generation-side failure 분해
- **Category-dependent mismatch**: 어떤 도메인에서 OCR-RAG gap이 큰지 카테고리별 분석

## Relevance to RADP
**Critical concurrent work.** 우리 H1 가설(parsing metric ↔ retrieval metric weak correlation)을 직접 검증하는 paper.

- **Overlap (HIGH)**:
  - 핵심 주장 "OCR quality ≠ RAG performance"가 우리 motivation과 동일
  - WER/CER → BC/CS/TEDS와 same family of human-readable metrics
  - downstream-aware assessment 주장 → 우리 RCPS와 motivation 일치
- **Difference**:
  - 그들: 11 document types, 영어 enterprise focus, benchmark/analysis only
  - 우리: 한국 정부문서, **method (RADP-B/A) + metric (RCPS) + benchmark all in one**
  - 그들 OCR-first pipeline, 우리 VLM-native parsing (Qwen3-VL-2B fine-tune)
- **Citation worthiness**: **HIGH (필수)** — concurrent confirmation

## Threat to our novelty
**Critical (C1 단독), Moderate (전체)**

- 위협 정도: C1 (diagnostic + new metric motivation)이 동시에 publish됨.
- 이유: "downstream-aware OCR assessment"라는 framing이 이미 점유됨. 우리는 RCPS가 이것의 concrete metric으로 차별화해야 함.
- **그러나** 그들은 metric을 새로 제안하지 않음 → 우리 RCPS는 여전히 novel.
- 그들은 학습 방법 제안 안 함 → 우리 RADP-B/A는 여전히 novel.

## Actionable Takeaways
1. **RCPS positioning 강화**: 이 paper의 "downstream-aware assessment" call에 대한 **concrete answer**로 framing
2. **Related Work에서 명시적으로 인용**: "Concurrent to our work, [X] confirms this in English industrial documents; we extend to Korean and provide a *training-time solution*."
3. **Method section에서 차별화**: 그들=benchmark only, 우리=benchmark + RADP method + RCPS metric (triple contribution)
4. **그들 11 categories 중 우리와 유사한 것 (manual, table, formula) 일부 cross-validation** 가능 시 강력
5. WER/CER vs RAG performance scatter plot을 우리 BC/CS vs Hit@1로 재현
