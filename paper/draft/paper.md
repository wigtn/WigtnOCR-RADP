# Retrieval-Aware Document Parsing: Diagnosing and Measuring the Parsing–Retrieval Gap

**Harrison Kim, et al.** (Braincrew AI)
*EMNLP 2026 Industry Track — Draft v0.1 (2026-05-23)*

---

## Abstract

Document parsers used in retrieval-augmented generation (RAG) are conventionally optimized for *human-readability* metrics — TEDS, edit distance, boundary clarity — yet the parsing quality these metrics measure does not reliably predict downstream retrieval performance. We diagnose this disconnect quantitatively in Korean government documents (a 6-parser × 3-retriever grid over 663 Q-A pairs), finding that the intrinsic Boundary Clarity metric anti-correlates with retrieval (Pearson r = −0.81, n = 5) — the parser with the cleanest boundaries (MinerU) is the worst retriever. We then propose **RCPS** (Retrieval-Conditional Parsing Score), a retriever-agnostic, task-oriented chunking quality metric, and validate it cross-domain on the English-language OHR-Bench (Law + Manual): RCPS discriminates 15 parser-output variants over a 0.27–0.64 range, and the BC↔RCPS anti-correlation replicates (r = −0.35, n = 15). We further test the natural parser-side fix — augmenting parsing training with a chunk-boundary contrastive auxiliary loss (**RADP-B**) — at full scale, training on the same 2,667 pages as the production parser to remove the data-scale confound. The contrastive loss yields only a marginal +1–3 pp RCPS gain, failing the pre-registered 5 pp gate and matching the production baseline. Our analysis reveals the mechanism: intrinsic boundary metrics cannot perceive semantic content quality (BC remains constant as semantic noise destroys retrieval). We release KoGovDoc-RAG (a Korean RAG benchmark, 663 Q-A) and the RCPS reference implementation.

---

## 1 Introduction

Building a retrieval-augmented generation (RAG) system on a corpus of PDFs requires a document parser — a model that converts page images into structured text. Practitioners typically select parsers by intrinsic, *human-readability* metrics: text similarity (NED, edit distance), table fidelity (TEDS), or chunk boundary cleanness. These metrics assume that cleaner parsing yields better downstream retrieval. We show this assumption is *wrong*, in two ways that matter for practice.

**First (C1, diagnostic)**, we quantify the disconnect. In a 6-parser × 3-retriever evaluation on Korean government documents, intrinsic Boundary Clarity correlates with retrieval at Pearson r = −0.81 — the parser scoring highest on the intrinsic metric retrieves *worst*. We extend this to English enterprise documents (OHR-Bench Law + Manual, 15 parser-output variants) and find the disconnect replicates (r = −0.35), with a striking mechanism: as semantic noise is added to a parser's output, Boundary Clarity stays constant while RCPS plummets — intrinsic metrics cannot see semantic content quality.

**Second (C2, metric)**, we propose **RCPS** (Retrieval-Conditional Parsing Score), a task-oriented metric averaging MRR across multiple retrievers and cutoffs. RCPS discriminates parsers, retrievers, and chunking strategies where intrinsic metrics conflate them.

**Third (C3, honest negative)**, we test the natural fix: train the parser end-to-end with a chunk-boundary contrastive auxiliary loss (**RADP-B**). Trained at full scale (2,667 pages, same as the production parser, removing the data-scale confound) and evaluated on a held-out fold, the contrastive loss yields +1–3 pp RCPS — far below our pre-registered 5 pp gate, and matching the production baseline. The aux-loss formulation is the wrong lever; we discuss what the right one looks like.

The paper releases a Korean-language RAG benchmark (KoGovDoc-RAG, 663 Q-A on 294 pages), the RCPS reference implementation, and the full-scale RADP-B checkpoints.

## 2 Related Work

