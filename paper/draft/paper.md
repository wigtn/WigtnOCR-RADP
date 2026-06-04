# RCPS: Choosing Document Parsers by Retrieval, Not by Appearance — Diagnosing the Parsing–Retrieval Gap

**Hyeong-seob Kim**\*, **Sang-woo Son**\* (WIGTN)
*\* Equal contribution (co-first authors). EMNLP 2026 Industry Track — Draft v0.6 (2026-05-31).*

---

## Abstract

The cleanest-looking document parser is the worst retriever. On Korean government documents, the parser with the *highest* intrinsic Boundary Clarity (MinerU, BC = 0.72) retrieves *worst*, and choosing a parser by retrieval instead of by appearance swings retrieval **Hit@1 by 2.8× (0.197 → 0.549)** — a decision the standard human-readability metrics (TEDS, edit distance, MoC Boundary Clarity) get exactly backwards (Boundary Clarity *anti*-correlates with retrieval at Pearson **r = −0.81, n = 5**). We make four contributions for production document-RAG. **(C1)** We diagnose this parsing–retrieval disconnect across Korean and English (OHR-Bench), with a controlled noise-perturbation mechanism showing intrinsic boundary metrics see *formatting, not content* — semantic noise that destroys retrieval leaves BC nearly unchanged (MinerU family BC 0.71–0.73 while RCPS falls −51%). **(C2)** A retriever-free **coverage diagnostic** localises the gap to a pipeline layer: 20.2 % of answers are *absent* from the parser output (a parser fault) versus a 0–2 % *split* rate, with the absent rate constant across all eight chunkers — an actionable rule (*if absent dominates, fix the parser; if split dominates, fix the chunker*) computable before any retriever or training. **(C3)** We propose **RCPS**, a cheap retrieval-grounded evaluation *protocol* — held-out Q-A, retriever-averaged, format-invariant relevance — that practitioners run on a small probe set (no training) to pick parsers and chunkers that standard metrics rank wrong; an ablation confirms it is not plain single-embedder MRR (dropping retriever-averaging inverts the top parser ranking). **(C4)** We map where parser-side training does and does not help: a hidden-state auxiliary loss (RADP-aux) and reference-free SimPO are sub-threshold — a useful *cost-saving negative* — while discrete-output preference training yields a small but real gain: on cross-domain English OHR-Bench **Hit@5 +0.85 pp [+0.35, +1.43], two-sided significant** (RADP-DPO, n = 2,264), with KoGov **+1.96 pp directional** (n = 663), at zero inference cost. A matched best-of-K control that ranks the *same* candidates by edit-distance-to-ground-truth instead of a retrieval reward reproduces the gain (OHR-Bench **Hit@5 +1.22 pp [+0.35, +2.15]**), so the operative lever is parser-to-GT **text-fidelity distillation**, not the retrieval signal per se — *consistent with* the text-fidelity mechanism (the gain moves TextNED, not chunk boundaries), not the original boundary hypothesis. We release **KoGovDoc-RAG** (a Korean document-RAG benchmark) and the RCPS reference implementation.

---

## 1 Introduction

Picking a document parser for a retrieval-augmented generation (RAG) system, a practitioner runs MinerU on Korean government PDFs and confirms it tops every intrinsic parsing-quality metric in our grid — highest MoC Boundary Clarity (0.72), competitive on text fidelity — and deploys it. Retrieval Hit@1 is 0.20, the *worst* of the six parsers evaluated. The cleanest-looking parser is the worst retriever.

This is not a one-off. In a 6-parser × 3-retriever evaluation on Korean government documents, Boundary Clarity *anti*-correlates with retrieval at Pearson r = −0.81 (n = 5). A cross-domain check on the English-language OHR-Bench reveals the *mechanism* behind the disconnect: across controlled noise perturbations of a parser's output, semantic noise that destroys retrieval leaves Boundary Clarity nearly unchanged — the intrinsic metric cannot see semantic content quality, and the practitioner has no way to know this from the metrics they see (§4.2).

**Contributions.**

- **C1. The parsing–retrieval disconnect, and the mechanism behind it.** The parser a team would pick by intrinsic metrics is not the parser retrieval wants: parser choice alone swings retrieval **Hit@1 by 2.8× (0.197 → 0.549)**, and Boundary Clarity *anti*-correlates with retrieval (Korean **r = −0.81, n = 5**). A controlled noise-perturbation mechanism (cross-domain, English OHR-Bench) shows *why*: intrinsic boundary metrics see **formatting, not content** — semantic noise that destroys retrieval leaves Boundary Clarity flat (MinerU family BC 0.71–0.73 constant while **RCPS −51%**), so the metric is structurally blind to the property retrieval depends on.
- **C2. A retriever-free coverage diagnostic that localises the gap to a pipeline layer.** Holding the parser output fixed and varying the chunker, we classify every answer as *covered*, *split* (chunker fault), or *absent* (parser fault). On the production parser, **20.2 % of answers are *absent* versus a 0–2 % *split* rate**, and the absent rate is **constant across all eight chunkers** (boundary-independent, as a parser fault must be). This turns "intrinsic metrics mislead" into an actionable rule — **if *absent* dominates, fix the parser; if *split* dominates, fix the chunker** — and tells a team whether a parser-side intervention can help *before* they run any retriever or any training.
- **C3. RCPS — a retriever-agnostic protocol for selecting parsers *and* chunkers — backed by an RCPS ≠ MRR ablation.** RCPS wraps ordinary retrieval MRR in three protocol choices (held-out Q-A, retriever-averaged, format-invariant relevance) that practitioners run on a small probe set, no training, to choose the **two** parser-side knobs they control. It is **not** plain single-embedder MRR: an ablation (Table 3b) shows that **averaging over retrievers is what resolves the top parser choice — naive single-embedder MRR inverts the #1 ranking** — so the protocol, not a new scoring function, is the contribution.
- **C4. A bounded map of what parser-side training adds: a ceiling and cost-saving negatives.** Two natural formulations *fail* and reporting them saves others the compute: a hidden-state contrastive auxiliary loss (**RADP-aux**, λ ∈ {0, 0.1, 0.3, 0.5}) is sub-threshold (+1–3 pp RCPS, below the pre-registered 5 pp gate, CIs spanning zero), and reference-free **SimPO** is negative across all cells. Only discrete-output preference training helps, and *modestly*: cross-domain English OHR-Bench **Hit@5 +0.85 pp [+0.35, +1.43], two-sided significant** (**RADP-DPO**, n = 2,264), with KoGov **+1.96 pp directional** (n = 663). A **matched best-of-K control** (RADP-Distill) that ranks the *same* candidates by edit-distance-to-ground-truth instead of the retrieval reward reproduces the gain (OHR-Bench **Hit@5 +1.22 pp [+0.35, +2.15]**, statistically indistinguishable) — so the lever is parser-to-GT **text-fidelity distillation**, *not* the retrieval signal, and the gain moves text fidelity (TextNED), not chunk boundaries (BC unchanged from v1). Parser-side training is a *bounded* lever (~1 pp Hit@5), and the retrieval reward is not the part that matters — a cost-saving negative: distil toward clean GT text, don't build a retrieval-reward pipeline.

