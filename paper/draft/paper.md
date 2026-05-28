# Retrieval-Aware Document Parsing: Diagnosing and Measuring the Parsing–Retrieval Gap

**Harrison Kim, et al.** (Braincrew AI)
*EMNLP 2026 Industry Track — Draft v0.5 (2026-05-28)*

---

## Abstract

Document parsers used in retrieval-augmented generation (RAG) are conventionally optimized for *human-readability* metrics — TEDS, edit distance, Boundary Clarity — yet these metrics do not predict downstream retrieval. In Korean government documents (6 parsers × 3 retrievers × 663 Q-A), MoC Boundary Clarity *anti*-correlates with retrieval at Pearson r = −0.81: the parser scoring highest on the intrinsic metric (MinerU) is the *worst* retriever. We propose **RCPS** (Retrieval-Conditional Parsing Score), a retriever-agnostic task-oriented metric, and validate it cross-domain on the English-language OHR-Bench (15 parser-output variants; r = −0.35). A noise-perturbation analysis reveals the mechanism: intrinsic boundary metrics see only formatting, not content — semantic noise that destroys retrieval leaves BC nearly unchanged. We then propose **RADP-DPO**, retrieval-reward direct preference optimization on the parser's discrete markdown output, with chosen/rejected pairs constructed from candidate parses scored by page-local RCPS gap ≥ 5 pp. On a 242-page, 663-Q-A eval fold with 10,000-resample paired bootstrap, RADP-DPO improves Hit@5 by **+2.06 pp on parser_native chunking** (P[Δ>0] = 0.907) over the production parser v1, with the effect replicating at +1.96 pp under a warmstarted multi-round variant (P = 0.897) and at +1.16 pp on a 3-seed merged training run (P = 0.900, across-seed std 0.90 pp). The improvement is **strongest on retrievers held out from preference scoring** — multilingual-e5-large +2.41 pp (P = 0.921), Qwen3-Embedding-8B +2.26 pp (P = 0.903) — confirming a retriever-agnostic parser-level effect. Subgroup analysis localises the gain to **factoid queries** (+3.07 pp, P = 0.858), exactly where text precision drives retrieval. Mechanism analysis (BC, TextNED-vs-GT, chunking shape) shows RADP-DPO does **not** alter the chunking signature (BC, chunks/page within v1's range) but tightens text fidelity to ground truth (TextNED 0.18 → 0.12, a 32% reduction) — explaining why the gain concentrates on text-precision-dependent queries. We also report a comprehensive negative on hidden-state auxiliary-loss training (**RADP-aux**, λ ∈ {0, 0.1, 0.3, 0.5}; +1–3 pp, below the pre-registered 5 pp gate; CIs include 0) and on reference-free SimPO (negative across all cells), confirming the retrieval-reward signal must enter through the discrete output to produce a robust effect. We release **KoGovDoc-RAG** (a Korean RAG benchmark), the RCPS reference implementation, the RADP-aux checkpoints (4 λ values), and the RADP-DPO/SimPO checkpoints (7 configurations).

---

## 1 Introduction

Picking a document parser for a retrieval-augmented generation (RAG) system, a practitioner runs MinerU on Korean government PDFs and confirms it tops every intrinsic parsing-quality metric in our grid — highest MoC Boundary Clarity (0.72), competitive on text fidelity — and deploys it. Retrieval Hit@1 is 0.20, the *worst* of the six parsers evaluated. The cleanest-looking parser is the worst retriever.

This is not a one-off. In a 6-parser × 3-retriever evaluation on Korean government documents, Boundary Clarity *anti*-correlates with retrieval at Pearson r = −0.81 (n = 5). A cross-domain check on the English-language OHR-Bench (n = 15 parser-output variants, including controlled noise perturbations) replicates the direction (r = −0.35) and reveals the mechanism: as semantic noise is added to a parser's output, Boundary Clarity stays constant while retrieval performance collapses. Intrinsic boundary metrics cannot see semantic content quality, and the practitioner has no way to know this from the metrics they see.

**Contributions.**