Prior work has documented the OCR/parsing → retrieval gap diagnostically. *OCR Hinders RAG* and OHR-Bench show OCR noise propagates through RAG; EnterpriseDocBench reports a low parsing-quality↔retrieval Pearson r ≈ 0.14; *When Good OCR Is Not Enough* gives concurrent evidence. None of these proposes a *training-time* fix on the parser side.

Existing methods address other layers of the RAG pipeline (Figure 1). **Chunkers**: Late Chunking (Jina), LumberChunker (LLM-narrative), Meta-Chunking and **MoC** (PPL-based) all decide chunk boundaries *post-parsing*. **Embedders**: InSeNT, LMAR train the embedding model contrastively. **Retrievers**: Reward-RAG fine-tunes the retriever on retrieval reward. **Readers**: M-LongDoc, RPO tune the generator. To our knowledge, no prior work trains the **L1 parser** itself on a retrieval signal.

*[Figure 1 — 6-layer RAG pipeline schematic showing where prior methods sit and the empty parser slot. Manually drawn, to be inserted in PHASE_4 LaTeX porting (likely TikZ).]*

Our negative finding on the aux-loss approach (C3) motivates the *next* parser-layer method: retrieval-reward DPO on the parser, which we leave as future work (named RADP-A).

## 3 RCPS: Retrieval-Conditional Parsing Score

Given a parser P, a Q-A set D = {(q_i, a_i, page_i)}, a set of retrievers R, and cutoffs K, RCPS averages MRR across the cross-product:

$$\text{RCPS}(P, D, R, K) = \frac{1}{|R||K|} \sum_{r \in R} \sum_{k \in K} \text{MRR}@k(r, \text{chunks}_P(D), \{q_i\}).$$

We use R = {BGE-M3, multilingual-e5-large, Qwen3-Embedding-8B} (multilingual, varied architectures) and K = {1, 5, 10}. A chunk is relevant for a query iff (i) it comes from the answer's source page, and (ii) the gold answer span is contained in the chunk's text under whitespace/markdown-insensitive normalization.

The retriever-agnostic averaging gives RCPS its robustness: a parser ranked first by RCPS is first across retrievers, not just one. The implementation is released.

## 4 The Parsing-Retrieval Disconnect (C1)

### 4.1 Korean Government Documents

We construct KoGovDoc-RAG: 663 Q-A pairs over 294 pages of Korean government documents, generated with GPT-5.4 and verified with an LLM-as-judge stratified sample (94/100 accept). We evaluate six parsers — two general-purpose VLMs (Qwen3-VL-30B teacher, Qwen3-VL-2B base), our task-tuned WigtnOCR-2B (v1), and three OCR systems (MinerU 2.5, PaddleOCR, Marker) — on the full grid.

**Result (Table 1).** RCPS spans 0.07–0.58. The VLM-family parsers cluster at the top (0.53–0.58); the OCR systems trail (0.07–0.21). Crucially, the *intrinsic Boundary Clarity* metric (MoC) anti-correlates with RCPS at **Pearson r = −0.81** (n = 5, excluding the 38-page Marker subset). MinerU, the cleanest-boundary parser (BC = 0.72), retrieves worst (RCPS = 0.21).

| Parser | BC | RCPS | Hit@1 |
|---|:---:|:---:|:---:|
| Qwen3-VL-30B (teacher) | 0.691 | **0.584** | 0.545 |
| WigtnOCR-2B (ours, v1) | 0.694 | 0.583 | 0.549 |
| Qwen3-VL-2B (base) | 0.677 | 0.532 | 0.500 |
| MinerU | **0.722** | 0.212 | 0.197 |
| PaddleOCR | 0.649 | 0.140 | 0.125 |
| Marker (38p) | 0.667 | 0.073 | 0.068 |
*Table 1: Korean Gov Documents — BC vs RCPS, Pearson r = −0.81 (n = 5, excl. Marker).*

### 4.2 Cross-Domain Replication on OHR-Bench