We release **KoGovDoc-RAG** (663 Q-A over 294 Korean government document pages), the RCPS reference implementation, the RADP-aux checkpoints (λ ∈ {0, 0.1, 0.3, 0.5}), the RADP-Distill checkpoint (the recommended parser-side lever), and the RADP-DPO checkpoints (R1–R3) + SimPO control (the controlled-against retrieval-reward route).

## 2 Related Work

**Diagnostic prior art.** The parsing–retrieval gap has been documented but not closed: OHR-Bench (*OCR Hinders RAG*), *EnterpriseDocBench* (parsing-quality↔retrieval r ≈ 0.14), and *When Good OCR Is Not Enough* all diagnose OCR noise cascading through the RAG pipeline, but none proposes a training-time fix on the parser side.

**Training-time methods, by layer (Figure 1).** Existing parser-adjacent training operates at every layer *except* the parser: chunking methods (Late Chunking, LumberChunker, Meta-Chunking, MoC) decide boundaries post-parsing; embedding-side methods (InSeNT, LMAR) train the embedder contrastively; and retrieval/reader-side methods (Reward-RAG, M-LongDoc, RPO) tune the retriever or generator. To our knowledge, **no prior work trains the L1 parser itself on a retrieval signal**, which is the gap our paper occupies.

*[Figure 1 — 6-layer RAG pipeline schematic showing where prior methods sit and the empty parser slot. Manually drawn, to be inserted in PHASE_4 LaTeX porting (likely TikZ).]*

Our primary contributions sit *upstream* of any training: a cross-domain diagnosis of the disconnect (C1) with a parser-vs-chunker localisation (C2) and a retrieval-grounded protocol for *selecting* parsers and chunkers (RCPS, C3). On top of that we also test parser-side training (C4) from both natural directions — the hidden-state aux-loss (RADP-aux, §3.3a) and the discrete-output DPO (RADP-DPO, §3.3) — and find only the discrete-output route works, and modestly (§4.4): the retrieval-reward signal must enter through the parser's discrete output, and even then it tightens text fidelity (§4.5) rather than transforming the parser. The headline for a practitioner is therefore *how to choose* a parser, with training a smaller, optional gain on top.

## 3 Method

### 3.1 RCPS: Retrieval-Conditional Parsing Score

We need a way to rank parsers by what *downstream* retrieval does with their output, not by how clean that output looks. **RCPS is deliberately *not* a new similarity function — it is an evaluation *protocol* that wraps ordinary retrieval MRR** in three choices that turn it into a reliable parser-selection tool: (i) **extrinsic** — score on the parsed corpus + a held-out Q-A probe, not on text alone; (ii) **retriever-agnostic** — average over several embedders so the ranking does not hinge on which one happens to sit in the production stack; and (iii) **format-invariant relevance** — a chunk counts as relevant iff its text contains the answer span, however the parser formatted it. The contribution is the *protocol* (what to measure, on what probe, and how to judge relevance), not a novel scoring function — which is also why this is not "just MRR": plain single-embedder MRR with format-sensitive matching yields a different, unstable parser ranking.

Given a parser P, a Q-A set D = {(q_i, a_i, page_i)}, a set of retrievers R, and cutoffs K, RCPS averages MRR across the cross-product:

$$\text{RCPS}(P, D, R, K) = \frac{1}{|R||K|} \sum_{r \in R} \sum_{k \in K} \text{MRR}@k(r, \text{chunks}_P(D), \{q_i\}).$$

We use R = {BGE-M3, multilingual-e5-large, Qwen3-Embedding-8B} (multilingual, varied architectures) and K = {1, 5, 10}. A chunk is relevant for a query iff (i) its source page matches the answer's source page, and (ii) the gold answer span is a substring of the chunk under whitespace/markdown-insensitive normalisation. The retriever average makes the ranking robust to embedder choice: a parser that wins one retriever but loses another does *not* dominate. In practice a team runs RCPS on a few hundred held-out Q-A, with no training, to pick a parser or chunker that intrinsic metrics (TEDS, BC) rank wrong; on our data this is the difference between a 0.20 and a 0.55 Hit@1 parser. The implementation is released.

### 3.2 Coverage Diagnostic — Locating the Gap (Parser vs Chunker)

RCPS scores the parser, chunker, and retriever *jointly*, so a low score does not say *which* layer is at fault. Before proposing any fix, we separate the parser from the chunker with a retriever-free diagnostic. Holding the parser output fixed and varying the chunker, we classify each Q-A's gold answer by where it lands after chunking:

- **covered** — the span sits inside a single chunk (retrievable);
- **split** — the span is in the page markdown but no single chunk holds it whole; a boundary cut through it (a *chunker* fault, recoverable with overlap or larger windows);
- **absent** — the span is not in the parser output at all (a *parser* fault, unrecoverable by any chunking; `no_parse` if the page produced nothing).

`coverage = covered / total` is the ceiling on retrieval — split and absent answers score zero for *any* retriever. Splitting the non-covered mass into chunker-fault (`split`) vs parser-fault (`absent` / `no_parse`) attributes the parsing–retrieval gap to a *pipeline layer*, deciding whether a parser-side intervention can help at all (§4.2). Relevance reuses RCPS's format-invariant matching (§3.1), so the diagnostic judges relevance exactly as RCPS does.

### 3.3 Parser-Side Training: Auxiliary Loss and Discrete-Output DPO

When the coverage diagnostic points to the parser (§4.2), we train it on a retrieval signal in the two natural ways; only the second produces a deployable effect.

**(a) Hidden-state auxiliary loss (RADP-aux).** Jointly train the parser to produce faithful markdown (`L_parse`) and to align its answer-span hidden state with the retriever's space: $\mathcal{L}_\text{total} = \mathcal{L}_\text{parse} + \lambda\,\mathcal{L}_\text{contrast}$, where `L_contrast` is an InfoNCE between the parser's pooled answer-span hidden state and the frozen BGE-M3 embedding of the gold chunk. This is the natural *differentiable* surrogate for the non-differentiable discrete output — but the signal reaches the deployed markdown only via backflow through `L_parse`, and it is sub-threshold (§4.4).

**(b) Discrete-output DPO (RADP-DPO).** Optimize the discrete markdown directly: for each train page we sample K alternative parses from the production parser v1, score each by a **page-local RCPS**, form preference pairs (chosen = higher-RCPS parse, gap ≥ 5 pp), and train with a **LoRA-toggle reference** (π_θ = LoRA on, π_ref = LoRA off) DPO loss. The reward is sharpened across three milestones R1→R2→R3 (milestone construction, the full-corpus hard-negative pool, and the DPO loss equation are in **Appendix A**). As a control, reference-free SimPO (β=2.0, γ=1.0) removes the reference policy entirely; it is negative across all cells (§4.4), confirming the reference anchoring is doing real work.

**(c) Reward-agnostic control (RADP-Distill).** To test whether the *retrieval reward* in (b) is necessary, we instantiate the identical best-of-K pipeline — same K=14 v1 candidate pool, same LoRA-toggle DPO loss, same β/lr/seed — but rank candidates by **character-level edit-distance to the ground-truth markdown** instead of page-local RCPS. This isolates the selection signal: if RADP-Distill matches RADP-DPO, the retrieval reward adds nothing over plain fidelity distillation (§4.4a, §4.5).

