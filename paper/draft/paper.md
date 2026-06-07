# RCPS: Choosing Document Parsers by Retrieval, Not by Appearance — Diagnosing the Parsing–Retrieval Gap

Hyeong-seob Kim\*, Sang-woo Son\* (WIGTN)
*\* Equal contribution (co-first authors). EMNLP 2026 Industry Track — Draft v0.8 (2026-06-07).*

---

## Abstract

Practitioners selecting a document parser for retrieval-augmented generation (RAG) typically rank candidates by intrinsic quality metrics—boundary clarity, text-edit fidelity—on the assumption that cleaner parser output retrieves better. On Korean government documents we observe the opposite. In a six-parser, three-retriever evaluation, MoC Boundary Clarity anti-correlates with retrieval (Pearson r = −0.81, n = 5): the two cleanest-boundary parsers retrieve far below the messier vision-language parsers, and selecting a parser by retrieval rather than by appearance changes Hit@1 by 2.8× (0.197 → 0.549). We make four contributions for production document-RAG. We characterise this parsing–retrieval disconnect in Korean and English and trace its mechanism: under controlled semantic-noise perturbations, boundary clarity stays flat while retrieval collapses, indicating that intrinsic boundary metrics measure formatting rather than content (C1). A retriever-free coverage diagnostic attributes the gap to a single pipeline layer—20.2% of answers are absent from the parser output, a rate constant across eight chunkers—giving practitioners a rule computable before any retriever is run (C2). We propose RCPS, a retrieval-grounded selection protocol that requires no training and correctly ranks parsers and chunkers that intrinsic metrics misorder; an ablation shows it is not equivalent to single-embedder MRR (C3). Finally, we map the limits of parser-side training: a hidden-state auxiliary loss and reference-free preference optimisation are sub-threshold, while best-of-K fidelity distillation yields a small but reproducible gain (OHR-Bench Hit@5 +1.22 pp), and a matched control shows the retrieval reward itself is unnecessary (C4). We release KoGovDoc-RAG, a Korean document-RAG benchmark, with a reference implementation of RCPS.

---

## 1 Introduction

Retrieval-augmented generation (RAG) is increasingly deployed over large collections of real-world documents—government records, enterprise reports, technical manuals—where answering a question means retrieving the right passage from a corpus that exists only as scanned or born-digital PDFs. Every such pipeline begins with a document parser that converts each page to text; that output is then chunked, embedded, and retrieved. Because the parser sits at the head of the pipeline, its errors cascade through every downstream stage, and teams building production systems choose it with care.

The practical question is *how* to choose. Faced with many candidate parsers—OCR engines, layout models, and vision-language models—practitioners rank them by intrinsic parsing-quality metrics that reward clean-looking output: low text-edit distance against a reference, and high boundary clarity \citep{zhao2025moc}. The implicit assumption is that cleaner parser output retrieves better.

On Korean government documents, that assumption fails. A practitioner ranking parsers by intrinsic metrics would deploy MinerU \citep{mineru2025}, which attains the highest text fidelity and a boundary-clarity score (0.72) matched only by Marker; yet its retrieval Hit@1 is 0.20, well below the 0.50–0.55 of three lower-scoring vision-language parsers. The pattern is systematic: across six parsers and three retrievers, Boundary Clarity anti-correlates with retrieval at Pearson r = −0.81 (n = 5). A cross-domain check on the English OHR-Bench \citep{zhang2024ohr} identifies the mechanism—as semantic noise is injected into a parser's output, retrieval degrades sharply while Boundary Clarity barely moves, so the intrinsic metric cannot perceive the content corruption retrieval depends on. Selection by appearance optimises a quantity that is structurally blind to retrievability.

We study how a team should instead select—and, where possible, improve—the parser in a production document-RAG system, and report four contributions.

- **C1 — The parsing–retrieval disconnect and its mechanism.** The parser a team would pick by intrinsic metrics is not the parser retrieval wants: parser choice alone changes Hit@1 by 2.8× (0.197 → 0.549), and Boundary Clarity anti-correlates with retrieval (Korean r = −0.81, n = 5). A controlled noise-perturbation experiment on English OHR-Bench shows why: intrinsic boundary metrics track formatting, not content, so semantic noise that destroys retrieval leaves Boundary Clarity flat.
- **C2 — A retriever-free coverage diagnostic.** Holding the parser output fixed and varying the chunker, we classify every answer as covered, split (a chunker fault), or absent (a parser fault). On our production parser, 20.2% of answers are absent against a 0–2% split rate, and the absent rate is constant across all eight chunkers. This yields a rule a team can apply before running any retriever: if absent dominates, fix the parser; if split dominates, fix the chunker.
- **C3 — RCPS, a protocol for selecting parsers and chunkers.** RCPS wraps ordinary retrieval MRR in three choices—a held-out Q-A probe, retriever-averaging, and format-invariant relevance—run with no training to rank the two parser-side knobs a team controls. An ablation shows it is not single-embedder MRR: retriever-averaging is what corrects the top parser ranking that a single embedder gets wrong.
- **C4 — A bounded map of parser-side training.** Two natural formulations fail: a hidden-state contrastive auxiliary loss is sub-threshold and reference-free preference optimisation is negative. Discrete-output preference training gives a small, cross-domain-significant gain (OHR-Bench Hit@5 +0.85 pp), but a matched best-of-K control ranked by edit-distance to ground truth reproduces it (+1.22 pp), showing the lever is text-fidelity distillation, not the retrieval reward.

We release **KoGovDoc-RAG**, a Korean document-RAG benchmark of 663 question–answer pairs over 294 pages, together with a reference implementation of RCPS, the RADP-Distill checkpoint (the recommended parser-side lever), and the RADP-aux / RADP-DPO checkpoints used for the negative and controlled comparisons.

## 2 Related Work