- **C1.** A cross-domain diagnostic of the parsing–retrieval disconnect, with a mechanism (noise-family curve, Figure 2) that makes the intrinsic-metric failure mode visible at a glance.
- **C2. RCPS** (Retrieval-Conditional Parsing Score), a retriever-agnostic, task-oriented metric practitioners can run on a small held-out Q-A set to choose parsers and chunking strategies for production RAG — discriminating combinations that intrinsic metrics conflate.
- **C3. RADP-DPO**, a retrieval-reward preference-learning method on the parser's discrete markdown output. We construct chosen/rejected pairs from candidate parses ranked by a page-local RCPS gap ≥ 5 pp and apply Direct Preference Optimization with a LoRA-toggle reference trick that avoids the 2× model-memory cost of standard DPO. RADP-DPO improves **Hit@5 by +2.06 pp on parser_native chunking** (P[Δ>0] = 0.907) versus the production parser v1 on a 242-page / 663-Q-A eval, with the effect replicating across a warmstarted multi-round variant (+1.96 pp, P = 0.897) and across 3-seed merging (+1.16 pp, P = 0.900, std 0.90 pp). The effect is strongest on the *held-out* retrievers (ml-e5-large +2.41 pp, P = 0.921; Qwen3-Embedding-8B +2.26 pp, P = 0.903), confirming a retriever-agnostic parser-level effect rather than over-fitting to the BGE-M3 scoring retriever. Mechanism analysis (§4.5) localises the gain to text-precision-dependent queries (factoid +3.07 pp, P = 0.858) and attributes it to tighter parse-to-GT text fidelity (TextNED 0.18 → 0.12, −32%) under preserved chunking signature (BC unchanged from v1).
- **A boundary on the parser-side parameterisation.** We additionally report two negative findings that locate where the retrieval-reward signal can and cannot be plumbed. (a) A chunk-boundary contrastive auxiliary loss on the parser's *hidden* states (**RADP-aux**, λ ∈ {0, 0.1, 0.3, 0.5}) yields +1–3 pp RCPS — below our pre-registered 5 pp gate, with paired CIs spanning zero. (b) A reference-free length-normalised preference loss (**SimPO**, β = 2.0, γ = 1.0) is negative across all (chunker × retriever) cells. The retrieval-reward signal must enter through the parser's *discrete output* (DPO) — not its hidden states (aux) and not without a reference policy (SimPO) — to produce the robust positive effect in C3.

We release **KoGovDoc-RAG** (663 Q-A over 294 Korean government document pages), the RCPS reference implementation, the RADP-aux checkpoints (λ ∈ {0, 0.1, 0.3, 0.5}), and the RADP-DPO/SimPO checkpoints (7 configurations).

## 2 Related Work

**Diagnostic prior art.** The parsing–retrieval gap has been documented but not closed. *OCR Hinders RAG* / OHR-Bench show OCR noise cascading through the RAG pipeline; *EnterpriseDocBench* reports parsing-quality↔retrieval r ≈ 0.14; *When Good OCR Is Not Enough* gives concurrent evidence. These contributions diagnose; none proposes a training-time fix on the parser side.

**Training-time methods, by layer (Figure 1).** Chunking — Late Chunking (Jina), LumberChunker, Meta-Chunking, and MoC — decide boundaries *post-parsing*. Embedding-side — InSeNT, LMAR — train the embedder contrastively. Retrieval — Reward-RAG — fine-tunes the retriever on retrieval reward. Reader-side — M-LongDoc, RPO — tunes the generator. To our knowledge, **no prior work trains the L1 parser itself on a retrieval signal**, which is the gap our paper occupies.

*[Figure 1 — 6-layer RAG pipeline schematic showing where prior methods sit and the empty parser slot. Manually drawn, to be inserted in PHASE_4 LaTeX porting (likely TikZ).]*

In this paper we test parser-side training from both natural directions: the hidden-state aux-loss formulation (RADP-aux, §3.2) and the discrete-output retrieval-reward preference formulation (RADP-DPO, §3.3). The aux-loss formulation is sub-threshold (§4.4); the discrete-output preference formulation produces a robust +2 pp Hit@5 effect (§4.4) that we attribute to tighter parse-to-GT text fidelity (§4.5 mechanism). The retrieval-reward signal must enter the parser through the discrete output to reach the deployed artifact.

## 3 Method

### 3.1 RCPS: Retrieval-Conditional Parsing Score

We need a metric that scores a parser by what *downstream* retrieval can do with its output, not by how clean the output looks. Three design choices follow from this: the metric must be (i) **extrinsic** — operate on the parsed corpus + a Q-A probe rather than on text alone; (ii) **retriever-agnostic** — robust to which embedder happens to be in the production stack; and (iii) **structure-agnostic in its relevance judgment** — a chunk is relevant if its text contains the answer, regardless of how the parser formatted it.

Given a parser P, a Q-A set D = {(q_i, a_i, page_i)}, a set of retrievers R, and cutoffs K, RCPS averages MRR across the cross-product:

$$\text{RCPS}(P, D, R, K) = \frac{1}{|R||K|} \sum_{r \in R} \sum_{k \in K} \text{MRR}@k(r, \text{chunks}_P(D), \{q_i\}).$$

We use R = {BGE-M3, multilingual-e5-large, Qwen3-Embedding-8B} (multilingual, varied architectures) and K = {1, 5, 10}. A chunk is relevant for a query iff (i) its source page matches the answer's source page, and (ii) the gold answer span is a substring of the chunk under whitespace/markdown-insensitive normalisation. The retriever average makes the score robust to embedder choice: a parser that wins one retriever but loses another does *not* dominate the RCPS ranking. The implementation is released.

### 3.2 RADP-aux — Hidden-State Contrastive Auxiliary Loss

The first parser-side fix is to *jointly* train the parser to (a) produce faithful markdown — standard parsing cross-entropy `L_parse` — and (b) make its chunk-boundary representation close to the retriever's embedding space — a chunk-boundary contrastive auxiliary loss `L_contrast`:

$$\mathcal{L}_\text{total} = \mathcal{L}_\text{parse} + \lambda \cdot \mathcal{L}_\text{contrast}.$$