## 4 Experiments

### 4.1 Setup

We construct **KoGovDoc-RAG**: 663 Q-A pairs over 294 pages of Korean government documents, generated with GPT-5.4 and verified with an LLM-as-judge stratified sample (94/100 accept). For RADP-aux's full-scale training, we additionally generate 6,164 GPT-5.4 Q-A on the 2,667-page v1 train set. Cross-domain replication uses **OHR-Bench** (Law + Manual, 1,043 verbatim-answerable Q-A) across the three released parser outputs (gt, MinerU, Qwen2.5-VL) plus twelve controlled noise perturbations.

**Eval folds.** RADP-aux is evaluated on the 73-page held-out fold (202 Q-A) of KoGovDoc-RAG. RADP-DPO/SimPO and the §4.5 mechanism analysis use the *combined* 242-page fold (train ∪ eval, 663 Q-A) of KoGovDoc-RAG. The combined fold is appropriate for the DPO comparison because the DPO preference pairs are constructed from parses on the 169-page train fold but the v1 production parser is held fixed; evaluating both on the union therefore measures system-level differences without favouring either. All parses for the 12-variant comparison in §4.4-§4.5 are regenerated with HuggingFace `transformers` deterministic decoding (temperature 0.0, max_tokens 1536) for fair like-for-like comparison.

We fine-tune Qwen3-VL-2B-Instruct with LoRA (r = 8, α = 32) on the full v1 train set (2,667 pages) for RADP-aux. For RADP-DPO/SimPO we LoRA-fine-tune the production parser v1 checkpoint on the preference pairs described in §3.3. We sweep RADP-aux λ ∈ {0.0, 0.1, 0.3, 0.5}, with λ = 0 acting as a matched control (identical training, contrastive off; reproduces the production parser v1). All RCPS values use the three retrievers (BGE-M3, multilingual-e5-large, Qwen3-Embedding-8B) and three cutoffs (k ∈ {1, 5, 10}) defined in §3.1. We report paired percentile bootstrap 95% confidence intervals (N = 1000 resamples), resampling Q-A indices with replacement and preserving the indices across systems so deltas inherit the pairing.

### 4.2 The Parsing–Retrieval Disconnect and Coverage Diagnostic (C1–C2)

**Korean government documents (Table 1).** RCPS spans 0.07–0.58 across the six parsers. The VLM-family parsers cluster at the top (0.53–0.58); the OCR systems trail (0.07–0.21). Crucially, the intrinsic Boundary Clarity metric (MoC) anti-correlates with RCPS at **Pearson r = −0.81** (n = 5, excluding the 38-page Marker subset). MinerU, the cleanest-boundary parser (BC = 0.72), retrieves worst (RCPS = 0.21). MoC's companion intrinsic metric, Chunk Stickiness, is similarly disconnected from retrieval (Pearson r = +0.26, n = 5 — a positive sign by convention, but with CS oriented so that *lower* indicates more cohesive chunks, this is the same direction as BC: more cohesive intrinsic structure tracks *worse* retrieval). Neither intrinsic axis predicts RCPS.

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

**Cross-domain — the mechanism (Figure 2, Table 2).** On OHR-Bench's Law and Manual domains (1,043 verbatim-answerable Q-A; consistent with §4.1), we evaluate 15 parser-output variants: the three released parser outputs (gt, MinerU, Qwen2.5-VL), three formatting-noise perturbations, and nine semantic-noise perturbations (GOT/MinerU/Qwen2.5-VL × mild/moderate/severe).

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

**Locating the gap — parser or chunker? (coverage diagnostic, Table 2b).** The disconnect shows intrinsic metrics mislead, but not *which pipeline layer* is at fault. We separate them with no retriever at all, applying the §3.2 covered/split/absent classification: on v1's output (294 pages, 663 Q-A), **20.2 % of answers are absent and only 0–2 % are split**, with the absent rate *constant across all eight chunkers* (boundary-independent, as a parser fault must be). The parsing–retrieval gap is therefore a **parser** problem, not a chunking one: one answer in five is never produced, so no re-chunking can recover it and a parser-side intervention is the correct lever. This both motivates the parser-side training in §4.4 and yields a practitioner rule — run this diagnostic first: if `absent` dominates, fix the parser; if `split` dominates, fix the chunker.

| Chunker | covered | split (chunker fault) | absent (parser fault) |
|---|:---:|:---:|:---:|
| md_h3 | 79.8% | 0.0% | 20.2% |
| parser_native | 78.1% | 1.7% | 20.2% |
| fixed500_ov200 | 79.8% | 0.0% | 20.2% |

*Table 2b: Answer-coverage diagnostic on the v1 parser output (294 pages, 663 KoGov Q-A; pure text matching, no retriever). `absent` (parser fault — answer never produced) is constant at 20.2 % across all eight chunkers tested (boundary-independent, the required sanity check); `split` (chunker fault — answer cut by a boundary) is ≤ 2 % and vanishes under overlap. The parsing–retrieval gap is overwhelmingly a parser problem, which is what licenses the parser-side intervention in §4.4.*

### 4.3 RCPS Selects Both Parsers and Chunkers (C3)

A selection protocol must separate the alternatives a practitioner actually compares — across *both* knobs they control, the parser and the chunker. **Parsers:** the 6-parser grid of §4.2 (Table 1) *is* an RCPS ranking — it is what tells a team that v1 (RCPS 0.583, Hit@1 0.55) beats MinerU (0.21, 0.20) by 2.8×, the ordering Boundary Clarity inverts. **Chunkers:** on a fixed parser output (Table 3), RCPS separates four strategies cleanly — markdown-header (md-h3) > parser-native > LumberChunker (LLM-narrative) > fixed-size — whereas intrinsic boundary metrics would rank them inconsistently, or rank fixed-size *highest* (cleanest boundaries by construction). In both cases RCPS captures *retrievability*, not surface appearance; and because it is retriever-averaged and format-invariant (§3.1), one ~500-Q-A probe ranks the parser choice and the chunker choice a team makes independently. This is the operational core of C3 — one cheap protocol for the two parser-side decisions that standard metrics get wrong.

| Chunker | RCPS | Hit@1 | MRR@10 |
|---|:---:|:---:|:---:|
| md-h3 | **0.593** | 0.556 | 0.613 |
| parser_native | 0.583 | 0.549 | 0.602 |
| LumberChunker | 0.557 | 0.514 | 0.580 |
| fixed500 | 0.535 | 0.491 | 0.560 |
*Table 3: KoGov chunking-strategy grid (663 Q-A, v1 parser output, 3-retriever RCPS average).*

