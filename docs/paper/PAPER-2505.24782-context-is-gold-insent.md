# Paper: Context is Gold to find the Gold Passage — Evaluating and Training Contextual Document Embeddings (InSeNT)

**arxiv**: https://arxiv.org/abs/2505.24782
**Authors**: Illuin Technology team
**Date**: 2025-05-30
**Venue**: arxiv preprint (likely EMNLP/NeurIPS submission)

## Core Idea (3줄 이내)
ConTEB benchmark + **InSeNT (In-sequence Negative Training)** 제안: late chunking pooling과 결합된 contrastive post-training.
같은 document 내 다른 chunk를 hard negative로 사용하여 chunk embedding이 document context를 더 잘 반영하도록 학습.
Chunking strategy 변화나 corpus 확장에도 robust.

## Key Techniques
- **InSeNT**: in-sequence negatives = 같은 document의 다른 chunks를 contrastive negative로
- **Late chunking pooling**: full document encoding 후 chunk-wise mean pool (Jina 방식)
- **Contrastive post-training**: pre-trained embedding model을 chunk-level contrastive로 추가 학습
- **ConTEB**: context-aware retrieval evaluation benchmark
- Open-source: https://github.com/illuin-tech/contextual-embeddings

## Relevance to RADP
**🚨 가장 위협적인 paper.** RADP-B의 contrastive loss formulation과 핵심 아이디어가 매우 가깝다.

- **Overlap (CRITICAL)**:
  - **In-sequence/in-batch hard negatives** = 우리 RADP-B의 "같은 페이지 내 다른 chunk" hard negative와 정확히 동일 아이디어
  - Chunk-level contrastive learning으로 retrieval 성능 개선
  - Late chunking과의 결합도 우리가 고려할 가능한 변형
- **Difference (CRUCIAL — defense line)**:
  - **그들**: pre-trained **embedding model** (E5, BGE 등)을 post-train. **Parser는 건드리지 않음**.
  - **우리**: **VLM parsing model** (Qwen3-VL-2B)을 post-train. **Embedding model은 frozen**.
  - 학습 대상이 다르다: 그들 = encoder/retriever, 우리 = parser/generator
  - 결과 인공물: 그들 = better embeddings (어떤 chunks든 잘 retrieve), 우리 = better chunks (어떤 embedding이든 잘 retrieve된다)
  - 이 차이가 **상호 보완적**임을 보일 수 있다 (InSeNT + RADP-B 결합 실험 가능)
- **Citation worthiness**: **HIGH (필수, 가장 가까운 prior work로 인용)**

## Threat to our novelty
**Critical**

- 위협 정도: contrastive learning + chunk + retrieval이라는 핵심 ingredient set이 겹침
- 이유: reviewer가 "why not just use InSeNT?" 또는 "this is just InSeNT applied to parser"라고 생각할 위험
- **방어 논리**:
  1. **학습 객체 다름**: parser ≠ retriever. Parser를 학습시키면 chunks 자체가 달라짐 (boundary가 옮겨감). InSeNT는 chunk boundary를 못 바꿈.
  2. **VLM 입력**: visual document image → contrastive signal이 visual layout과 정렬됨. InSeNT는 text-only.
  3. **새 application domain**: document parsing model fine-tuning이라는 task에 처음 contrastive RAG signal 적용

## Actionable Takeaways
1. **RADP positioning 재정의 (CRITICAL)**: "first to apply chunk-level contrastive retrieval signal to **document parser fine-tuning** (vs prior work that targeted embedding models)"
2. **Method 차별화 figure**: 4-layer stack (image → parser → chunks → embeddings → retrieval) 그리고 InSeNT가 어느 layer, RADP가 어느 layer를 학습하는지 명확히 표시
3. **실험적 차별화**:
   - InSeNT를 baseline으로 포함 → "InSeNT (post-train BGE-M3 with in-sequence negatives) + WigtnOCR-v1 parser"
   - vs "BGE-M3 frozen + RADP-B parser"
   - 가능하면 둘 다 결합한 ablation도 — 두 layer 모두 학습하면 추가 gain이 있는지
4. **Combined experiment**: RADP-B + InSeNT가 orthogonal한지 검증. Orthogonal이면 강력한 차별화.
5. Code repo (illuin-tech/contextual-embeddings) 활용하여 reproducible comparison