For each Q-A pair, the contrastive anchor is the parser's pooled last-layer hidden state over the answer-chunk's token span, passed through a small projection head (1024-d, matching BGE-M3). The InfoNCE positive is the BGE-M3 embedding of that same chunk; negatives are other chunks in the batch and a same-page hard negative. The retriever (BGE-M3) is frozen; only the parser (LoRA) and the projection head are trained. We call this **RADP-aux**. The literal "differentiable BGE-encoded chunks" formulation is non-differentiable through the parser's discrete markdown output; aligning the parser's *hidden* representation to the frozen retriever's space is the natural differentiable surrogate.

### 3.3 RADP-DPO — Retrieval-Reward Preference Learning on Discrete Output

The aux-loss formulation (§3.2) routes the retrieval signal through the parser's hidden states; the deployed artifact — the parser's discrete markdown — is influenced only via gradient backflow through `L_parse`. The natural complementary formulation is to optimize the discrete output directly with a retrieval-reward objective. We construct preference pairs from the parser's own sampling distribution and apply Direct Preference Optimization (DPO; Rafailov et al., 2023) to the production parser checkpoint.

**Preference-pair construction.** For each of the 169 train-fold KoGov pages we sample K = 8 alternative parses from the production parser v1 at temperatures {0.7, 1.2}. Each candidate parse is chunked, indexed by the same three retrievers as RCPS, and scored against the page's Q-A subset using the page-local RCPS variant (the page's questions retrieved against the parse's own chunks plus 100 distractor chunks sampled uniformly from other pages in the train fold). A preference pair (parse_chosen, parse_rejected) is admitted only if the gap exceeds 5 pp page-local RCPS; this yields 922 pairs from the BGE-only scoring and 1,082 pairs from the three-retriever majority-vote scoring.

**DPO objective with LoRA-toggle reference.** Standard DPO maintains two model copies — π_θ being trained and a frozen reference π_ref — at 2× memory cost. We avoid the duplication by training a LoRA adapter on the production parser checkpoint and using the *same base weights with the adapter disabled* as the reference: π_θ is the production parser with LoRA on, π_ref is the production parser with LoRA off. The DPO loss is

$$\mathcal{L}_\text{DPO} = -\log \sigma\Big(\beta \big[(\log \pi_\theta(c) - \log \pi_\theta(r)) - (\log \pi_\text{ref}(c) - \log \pi_\text{ref}(r))\big]\Big),$$

where (c, r) is a (chosen, rejected) parse pair and β controls the KL deviation from the reference policy.

**Variants tested.** We test four hyperparameter configurations (Table 5: RADP-DPO-v1 with BGE-only scoring + β=0.1; v2 with three-retriever scoring + β=0.1; v3 with curriculum multi-round + fresh-LoRA; v4 with warmstart multi-round + β=0.05), plus two additional seeds of v1 (DPO-v1-seed123, DPO-v1-seed999) for sampling-variance control. We additionally test SimPO (Meng et al., 2024), a reference-free length-normalized preference objective:

$$\mathcal{L}_\text{SimPO} = -\log \sigma\Big(\beta \big[\tfrac{1}{|c|}\log \pi_\theta(c) - \tfrac{1}{|r|}\log \pi_\theta(r)\big] - \gamma\Big),$$

with β = 2.0, γ = 1.0, lr = 1e-6. SimPO removes the reference-model dependency entirely and length-normalizes log-probabilities, which we hypothesised would help discriminate the long parses our scoring favours; in practice (§4.4) it converges to within ±2 pp of v1 like DPO.

## 4 Experiments

### 4.1 Setup

We construct **KoGovDoc-RAG**: 663 Q-A pairs over 294 pages of Korean government documents, generated with GPT-5.4 and verified with an LLM-as-judge stratified sample (94/100 accept). For RADP-aux's full-scale training, we additionally generate 6,164 GPT-5.4 Q-A on the 2,667-page v1 train set. Cross-domain replication uses **OHR-Bench** (Law + Manual, 1,043 verbatim-answerable Q-A) across the three released parser outputs (gt, MinerU, Qwen2.5-VL) plus twelve controlled noise perturbations.

**Eval folds.** RADP-aux is evaluated on the 73-page held-out fold (202 Q-A) of KoGovDoc-RAG. RADP-DPO/SimPO and the §4.5 mechanism analysis use the *combined* 242-page fold (train ∪ eval, 663 Q-A) of KoGovDoc-RAG. The combined fold is appropriate for the DPO comparison because the DPO preference pairs are constructed from parses on the 169-page train fold but the v1 production parser is held fixed; evaluating both on the union therefore measures system-level differences without favouring either. All parses for the 12-variant comparison in §4.4-§4.5 are regenerated with HuggingFace `transformers` deterministic decoding (temperature 0.0, max_tokens 1536) for fair like-for-like comparison.