**RCPS is not plain MRR — the protocol choices change the ranking (Table 3b).** RCPS wraps MRR in three choices (§3.1); stripping them on the 6-parser KoGov grid shows they are not cosmetic. Dropping retriever-averaging — scoring on a single embedder (BGE-M3) — **inverts the top parser choice**: naive single-embedder MRR ranks WigtnOCR-2B first, while full RCPS ranks the Qwen3-VL-30B teacher first (rows A, C vs D). Format-invariant matching, by contrast, shifts every parser's RCPS by ≈ 0.02–0.03 but does not reorder the grid here (row B vs D). The inversion is between two near-tied parsers (RCPS 0.584 vs 0.583), so the operational claim is precise: **single-embedder MRR cannot reliably resolve the top parser a team would actually deploy** — exactly the decision RCPS is run to make. The naive-vs-RCPS ordering disagreement (Kendall τ = 0.87) substantiates §3.1's claim that RCPS is a protocol, not a relabelled MRR.

| Row | Protocol (retrievers × relevance) | Parser ranking (best → worst) | Inv. vs RCPS | Kendall τ |
|---|---|---|:---:|:---:|
| A | naive MRR: BGE-M3 only × format-sensitive | **WigtnOCR-2B** ≻ Qwen3-VL-30B ≻ Qwen3-VL-2B ≻ MinerU ≻ PaddleOCR ≻ Marker | 1 | 0.87 |
| B | + retriever-averaging: 3-retriever × format-sensitive | Qwen3-VL-30B ≻ WigtnOCR-2B ≻ Qwen3-VL-2B ≻ MinerU ≻ PaddleOCR ≻ Marker | 0 | 1.00 |
| C | + format-invariant only: BGE-M3 only × format-invariant | **WigtnOCR-2B** ≻ Qwen3-VL-30B ≻ Qwen3-VL-2B ≻ MinerU ≻ PaddleOCR ≻ Marker | 1 | 0.87 |
| D | **Full RCPS**: 3-retriever × format-invariant | Qwen3-VL-30B ≻ WigtnOCR-2B ≻ Qwen3-VL-2B ≻ MinerU ≻ PaddleOCR ≻ Marker | — (ref) | 1.00 |
*Table 3b: RCPS protocol ablation on the KoGov 6-parser grid (RCPS = mean MRR@{1,5,10}). The single protocol choice that reorders the grid is retriever-averaging (rows A, C invert the top pair vs D); format-invariance shifts scores but not order on this grid. Rows C, D are re-aggregations of the stored per-retriever scores; rows A, B re-index under format-sensitive relevance. Script: `scripts/evaluation/rcps_protocol_ablation.py`; data: `output/results/rcps_protocol_ablation.json`.*

### 4.4 Parser-Side Training: A Bounded, Reward-Agnostic Lever (C4)

The coverage diagnostic (§4.2) has already licensed this step: with 20 % of answers *absent* from the parser output and almost none merely *split*, the gap is a parser problem, so a parser-side fix is the right lever (a chunker-side fix could only ever recover the ≤ 2 % split mass). We test both natural directions — the hidden-state aux-loss (RADP-aux, §3.3a) and the discrete-output retrieval-reward DPO (RADP-DPO/SimPO, §3.3) — and only the discrete-output route produces a deployable effect.

**Headline: RADP-Distill ≥ RADP-DPO on both folds (Table 5b).** Discrete-output preference training gives a small, directional KoGov gain that the pre-specified cross-domain OHR-Bench confirms. On the 242-page / 663-Q-A KoGov fold the RADP-DPO milestones improve Hit@5 on parser_native over v1 by +1.96 to +2.11 pp (all P[Δ>0] ≈ 0.90); **at n = 663 every two-sided CI spans zero**, so we treat KoGov as *exploratory* — the reported cell was chosen from a multi-cell scan over (chunker × retriever × k) and establishes *direction* only (KoGov progression and the SimPO control are in **Appendix B**, Table 5). The confirmatory test is the pre-specified cross-domain OHR-Bench replication (2,264 verbatim-answerable Q-A over seven English domains, where the Korean→English shift also tests generalisation): the headline retrieval-reward variant **R2 (RADP-DPO-v4)** — whose mechanism §4.5 isolates — gives Hit@5 **+0.85 pp [+0.35, +1.43]**, two-sided significant, positive across all seven domains; the more-aggressive R3 reaches **+1.03 pp [+0.24, +1.84]** (Hit@1 +1.31 pp [+0.55, +2.09]) but, as §4.5 shows, without a matching per-page fidelity gain, so R2 is the representative retrieval-reward variant. Crucially, the **reward-agnostic RADP-Distill control matches or exceeds RADP-DPO on both folds** (Table 5b, §4.4a). The gain is causal for parser-side *training* — training signal, evaluation metric, and document language are mutually disjoint, ruling out metric circularity and domain over-fitting — and modest but real (~1 pp Hit@5 on every query) and retriever-agnostic. The smaller magnitude on OHR than KoGov is expected: v1's zero-shot English TextNED (0.192) already sits below its Korean TextNED (0.240), leaving less fidelity headroom (§4.5). RADP-aux is sub-threshold and SimPO is uniformly negative (**Appendix B**, Table 4); two robustness checks (held-out-retriever and factoid/tabular) are in **Appendix B**.

**§4.4a — Is the retrieval reward necessary? A best-of-K distillation control (RADP-Distill).** The §4.5 mechanism — the gain is text fidelity, not chunk boundaries — raises a sharp question: does the *retrieval* reward do anything a plain fidelity objective cannot? We test it with a matched control, **RADP-Distill**: identical to RADP-DPO in every respect (same v1 K=14 candidate pool, same LoRA-toggle DPO, β=0.1, lr, seed) except that preference pairs are ranked by **character-level edit-distance to the ground-truth markdown** instead of page-local RCPS — the retrieval reward is removed, only the selection signal changes. RADP-Distill *matches or exceeds* RADP-DPO on **both** folds and both metrics: OHR-Bench Hit@5 **+1.22 pp [+0.35, +2.15]** (vs RADP-DPO's +0.85 pp; n = 2,264, two-sided significant), and on KoGov both Hit@5 **+2.61 pp [−0.35, +5.68]** (P[Δ>0] = 0.95, vs RADP-DPO's +1.96; exploratory, CI spans zero) and RCPS **0.600** (vs RADP-DPO 0.590, v1 0.586). Across every cell RADP-Distill's point estimate is equal-or-higher; the two are statistically indistinguishable on the powered OHR fold. **The retrieval reward therefore buys nothing over plain fidelity distillation** — it is one (more expensive) way to obtain a target that edit-distance-to-ground-truth supplies directly. This is the controlled-ablation evidence for the §4.5 self-distillation reading, and a cost-saving result for practitioners: the parser-side lever is best-of-K distillation toward clean ground-truth text, not a retrieval-reward pipeline.

| Δ vs v1 (pp) | Hit@1 | Hit@5 | Hit@10 | MRR@10 | nDCG@5 |
|---|:---:|:---:|:---:|:---:|:---:|
| **RADP-Distill** — headline | **+0.88** | **+1.22** | **+1.32** | **+1.01** | **+1.05** |
| RADP-DPO-v4 (R2, retrieval reward) | +0.53 | +0.85 | +0.81 | +0.70 | +0.74 |
| RADP-DPO-v5 (R3, hard-neg) | +1.31 | +1.03 | +0.81 | +1.17 | +1.15 |

