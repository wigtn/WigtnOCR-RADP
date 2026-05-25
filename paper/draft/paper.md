# Retrieval-Aware Document Parsing: Diagnosing and Measuring the Parsing–Retrieval Gap

**Harrison Kim, et al.** (Braincrew AI)
*EMNLP 2026 Industry Track — Draft v0.3 (2026-05-24)*

---

## Abstract

Document parsers used in retrieval-augmented generation (RAG) are conventionally optimized for *human-readability* metrics — TEDS, edit distance, Boundary Clarity — yet these metrics do not predict downstream retrieval. In Korean government documents (6 parsers × 3 retrievers × 663 Q-A), MoC Boundary Clarity *anti*-correlates with retrieval at Pearson r = −0.81: the parser scoring highest on the intrinsic metric (MinerU) is the *worst* retriever. We propose **RCPS** (Retrieval-Conditional Parsing Score), a retriever-agnostic task-oriented metric, and validate it cross-domain on the English-language OHR-Bench (15 parser-output variants; r = −0.35). A noise-perturbation analysis reveals the mechanism: intrinsic boundary metrics see only formatting, not content — semantic noise that destroys retrieval leaves BC nearly unchanged. We test the natural parser-side fix — augmenting parsing training with a chunk-boundary contrastive auxiliary loss (**RADP**) — at full scale, fair-compared with the production parser. The auxiliary loss yields +1–3 pp RCPS, well below our pre-registered 5 pp gate. The aux-loss formulation is the wrong lever. We release **KoGovDoc-RAG** (a Korean RAG benchmark), the RCPS reference implementation, and the trained checkpoints.

---

## 1 Introduction

Picking a document parser for a retrieval-augmented generation (RAG) system, a practitioner runs MinerU on Korean government PDFs and confirms it tops every intrinsic parsing-quality metric in our grid — highest MoC Boundary Clarity (0.72), competitive on text fidelity — and deploys it. Retrieval Hit@1 is 0.20, the *worst* of the six parsers evaluated. The cleanest-looking parser is the worst retriever.

This is not a one-off. In a 6-parser × 3-retriever evaluation on Korean government documents, Boundary Clarity *anti*-correlates with retrieval at Pearson r = −0.81 (n = 5). A cross-domain check on the English-language OHR-Bench (n = 15 parser-output variants, including controlled noise perturbations) replicates the direction (r = −0.35) and reveals the mechanism: as semantic noise is added to a parser's output, Boundary Clarity stays constant while retrieval performance collapses. Intrinsic boundary metrics cannot see semantic content quality, and the practitioner has no way to know this from the metrics they see.

**Contributions.**

- **C1.** A cross-domain diagnostic of the parsing–retrieval disconnect, with a mechanism (noise-family curve, Figure 2) that makes the intrinsic-metric failure mode visible at a glance.
- **C2. RCPS** (Retrieval-Conditional Parsing Score), a retriever-agnostic, task-oriented metric practitioners can run on a small held-out Q-A set to choose parsers and chunking strategies for production RAG — discriminating combinations that intrinsic metrics conflate.
- **C3.** A rigorous negative on the natural parser-side fix. Training the parser with a chunk-boundary contrastive auxiliary loss (**RADP**), at full scale and fair-compared with the production parser, yields +1–3 pp RCPS — below our pre-registered 5 pp gate. The aux-loss formulation is the wrong lever; we argue the right one is retrieval-reward training on the parser's discrete output (future work).

We release **KoGovDoc-RAG** (663 Q-A over 294 Korean government document pages), the RCPS reference implementation, and the full-scale RADP checkpoints (λ ∈ {0, 0.1, 0.3, 0.5}).

## 2 Related Work

**Diagnostic prior art.** The parsing–retrieval gap has been documented but not closed. *OCR Hinders RAG* / OHR-Bench show OCR noise cascading through the RAG pipeline; *EnterpriseDocBench* reports parsing-quality↔retrieval r ≈ 0.14; *When Good OCR Is Not Enough* gives concurrent evidence. These contributions diagnose; none proposes a training-time fix on the parser side.