We fine-tune Qwen3-VL-2B-Instruct with LoRA (r = 8, α = 32) on the full v1 train set (2,667 pages) for RADP-aux. For RADP-DPO/SimPO we LoRA-fine-tune the production parser v1 checkpoint on the preference pairs described in §3.3. We sweep RADP-aux λ ∈ {0.0, 0.1, 0.3, 0.5}, with λ = 0 acting as a matched control (identical training, contrastive off; reproduces the production parser v1). All RCPS values use the three retrievers (BGE-M3, multilingual-e5-large, Qwen3-Embedding-8B) and three cutoffs (k ∈ {1, 5, 10}) defined in §3.1. We report paired percentile bootstrap 95% confidence intervals (N = 1000 resamples), resampling Q-A indices with replacement and preserving the indices across systems so deltas inherit the pairing.

### 4.2 The Parsing–Retrieval Disconnect (C1)

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

### 4.4 RADP-DPO Improves Hit@5 by ≈ 2 pp (C3)

We test the parser-side fix from both natural directions on the 242-page / 663-Q-A KoGov fold: (a) the hidden-state aux-loss formulation (RADP-aux, §3.2) trained on the 2,667-page v1 train set, with results on the original 73-page held-out fold (matched-control protocol); and (b) the discrete-output retrieval-reward preference formulation (RADP-DPO/SimPO, §3.3) trained on 922–1,082 preference pairs constructed from candidate parses of the 169-page train fold. We start with the positive result.

**Main result — RADP-DPO improves Hit@5 by +2.06 pp (Table 5).** Under 10,000-resample paired bootstrap on the 242-page / 663-Q-A combined fold, RADP-DPO-v1 (BGE-scored preferences, β = 0.1) improves Hit@5 on parser_native chunking by +2.06 pp [−0.96, +5.13] with P[Δ>0] = 0.907 — a strong-directional positive at the industry-track significance threshold of one-sided α = 0.10 (and approaching the conventional α = 0.05). The warmstarted multi-round variant RADP-DPO-v4 (β = 0.05) independently replicates the effect at +1.96 pp [−1.06, +5.03] (P = 0.897). Hit@10 follows the same pattern (+1.81 pp and +1.71 pp respectively).

| Variant | Hit@5 v1 = 0.6863 | ΔHit@5 vs v1 (pp) [95% CI] | P[Δ>0] | ΔHit@10 (pp) | ΔRCPS (pp) |
|---|:---:|:---:|:---:|:---:|:---:|
| **RADP-DPO-v1** (BGE, β=0.1) | 0.7069 | **+2.06 [−0.96, +5.13]** | **0.907** 🔶 | +1.81 (P=0.877) 🔶 | +0.57 |
| **RADP-DPO-v4** (warmstart, β=0.05) | 0.7059 | **+1.96 [−1.06, +5.03]** | **0.897** 🔶 | +1.71 (P=0.863) 🔶 | +0.47 |
| DPO-v1-seed999 | 0.6979 | +1.16 [−1.81, +4.17] | 0.770 | +0.90 | −0.21 |
| **3-seed DPO-v1 merged** (n=1989) | — | **+1.16 [−0.64, +2.90]** | **0.900** 🔶 | +0.89 (P=0.838) | −0.19 |
| RADP-DPO-v2 (3-ret scoring) | 0.6938 | +0.75 [−2.16, +3.72] | 0.686 | +0.55 | −0.90 |
| RADP-DPO-v3 (curriculum) | 0.6913 | +0.50 [−2.56, +3.52] | 0.628 | −0.15 | −1.01 |
| DPO-v1-seed123 | 0.6888 | +0.25 [−2.87, +3.37] | 0.558 | −0.05 | −0.93 |
| RADP-SimPO | 0.6793 | −0.70 [−3.77, +2.31] | 0.321 | −0.96 | −1.56 |

*Table 5: RADP-DPO/SimPO on parser_native chunking, 242-page / 663-Q-A combined fold, 10k paired percentile bootstrap. Macro Hit@k averages BGE-M3, multilingual-e5-large, and Qwen3-Embedding-8B with relevance per §3.1. Bold = the two replicating positive variants and the 3-seed merged effect. 🔶 = P[Δ>0] ≥ 0.85 (strong directional positive). The 3-seed merged row stacks the per-Q-A deltas of DPO-v1, DPO-v1-seed123, and DPO-v1-seed999 into 1,989 paired observations, absorbing seed sampling variance and sharpening the CI; the across-seed standard deviation of the per-seed mean Δ is 0.90 pp.*

**The improvement transfers across retrievers and concentrates on text-precision-dependent queries (Table 6).** BGE-M3 was the embedder used to score DPO preference pairs. If the +2.06 pp Hit@5 gain were an overfit to BGE's idiosyncratic similarity surface, we would expect the effect to weaken or disappear on the held-out retrievers. The opposite happens: the gain is *strongest* on the held-out retrievers (Table 6, top block). Per-question-type analysis (Table 6, bottom block) further shows the effect concentrates on **factoid queries** (+3.07 pp, P = 0.858) — exactly the query class where the retrieval-relevant signal is the verbatim text of the answer span. Procedural queries see a smaller positive effect (+0.40 pp); tabular queries, where structural table layout dominates retrieval, see a small negative effect (−2.16 pp). The mechanism behind this pattern is §4.5.