*Table 5b: OHR-Bench cross-domain Δ vs v1, in pp (2,264 verbatim-answerable Q-A over 7 English domains; three-retriever macro; 1,000-resample paired bootstrap). Every cell is two-sided significant (95% CI excludes 0; e.g. R2 Hit@5 [+0.35, +1.43], R3 Hit@5 [+0.24, +1.84]). Hit@k, MRR@k, and nDCG@k are monotone functions of the same retrieved ranking, **not independent endpoints** — we report them only because practitioners use different ones. The headline is **RADP-Distill** — a best-of-K control that ranks candidates by edit-distance-to-GT with no retrieval reward — at Hit@5 **+1.22 pp**; the retrieval-reward route (RADP-DPO-v4/R2 +0.85; R3 +1.03) reproduces no more than this, confirming (§4.4a) that the retrieval reward is unnecessary.*
### 4.5 Mechanism: DPO Tightens Text Fidelity Without Changing Chunking Signature

**Text fidelity is the lever; the chunking signature is unchanged.** The §4.4 gain calls for a mechanism, so we measure four chunk-level statistics on the 242-page fold for all 12 systems (BC, CS, TextNED against GT markdown, and chunking shape; full grid in **Appendix C**, Table 7). The signal is text fidelity: all four RADP-DPO variants drop TextNED from v1's 0.240 to 0.163–0.182 (a 24–32% reduction toward GT), the reward-agnostic **RADP-Distill control drops it furthest of all (0.158)** while leading on retrieval (§4.4a), and the TextNED column tracks Hit@5 monotonically — the cleanest demonstration that text fidelity, not the retrieval reward, is the operative lever (RADP-aux, by contrast, *increases* TextNED to 0.318–0.626 as its hidden-state objective degrades surface text). The chunking signature does *not* move: BC for every DPO variant lands in 0.60–0.66 (v1 0.63), CS in 0.469–0.478 (v1 0.474), and chunks/page and chunk length within v1's range — so the Hit@5 gain comes from *what* is parsed, not *how* chunks are split. This is the same fact as §4.2's intrinsic-metric blindness: MoC's chunkability axes do not reach the surface property retrieval depends on. The mechanism replicates cross-domain (OHR-Bench English TextNED, R2 −1.36% two-sided significant) and the secondary patterns — factoid > tabular, larger on held-out retrievers, RADP-aux sub-threshold — all follow from text fidelity (**Appendix C**).

## 5 Discussion and Conclusion

**The headline is parser *selection*, not parser *training*.** The largest and most certain effect in this paper is not our training method — it is that **choosing a parser by retrieval (RCPS) instead of by intrinsic metrics changes Hit@1 by 2.8×** (§4.2). A team that takes only the RCPS protocol from this paper already avoids shipping the parser that looks best (MinerU, BC = 0.72) and retrieves worst. Parser-side training — best-of-K fidelity distillation toward clean GT text — is a secondary, bounded lever (~1 pp Hit@5) on top of an already-good parser; the retrieval-reward apparatus (RADP-DPO) buys nothing over it (§4.4a).

**Reconciling C1 with the mechanism — formatting-clean ≠ content-faithful.** C1 says the *cleanest-boundary* parser retrieves worst; §4.5 says DPO wins partly by producing text *closer* to ground truth. These are consistent once "clean" is split into two axes: Boundary Clarity measures *formatting* cleanliness (how crisp the chunk edges look), while TextNED measures *content* fidelity (does the parsed text actually contain the answer span). MinerU is formatting-clean but loses content; RADP-DPO leaves the formatting/boundary signature unchanged (BC ≈ v1) and improves content fidelity. Intrinsic boundary metrics see only the first axis — which is exactly why they mispredict retrieval.

**The original hypothesis, refined.** We began expecting parser-side training to move chunk *boundaries* from human-friendly to retrieval-friendly. The data do not confirm that: the chunking signature (BC, CS, chunks/page) is essentially unchanged. What moves is text fidelity. We therefore report text fidelity as the operative mechanism — a post-hoc explanation we had pre-registered as a possibility — and treat the boundary-shift hypothesis as **not confirmed**, an honest negative nested inside the positive C4. Seen this way, RADP-DPO is best understood as *best-of-K rejection-sampling self-distillation* — and the **RADP-Distill control (§4.4a) confirms this directly**: replacing the retrieval reward with edit-distance-to-ground-truth as the selection signal reproduces the gain, so the retrieval reward was merely selecting whichever candidate parse already lands closest to the ground-truth text (sampled from v1 itself; Limitations), which DPO then amortises into the weights. The gain is the parser learning to emit by default the higher-fidelity outputs it could already occasionally produce — not the acquisition of a new retrieval-aware chunking capability. This reframing is *consistent* with the modest, fidelity-bounded effect size we observe, and sets the expectation for practitioners (§5).

**Where the parser-side lever is and isn't.** A boundary on the design space emerges from §4.4 and Appendix B: only the *discrete-output preference* formulation works (the retrieval signal reaches the exact surface tokens the retriever rewards), while the *hidden-state aux-loss* (RADP-aux) is sub-threshold and *reference-free* SimPO is uniformly negative. The three results jointly locate the working parameterisation: (a) discrete output, (b) preference loss with reference anchoring, (c) candidate pool sampled from the production parser itself.

**A decision playbook for document-RAG teams.**

1. **Evaluate parsers with RCPS, never intrinsic metrics alone.** A few hundred domain-representative held-out Q-A, scored with **no training**, reorder parsers in the way the downstream retriever actually sees — on our data, a 0.20 → 0.55 Hit@1 decision. This is the single highest-leverage takeaway.
2. **If you train the parser, use discrete-output retrieval-reward DPO — and only that.** The hidden-state auxiliary loss and reference-free SimPO are both sub-threshold. Expect a *modest* return — on the order of +1 pp Hit@5 cross-domain, two-sided significant, and transferring to the retriever you actually deploy (it is largest on retrievers *not* used for preference scoring; Appendix B) — not a breakthrough.
3. **Spend the budget where text precision drives retrieval.** RADP-DPO helps most on factoid queries and is roughly neutral on structural/tabular ones; teams with layout-heavy query mixes should expect little from parser-side training and look to the chunker or embedder instead.

**Conclusion.** We documented the parsing–retrieval disconnect in two languages and document types (Korean government, English enterprise), proposed **RCPS** — a cheap, retriever-agnostic *protocol* for selecting parsers and chunkers by retrieval rather than by appearance — and mapped what parser-side training can and cannot add on top. Hidden-state auxiliary loss and reference-free SimPO fail; discrete-output preference training gives a modest, cross-domain-significant gain (OHR-Bench +0.85 pp two-sided significant), but a matched edit-distance control (RADP-Distill) reproduces it (+1.22 pp), so the gain is parser-to-GT **fidelity distillation**, not a retrieval-reward effect — it tightens text fidelity, not chunk boundaries. The practical contribution is a decision procedure: *evaluate parsers with RCPS, and if you train, distill the discrete output toward clean ground-truth text — a retrieval reward is unnecessary.* Code, data, and checkpoints are released.

---

## Released artifacts