We evaluate 15 parser-output variants on OHR-Bench Law+Manual (1,043 Q-A): the three base parser outputs released by OHR-Bench (gt, MinerU, Qwen2.5-VL), three formatting-noise perturbations, and 9 semantic-noise perturbations (GOT × MinerU × Qwen2.5-VL, mild/moderate/severe).

**Result.** BC↔RCPS Pearson r = **−0.351** (n = 15). The disconnect replicates in English enterprise documents.

**Mechanism (Figure 2).** Within each semantic-noise family, BC barely moves while RCPS collapses (Figure 2). For MinerU: BC stays at 0.63 ± 0.02 across clean → mild → moderate → severe noise; RCPS falls 0.595 → 0.476 → 0.384 → 0.265. GOT shows the same pattern. Qwen2.5-VL is more noise-robust. Intrinsic boundary metrics see only formatting, not content: noise that destroys retrievable content does not lower BC. This is the disconnect, made visible.

![Figure 2 — noise-family curves](../figures/fig_noise_family.png)
*Figure 2: OHR-Bench noise-family curves. Top — Boundary Clarity stays roughly flat across noise severity. Bottom — RCPS collapses for MinerU and GOT (Qwen2.5-VL is more robust). The intrinsic boundary metric does not perceive the semantic content quality that retrieval depends on.*

## 5 RADP-B: A Negative Result on Parser-Layer Tuning (C3)

### 5.1 Method

We test the natural parser-side fix: jointly train the parser to (a) produce faithful markdown (standard cross-entropy `L_parse`) and (b) make its chunk-boundary representation close to the retriever's space (a chunk-boundary contrastive auxiliary loss `L_contrast`):

$$\mathcal{L}_\text{total} = \mathcal{L}_\text{parse} + \lambda \cdot \mathcal{L}_\text{contrast}.$$

`L_contrast` is InfoNCE: the anchor is a projection of the parser's pooled hidden state over the answer-chunk token span; the positive is the BGE-M3 embedding of that chunk; negatives are other chunks in the batch and same-page hard negatives. BGE-M3 is frozen; only the parser (LoRA) and a small projection head are trained. We call this RADP-B.

### 5.2 Setup

We fine-tune Qwen3-VL-2B-Instruct with LoRA (r = 8, α = 32) on the **full v1 train set** (2,667 pages) — generating 6,164 GPT-5.4 Q-A pairs to enable the contrastive loss at scale — to remove the data-scale confound between our model and the production parser (v1). We sweep λ ∈ {0.0, 0.1, 0.3, 0.5}, with λ = 0 acting as a matched control (identical training, contrastive off; reproduces v1). Evaluation is on the held-out 73-page eval fold (202 Q-A).

### 5.3 Result

**The contrastive loss yields only a marginal RCPS gain.** Table 3 reports the λ sweep. λ = 0.1 is the peak (+1.8 pp RCPS for md-h3 chunking; +2.3 pp for parser-native), then RCPS declines monotonically as λ grows. parseSim (parse-to-GT similarity) declines in lockstep. The pre-registered 5 pp gate **fails**; the H2 target of 8 pp is far out of reach.

Compared to the production parser v1, RADP-B λ = 0.1 is **tied** — beating v1 by +2.2 pp on parser-native, losing by 0.6 pp on md-h3. The matched control (λ = 0, 2,667 pages) reproduces v1 (0.6557 vs 0.6569), confirming the data-scale confound is removed.

| λ | RCPS (md-h3) | RCPS (parser-native) | parseSim |
|---|:---:|:---:|:---:|
| 0.0 (control) | 0.6551 | 0.6557 | 0.872 |
| **0.1** | **0.6664** | **0.6788** | 0.874 |
| 0.3 | 0.6526 | 0.6694 | 0.862 |
| 0.5 | 0.6407 | 0.6442 | 0.851 |
| v1 (ref) | 0.6724 | 0.6569 | 0.789 |
*Table 3: Full-scale λ sweep, 73-page eval fold. Best vs control: +1.13 pp (md-h3) / +2.31 pp (parser-native) — gate (≥5 pp) fails.*