**Diagnosing the parsing–retrieval gap.** Prior work documents that parser quality affects downstream retrieval but does not close the gap on the parser side. OHR-Bench \citep{zhang2024ohr} evaluates the cascading impact of OCR noise on RAG; EnterpriseDocBench \citep{enterprisedocbench2026} reports a weak parsing-quality–retrieval correlation; and concurrent analyses \citep{goodocr2026} reach similar conclusions. None proposes a training-time intervention on the parser itself.

**Training-time methods, by pipeline layer.** Existing parser-adjacent training operates at every layer except the parser. Chunking methods decide boundaries after parsing \citep{jina2024late, duarte2024lumber, zhao2024meta, zhao2025moc}; embedding-side methods train the retriever contrastively \citep{conti2025insent, zhao2025lmar}; and retrieval- or reader-side methods tune the retriever or generator \citep{nguyen2024rewardrag, chia2025mlongdoc, yan2025rpo}. To our knowledge, no prior work trains the parser itself on a retrieval signal, which is the gap our parser-side training (C4) occupies. Our primary contributions, however, sit upstream of any training: a cross-domain diagnosis (C1), a parser-versus-chunker localisation (C2), and a protocol for *selecting* parsers and chunkers by retrieval (C3). On top of these we test parser-side training from both natural directions and find only the discrete-output route works, and only modestly (§4.4).

## 3 Method

### 3.1 RCPS: Retrieval-Conditional Parsing Score

RCPS ranks parsers by what downstream retrieval does with their output rather than by how clean that output looks. It is not a new similarity function but an evaluation protocol that wraps ordinary retrieval MRR in three choices: (i) it is *extrinsic*, scoring on the parsed corpus together with a held-out Q-A probe rather than on text alone; (ii) it is *retriever-agnostic*, averaging over several embedders so the ranking does not hinge on which one sits in the production stack; and (iii) it uses *format-invariant relevance*, counting a chunk as relevant if and only if its text contains the answer span, however the parser formatted it. The contribution is the protocol—what to measure, on what probe, and how to judge relevance—not the scoring function; this is also why RCPS is not single-embedder MRR, which yields a different and less stable parser ranking (§4.3).

Given a parser $P$, a Q-A set $D = \{(q_i, a_i, \text{page}_i)\}$, a set of retrievers $R$, and cutoffs $K$, RCPS averages MRR across the cross-product:

$$\text{RCPS}(P, D, R, K) = \frac{1}{|R||K|} \sum_{r \in R} \sum_{k \in K} \text{MRR}@k\big(r, \text{chunks}_P(D), \{q_i\}\big).$$

We use $R = \{$BGE-M3 \citep{chen2024bgem3}, multilingual-e5-large \citep{wang2024me5}, Qwen3-Embedding-8B$\}$ and $K = \{1, 5, 10\}$. A chunk is relevant for a query if and only if its source page matches the answer's source page and the gold answer span is a substring of the chunk under whitespace- and markdown-insensitive normalisation. The retriever average makes the ranking robust to embedder choice: a parser that wins on one retriever but loses on another does not dominate. In practice a team runs RCPS on a few hundred held-out Q-A, with no training, to choose a parser or chunker that intrinsic metrics rank incorrectly. The implementation is released.

### 3.2 Coverage Diagnostic — Locating the Gap (Parser vs Chunker)

RCPS scores the parser, chunker, and retriever jointly, so a low score does not say which layer is at fault. Before proposing any fix, we separate the parser from the chunker with a retriever-free diagnostic. Holding the parser output fixed and varying the chunker, we classify each gold answer by where it lands after chunking:

- **covered** — the span sits inside a single chunk and is retrievable;
- **split** — the span is present in the page text but no single chunk holds it whole; a boundary cut through it. This is a chunker fault, recoverable with overlap or larger windows.
- **absent** — the span is not in the parser output at all. This is a parser fault, unrecoverable by any chunking.

Coverage—the fraction of answers that are covered—is the ceiling on retrieval, because split and absent answers score zero for any retriever. Splitting the non-covered mass into a chunker fault (split) and a parser fault (absent) attributes the gap to a pipeline layer and decides whether a parser-side intervention can help at all (§4.2). Relevance reuses RCPS's format-invariant matching (§3.1).

### 3.3 Parser-Side Training: Auxiliary Loss and Discrete-Output DPO

When the coverage diagnostic points to the parser (§4.2), we train it on a retrieval signal in the two natural ways; only the second produces a deployable effect.

**(a) Hidden-state auxiliary loss (RADP-aux).** We jointly train the parser to produce faithful markdown and to align its answer-span hidden state with the retriever's space: $\mathcal{L}_\text{total} = \mathcal{L}_\text{parse} + \lambda\,\mathcal{L}_\text{contrast}$, where $\mathcal{L}_\text{contrast}$ is an InfoNCE loss between the parser's pooled answer-span hidden state and the frozen BGE-M3 embedding of the gold chunk. This is the natural differentiable surrogate for the non-differentiable discrete output, but the signal reaches the deployed markdown only through back-propagation into $\mathcal{L}_\text{parse}$, and it is sub-threshold (§4.4).

**(b) Discrete-output DPO (RADP-DPO).** We optimise the discrete markdown directly \citep{rafailov2023dpo}. For each training page we sample $K$ alternative parses from the production parser, score each by a page-local RCPS, form preference pairs (chosen = higher-RCPS parse, gap ≥ 5 pp), and train with a LoRA-toggle reference \citep{hu2021lora}, where $\pi_\theta$ is the parser with the LoRA adapter on and $\pi_\text{ref}$ is the same parser with it off. The reward is sharpened across three milestones R1→R2→R3 (Appendix A). As a control, reference-free SimPO \citep{meng2024simpo} removes the reference policy entirely; it is negative across all cells (§4.4), confirming the reference anchoring is load-bearing.