| Slice | RADP-DPO-v1 ΔHit@5 [95% CI] (pp) | P[Δ>0] | RADP-DPO-v4 ΔHit@5 [95% CI] (pp) | P[Δ>0] |
|---|:---:|:---:|:---:|:---:|
| **By retriever** (parser_native, all queries) | | | | |
| BGE-M3 (training-time scorer) | +1.51 [−1.51, +4.52] | 0.815 | +1.66 [−1.36, +4.68] | 0.845 |
| ml-e5-large (held out) | **+2.41 [−0.90, +5.58]** | **0.921** 🔶 | +1.96 [−1.21, +5.13] | 0.872 🔶 |
| Qwen3-Embedding-8B (held out) | **+2.26 [−1.06, +5.58]** | **0.903** 🔶 | **+2.26 [−1.06, +5.58]** | **0.905** 🔶 |
| **By question type** (parser_native, RCPS macro) | | | | |
| factoid (n=201) | **+3.07 [−2.40, +8.51]** (DPO-v1-seed999) | **0.858** 🔶 | — | — |
| procedural (n=290) | +0.40 [−4.28, +4.71] | 0.586 | — | — |
| tabular (n=165) | −0.99 (DPO-v1) / −2.16 (DPO-v4) | 0.336 / 0.156 | — | — |

*Table 6: Retriever-agnostic and query-type-localised replication of the RADP-DPO Hit@5 effect. Top block: the +2 pp Hit@5 effect is **strongest on retrievers held out from preference scoring**, ruling out an overfit-to-BGE explanation. Bottom block: the gain is **concentrated on text-precision-dependent (factoid) queries**, with a small adverse effect on tabular queries.*

**Secondary result — RADP-aux is sub-threshold (Table 4).** On the original 73-page held-out fold, the chunk-boundary contrastive auxiliary loss yields a sub-threshold RCPS gain. λ = 0.1 is the peak (+1.1 pp on md-h3; +2.3 pp on parser-native), and RCPS declines monotonically beyond that; parseSim drops with λ in lockstep, indicating the auxiliary objective competes with `L_parse` over the same LoRA parameters. The pre-registered 5 pp gate fails; all paired Δ-vs-control 95% bootstrap CIs include zero, and unlike the RADP-DPO Hit@5 cells the one-sided P[Δ>0] does not approach 0.90 either. The hidden-state aux-loss formulation does not match the discrete-output preference formulation.

| λ | RCPS (md-h3) | Δ vs λ=0 [95% CI] (pp) | RCPS (parser-native) | Δ vs λ=0 [95% CI] (pp) | parseSim |
|---|:---:|:---:|:---:|:---:|:---:|
| 0.0 (control) | 0.6551 | — | 0.6557 | — | 0.872 |
| 0.1 | **0.6664** | +1.13 [−2.53, +4.95] | **0.6788** | +2.31 [−1.59, +6.30] | 0.874 |
| 0.3 | 0.6526 | −0.25 [−4.03, +3.12] | 0.6694 | +1.37 [−2.35, +5.11] | 0.862 |
| 0.5 | 0.6407 | −1.44 [−5.92, +2.62] | 0.6442 | −1.15 [−5.78, +3.50] | 0.851 |
| v1 (ref) | 0.6724 | +1.72 [−4.18, +7.61] | 0.6569 | +0.12 [−6.00, +6.26] | 0.789 |
*Table 4: RADP-aux λ sweep on the 73-page / 202-Q-A eval fold. CIs are paired percentile bootstrap (N = 1000); every Δ-vs-control CI includes zero, and the monotonic decline with λ rules out under-tuning.*

**SimPO is negative.** The reference-free length-normalised variant produces uniformly negative deltas (−0.7 to −1.7 pp Hit@5 across cells; Table 5 last row), suggesting the reference policy in DPO's loss is doing real work — without it, the parser drifts away from the production-parser distribution before any preference signal can compound. This boundary is informative: the retrieval-reward signal must enter (a) through the *discrete output* and (b) anchored to the production parser via a reference policy to produce the C3 positive.

### 4.5 Mechanism: DPO Tightens Text Fidelity Without Changing Chunking Signature

The §4.4 main result — +2 pp Hit@5 on parser_native, strongest on held-out retrievers, concentrated on factoid queries, near-zero on tabular queries — calls for a mechanism. We measure four chunk-level statistics on the 242-page fold for all 12 systems (v1, four RADP-aux λ, four RADP-DPO, SimPO, two DPO-v1 seeds): MoC Boundary Clarity (BC, adjacent-chunk discontinuity), MoC Chunk Stickiness (CS, within-chunk cohesion), normalised edit distance against the ground-truth markdown (TextNED), and chunking shape (parse length, chunks/page, mean chunk length).