- **KoGovDoc-RAG** — 663 Q-A on 294 Korean government document pages.
- **RCPS reference implementation** — `src/wigtnocr_radp/evaluation/`.
- **RADP-Distill checkpoint** — Qwen3-VL-2B-Instruct + LoRA; the **recommended deployable parser-side lever** (§4.4a): best-of-K preference training with candidates ranked by edit-distance-to-GT, no retrieval reward.
- **RADP-aux checkpoints (4)** — Qwen3-VL-2B-Instruct + LoRA, fine-tuned on the 2,667-page v1 train set with λ ∈ {0, 0.1, 0.3, 0.5}.
- **RADP-DPO checkpoints (R1–R3) + SimPO control** *(the controlled-against retrieval-reward route, §4.4a — released for reproducibility; RADP-Distill above is the recommended recipe)* — Qwen3-VL-2B-Instruct + LoRA, retrieval-reward preference learning: **R1** (DPO-v1, page-local BGE scoring, β=0.1), **R2** (DPO-v4, warmstart multi-round, β=0.05), **R3** (DPO-v5, full-corpus hard-negative reward, K=14). Sub-threshold variants (DPO-v2 three-retriever, DPO-v3 curriculum, seed replicates) and the SimPO control (β=2.0, γ=1.0) are released as supplementary.
- **OHR-Bench cross-domain results** — 15-variant RCPS + Boundary Clarity correlation.
- **Mechanism analysis data** — BC, CS, TextNED, chunking shape on 12 systems × 242 pages (`output/results/mechanism_242p.json`, `output/results/cs_242p.json`).

## Limitations

- **Single primary language.** The C1 diagnostic is strongest in Korean (n = 5, r = −0.81). The English cross-domain replication on OHR-Bench is directionally consistent but weaker in magnitude (n = 15, r = −0.35), and is built on three real parser outputs plus twelve controlled noise perturbations rather than fifteen independent real parsers. Multi-language generalisation beyond Korean and English remains future work.
- **Statistical power.** With n = 5 (Korean grid) and n = 15 (OHR-Bench), our correlations are illustrative rather than inferential — they support a directional finding that future work can extend by enlarging the parser pool.
- **Q-A generation and construct validity.** The KoGov Q-A (663 eval + 6,164 train) were produced by GPT-5.4 and verified by LLM-as-judge against the human-curated GT markdown (100 stratified eval Q-A sampled for verification, 94/100 accept; pure human verification at train-set scale was cost-prohibitive). Synthetic queries bound what RCPS can claim, but the exposure is narrower than it first appears. First, our *comparative* findings — the 2.8× parser-choice swing (§4.2) and every parser/chunker ranking — hold the Q-A set fixed across systems, so they are internally valid regardless of how the queries were generated; only an *absolute* claim that RCPS is the uniquely right protocol leans on query realism. Second, the confirmatory cross-domain test (§4.4) is run on **OHR-Bench's own externally-curated Q-A**, not our GPT-generated set, giving the C4 result a non-self-generated anchor. We froze and released the KoGov eval set so future evaluators can audit it.
- **KoGov effect is exploratory; OHR-Bench is the confirmatory test.** The headline KoGov cell (R2 +1.96 pp Hit@5, Table 5) has a paired 95% CI of [−1.06, +5.03] — two-sided non-significant, and selected from a multi-cell scan (§4.4) — so we report it as exploratory and claim no two-sided significance on KoGov. The confirmatory evidence is the pre-specified cross-domain OHR-Bench replication, where the headline R2 is two-sided significant (+0.85 pp [+0.35, +1.43], n = 2,264) and the more-aggressive R3 reaches +1.03 pp [+0.24, +1.84]. A larger KoGov eval fold (≥ 1,500 Q-A) would be needed for a powered two-sided KoGov result; that scaling is the natural next experiment.
- **DPO candidate pool drawn from the production parser only.** Our preference pairs are constructed by sampling K alternatives from the production parser v1 itself (K=2 at temperatures {0.7, 1.2} for R1; K=14 at temperatures 0.3–2.0 for R3). This anchors the LoRA-toggle reference trick (§3.3) and produces the §4.5 GT-fidelity mechanism. An alternative candidate pool — for example, alternative parsers (MinerU, GOT, Qwen3-VL-30B teacher) producing the chosen/rejected pairs — would give the parser exposure to off-distribution candidates and may shift the mechanism away from GT-fidelity toward novel-style chunking. We did not test this.
- **Eval fold sizes.** RADP-aux uses the 73-page / 202-Q-A held-out fold for backward comparability with Table 4's pre-registered protocol. RADP-DPO/SimPO and the mechanism analysis use the 242-page / 663-Q-A combined fold. The 5 pp gate against RADP-aux remains a conservative bar in absolute terms at the smaller fold; the 242-page DPO comparison has CIs of ±2.5–3 pp width, well-matched to detecting a +2 pp effect at one-sided P ≈ 0.90 but tight for two-sided sig.
- **Alternative parser-side paradigms not exhausted.** We test the hidden-state aux-loss (RADP-aux), discrete-output DPO with a reference policy (RADP-DPO), and reference-free SimPO. We do not test token-level RL with a per-token retrieval signal, multi-task training that interleaves retrieval and parsing objectives at the data-mix level, curriculum schedules that anneal `L_parse` weight over training, or distillation from an oracle parser at chunk granularity. The §4.5 mechanism argument suggests these would land in regimes similar to the ones we test, but the empirical question is open.
- **Chunker, embedder, retriever-side training (future work).** RADP-DPO is a parser-layer intervention. The complementary layers — chunker (retrieval-reward boundary selection on the parser's output), embedder (contrastive training of the dense retriever on RCPS-graded chunks), and retriever (reranker on the parser's chunk pool) — are not addressed and would each be an independent research thread. Comparing the parser-layer +2 pp ceiling we report against gains achievable at each downstream layer would localise the dominant retrieval-improvement mechanism in document-RAG pipelines.

## Appendix

### Appendix A — RADP-DPO milestone construction (detail for §3.3b)