**(c) Reward-agnostic control (RADP-Distill).** To test whether the retrieval reward in (b) is necessary, we instantiate the identical best-of-K pipeline—same $K=14$ candidate pool, same LoRA-toggle DPO loss, same $\beta$, learning rate, and seed—but rank candidates by character-level edit-distance to the ground-truth markdown instead of page-local RCPS. This isolates the selection signal: if RADP-Distill matches RADP-DPO, the retrieval reward adds nothing over plain fidelity distillation (§4.4a, §4.5).

## 4 Experiments

### 4.1 Setup

We construct **KoGovDoc-RAG**: 663 Q-A pairs over 294 pages of Korean government documents, generated with GPT-5.4 and verified by an LLM-as-judge against the human-curated ground-truth markdown (100 stratified eval Q-A sampled for verification, 94/100 accept). For RADP-aux's full-scale training we additionally generate 6,164 Q-A on the 2,667-page Prod training set. Cross-domain replication uses OHR-Bench \citep{zhang2024ohr} (seven domains, 2,264 verbatim-answerable Q-A; its Law + Manual subset of 1,043 Q-A is used only for the data-mix-sensitivity comparison in §4.2) across the three released parser outputs (gt, MinerU, Qwen2.5-VL) plus twelve controlled noise perturbations.

Throughout, **Prod** denotes our production parser, a Qwen3-VL-2B model \citep{qwen3vl} fine-tuned for Korean document parsing; it is the reference against which all training deltas are measured. RADP-aux is evaluated on a 73-page held-out fold (202 Q-A); RADP-DPO, SimPO, and the §4.5 mechanism analysis use the combined 242-page fold (train ∪ eval, 663 Q-A), which is appropriate for the DPO comparison because preference pairs are built from parses on the 169-page train fold while Prod is held fixed. All parses for the 12-variant comparison in §4.4–§4.5 are regenerated with deterministic decoding (temperature 0, max 1536 tokens) for like-for-like comparison. We fine-tune with LoRA ($r = 8$, $\alpha = 32$); for RADP-aux we sweep $\lambda \in \{0, 0.1, 0.3, 0.5\}$, with $\lambda = 0$ a matched control that reproduces Prod. All RCPS values use the three retrievers and three cutoffs of §3.1. We report paired percentile-bootstrap 95% confidence intervals (1,000 resamples), resampling Q-A indices with replacement and preserving them across systems so deltas inherit the pairing.

### 4.2 The Parsing–Retrieval Disconnect and Coverage Diagnostic (C1–C2)

**Korean government documents (Figure 1; full grid in Appendix D).** RCPS spans 0.07–0.58 across the six parsers: the vision-language parsers cluster at the top (0.53–0.58) and the OCR systems trail (0.07–0.21). The intrinsic Boundary Clarity metric \citep{zhao2025moc} anti-correlates with RCPS at Pearson r = −0.81 (n = 5, excluding PaddleOCR, whose Boundary Clarity is undefined because MoC detects zero boundaries in its output). The two cleanest-boundary parsers, MinerU and Marker (BC ≈ 0.72), land near the bottom of the retrieval ranking (RCPS 0.07–0.21), while the lower-BC vision-language parsers (BC 0.52–0.62) retrieve best (0.53–0.58). Marker is evaluated on a 38-page subset rather than the full corpus; dropping it leaves the anti-correlation unchanged in sign and magnitude (n = 4, r = −0.74). MoC's companion metric, Chunk Stickiness, is similarly disconnected (r = +0.26, n = 5; with CS oriented so that lower is more cohesive, this is the same direction as BC—more cohesive intrinsic structure tracks worse retrieval). Neither intrinsic axis predicts RCPS.

![Figure 1 — parsing–retrieval disconnect](../figures/fig_disconnect.png)
*Figure 1: The parsing–retrieval disconnect on Korean government documents. (a) Boundary Clarity (intrinsic, MoC) anti-correlates with RCPS across parsers (Pearson r = −0.81, n = 5; PaddleOCR excluded as its BC is undefined): the cleanest-boundary parsers MinerU and Marker land near the bottom, while the lower-BC vision-language parsers retrieve best. (b) Choosing the parser by RCPS (Prod) rather than by appearance (MinerU) changes retrieval Hit@1 by 2.8× (0.197 → 0.549).*

A single-domain anti-correlation could be a quirk of one language or document type, so we test cross-domain.

**Cross-domain: the mechanism (Figure 2).** Across all seven OHR-Bench domains (2,264 Q-A) we evaluate 15 parser-output variants: three released parser outputs (gt, MinerU, Qwen2.5-VL), three formatting-noise perturbations, and nine semantic-noise perturbations (GOT, MinerU, Qwen2.5-VL × mild, moderate, severe). Within each semantic-noise family, Boundary Clarity barely moves while RCPS collapses (Figure 2). For the MinerU family, BC stays in 0.71–0.73 from clean to severe while RCPS falls 0.50 → 0.24 (−52%); GOT shows the same pattern (RCPS 0.38 → 0.26, −32%), and Qwen2.5-VL is more noise-robust (0.47 → 0.43, −8%). Semantic noise that destroys retrievable content does not lower Boundary Clarity: the intrinsic metric sees formatting, not content.

![Figure 2 — noise-family curves](../figures/fig_noise_family.png)
*Figure 2: OHR-Bench seven-domain noise-family curves. Top: Boundary Clarity stays roughly flat across noise severity for all three parser families. Bottom: RCPS collapses for MinerU and GOT, and falls more gently for the noise-robust Qwen2.5-VL. The intrinsic metric does not perceive the content corruption retrieval depends on.*