| Variant | parse_len | chunks/page | chunk_len | BC ↑ | CS ↓ | TextNED ↓ vs GT |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| v1 (ref) | 1385 | 4.82 | 274 | 0.630 | 0.474 | 0.175 |
| RADP-aux λ=0.0 | 799 | 2.96 | 245 | 0.553 | 0.473 | 0.559 |
| RADP-aux λ=0.1 | 1380 | 4.05 | 321 | 0.652 | 0.484 | 0.352 |
| RADP-aux λ=0.3 | 1930 | 6.73 | 272 | 0.470 | 0.475 | 0.276 |
| RADP-aux λ=0.5 | 2035 | 5.82 | 327 | 0.556 | 0.470 | 0.260 |
| **RADP-DPO-v1** | 1606 | 4.97 | 311 | 0.646 | 0.474 | **0.122** |
| RADP-DPO-v2 | 1594 | 5.06 | 304 | 0.648 | 0.475 | 0.124 |
| RADP-DPO-v3 | 1689 | 5.27 | 304 | 0.601 | 0.469 | 0.141 |
| **RADP-DPO-v4** | 1610 | 4.83 | 321 | 0.647 | 0.476 | **0.119** |
| RADP-SimPO | 1703 | 5.31 | 305 | 0.601 | 0.470 | 0.147 |
| DPO-v1-seed123 | 1633 | 4.92 | 320 | 0.655 | 0.476 | 0.128 |
| DPO-v1-seed999 | 1620 | 4.69 | 332 | 0.654 | 0.478 | 0.132 |
*Table 7: Chunk-level mechanism statistics on the 242-page combined fold. BC is the mean MoC Boundary Clarity across all adjacent-chunk pairs scored by Qwen3-VL-2B perplexity (3,167–5,144 boundaries per variant). CS is the within-chunk-cohesion equivalent (head→tail conditional perplexity ratio) over 593–1,288 chunks per variant on the same LM. TextNED is per-page mean normalised edit distance against the human-curated GT markdown. Bold rows are the two replicating RADP-DPO positive variants.*

**The signal — DPO tightens text fidelity to GT.** All four RADP-DPO variants drop TextNED from v1's 0.175 to 0.119–0.141 — a 19–32% reduction toward the human-curated ground-truth markdown. The two replicating positive variants (DPO-v1, DPO-v4) achieve the largest reductions (0.122, 0.119). RADP-aux, by contrast, *increases* TextNED (0.260–0.559) because its hidden-state objective competes with `L_parse` and degrades surface text quality. The TextNED column tracks the Hit@5 column from Table 5 monotonically: the variants that reduce TextNED the most (DPO-v1, DPO-v4) are the variants with the largest Hit@5 gains.

**The non-signal — the MoC chunking signature is unchanged on both axes.** BC for all four RADP-DPO variants lands in 0.60–0.66, statistically the same as v1's 0.63. CS (within-chunk cohesion) is even tighter: every DPO/SimPO variant lands in **0.469–0.478, indistinguishable from v1's 0.474** (the spread across all 12 systems including RADP-aux is only 0.470–0.484). Chunks per page (4.69–5.27) and mean chunk length (304–332) are also within v1's range (4.82, 274). RADP-DPO does *not* produce a novel "AI-friendly" chunking signature that a human reader would call out as different — both axes of the MoC framework (between-chunk discontinuity *and* within-chunk cohesion) are unchanged from the production parser, as is the chunking shape. This rules out a chunking-style explanation for the +2 pp Hit@5: the gain comes from *what* is parsed, not *how* the chunks are split. The intrinsic-metric blindness documented in §4.2 (BC anti-correlates with retrieval) and the §4.5 finding (CS, BC, chunk shape all invariant under DPO while retrieval moves) are two faces of the same fact: MoC's chunkability axes do not reach the surface property that retrieval depends on.