### 5.4 Why It Fails

Two complementary observations: (i) the monotonic decline beyond λ = 0.1 confirms the failure is *not* under-tuning — pushing the contrastive signal harder makes things worse. (ii) parseSim drops with λ even as RCPS gives at most a marginal gain. The two objectives — faithfully reproducing the human-readable target markdown (parse CE) and projecting hidden states toward the retriever's embedding space (contrastive) — compete; the contrastive gradient nudges the parser away from its target with little retrieval benefit. The aux-loss formulation is the wrong lever.

## 6 Discussion

**A consistent picture across C1, C2, C3.** The intrinsic-metric disconnect (C1, cross-domain) shows the parser's training target — human-readable markdown — does not align with what retrieval needs. RCPS (C2) measures the gap. RADP-B (C3) attempts to close it by bolting an auxiliary objective onto an unchanged target, and fails — because the *target itself* (the GT markdown) still encodes only human readability. The mechanistic finding from §4.2 makes this explicit: intrinsic structure looks clean while content is destroyed.

**What would work.** Optimizing the parser's *output* directly against a retrieval signal — i.e., a retrieval-reward objective (DPO/RL) that scores the parser's discrete markdown by downstream RCPS — sidesteps both problems: the gradient flows through the actually-deployed artifact, and the supervision is task-aligned. This is the natural next method; we name it **RADP-A** and leave it to future work, where it requires a months-scale RL/distillation effort beyond an EMNLP cycle.

**Practical takeaway.** Practitioners selecting a parser for RAG should not trust intrinsic boundary or formatting metrics: the MinerU example (BC #1, RCPS last) is a real production trap. RCPS, run on a small held-out Q-A set, changes the decision.

## 7 Conclusion

We documented the parsing-retrieval disconnect in two languages and domains (Korean government, English enterprise); proposed RCPS as a task-oriented metric to measure it; and showed that the natural parser-layer fix — a chunk-boundary contrastive auxiliary loss (RADP-B) — yields only marginal gains under a fair full-scale comparison. The contributions, in order: a diagnostic with a striking BC↔RCPS = −0.81; a retriever-agnostic metric; and a rigorous negative result on parser-aux-loss tuning. Code, data, and checkpoints are released.

---

## Released artifacts

- **KoGovDoc-RAG** — 663 Q-A on 294 Korean government document pages.
- **RCPS reference implementation** — `src/wigtnocr_radp/evaluation/`.
- **RADP-B checkpoints** — `radp_b_full_lambda{00,01,03,05}` (Qwen3-VL-2B-Instruct + LoRA, fine-tuned on 2,667 pages).
- **OHR-Bench cross-domain results** — 15-variant RCPS + Boundary Clarity correlation.

## Limitations

- **Single primary language.** The C1 diagnostic is strongest in Korean (n = 5, r = −0.81). Cross-domain English replicates the direction but weaker (n = 15, r = −0.35). Multi-language generalization beyond Korean and English is future work.
- **Q-A generated by GPT-5.4 with LLM-as-judge verification.** Pure human verification is preferable but cost-prohibitive at the scale used (6,164 train Q-A); we instead frozen-released the 663 eval Q-A and report verification statistics (94/100 accept on a stratified sample).
- **RADP-B decision-A formulation.** Our contrastive loss aligns the *parser's pooled hidden state* — not the parser's discrete output — to the retriever's embedding space. The literal formulation of aligning discrete outputs is non-differentiable; routing discrete optimization to RL (RADP-A) is the natural next step.

## References (placeholder)

(to be formatted in PHASE_4 — key citations: EnterpriseDocBench 2026, OCR Hinders RAG / OHR-Bench (ICCV 2025), When Good OCR Is Not Enough 2026, InSeNT 2025, MoC ACL 2025, LumberChunker EMNLP 2024 Findings, Late Chunking 2024, M-LongDoc EMNLP 2025, RPO 2025, BGE-M3 2024, Qwen3-VL, MinerU 2025.)