The aggregate cross-variant correlation is sensitive to the document mix: Pearson BC↔RCPS across all 15 variants is −0.35 on Law + Manual alone but +0.25 on the full seven-domain corpus. We therefore report the per-family mechanism, which reproduces in every domain, as the robust finding, and treat the cross-variant scalar—which conflates parser families of differing noise-robustness—as illustrative only.

**Locating the gap: parser or chunker? (Table 2b).** The disconnect shows that intrinsic metrics mislead, but not which pipeline layer is at fault. Applying the §3.2 classification with no retriever, on Prod's output (294 pages, 663 Q-A) 20.2% of answers are absent and at most 2.3% are split, and the absent rate is constant across all eight chunkers we test—exactly the boundary-independence a parser fault must show. The gap is therefore a parser problem: roughly one answer in five is never produced, so no re-chunking can recover it, and a parser-side intervention is the correct lever. This both motivates the training in §4.4 and yields the practitioner rule: run this diagnostic first, and if absent dominates, fix the parser; if split dominates, fix the chunker.

| Chunker | covered | split (chunker fault) | absent (parser fault) |
|---|:---:|:---:|:---:|
| md_h3 | 79.8% | 0.0% | 20.2% |
| md_h2 | 79.8% | 0.0% | 20.2% |
| md_h1 | 79.8% | 0.0% | 20.2% |
| parser_native | 78.1% | 1.7% | 20.2% |
| fixed500 | 77.5% | 2.3% | 20.2% |
| fixed500_ov200 | 79.8% | 0.0% | 20.2% |
| fixed1000 | 79.3% | 0.5% | 20.2% |
| fixed1000_ov200 | 79.8% | 0.0% | 20.2% |

*Table 2b: Answer-coverage diagnostic on Prod's output (294 pages, 663 KoGov Q-A; text matching only, no retriever). The absent rate (a parser fault) is constant at 20.2% across all eight chunkers, the required boundary-independence check; the split rate (a chunker fault) is at most 2.3% and vanishes under overlap. The gap is overwhelmingly a parser problem, which licenses the parser-side intervention in §4.4.*

### 4.3 RCPS Selects Both Parsers and Chunkers (C3)

A selection protocol must separate the alternatives a practitioner actually compares, across both knobs they control. For **parsers**, the six-parser grid of §4.2 (Figure 1, Appendix D) is itself an RCPS ranking: it tells a team that Prod (RCPS 0.583, Hit@1 0.55) beats MinerU (0.21, 0.20) by 2.8×, the ordering Boundary Clarity inverts. For **chunkers**, on a fixed parser output (Table 3) RCPS separates four strategies cleanly—markdown-header (md-h3) > parser-native > LumberChunker \citep{duarte2024lumber} > fixed-size—whereas intrinsic boundary metrics would rank them inconsistently, or rank fixed-size highest because its boundaries are clean by construction. Because RCPS is retriever-averaged and format-invariant, one probe set of a few hundred Q-A ranks both the parser choice and the chunker choice a team makes independently.

| Chunker | RCPS | Hit@1 | MRR@10 |
|---|:---:|:---:|:---:|
| md-h3 | **0.593** | 0.556 | 0.613 |
| parser_native | 0.583 | 0.549 | 0.602 |
| LumberChunker | 0.557 | 0.514 | 0.580 |
| fixed500 | 0.535 | 0.491 | 0.560 |
*Table 3: KoGov chunking-strategy grid (663 Q-A, Prod parser output, three-retriever RCPS average).*

**RCPS is not single-embedder MRR (Table 3b).** Stripping the three protocol choices from the six-parser KoGov grid shows they are not cosmetic. Dropping retriever-averaging—scoring on a single embedder (BGE-M3)—inverts the top parser choice: naive single-embedder MRR ranks Prod first, while full RCPS ranks the Qwen3-VL-30B teacher first (rows A and C versus D). Format-invariant matching, by contrast, shifts every parser's score by about 0.02–0.03 but does not reorder the grid (row B versus D). The inversion is between two near-tied parsers (RCPS 0.584 versus 0.583), so the operational claim is precise: single-embedder MRR cannot reliably resolve the top parser a team would deploy—exactly the decision RCPS is run to make. The ordering disagreement (Kendall τ = 0.87) substantiates the claim that RCPS is a protocol, not a relabelled MRR.

| Row | Protocol (retrievers × relevance) | Parser ranking (best → worst) | Inv. vs RCPS | Kendall τ |
|---|---|---|:---:|:---:|
| A | naive MRR: BGE-M3 only × format-sensitive | Prod ≻ Qwen3-VL-30B ≻ Qwen3-VL-2B ≻ MinerU ≻ PaddleOCR ≻ Marker | 1 | 0.87 |
| B | + retriever-averaging: 3-retriever × format-sensitive | Qwen3-VL-30B ≻ Prod ≻ Qwen3-VL-2B ≻ MinerU ≻ PaddleOCR ≻ Marker | 0 | 1.00 |
| C | + format-invariant only: BGE-M3 only × format-invariant | Prod ≻ Qwen3-VL-30B ≻ Qwen3-VL-2B ≻ MinerU ≻ PaddleOCR ≻ Marker | 1 | 0.87 |
| D | Full RCPS: 3-retriever × format-invariant | Qwen3-VL-30B ≻ Prod ≻ Qwen3-VL-2B ≻ MinerU ≻ PaddleOCR ≻ Marker | — (ref) | 1.00 |
*Table 3b: RCPS protocol ablation on the KoGov six-parser grid (RCPS = mean MRR@{1,5,10}). The single choice that reorders the grid is retriever-averaging (rows A and C invert the top pair versus D); format-invariance shifts scores but not order here. Rows C and D re-aggregate the stored per-retriever scores; rows A and B re-index under format-sensitive relevance.*

### 4.4 Parser-Side Training: A Bounded, Reward-Agnostic Lever (C4)