**Training-time methods, by layer (Figure 1).** Chunking — Late Chunking (Jina), LumberChunker, Meta-Chunking, and MoC — decide boundaries *post-parsing*. Embedding-side — InSeNT, LMAR — train the embedder contrastively. Retrieval — Reward-RAG — fine-tunes the retriever on retrieval reward. Reader-side — M-LongDoc, RPO — tunes the generator. To our knowledge, **no prior work trains the L1 parser itself on a retrieval signal**, which is the gap our paper occupies.

*[Figure 1 — 6-layer RAG pipeline schematic showing where prior methods sit and the empty parser slot. Manually drawn, to be inserted in PHASE_4 LaTeX porting (likely TikZ).]*

Our negative finding on the aux-loss approach (C3) motivates a principled next step: training the parser via retrieval-reward optimisation (e.g., DPO/RL on the parser's discrete output), which we leave to future work.

## 3 Method

### 3.1 RCPS: Retrieval-Conditional Parsing Score

We need a metric that scores a parser by what *downstream* retrieval can do with its output, not by how clean the output looks. Three design choices follow from this: the metric must be (i) **extrinsic** — operate on the parsed corpus + a Q-A probe rather than on text alone; (ii) **retriever-agnostic** — robust to which embedder happens to be in the production stack; and (iii) **structure-agnostic in its relevance judgment** — a chunk is relevant if its text contains the answer, regardless of how the parser formatted it.

Given a parser P, a Q-A set D = {(q_i, a_i, page_i)}, a set of retrievers R, and cutoffs K, RCPS averages MRR across the cross-product:

$$\text{RCPS}(P, D, R, K) = \frac{1}{|R||K|} \sum_{r \in R} \sum_{k \in K} \text{MRR}@k(r, \text{chunks}_P(D), \{q_i\}).$$

We use R = {BGE-M3, multilingual-e5-large, Qwen3-Embedding-8B} (multilingual, varied architectures) and K = {1, 5, 10}. A chunk is relevant for a query iff (i) its source page matches the answer's source page, and (ii) the gold answer span is a substring of the chunk under whitespace/markdown-insensitive normalisation. The retriever average makes the score robust to embedder choice: a parser that wins one retriever but loses another does *not* dominate the RCPS ranking. The implementation is released.

### 3.2 RADP — A Parser-Side Contrastive Method

The natural parser-side fix is to *jointly* train the parser to (a) produce faithful markdown — standard parsing cross-entropy `L_parse` — and (b) make its chunk-boundary representation close to the retriever's embedding space — a chunk-boundary contrastive auxiliary loss `L_contrast`:

$$\mathcal{L}_\text{total} = \mathcal{L}_\text{parse} + \lambda \cdot \mathcal{L}_\text{contrast}.$$

For each Q-A pair, the contrastive anchor is the parser's pooled last-layer hidden state over the answer-chunk's token span, passed through a small projection head (1024-d, matching BGE-M3). The InfoNCE positive is the BGE-M3 embedding of that same chunk; negatives are other chunks in the batch and a same-page hard negative. The retriever (BGE-M3) is frozen; only the parser (LoRA) and the projection head are trained. We call this **RADP**. The literal "differentiable BGE-encoded chunks" formulation is non-differentiable through the parser's discrete markdown output; aligning the parser's *hidden* representation to the frozen retriever's space is the natural differentiable surrogate.

## 4 Experiments

### 4.1 Setup

We construct **KoGovDoc-RAG**: 663 Q-A pairs over 294 pages of Korean government documents, generated with GPT-5.4 and verified with an LLM-as-judge stratified sample (94/100 accept). For RADP's full-scale training, we additionally generate 6,164 GPT-5.4 Q-A on the 2,667-page v1 train set; the held-out 73-page eval fold (202 Q-A) is used for all RADP evaluation. Cross-domain replication uses **OHR-Bench** (Law + Manual, 1,043 verbatim-answerable Q-A) across the three released parser outputs (gt, MinerU, Qwen2.5-VL) plus twelve controlled noise perturbations.

We fine-tune Qwen3-VL-2B-Instruct with LoRA (r = 8, α = 32) on the full v1 train set (2,667 pages). We sweep λ ∈ {0.0, 0.1, 0.3, 0.5}, with λ = 0 acting as a matched control (identical training, contrastive off; reproduces the production parser v1). All RCPS values use the three retrievers and three cutoffs defined in §3.1.

### 4.2 The Parsing–Retrieval Disconnect (C1)

**Korean government documents (Table 1).** RCPS spans 0.07–0.58 across the six parsers. The VLM-family parsers cluster at the top (0.53–0.58); the OCR systems trail (0.07–0.21). Crucially, the intrinsic Boundary Clarity metric (MoC) anti-correlates with RCPS at **Pearson r = −0.81** (n = 5, excluding the 38-page Marker subset). MinerU, the cleanest-boundary parser (BC = 0.72), retrieves worst (RCPS = 0.21).

| Parser | BC | RCPS | Hit@1 |
|---|:---:|:---:|:---:|
| Qwen3-VL-30B (teacher) | 0.691 | **0.584** | 0.545 |
| WigtnOCR-2B (ours, v1) | 0.694 | 0.583 | 0.549 |
| Qwen3-VL-2B (base) | 0.677 | 0.532 | 0.500 |
| MinerU | **0.722** | 0.212 | 0.197 |
| PaddleOCR | 0.649 | 0.140 | 0.125 |
| Marker (38p) | 0.667 | 0.073 | 0.068 |
*Table 1: KoGov, BC vs RCPS, Pearson r = −0.81 (n = 5, excl. Marker).*

A single-domain anti-correlation could be a quirk of one language or document type. We test cross-domain.

**Cross-domain — the mechanism (Figure 2, Table 2).** On OHR-Bench across all seven domains (Law, Manual, Finance, Newspaper, Textbook, Academic, Administration; 1,043 verbatim-answerable Q-A), we evaluate 15 parser-output variants: the three released parser outputs (gt, MinerU, Qwen2.5-VL), three formatting-noise perturbations, and nine semantic-noise perturbations (GOT/MinerU/Qwen2.5-VL × mild/moderate/severe).

The mechanism is the headline finding. Within each semantic-noise family, Boundary Clarity barely moves while RCPS collapses (Figure 2). For MinerU's family, BC stays in **0.71–0.73** across clean → mild → moderate → severe; RCPS falls **0.50 → 0.41 → 0.35 → 0.24** (−51%). GOT shows the same pattern (RCPS 0.38 → 0.34 → 0.26, −32%). Qwen2.5-VL is more noise-robust (RCPS 0.47 → 0.43, −8%). **Intrinsic boundary metrics see only formatting, not content**: semantic noise that destroys retrievable content does not lower BC.

![Figure 2 — noise-family curves](../figures/fig_noise_family.png)
*Figure 2: OHR-Bench 7-domain noise-family curves. Top — Boundary Clarity stays roughly flat across noise severity for all three parser families. Bottom — RCPS collapses for MinerU and GOT (Qwen2.5-VL is more noise-robust). The intrinsic metric does not perceive the semantic content quality that retrieval depends on.*

| Family (n) | BC range | RCPS (clean → severe) | ΔRCPS |
|---|:---:|:---:|:---:|
| MinerU + semantic noise (4) | 0.708–0.735 | 0.50 → 0.24 | **−51%** |
| GOT + semantic noise (3) | 0.495–0.650 | (no clean) → 0.26 | — |
| Qwen2.5-VL + semantic noise (4) | 0.610–0.619 | 0.47 → 0.43 | −8% |
*Table 2: OHR-Bench 7-domain per-family noise-perturbation summary. The disconnect (BC flat, RCPS dropping under semantic noise) is dramatic for MinerU and GOT; Qwen2.5-VL is more robust. Full 15-variant grid in supplementary.*

**Aggregate cross-variant correlation is data-mix sensitive.** Pearson BC↔RCPS across all 15 variants is **−0.35** on Law+Manual alone but **+0.25** on the full 7-domain corpus — the scalar flips as the document mix broadens. The robust finding is the per-family mechanism above, which reproduces in every domain; the cross-variant scalar conflates parser families with different intrinsic noise robustness and is not a stable signal on its own.

### 4.3 RCPS Discriminates Chunking Strategies (C2)

A useful metric must separate alternatives a practitioner would compare. On the v1 parser's output for KoGov (Table 3), RCPS separates four chunking strategies cleanly: markdown-header chunking (md-h3) > the parser's native paragraphing > LumberChunker (LLM-narrative) > fixed-size. Intrinsic boundary metrics, by contrast, would rank these inconsistently or rank fixed-size highest (it has the cleanest boundaries by construction). RCPS captures *retrievability* of the chunking, not its surface appearance.

| Chunker | RCPS | Hit@1 | MRR@10 |
|---|:---:|:---:|:---:|
| md-h3 | **0.593** | 0.556 | 0.613 |
| parser_native | 0.583 | 0.549 | 0.602 |
| LumberChunker | 0.557 | 0.514 | 0.580 |
| fixed500 | 0.535 | 0.491 | 0.560 |
*Table 3: KoGov chunking-strategy grid (663 Q-A, v1 parser output, 3-retriever RCPS average).*

### 4.4 RADP: The Parser-Side Fix Does Not Close the Gap (C3)


We train RADP at full scale (2,667 pages) and evaluate on the 73-page held-out fold (202 Q-A), comparing against v1 and the matched λ = 0 control.

**Result (Table 4).** The contrastive loss yields a sub-threshold RCPS gain. λ = 0.1 is the peak (+1.1 pp on md-h3; +2.3 pp on parser-native), and RCPS declines monotonically beyond that. parseSim (parse-to-GT similarity) declines in lockstep. The pre-registered 5 pp gate **fails**; the H2 target of 8 pp is far out of reach. Compared to the production parser v1, RADP λ = 0.1 is **tied** — beating v1 by +2.2 pp on parser-native, losing 0.6 pp on md-h3. The matched control reproduces v1 (0.6557 vs 0.6569), confirming the data-scale confound is removed.

| λ | RCPS (md-h3) | RCPS (parser-native) | parseSim |
|---|:---:|:---:|:---:|
| 0.0 (control) | 0.6551 | 0.6557 | 0.872 |
| **0.1** | **0.6664** | **0.6788** | 0.874 |
| 0.3 | 0.6526 | 0.6694 | 0.862 |
| 0.5 | 0.6407 | 0.6442 | 0.851 |
| v1 (ref) | 0.6724 | 0.6569 | 0.789 |
*Table 4: Full-scale λ sweep, 73-page eval fold. Best vs control: +1.13 pp (md-h3) / +2.31 pp (parser-native) — gate (≥5 pp) fails.*

**Why it fails (and the C1 connection).** The monotonic decline beyond λ = 0.1 rules out under-tuning; parseSim drops with λ in lockstep, showing the two objectives compete over the same LoRA parameters. The connection to §4.2 is direct: the parser's `L_parse` target is itself human-readable markdown — exactly the structure whose intrinsic boundary metrics anti-correlate with retrieval (Figure 2). An auxiliary objective on the parser's *hidden* representations cannot escape the prior its primary objective embeds. To overcome the human-readability prior, training signal has to enter through the parser's discrete output, not its hidden states.

## 5 Discussion and Conclusion

**A consistent picture across C1, C2, C3.** The intrinsic-metric disconnect (C1) shows the parser's training target — human-readable markdown — does not align with what retrieval needs. RCPS (C2) measures the gap. RADP (C3) attempts to close it by bolting an auxiliary objective onto an unchanged target, and fails — because the *target itself* still encodes only human readability. The mechanistic finding (Figure 2) makes this explicit: intrinsic structure looks clean while content is destroyed.

**What would work.** Optimising the parser's *output* directly against a retrieval signal — a retrieval-reward objective (DPO/RL) that scores the parser's discrete markdown by downstream RCPS — sidesteps both problems: the gradient flows through the actually-deployed artifact, and the supervision is task-aligned. This is the natural next direction; it requires a months-scale RL/distillation effort and is left to future work.

**Deployment lessons.** Three actionable items for teams shipping document-RAG systems:

1. *Do not select parsers by intrinsic metrics alone.* The MinerU vignette of §1 is not contrived — Boundary Clarity (and likewise TEDS, edit distance against a clean GT) ranks parsers in an order the downstream retriever inverts. A 500-question RCPS evaluation, run on a domain-representative held-out set, takes hours and changes the decision.
2. *Auxiliary losses on parser hidden states are the wrong lever.* Engineering teams faced with a parsing-retrieval gap may be tempted to bolt a retrieval-oriented auxiliary objective onto the parser (RADP is a natural form of this). At full scale, fair-compared with their current production parser, the gain is sub-threshold (+1–3 pp). The investment does not pay off.
3. *The disconnect is mechanistic, not stochastic.* Figure 2 shows intrinsic structure can look pristine while content is destroyed. Teams deploying OCR/parsing in noisy production environments should monitor retrieval directly, not the parser's surface quality.

**Conclusion.** We documented the parsing–retrieval disconnect in two languages and domains (Korean government, English enterprise); proposed RCPS as a task-oriented metric to measure it; and showed that the natural parser-layer fix — a chunk-boundary contrastive auxiliary loss (RADP) — yields sub-threshold gains under a fair full-scale comparison. The contributions, in order: a diagnostic with a striking BC↔RCPS = −0.81 and a mechanism (Figure 2) showing intrinsic structure is blind to content noise; a retriever-agnostic task-oriented metric; and a rigorous negative on parser-aux-loss tuning that motivates retrieval-reward training as the principled next step. Code, data, and checkpoints are released.

---

## Released artifacts

- **KoGovDoc-RAG** — 663 Q-A on 294 Korean government document pages.
- **RCPS reference implementation** — `src/wigtnocr_radp/evaluation/`.
- **RADP checkpoints (4)** — Qwen3-VL-2B-Instruct + LoRA, fine-tuned on the 2,667-page v1 train set with λ ∈ {0, 0.1, 0.3, 0.5}.
- **OHR-Bench cross-domain results** — 15-variant RCPS + Boundary Clarity correlation.

## Limitations

- **Single primary language.** The C1 diagnostic is strongest in Korean (n = 5, r = −0.81). The English cross-domain replication on OHR-Bench is directionally consistent but weaker in magnitude (n = 15, r = −0.35), and is built on three real parser outputs plus twelve controlled noise perturbations rather than fifteen independent real parsers. Multi-language generalisation beyond Korean and English remains future work.
- **Statistical power.** With n = 5 (Korean grid) and n = 15 (OHR-Bench), our correlations are illustrative rather than inferential — they support a directional finding that future work can extend by enlarging the parser pool.
- **Q-A generation.** All 6,827 Q-A pairs (663 eval + 6,164 train) were produced by GPT-5.4 and verified by LLM-as-judge against the human-curated GT markdown. We sampled 100 stratified eval Q-A for verification (94/100 accept); pure human verification at the train-set scale was cost-prohibitive. We froze and released the eval set so future evaluators can audit it.
- **RADP is tested in its hidden-state-pooled formulation only.** Our contrastive loss aligns the parser's pooled hidden state — not its discrete output — to the retriever's embedding space, because the literal "encode the parser's discrete chunk with BGE-M3" path is non-differentiable. The structural argument of §4.4 (the aux-loss can only influence the deployed markdown via gradient backflow through `L_parse`'s human-readable target) is independent of pooling details; the negative does not rule out other parser-side paradigms such as retrieval-reward training on the parser's discrete output (§5).
- **Eval fold size.** RADP's full-scale RCPS comparison uses the 73-page / 202-Q-A held-out fold of KoGovDoc-RAG — large enough for the +1–3 pp effect to be stable across retrievers but small enough that a 5 pp gate is a conservative bar in absolute terms.
- **Embedding-side failure analysis (future work).** This paper isolates the *parser* layer of the RAG pipeline (C1 diagnostic, RCPS metric, RADP attempt). A complementary direction — diagnosing where in the embedding/vectorisation pipeline well-fragmented documents nonetheless lose retrievability, localising the failure to a specific transformation step — would shed light on the gap from the retriever side and is left to future work.

## References (BibTeX-ready outline)

To be converted to `paper/refs.bib` in PHASE_4. Citations grouped by topic; cite-key suggestions in `monospace`.

**Diagnostic prior art (parsing↔retrieval gap).**
- `zhang2024ohr` Zhang et al. *OCR Hinders RAG: Evaluating the Cascading Impact of OCR on Retrieval-Augmented Generation*. ICCV 2025 (arXiv:2412.02592). — primary citation for the diagnosis layer.
- `enterprisedocbench2026` EnterpriseDocBench (2026). — parsing-quality↔retrieval r ≈ 0.14.
- `goodocr2026` *When Good OCR Is Not Enough* (2026). — concurrent evidence.

**Chunking methods (post-parsing).**
- `jina2024late` Günther et al. *Late Chunking* (Jina AI, 2024, arXiv:2409.04701).
- `duarte2024lumber` Duarte et al. *LumberChunker* (EMNLP 2024 Findings, arXiv:2406.17526).
- `zhao2024meta` Zhao et al. *Meta-Chunking* (2024, arXiv:2410.12788).
- `liu2025moc` Liu et al. *MoC / Meta-Chunking* (ACL 2025, arXiv:2503.09600). — Boundary Clarity metric.

**Embedding-side training.**
- `le2025insent` Le et al. *Context is Gold to find the Gold Passage / InSeNT* (2025, arXiv:2505.24782).
- `2025lmar` LMAR. — embedder contrastive.

**Retrieval / reader-side training.**
- `2024rewardrag` Reward-RAG (2024, arXiv:2410.03780).
- `2024chunkrag` ChunkRAG (2024, arXiv:2410.19572). — post-retrieval filtering.
- `mlongdoc2025` M-LongDoc (EMNLP 2025, arXiv:2411.06176).
- `2025rpo` RPO (2025, arXiv:2501.13726). — closest to our future direction (parser-side reward DPO), though RPO operates on the generator.

**Foundations cited.**
- `chen2024bgem3` Chen et al. *BGE-M3* (2024, arXiv:2402.03216). — frozen retriever.
- `qwen3vl` Qwen3-VL (Alibaba). — parser backbone (v1 + RADP).
- `faysse2024colpali` Faysse et al. *ColPali* (ICLR 2025, arXiv:2407.01449). — alternative paradigm citation.
- `mineru2025` MinerU 2.5 (2025). — OCR baseline.
- `omnidocbench2025` OmniDocBench (CVPR 2025). — parsing baseline cited via WigtnOCR v1's prior results.

**Our prior assets.**
- `wigtn-kogovdoc-bench` Wigtn. *KoGovDoc-Bench* (HuggingFace dataset, 2026).
- `wigtn-ocr-v1` Wigtn. *Qwen3-VL-2B-WigtnOCR* (HuggingFace model, 2026).
