# Paper: OCR Hinders RAG: Evaluating the Cascading Impact of OCR on Retrieval-Augmented Generation

**arxiv**: https://arxiv.org/abs/2412.02592
**Authors**: Junyuan Zhang, Qintong Zhang, Bin Wang, Linke Ouyang, Zichen Wen, Ying Li, Ka-Ho Chow, Conghui He, Wentao Zhang (OpenDataLab/Shanghai AI Lab)
**Date**: 2024-12-03 (v1), v2 in 2025
**Venue**: **ICCV 2025**

## Core Idea (3줄 이내)
OCR/parsing 결과의 noise (Semantic Noise + Formatting Noise)가 RAG pipeline의 retrieval/generation 단계에 어떻게 전파되는지 정량 분석.
OHRBench (8,561 PDF + 8,498 Q-A pairs, 7 domains) 구축하여 SOTA OCR도 ground truth 대비 ≥7.5% gap이 있음을 보임.
"None of the current OCR solutions' extracted structured data is competent for constructing high-quality knowledge bases for RAG."

## Key Techniques
- **OHRBench**: 7 domains (Textbook, Law, Finance, Newspaper, Manual, Academia + 1) 8,561 docs, 8,498 Q-A
- **Two noise types**: Semantic Noise (예측 오류), Formatting Noise (구조 비균일성)
- **Perturbation protocol**: ground truth structured data를 OCR 오류 분포에 맞춰 systematic perturbation
- **Cascading impact 평가**: parsing → retrieval → generation 각 단계 영향 측정

## Relevance to RADP
이 논문이 **우리 motivation의 가장 강력한 선행 evidence**다.

- **Overlap (HIGH)**:
  - "OCR/parsing quality와 RAG 성능의 disconnect"라는 동일한 관찰
  - Q-A pair 기반 retrieval evaluation 프로토콜이 우리와 유사
- **Difference**:
  - 그들: **diagnostic + perturbation analysis만**, 학습 방법 없음
  - 그들 benchmark: 영어 + 중국어, 7 enterprise domains, 우리: 한국 정부문서 특화
  - 그들 noise framing: 예측 오류 vs 포맷팅 — 우리 RADP는 **chunk boundary alignment**라는 다른 차원의 처방
  - 우리: parsing model을 **retrieval objective와 align되도록 학습**하는 방법 제안
- **Citation worthiness**: **HIGH (필수)** — Related Work에서 "evidence of the problem" 섹션의 primary citation, motivation 부분 핵심

## Threat to our novelty
**Moderate**

- 위협 정도: C1 (diagnostic)을 강화하지만 대체하지는 않음. 그들은 perturbation 기반 합성 noise 분석, 우리는 실제 parser들의 real-world 차이 비교.
- 이유: 그들은 "OCR noise가 문제다"까지, 우리는 "그래서 어떻게 학습으로 풀까"까지 간다. **Method contribution은 우리만의 것**.

## Actionable Takeaways
1. **Related Work 핵심 인용** — Section "Problem Identification" 또는 "RAG with Imperfect Parsing"
2. **OHRBench와 cross-domain 비교 실험 검토**: 우리 RADP가 OHRBench 일부 데이터셋(예: Manual, Law)에서도 통하는지 보면 강력한 증거
3. **Noise taxonomy 인용**: Semantic Noise vs Formatting Noise 개념을 우리도 사용. 우리 chunk boundary 문제는 "Formatting Noise + Chunking Misalignment"라는 새 카테고리로 framing 가능
4. 우리 KoGovDoc-RAG 구축 시 그들 Q-A 생성 프로토콜 참조 (factoid + 절차적 + 표/그림 비율)