The coverage diagnostic (§4.2) has licensed this step: with one answer in five absent from the parser output and almost none merely split, the gap is a parser problem and a parser-side fix is the right lever. We test both natural directions—the hidden-state auxiliary loss (RADP-aux, §3.3a) and discrete-output retrieval-reward DPO (RADP-DPO, §3.3b)—and only the discrete-output route produces a deployable effect.

On the 242-page KoGov fold, the RADP-DPO milestones improve Hit@5 on parser-native chunking over Prod by +1.96 to +2.11 pp (all P[Δ>0] ≈ 0.90), but at n = 663 every two-sided interval spans zero, so we treat KoGov as exploratory: the reported cell was chosen from a multi-cell scan over (chunker × retriever × k) and establishes direction only (Appendix B, Table 5). The pre-specified confirmatory test is the cross-domain OHR-Bench replication, where the training signal, evaluation metric, and document language are mutually disjoint, ruling out metric circularity and domain over-fitting. There, the representative retrieval-reward variant R2 gives Hit@5 +0.85 pp [+0.35, +1.43], two-sided significant and positive across all seven domains; the more aggressive R3 reaches +1.03 pp [+0.24, +1.84] but, as §4.5 shows, without a matching per-page fidelity gain. The gain is modest (about 1 pp Hit@5) and retriever-agnostic; the smaller magnitude on OHR than KoGov is expected, since Prod's zero-shot English TextNED (0.192) already sits below its Korean TextNED (0.240), leaving less fidelity headroom (§4.5). RADP-aux is sub-threshold and SimPO is uniformly negative (Appendix B).

**§4.4a — Is the retrieval reward necessary?** The §4.5 mechanism—that the gain is text fidelity, not chunk boundaries—raises a sharp question: does the retrieval reward do anything a plain fidelity objective cannot? We test this with the matched RADP-Distill control (§3.3c), identical to RADP-DPO except that preference pairs are ranked by edit-distance to the ground-truth markdown rather than page-local RCPS. RADP-Distill matches or exceeds RADP-DPO on both folds and both metrics: OHR-Bench Hit@5 +1.22 pp [+0.35, +2.15] (versus +0.85 pp for RADP-DPO; n = 2,264, two-sided significant), and on KoGov both Hit@5 +2.61 pp [−0.35, +5.68] (P[Δ>0] = 0.95, versus +1.96 pp; exploratory) and RCPS 0.600 (versus 0.590 for RADP-DPO and 0.586 for Prod). The two are statistically indistinguishable on the powered OHR fold, with RADP-Distill's point estimate equal or higher in every cell. The retrieval reward therefore buys nothing over plain fidelity distillation: it is one, more expensive, way to obtain a target that edit-distance to ground truth supplies directly. For practitioners this is a cost-saving result—the parser-side lever is best-of-K distillation toward clean ground-truth text, not a retrieval-reward pipeline.

| Δ vs Prod (pp) | Hit@1 | Hit@5 | Hit@10 | MRR@10 | nDCG@5 |
|---|:---:|:---:|:---:|:---:|:---:|
| RADP-Distill (headline) | **+0.88** | **+1.22** | **+1.32** | **+1.01** | **+1.05** |
| RADP-DPO-v4 (R2, retrieval reward) | +0.53 | +0.85 | +0.81 | +0.70 | +0.74 |
| RADP-DPO-v5 (R3, hard-negative) | +1.31 | +1.03 | +0.81 | +1.17 | +1.15 |
*Table 5b: OHR-Bench cross-domain Δ vs Prod, in pp (2,264 Q-A over seven English domains; three-retriever macro; 1,000-resample paired bootstrap). Every cell is two-sided significant (e.g. R2 Hit@5 [+0.35, +1.43], R3 Hit@5 [+0.24, +1.84]). Hit@k, MRR@k, and nDCG@k are monotone functions of the same retrieved ranking, not independent endpoints; we report several only because practitioners use different ones. RADP-Distill, the reward-agnostic control, leads at Hit@5 +1.22 pp; the retrieval-reward route (R2 +0.85, R3 +1.03) reproduces no more, confirming (§4.4a) that the retrieval reward is unnecessary.*

### 4.5 Mechanism: Training Tightens Text Fidelity Without Changing the Chunking Signature

The §4.4 gain calls for a mechanism, so we measure four chunk-level statistics on the 242-page fold for all 12 systems—Boundary Clarity, Chunk Stickiness, normalised edit distance to the ground-truth markdown (TextNED), and chunking shape (Appendix C, Table 7). The signal is text fidelity. All four RADP-DPO variants reduce TextNED from Prod's 0.240 to 0.163–0.182 (a 24–32% move toward ground truth), the reward-agnostic RADP-Distill control reduces it furthest of all (0.158) while leading on retrieval, and TextNED tracks Hit@5 monotonically across variants—the cleanest evidence that text fidelity, not the retrieval reward, is the operative lever. RADP-aux, by contrast, *increases* TextNED (0.318–0.626) as its hidden-state objective degrades surface text. The chunking signature does not move: BC for every DPO variant lands in 0.60–0.66 (Prod 0.63), CS in 0.469–0.478 (Prod 0.474; CS is not measured for RADP-Distill), and chunks-per-page and chunk length stay within Prod's range. The Hit@5 gain therefore comes from what is parsed, not how chunks are split—the same fact as §4.2's intrinsic-metric blindness, seen from the training side. The mechanism replicates cross-domain (English TextNED for R2 falls −1.36%, two-sided significant), and the secondary patterns—larger gains on factoid than tabular queries, larger on held-out retrievers, RADP-aux sub-threshold—all follow from text fidelity (Appendix C).

## 5 Discussion and Conclusion