**Milestone construction (R1→R2→R3).** For each train page we sample K alternative parses from the production parser v1, chunk and score each by a **page-local RCPS** (the page's questions against the parse's own chunks plus distractors), and form preference pairs (chosen = higher-RCPS parse, gap ≥ 5 pp). The reward is sharpened across three milestones (Table 5): **R1** (K=2 parses, uniform distractors, β=0.1) → **R2** (warmstarted iterative round, β=0.05) → **R3** (K=14 parses with a **full-corpus hard-negative** pool — the other-page chunks closest to the page's queries — widening the candidate-score gap from ≈0.05 to 0.56).

**LoRA-toggle reference and DPO loss.** We train with a **LoRA-toggle reference** (π_θ = parser with LoRA on, π_ref = LoRA off):

$$\mathcal{L}_\text{DPO} = -\log \sigma\Big(\beta \big[(\log \pi_\theta(c) - \log \pi_\theta(r)) - (\log \pi_\text{ref}(c) - \log \pi_\text{ref}(r))\big]\Big).$$

The reference-free SimPO control (β=2.0, γ=1.0) removes the reference policy entirely.

### Appendix B — KoGov DPO progression, RADP-aux sweep, SimPO, and robustness (detail for §4.4)

**KoGov milestone progression and SimPO control (Table 5).** On the 242-page / 663-Q-A KoGov fold (10,000-resample paired bootstrap), the three RADP-DPO milestones improve Hit@5 on parser_native over v1 along the reward-sharpening axis: R1 +2.06 pp [−0.96, +5.13], R2 +1.96 pp [−1.06, +5.03], R3 +2.1 pp (all P[Δ>0] ≈ 0.90). At n = 663 every two-sided CI spans zero, so we treat these KoGov numbers as exploratory: the Hit@5 / parser_native cell was selected from a multi-cell scan over (chunker × retriever × k), with no family-wise correction applied to a chosen cell. Consistent with the mechanism (DPO tightens text fidelity, §4.5), the DPO parser also lowers the absent rate slightly (20.2 % → 19.3 % on its 242-page output), recovering some parser-fault mass (a same-page comparison is left to future work).

| Variant | Hit@5 v1 = 0.6863 | ΔHit@5 vs v1 (pp) [95% CI] | P[Δ>0] | ΔHit@10 (pp) | ΔRCPS (pp) |
|---|:---:|:---:|:---:|:---:|:---:|
| **RADP-Distill** — headline † | 0.702 † | **+2.61 [−0.35, +5.68]** | **0.954** 🔶 | +2.71 (P=0.96) 🔶 | +1.45 |
| **RADP-DPO-v5** (R3, hard-neg) | 0.7074 | **+2.11 [−0.96, +5.13]** | **0.913** 🔶 | +2.21 (P=0.926) 🔶 | +1.72 |
| **RADP-DPO-v1** (R1, BGE β=0.1) | 0.7069 | **+2.06 [−0.96, +5.13]** | **0.907** 🔶 | +1.81 (P=0.877) 🔶 | +0.57 |
| **RADP-DPO-v4** (R2, warmstart β=0.05) | 0.7059 | **+1.96 [−1.06, +5.03]** | **0.897** 🔶 | +1.71 (P=0.863) 🔶 | +0.47 |
| RADP-SimPO (ref-free ctrl) | 0.6793 | −0.70 [−3.77, +2.31] | 0.321 | −0.96 | −1.56 |

*Table 5: RADP-DPO progression and the SimPO control on parser_native chunking, 242-page / 663-Q-A combined fold, 10k paired percentile bootstrap. Macro Hit@k averages BGE-M3, multilingual-e5-large, and Qwen3-Embedding-8B with relevance per §3.1. The top row is **RADP-Distill**, the reward-agnostic headline (KoGov ΔHit@5 **+2.61 pp** ≥ RADP-DPO's +1.96); its confirmatory result is the powered OHR-Bench fold (Table 5b, +1.22 pp). **This KoGov fold is exploratory** — every two-sided CI spans zero (§4.4). **† RADP-Distill and the RADP-DPO-v4 reference are computed on the §4.4a eval run (v1 KoGov Hit@5 = 0.676), on which RADP-DPO-v4 reproduces +1.96 pp; the milestone rows below use an earlier 10k-bootstrap run (v1 = 0.6863), so absolute Hit@5 differs by run while ΔHit@5 is directly comparable.** 🔶 = P[Δ>0] ≥ 0.85 (strong directional positive). RADP-SimPO is the reference-free negative control (§4.4). Per-seed variance is small: across three v1 seeds the standard deviation of the mean ΔHit@5 is 0.90 pp, and a 3-seed merge tightens R1 to +1.16 pp [−0.64, +2.90] (P = 0.90). Sub-threshold hyperparameter variants (three-retriever scoring, curriculum schedule) are released as supplementary.*

**RADP-aux (hidden-state) is sub-threshold (Table 4).** The auxiliary loss peaks at λ = 0.1 (+1–2 pp RCPS) then declines monotonically as the contrastive objective competes with `L_parse` over the same LoRA parameters; every Δ-vs-control CI includes zero and the one-sided P[Δ>0] never approaches 0.90. The hidden-state route does not reach the deployed markdown — only the discrete output (DPO) does.

**SimPO is negative.** The reference-free length-normalised variant produces uniformly negative deltas (−0.7 to −1.7 pp Hit@5 across cells; Table 5 last row), suggesting the reference policy in DPO's loss is doing real work — without it, the parser drifts away from the production-parser distribution before any preference signal can compound. The retrieval-reward signal must enter (a) through the *discrete output* and (b) anchored to the production parser via a reference policy to produce the C4 positive.

**Robustness checks (full grid as supplementary).** The OHR-Bench gain survives two checks. It is *equal-or-larger on the two retrievers held out from preference scoring* (ml-e5-large +2.4 pp, Qwen3-Emb +2.3 pp, vs the BGE-M3 scorer +1.5 pp), ruling out a BGE-overfit artifact; and it concentrates on **factoid** queries (+3.1 pp — where verbatim answer-span text drives retrieval) while neutral-to-slightly-negative on tabular ones (structural layout), consistent with the text-fidelity mechanism (§4.5).

### Appendix C — Chunk-level mechanism statistics and sub-analyses (detail for §4.5)

We measure four chunk-level statistics on the 242-page fold for all 12 systems (v1, four RADP-aux λ, four RADP-DPO, SimPO, two DPO-v1 seeds), plus the R3 (DPO-v5) variant reported alongside for the headline-vs-mechanism check (Table 7): MoC Boundary Clarity (BC, adjacent-chunk discontinuity), MoC Chunk Stickiness (CS, within-chunk cohesion), normalised edit distance (character-level Levenshtein distance ÷ longer-string length) against the ground-truth markdown (TextNED), and chunking shape (parse length, chunks/page, mean chunk length).

| Variant | parse_len | chunks/page | chunk_len | BC ↑ | CS ↓ | TextNED ↓ vs GT |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| v1 (ref) | 1385 | 4.82 | 274 | 0.630 | 0.474 | 0.240 |
| **RADP-Distill** | 1597 | 5.29 | 291 | 0.641 | — | **0.158** |
| RADP-aux λ=0.0 | 799 | 2.96 | 245 | 0.553 | 0.473 | 0.626 |
| RADP-aux λ=0.1 | 1380 | 4.05 | 321 | 0.652 | 0.484 | 0.423 |
| RADP-aux λ=0.3 | 1930 | 6.73 | 272 | 0.470 | 0.475 | 0.332 |
| RADP-aux λ=0.5 | 2035 | 5.82 | 327 | 0.556 | 0.470 | 0.318 |
| **RADP-DPO-v1** | 1606 | 4.97 | 311 | 0.646 | 0.474 | **0.167** |
| RADP-DPO-v2 | 1594 | 5.06 | 304 | 0.648 | 0.475 | 0.168 |
| RADP-DPO-v3 | 1689 | 5.27 | 304 | 0.601 | 0.469 | 0.182 |
| **RADP-DPO-v4** (headline R2) | 1610 | 4.83 | 321 | 0.647 | 0.476 | **0.163** |
| RADP-DPO-v5 (R3) | 1514 | 4.88 | 300 | 0.656 | 0.485 | 0.185 |
| RADP-SimPO | 1703 | 5.31 | 305 | 0.601 | 0.470 | 0.186 |
| DPO-v1-seed123 | 1633 | 4.92 | 320 | 0.655 | 0.476 | 0.171 |
| DPO-v1-seed999 | 1620 | 4.69 | 332 | 0.654 | 0.478 | 0.174 |
*Table 7: Chunk-level mechanism statistics on the 242-page combined fold. BC is the mean MoC Boundary Clarity across all adjacent-chunk pairs scored by Qwen3-VL-2B perplexity (3,167–5,144 boundaries per variant). CS is the within-chunk-cohesion equivalent (head→tail conditional perplexity ratio) over 593–1,288 chunks per variant on the same LM. TextNED is per-page mean normalised edit distance against the human-curated GT markdown. The reward-agnostic control **RADP-Distill** achieves the **lowest TextNED of all (0.158** < R2's 0.163 < v1's 0.240) with an unchanged BC (0.641, within the v1 range) — directly confirming text fidelity, not chunk structure, is the operative axis (CS not measured for RADP-Distill). Among retrieval-reward variants, R2 (DPO-v4) has the lowest TextNED (0.163); the more-aggressive **R3 (DPO-v5)** is included for the headline-vs-mechanism check — its BC (0.656) and CS (0.485) likewise stay within the variant spread (v1 BC 0.630 / CS 0.474), but its KoGov TextNED (0.185) does not beat R2, which is why R2 is the headline — so neither chunking-signature axis distinguishes R3 from v1, only text fidelity moves.*

**The signal — DPO tightens text fidelity to GT.** All four RADP-DPO variants drop TextNED from v1's 0.240 to 0.163–0.182 — a 24–32% reduction toward the human-curated ground-truth markdown. The two replicating positive variants (DPO-v1, DPO-v4) achieve the largest reductions (0.167, 0.163). RADP-aux, by contrast, *increases* TextNED (0.318–0.626) because its hidden-state objective competes with `L_parse` and degrades surface text quality. The TextNED column tracks the Hit@5 column monotonically: the variants that reduce TextNED the most are the variants with the largest Hit@5 gains — and the reward-agnostic **RADP-Distill control drops TextNED furthest of all (0.158)** while leading on retrieval (§4.4a), the cleanest demonstration that text fidelity, not the retrieval reward, is the operative lever.

**The text-fidelity mechanism replicates cross-domain.** To test whether this mechanism generalises beyond Korean, we measure TextNED against OHR-Bench GT on all 4,040 English pages. The zero-shot v1 parser already reaches TextNED 0.192 — below its 0.240 on Korean — confirming English documents leave less fidelity headroom. The **headline variant R2 (RADP-DPO-v4)** reduces it to 0.189 (−1.36%, 95% CI [−0.0043, −0.0010], two-sided significant), and on KoGov its reduction is the largest of all variants (TextNED 0.240 → **0.163**, Table 7) — so the mechanism is measured *on the headline variant itself*: lower TextNED tracks higher retrieval. The more aggressive R3 (RADP-DPO-v5) pushes the OHR TextNED marginally lower still (0.184) yet does **not** improve KoGov text fidelity (Table 7: v5 0.185 > v4 0.163) — its harder full-corpus reward broadens the cross-domain effect more than it sharpens per-page fidelity, which is why we keep R2 as the headline and report R3 as a more-aggressive variant. Chunk shape shifts only marginally (chunks/page −3.2%, chunk length +3.7%), reaffirming text fidelity — not chunk restructuring — as the operative lever; R3's BC (0.656, Table 7) likewise stays within v1's range, so neither variant alters the chunking signature.

**The non-signal — the MoC chunking signature is unchanged on both axes.** BC for all four RADP-DPO variants lands in 0.60–0.66, statistically the same as v1's 0.63. CS (within-chunk cohesion) is even tighter: every DPO/SimPO variant lands in **0.469–0.478, indistinguishable from v1's 0.474** (the spread across all 12 systems including RADP-aux is only 0.470–0.484). Chunks per page (4.69–5.27) and mean chunk length (304–332) are also within v1's range (4.82, 274). RADP-DPO does *not* produce a novel "AI-friendly" chunking signature that a human reader would call out as different — both axes of the MoC framework (between-chunk discontinuity *and* within-chunk cohesion) are unchanged from the production parser, as is the chunking shape. This rules out a chunking-style explanation for the gain: it comes from *what* is parsed, not *how* the chunks are split. The intrinsic-metric blindness documented in §4.2 (BC anti-correlates with retrieval) and the §4.5 finding (CS, BC, chunk shape all invariant under DPO while retrieval moves) are two faces of the same fact: MoC's chunkability axes do not reach the surface property that retrieval depends on.

**Why factoid, why held-out, why aux fails.** Three secondary patterns all follow from text fidelity. The gain concentrates on **factoid** queries — fidelity tightening helps exactly where the verbatim answer span must land inside a chunk — and is neutral on tabular ones (structural, not text, fidelity). It is *larger* on the retrievers held out from preference scoring (ml-e5-large, Qwen3-Emb) than on the BGE-M3 scorer: v1's text was already BGE-aligned, so the fidelity gain has more room elsewhere — confirming a parser-level effect, not a BGE-overfit. And **RADP-aux** stays sub-threshold because its hidden-state signal reaches the deployed markdown only via diffuse `L_parse` backflow, never localising to the surface tokens the retriever rewards — the boundary that makes *discrete-output* DPO the parameterisation that works.

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
- `2025rpo` RPO (2025, arXiv:2501.13726). — preference optimization on the generator, parallel paradigm to our RADP-DPO on the parser.

**Preference learning (RADP-DPO §3.3).**
- `rafailov2023dpo` Rafailov et al. *Direct Preference Optimization: Your Language Model is Secretly a Reward Model* (NeurIPS 2023, arXiv:2305.18290).
- `meng2024simpo` Meng et al. *SimPO: Simple Preference Optimization with a Reference-Free Reward* (NeurIPS 2024, arXiv:2405.14734).
- `hu2021lora` Hu et al. *LoRA: Low-Rank Adaptation of Large Language Models* (ICLR 2022, arXiv:2106.09685). — LoRA-toggle reference trick (§3.3).

**Foundations cited.**
- `chen2024bgem3` Chen et al. *BGE-M3* (2024, arXiv:2402.03216). — frozen retriever.
- `qwen3vl` Qwen3-VL (Alibaba). — parser backbone (v1 + RADP).
- `faysse2024colpali` Faysse et al. *ColPali* (ICLR 2025, arXiv:2407.01449). — alternative paradigm citation.
- `mineru2025` MinerU 2.5 (2025). — OCR baseline.
- `omnidocbench2025` OmniDocBench (CVPR 2025). — parsing baseline cited via WigtnOCR v1's prior results.

**Our prior assets.**
- `wigtn-kogovdoc-bench` Wigtn. *KoGovDoc-Bench* (HuggingFace dataset, 2026).
- `wigtn-ocr-v1` Wigtn. *Qwen3-VL-2B-WigtnOCR* (HuggingFace model, 2026).