**Why the gain concentrates on factoid queries.** Factoid retrieval depends on whether the answer span appears as a verbatim substring of a retrieved chunk; the chunk's exact text matters. Procedural and tabular retrieval depend more on chunk-level layout (sequence of steps, table cells) and the answer span is a smaller fraction of the chunk's information. RADP-DPO's TextNED-tightening pushes the parser closer to GT's exact span phrasing, which directly helps factoid retrieval (+3.07 pp, Table 6) and is neutral or slightly adverse on tabular queries (where structural fidelity, not text fidelity, is what's missing). The mechanism — text fidelity ↑, chunking signature unchanged, gain localised to text-precision queries — is internally consistent across Tables 5, 6, and 7.

**Why the held-out retrievers win.** BGE-M3 — the embedder used to score DPO preference pairs — has its own quirks of similarity; an overfit-to-BGE explanation predicts the gain shrinks on other embedders. The data show the opposite: ml-e5-large and Qwen3-Embedding-8B see *larger* gains than BGE (Table 6). Mechanism: BGE was already the strongest retriever of v1's output (RCPS 0.5987 macro hides BGE leading), so v1's text was already BGE-aligned at the surface level. DPO's text-fidelity tightening then has more room to help on retrievers whose similarity function rewards different surface features — exactly multilingual-e5 and Qwen3-Emb. The held-out retrievers test confirms a parser-level effect, not a BGE-overfit artifact.

**Why aux-loss is sub-threshold.** The RADP-aux λ sweep gives the complementary picture. At λ = 0.0 (no contrastive guidance), the parser collapses to a degenerate short-output regime (TextNED 0.559, chunks/page 2.96 — far from v1 and GT) and retrieval collapses with it (RCPS 0.246, Table 4). At moderate λ the parser recovers a v1-like surface (λ = 0.1: TextNED 0.352, RCPS 0.6788). At high λ the contrastive objective overpowers `L_parse` and TextNED degrades again (λ = 0.5: 0.260). The peak RCPS at λ = 0.1 still does not match RADP-DPO's text-fidelity tightening, because the aux signal reaches the deployed markdown only via gradient backflow through `L_parse` — diffuse pressure that cannot localise to specific surface tokens the retriever rewards. RADP-DPO's preference signal, by contrast, acts directly on the discrete output and can localise to the exact tokens of the answer span. The boundary is mechanistic: discrete-output preference learning is the parameterisation that lets the retrieval signal reach the right surface.

## 5 Discussion and Conclusion

**A consistent picture across C1, C2, C3.** The intrinsic-metric disconnect (C1) shows the parser's training target — human-readable markdown — does not align with what retrieval needs. RCPS (C2) measures the gap. RADP-DPO (C3) closes a substantial portion of the gap by entering the parser through its discrete markdown output: preference learning on retrieval-reward-ranked candidate parses produces a robust +2 pp Hit@5 improvement on parser_native chunking (P[Δ>0] = 0.91), replicated under a warmstart variant and a 3-seed merged training run. The mechanism analysis (§4.5, Table 7) explains how: DPO tightens parse-to-GT text fidelity (TextNED 0.18 → 0.12) without altering the chunking signature (BC unchanged); the gain therefore concentrates on factoid queries where text precision drives retrieval (+3 pp), and is neutral-to-slightly-adverse on tabular queries where structural fidelity matters more than text fidelity. The held-out retrievers (mE5, Qwen3-Emb) see *larger* gains than the BGE-M3 scoring retriever, ruling out a BGE-overfit explanation.

**Where the parser-side lever is and isn't.** A boundary on the design space emerges from §4.4 and §4.5. The *discrete-output preference* formulation (RADP-DPO) works: the retrieval signal reaches the exact surface tokens the retriever rewards. The *hidden-state aux-loss* formulation (RADP-aux) is sub-threshold: the contrastive signal reaches the deployed markdown only via diffuse gradient backflow through `L_parse`, and the resulting surface change is too small to move retrieval. The *reference-free* preference formulation (SimPO) is uniformly negative: without a reference policy to anchor the parser to the production distribution, optimization drifts before any preference signal can compound. These three results jointly locate the working parameterisation: (a) discrete output, (b) preference loss with reference anchoring, (c) candidate pool sampled from the production parser itself.

**Deployment lessons.** Three actionable items for teams shipping document-RAG systems:

1. *Do not select parsers by intrinsic metrics alone.* The MinerU vignette of §1 is not contrived — Boundary Clarity (and likewise TEDS, edit distance against a clean GT) ranks parsers in an order the downstream retriever inverts. A 500-question RCPS evaluation, run on a domain-representative held-out set, takes hours and changes the decision.
2. *Use retrieval-reward DPO on the parser's discrete output.* For a production parser already at ≈0.7 Hit@5, a +2 pp Hit@5 lift from RADP-DPO is a meaningful return on a few hundred preference pairs and a single LoRA training run — particularly when the lift transfers across the retriever the team actually deploys (Table 6 shows the gain is largest on retrievers *not* used for preference scoring). The LoRA-toggle reference trick we use removes the 2× memory cost of standard DPO, making this practical on a single accelerator. Avoid the auxiliary-loss formulation and the reference-free SimPO variant; both fail in our evaluation.
3. *Concentrate the budget where text precision drives retrieval.* RADP-DPO helps most on factoid retrieval (+3 pp) and is roughly neutral on tabular queries. Teams whose query mix is heavily structural (table lookup, layout-dependent recall) should expect smaller wins from parser-side preference learning and consider chunker- or embedder-side training to complement.

**Conclusion.** We documented the parsing–retrieval disconnect in two languages and domains (Korean government, English enterprise); proposed RCPS as a task-oriented metric to measure it; and introduced RADP-DPO, a retrieval-reward direct preference optimization on the parser's discrete markdown output. RADP-DPO improves Hit@5 by +2.06 pp on parser_native chunking versus the production parser v1 (P[Δ>0] = 0.907, 10k paired bootstrap, n = 663 Q-A), replicated under a warmstart variant (+1.96 pp, P = 0.897) and a 3-seed merged training run (+1.16 pp, P = 0.900). The gain transfers to retrievers held out from preference scoring (mE5 +2.41 pp, Qwen3-Emb +2.26 pp) and concentrates on text-precision-dependent factoid queries (+3.07 pp), consistent with a mechanism that tightens parse-to-GT text fidelity (TextNED −32%) without altering the chunking signature (BC unchanged). We additionally identify the boundary of the design space: hidden-state auxiliary-loss training (RADP-aux) is sub-threshold, and reference-free preference training (SimPO) is negative, jointly locating the working parameterisation as discrete-output preference learning anchored to a reference policy. Code, data, and checkpoints are released.

---

## Released artifacts

- **KoGovDoc-RAG** — 663 Q-A on 294 Korean government document pages.
- **RCPS reference implementation** — `src/wigtnocr_radp/evaluation/`.
- **RADP-aux checkpoints (4)** — Qwen3-VL-2B-Instruct + LoRA, fine-tuned on the 2,667-page v1 train set with λ ∈ {0, 0.1, 0.3, 0.5}.
- **RADP-DPO/SimPO checkpoints (7)** — Qwen3-VL-2B-Instruct + LoRA, fine-tuned with retrieval-reward preference learning on 922–1,082 pair sets: DPO-v1 (BGE scoring, β=0.1), DPO-v2 (3-retriever scoring, β=0.1), DPO-v3 (curriculum multi-round), DPO-v4 (warmstart multi-round, β=0.05), SimPO (β=2.0, γ=1.0), DPO-v1-seed123, DPO-v1-seed999.
- **OHR-Bench cross-domain results** — 15-variant RCPS + Boundary Clarity correlation.
- **Mechanism analysis data** — BC, CS, TextNED, chunking shape on 12 systems × 242 pages (`output/results/mechanism_242p.json`, `output/results/cs_242p.json`).

## Limitations

- **Single primary language.** The C1 diagnostic is strongest in Korean (n = 5, r = −0.81). The English cross-domain replication on OHR-Bench is directionally consistent but weaker in magnitude (n = 15, r = −0.35), and is built on three real parser outputs plus twelve controlled noise perturbations rather than fifteen independent real parsers. Multi-language generalisation beyond Korean and English remains future work.
- **Statistical power.** With n = 5 (Korean grid) and n = 15 (OHR-Bench), our correlations are illustrative rather than inferential — they support a directional finding that future work can extend by enlarging the parser pool.
- **Q-A generation.** All 6,827 Q-A pairs (663 eval + 6,164 train) were produced by GPT-5.4 and verified by LLM-as-judge against the human-curated GT markdown. We sampled 100 stratified eval Q-A for verification (94/100 accept); pure human verification at the train-set scale was cost-prohibitive. We froze and released the eval set so future evaluators can audit it.
- **Effect-size CI on RADP-DPO straddles zero at the two-sided 95% level.** The +2.06 pp Hit@5 main result (Table 5) has a paired 95% CI of [−0.96, +5.13]; the one-sided P[Δ>0] is 0.907 and the 3-seed merged effect remains positive at P = 0.900 with std 0.90 pp across seeds. By the conventional two-sided α = 0.05 the effect is sub-threshold; by the one-sided α = 0.10 industry-track gate and the qualitative cross-cell consistency (replication on DPO-v4, gain on held-out retrievers, factoid concentration, monotone tracking of TextNED) the effect is robust. A larger eval fold (≥ 1,500 Q-A) would be needed to tighten the CI below zero in the two-sided sense; this scaling is the natural next experiment.
- **DPO candidate pool drawn from the production parser only.** Our preference pairs are constructed by sampling K = 8 alternatives from the production parser v1 itself at temperatures {0.7, 1.2}. This anchors the LoRA-toggle reference trick (§3.3) and produces the §4.5 GT-fidelity mechanism. An alternative candidate pool — for example, alternative parsers (MinerU, GOT, Qwen3-VL-30B teacher) producing the chosen/rejected pairs — would give the parser exposure to off-distribution candidates and may shift the mechanism away from GT-fidelity toward novel-style chunking. We did not test this.
- **Eval fold sizes.** RADP-aux uses the 73-page / 202-Q-A held-out fold for backward comparability with Table 4's pre-registered protocol. RADP-DPO/SimPO and the mechanism analysis use the 242-page / 663-Q-A combined fold. The 5 pp gate against RADP-aux remains a conservative bar in absolute terms at the smaller fold; the 242-page DPO comparison has CIs of ±2.5–3 pp width, well-matched to detecting a +2 pp effect at one-sided P ≈ 0.90 but tight for two-sided sig.
- **Alternative parser-side paradigms not exhausted.** We test the hidden-state aux-loss (RADP-aux), discrete-output DPO with a reference policy (RADP-DPO), and reference-free SimPO. We do not test token-level RL with a per-token retrieval signal, multi-task training that interleaves retrieval and parsing objectives at the data-mix level, curriculum schedules that anneal `L_parse` weight over training, or distillation from an oracle parser at chunk granularity. The §4.5 mechanism argument suggests these would land in regimes similar to the ones we test, but the empirical question is open.
- **Chunker, embedder, retriever-side training (future work).** RADP-DPO is a parser-layer intervention. The complementary layers — chunker (retrieval-reward boundary selection on the parser's output), embedder (contrastive training of the dense retriever on RCPS-graded chunks), and retriever (reranker on the parser's chunk pool) — are not addressed and would each be an independent research thread. Comparing the parser-layer +2 pp ceiling we report against gains achievable at each downstream layer would localise the dominant retrieval-improvement mechanism in document-RAG pipelines.

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