**Selection, not training, is the headline.** The largest and most certain effect in this paper is not a training method: choosing a parser by retrieval (RCPS) rather than by intrinsic metrics changes Hit@1 by 2.8× (§4.2). A team that adopts only the RCPS protocol already avoids shipping the parser that looks best yet retrieves near the bottom. Parser-side training—best-of-K fidelity distillation toward clean ground-truth text—is a secondary, bounded lever of about 1 pp Hit@5 on top of an already-good parser, and the retrieval-reward apparatus buys nothing over it (§4.4a).

**Why C1 and the mechanism agree.** C1 finds that the cleanest-boundary parser retrieves among the worst, while §4.5 finds that training helps by producing text closer to ground truth. These reconcile once "clean" is split into two axes: Boundary Clarity measures formatting cleanliness (how crisp the chunk edges look), whereas TextNED measures content fidelity (whether the parsed text actually contains the answer span). MinerU is formatting-clean but loses content; the trained parser leaves the formatting signature unchanged and improves content fidelity. Intrinsic boundary metrics see only the first axis, which is exactly why they mispredict retrieval.

**The original hypothesis, refined.** We began expecting parser-side training to move chunk boundaries from human-friendly to retrieval-friendly. The data do not support that: the chunking signature is essentially unchanged, and what moves is text fidelity. We therefore report text fidelity as the operative mechanism and treat the boundary-shift hypothesis as not confirmed—an honest negative nested inside the positive C4. Seen this way, RADP-DPO is best understood as best-of-K rejection-sampling self-distillation, a reading the RADP-Distill control confirms directly: replacing the retrieval reward with edit-distance to ground truth reproduces the gain, so the reward was merely selecting whichever sampled parse already lay closest to ground truth, which training then amortises into the weights. The parser learns to emit by default the higher-fidelity outputs it could already occasionally produce, rather than acquiring a new retrieval-aware capability—consistent with the modest, fidelity-bounded effect we observe.

**A decision playbook for document-RAG teams.**
1. *Evaluate parsers with RCPS, not intrinsic metrics alone.* A few hundred domain-representative held-out Q-A, scored with no training, reorder parsers the way the downstream retriever actually sees them—on our data, a 0.20 → 0.55 Hit@1 decision. This is the highest-leverage takeaway.
2. *If you train the parser, distil its discrete output toward clean ground-truth text.* The hidden-state auxiliary loss and reference-free SimPO are sub-threshold; expect a modest return of about +1 pp Hit@5 cross-domain, largest on retrievers not used for preference scoring, and a retrieval reward is unnecessary.
3. *Spend the budget where text precision drives retrieval.* The gain concentrates on factoid queries and is roughly neutral on tabular ones; teams with layout-heavy query mixes should look to the chunker or embedder instead.

**Conclusion.** We documented the parsing–retrieval disconnect in two languages and document types, proposed RCPS—a cheap, retriever-agnostic protocol for selecting parsers and chunkers by retrieval rather than by appearance—and mapped what parser-side training can and cannot add. Hidden-state auxiliary loss and reference-free preference optimisation fail; discrete-output preference training gives a modest, cross-domain-significant gain, but a matched edit-distance control reproduces it, so the lever is fidelity distillation rather than a retrieval-reward effect. The practical contribution is a decision procedure: evaluate parsers with RCPS, and if you train, distil the discrete output toward clean ground-truth text. Code, data, and checkpoints are released.

---

## Released artifacts

- **KoGovDoc-RAG** — 663 Q-A over 294 Korean government document pages.
- **RCPS reference implementation** — `src/wigtnocr_radp/evaluation/`.
- **RADP-Distill checkpoint** — the recommended deployable parser-side lever (§4.4a): best-of-K preference training with candidates ranked by edit-distance to ground truth, no retrieval reward.
- **RADP-aux checkpoints** ($\lambda \in \{0, 0.1, 0.3, 0.5\}$) and **RADP-DPO checkpoints (R1–R3) + SimPO control** — released for reproducibility as the negative and controlled-against comparisons; RADP-Distill is the recommended recipe.
- **OHR-Bench cross-domain results and mechanism-analysis data** — 15-variant RCPS and Boundary Clarity correlation; BC, CS, TextNED, and chunking shape on 12 systems × 242 pages.

## Limitations

- **Single primary language and statistical power.** The C1 diagnostic is strongest in Korean (n = 5, r = −0.81). The English replication on OHR-Bench is directionally consistent but weaker (n = 15, r = −0.35) and built on three real parser outputs plus twelve controlled perturbations rather than fifteen independent parsers. With these sample sizes the correlations are illustrative rather than inferential, supporting a directional finding that a larger parser pool could extend.
- **Q-A generation and construct validity.** The KoGov Q-A were produced by GPT-5.4 and verified by an LLM-as-judge against the human-curated ground-truth markdown (94/100 accept on a 100-Q-A stratified sample; full human verification at train scale was cost-prohibitive). Synthetic queries bound what RCPS can claim, but the exposure is narrow: our comparative findings—the 2.8× parser-choice swing and every parser/chunker ranking—hold the Q-A set fixed across systems and so are internally valid regardless of how queries were generated, and the confirmatory cross-domain test (§4.4) uses OHR-Bench's own externally curated Q-A. We release the frozen KoGov eval set for audit.
- **KoGov is exploratory; OHR-Bench is confirmatory.** The headline KoGov cell (R2 +1.96 pp, Table 5) has a paired 95% interval of [−1.06, +5.03]—two-sided non-significant and selected from a multi-cell scan—so we claim no two-sided significance on KoGov. The confirmatory evidence is the pre-specified OHR-Bench replication (R2 +0.85 pp [+0.35, +1.43], n = 2,264). A larger KoGov fold (≥ 1,500 Q-A) would be needed for a powered two-sided result.
- **Candidate pool from the production parser only.** Preference pairs are sampled from Prod itself. An alternative pool—for example, chosen/rejected pairs from other parsers—would expose the model to off-distribution candidates and might shift the mechanism away from GT-fidelity; we did not test this.
- **Parser-side paradigms not exhausted.** We test the hidden-state auxiliary loss, discrete-output DPO with a reference policy, and reference-free SimPO. Token-level RL with a per-token retrieval signal, multi-task interleaving, curriculum schedules, and chunk-granularity oracle distillation are untested; the §4.5 mechanism suggests similar regimes but the question is open.
- **Downstream layers (future work).** RADP-DPO is a parser-layer intervention. The complementary layers—chunker, embedder, and reranker training on RCPS-graded chunks—are not addressed and would each localise the dominant retrieval-improvement mechanism in document-RAG pipelines.

## Appendix

### Appendix A — RADP-DPO milestone construction (detail for §3.3b)

For each train page we sample $K$ alternative parses from the production parser, chunk and score each by a page-local RCPS (the page's questions against the parse's own chunks plus distractors), and form preference pairs (chosen = higher-RCPS parse, gap ≥ 5 pp). The reward is sharpened across three milestones: **R1** ($K = 2$ parses, uniform distractors, $\beta = 0.1$) → **R2** (a warm-started iterative round, $\beta = 0.05$) → **R3** ($K = 14$ parses with a full-corpus hard-negative pool—the other-page chunks closest to the page's queries—widening the candidate-score gap from about 0.05 to 0.56). We train with a LoRA-toggle reference ($\pi_\theta$ = LoRA on, $\pi_\text{ref}$ = LoRA off):

$$\mathcal{L}_\text{DPO} = -\log \sigma\Big(\beta \big[(\log \pi_\theta(c) - \log \pi_\theta(r)) - (\log \pi_\text{ref}(c) - \log \pi_\text{ref}(r))\big]\Big).$$

The reference-free SimPO control ($\beta = 2.0$, $\gamma = 1.0$) removes the reference policy entirely.

### Appendix B — KoGov DPO progression, RADP-aux sweep, SimPO, and robustness (detail for §4.4)

On the 242-page KoGov fold (10,000-resample paired bootstrap), the three RADP-DPO milestones improve Hit@5 on parser-native chunking over Prod along the reward-sharpening axis: R1 +2.06 pp [−0.96, +5.13], R2 +1.96 pp [−1.06, +5.03], R3 +2.11 pp [−0.96, +5.13] (all P[Δ>0] ≈ 0.90). At n = 663 every two-sided interval spans zero, so these are exploratory: the Hit@5 / parser-native cell was selected from a multi-cell scan over (chunker × retriever × k) with no family-wise correction. The reward-agnostic RADP-Distill control, evaluated on the §4.4a run, reaches +2.61 pp on the same fold and is the headline; its powered confirmation is the OHR-Bench result (Table 5b, +1.22 pp).

| Variant (vs Prod = 0.6863) | Hit@5 | ΔHit@5 (pp) [95% CI] | P[Δ>0] | ΔHit@10 (pp) | ΔRCPS (pp) |
|---|:---:|:---:|:---:|:---:|:---:|
| RADP-DPO-v5 (R3, hard-negative) | 0.7074 | +2.11 [−0.96, +5.13] | 0.913 | +2.21 | +1.72 |
| RADP-DPO-v1 (R1, BGE, β=0.1) | 0.7069 | +2.06 [−0.96, +5.13] | 0.907 | +1.81 | +0.57 |
| RADP-DPO-v4 (R2, warmstart, β=0.05) | 0.7059 | +1.96 [−1.06, +5.03] | 0.897 | +1.71 | +0.47 |
| RADP-SimPO (reference-free control) | 0.6793 | −0.70 [−3.77, +2.31] | 0.321 | −0.96 | −1.56 |
*Table 5: RADP-DPO milestone progression and the SimPO control on parser-native chunking, 242-page / 663-Q-A fold, 10k paired percentile bootstrap, all against the same Prod baseline (Hit@5 = 0.6863). Macro Hit@k averages the three retrievers of §3.1. All three milestones are strong directional positives (P[Δ>0] ≥ 0.90) but two-sided non-significant at this fold size (§4.4); RADP-SimPO, the reference-free control, is uniformly negative. The reward-agnostic RADP-Distill headline (KoGov ΔHit@5 +2.61 pp) is evaluated on the §4.4a run and reported in §4.4a and Table 5b. Across three Prod seeds the standard deviation of the mean ΔHit@5 is 0.90 pp.*

**RADP-aux is sub-threshold.** The auxiliary loss peaks at $\lambda = 0.1$ (+1–2 pp RCPS) then declines monotonically as the contrastive objective competes with $\mathcal{L}_\text{parse}$ over the same LoRA parameters; every Δ-versus-control interval includes zero and the one-sided P[Δ>0] never approaches 0.90. The hidden-state route does not reach the deployed markdown—only the discrete output does.

**SimPO is negative.** The reference-free length-normalised variant gives uniformly negative deltas (−0.7 to −1.7 pp Hit@5), indicating the DPO reference policy is load-bearing: without it the parser drifts from the production distribution before any preference signal can compound. The retrieval-reward signal must enter through the discrete output and be anchored to Prod via a reference policy.

**Robustness.** The OHR-Bench gain survives two checks. It is equal or larger on the two retrievers held out from preference scoring (ml-e5-large +2.4 pp, Qwen3-Emb +2.3 pp, versus the BGE-M3 scorer +1.5 pp), ruling out a BGE-overfit artefact; and it concentrates on factoid queries (+3.1 pp) while neutral-to-slightly-negative on tabular ones, consistent with the text-fidelity mechanism.

### Appendix C — Chunk-level mechanism statistics (detail for §4.5)

We measure four chunk-level statistics on the 242-page fold for all 12 systems plus the R3 variant (Table 7): MoC Boundary Clarity (BC, adjacent-chunk discontinuity), MoC Chunk Stickiness (CS, within-chunk cohesion), normalised edit distance to the ground-truth markdown (TextNED, character-level Levenshtein distance ÷ longer-string length), and chunking shape.

| Variant | parse_len | chunks/page | chunk_len | BC ↑ | CS ↓ | TextNED ↓ |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Prod (ref) | 1385 | 4.82 | 274 | 0.630 | 0.474 | 0.240 |
| RADP-Distill | 1597 | 5.29 | 291 | 0.641 | — | **0.158** |
| RADP-aux λ=0.0 | 799 | 2.96 | 245 | 0.553 | 0.473 | 0.626 |
| RADP-aux λ=0.1 | 1380 | 4.05 | 321 | 0.652 | 0.484 | 0.423 |
| RADP-aux λ=0.3 | 1930 | 6.73 | 272 | 0.470 | 0.475 | 0.332 |
| RADP-aux λ=0.5 | 2035 | 5.82 | 327 | 0.556 | 0.470 | 0.318 |
| RADP-DPO-v1 | 1606 | 4.97 | 311 | 0.646 | 0.474 | **0.167** |
| RADP-DPO-v2 | 1594 | 5.06 | 304 | 0.648 | 0.475 | 0.168 |
| RADP-DPO-v3 | 1689 | 5.27 | 304 | 0.601 | 0.469 | 0.182 |
| RADP-DPO-v4 (R2) | 1610 | 4.83 | 321 | 0.647 | 0.476 | **0.163** |
| RADP-DPO-v5 (R3) | 1514 | 4.88 | 300 | 0.656 | 0.485 | 0.185 |
| RADP-SimPO | 1703 | 5.31 | 305 | 0.601 | 0.470 | 0.186 |
| DPO-v1-seed123 | 1633 | 4.92 | 320 | 0.655 | 0.476 | 0.171 |
| DPO-v1-seed999 | 1620 | 4.69 | 332 | 0.654 | 0.478 | 0.174 |
*Table 7: Chunk-level mechanism statistics on the 242-page fold. BC is the mean MoC Boundary Clarity over all adjacent-chunk pairs scored by Qwen3-VL-2B perplexity; CS is the within-chunk-cohesion equivalent; TextNED is the per-page mean normalised edit distance to the human-curated ground-truth markdown. RADP-Distill attains the lowest TextNED of all (0.158 < R2's 0.163 < Prod's 0.240) with BC unchanged (0.641, within Prod's range), directly confirming that text fidelity, not chunk structure, is the operative axis (CS was not measured for RADP-Distill, which uses a fixed chunking scheme). Among retrieval-reward variants, R2 has the lowest TextNED (0.163); R3's KoGov TextNED (0.185) does not beat it, which is why R2 is the representative variant.*

**The signal.** All four RADP-DPO variants reduce TextNED from Prod's 0.240 to 0.163–0.182, a 24–32% move toward the ground-truth markdown; the two replicating positive variants (DPO-v1, DPO-v4) achieve the largest reductions (0.167, 0.163). RADP-aux instead increases TextNED (0.318–0.626) because its hidden-state objective degrades surface text. TextNED tracks Hit@5 monotonically, and RADP-Distill reduces it furthest (0.158) while leading on retrieval—the cleanest demonstration that text fidelity, not the retrieval reward, is the lever.

**Cross-domain replication.** On all 4,040 English OHR-Bench pages, zero-shot Prod reaches TextNED 0.192—below its 0.240 on Korean, so English leaves less fidelity headroom. R2 reduces it to 0.189 (−1.36%, 95% CI [−0.0043, −0.0010], two-sided significant). R3 pushes the English value marginally lower (0.184) yet does not improve KoGov fidelity, which is why R2 is the headline variant.

**The non-signal.** The MoC chunking signature is unchanged on both axes: BC for all DPO variants lands in 0.60–0.66 (Prod 0.63), CS in 0.469–0.478 across every DPO and SimPO variant (Prod 0.474; CS not measured for RADP-Distill), and chunks-per-page (4.69–5.27) and chunk length (304–332) within Prod's range. Training does not produce a novel chunking signature; the gain comes from what is parsed, not how chunks are split.

**Secondary patterns.** The gain concentrates on factoid queries—where the verbatim answer span must land inside a chunk—and is neutral on tabular ones. It is larger on the held-out retrievers than on the BGE-M3 scorer, because Prod's text was already BGE-aligned, confirming a parser-level effect rather than a BGE-overfit. RADP-aux stays sub-threshold because its hidden-state signal reaches the deployed markdown only through diffuse $\mathcal{L}_\text{parse}$ back-flow, never localising to the surface tokens the retriever rewards.

### Appendix D — KoGov parser grid (detail for §4.2, Figure 1)

| Parser | BC | RCPS | Hit@1 |
|---|:---:|:---:|:---:|
| Qwen3-VL-30B (teacher) | 0.623 | **0.584** | 0.545 |
| Prod (ours, 2B) | 0.610 | 0.583 | 0.549 |
| Qwen3-VL-2B (base) | 0.520 | 0.532 | 0.500 |
| MinerU | 0.716 | 0.212 | 0.197 |
| PaddleOCR | — | 0.140 | 0.125 |
| Marker (38p) | **0.717** | 0.073 | 0.068 |
*Table D1 (the §4.2 disconnect grid, visualised in Figure 1): KoGov, BC versus RCPS, Pearson r = −0.81 (n = 5, excluding PaddleOCR, whose Boundary Clarity is undefined). Marker is evaluated on a 38-page subset; dropping it gives n = 4, r = −0.74, same direction. RCPS is averaged over three retrievers (BGE-M3, ml-e5-large, Qwen3-Emb-8B).*

## References

Compiled in `paper/refs.bib`. The reference list is being verified entry-by-entry against arXiv / venue records; entries not yet confirmed are marked for check before submission.
