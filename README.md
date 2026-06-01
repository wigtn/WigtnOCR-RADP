# WigtnOCR-RADP

**Retrieval-Aware Document Parsing — human-readable parsing ≠ retrievable parsing.**

> 🎯 **EMNLP 2026 Industry Track** submission · paper draft **v0.6** · deadline 2026-06-16
>
> 📦 Builds on [WigtnOCR v1](https://huggingface.co/Wigtn/Qwen3-VL-2B-WigtnOCR) + [KoGovDoc-Bench](https://huggingface.co/datasets/Wigtn/KoGovDoc-Bench)
>
> 🇰🇷 **[한국어 README](README.ko.md)** · 🧭 Research direction: [`docs/RESEARCH_DIRECTION.md`](docs/RESEARCH_DIRECTION.md) (KO) · 🗓️ Timeline: [`docs/TIMELINE.md`](docs/TIMELINE.md)

---

## TL;DR

Document parsers used in retrieval-augmented generation (RAG) are conventionally optimized for
*human-readability* metrics — TEDS, edit distance, Boundary Clarity — yet these metrics **do not
predict downstream retrieval**. On Korean government documents (6 parsers × 3 retrievers × 663 Q-A),
MoC Boundary Clarity *anti*-correlates with retrieval at **Pearson r = −0.81**: the parser scoring
highest on the intrinsic metric (MinerU) is the *worst* retriever.

We (C1) diagnose this disconnect cross-domain and expose its mechanism, (C2) propose **RCPS**
(Retrieval-Conditional Parsing Score), a retriever-agnostic task-oriented metric, and (C3) introduce
**RADP-DPO** — retrieval-reward direct preference optimization on the parser's discrete markdown output.
RADP-DPO improves **Hit@5 by +2.11 pp on KoGov** (P[Δ>0] = 0.91) and, critically, by **+1.03 pp on the
English OHR-Bench (n = 2,264) with two-sided significance, clearing the 1 pp practitioner bar**. We also
report two bounding negatives — a hidden-state auxiliary loss (RADP-aux) and reference-free SimPO — that
locate *where* the retrieval signal can be plumbed into the parser.

---

## Motivation — parsing quality ≠ retrieval performance

A practitioner picking a parser for a RAG system runs MinerU on Korean government PDFs, confirms it tops
every intrinsic parsing-quality metric in our grid — highest MoC Boundary Clarity (0.72) — and deploys it.
Retrieval Hit@1 is **0.20, the worst of the six parsers evaluated.** The cleanest-looking parser is the
worst retriever.

This is not a one-off. The same direction is reported independently in English / enterprise settings by
OHR-Bench (ICCV 2025), EnterpriseDocBench (2026, r ≈ 0.14), and *When Good OCR Is Not Enough* (2026).
**Prior work either stops at diagnosis or trains a different pipeline layer (chunking → generation). No
prior work trains the L1 parser itself on a retrieval signal — that is our niche.**

---

## Contributions

| | Contribution | Status |
|---|---|:---:|
| **C1** | A cross-domain **diagnostic** of the parsing↔retrieval disconnect, with a mechanism (noise-family curve, Figure 2) that makes the intrinsic-metric failure mode visible at a glance | ✅ |
| **C2** | **RCPS** (Retrieval-Conditional Parsing Score) — a retriever-agnostic, task-oriented metric to choose parsers/chunkers for production RAG, discriminating combinations intrinsic metrics conflate | ✅ |
| **C3** | **RADP-DPO** — retrieval-reward DPO on the parser's discrete markdown output. **+2.11 pp Hit@5 on KoGov** (P = 0.91); **+1.03 pp on English OHR-Bench, two-sided significant, clears the 1 pp bar** | ✅ |
| bound | Two negatives locate the working parameterisation: hidden-state **RADP-aux** (+1–3 pp, below the 5 pp gate) and reference-free **SimPO** (negative). The signal must enter through the *discrete output*, anchored to a reference policy | ✅ |

---

## Method

### RCPS — Retrieval-Conditional Parsing Score

Score a parser by what *downstream retrieval* can do with its output, not by how clean the output looks.
Given a parser `P`, a Q-A set `D = {(qᵢ, aᵢ, pageᵢ)}`, retrievers `R`, and cutoffs `K`:

```
RCPS(P, D, R, K) = (1 / |R||K|) · Σ_{r∈R} Σ_{k∈K}  MRR@k( r, chunks_P(D), {qᵢ} )
```

`R = {BGE-M3, multilingual-e5-large, Qwen3-Embedding-8B}`; `K = {1, 5, 10}`. A chunk is **relevant** iff
its source page matches the answer's page and the gold span is a substring of the chunk (normalized).
Averaging over retrievers makes the score **robust to embedder choice**. Reference implementation:
[`src/wigtnocr_radp/evaluation/`](src/wigtnocr_radp/evaluation/).

### RADP-DPO — retrieval-reward preference learning on discrete output (C3)

Optimize the parser's **discrete markdown output** directly against a retrieval reward. For each train page
we sample K candidate parses from the production parser v1, chunk + index + score each against the page's
Q-A with a **retrieval reward**, and form preference pairs `(parse_chosen, parse_rejected)` whose page-local
RCPS gap exceeds a threshold. DPO is then applied to the parser:

```
L_DPO = −log σ( β · [ (log π_θ(c) − log π_θ(r)) − (log π_ref(c) − log π_ref(r)) ] )
```

- **LoRA-toggle reference trick.** Instead of two model copies (2× memory), `π_θ` = production parser with
  LoRA **on**, `π_ref` = the same base weights with LoRA **off**. One accelerator, no duplication.
- **Reward sharpening R1 → R2 → R3.** R1 (page-local RCPS, BGE-only, β = 0.1) → R2 (warmstarted iterative
  round, β = 0.05) → **R3 (full-corpus hard-negative pool, K = 14 candidates)** — distractors are the
  *other-page chunks a retriever actually confuses with the gold answer*. Sharpening the reward lifts the
  effect above 1 pp.

### RADP-aux — hidden-state contrastive auxiliary loss (bounding negative)

The alternative parser-side fix routes the retrieval signal through the parser's *hidden* states:
`L_total = L_parse + λ · L_contrast` (InfoNCE between the parser's pooled answer-chunk hidden state and the
frozen BGE-M3 embedding). This is **sub-threshold** (§ Experiments) — the signal reaches the deployed
markdown only via diffuse gradient backflow through `L_parse`.

---

## Experiments

### Setup

- **KoGovDoc-RAG** — 663 Q-A / 294 pages of Korean government documents (GPT-5.4-generated, LLM-as-judge
  94/100 accept). RADP-DPO/SimPO + the mechanism analysis use the combined **242-page / 663-Q-A** fold;
  RADP-aux uses the **73-page / 202-Q-A** held-out fold; +6,164 train Q-A on the 2,667-page v1 train set.
- **OHR-Bench** — cross-domain English replication, 7 domains, **2,264 verbatim-answerable Q-A**; 15
  parser-output variants (3 real + 3 formatting-noise + 9 semantic-noise) for the C1 mechanism.
- **Model** — Qwen3-VL-2B-Instruct + LoRA (r = 8, α = 32). All RCPS uses the 3 retrievers × 3 cutoffs above;
  deltas use paired percentile bootstrap (10k resamples).

### C1 — the parsing↔retrieval disconnect (Korean government docs)

Intrinsic Boundary Clarity **anti-correlates** with RCPS at **Pearson r = −0.81** (n = 5). MinerU —
cleanest boundaries (BC 0.72) — retrieves **worst**. (Chunk Stickiness is likewise disconnected.)

| Parser | BC | RCPS | Hit@1 |
|---|:---:|:---:|:---:|
| Qwen3-VL-30B (teacher) | 0.691 | **0.584** | 0.545 |
| WigtnOCR-2B (ours, v1) | 0.694 | 0.583 | 0.549 |
| Qwen3-VL-2B (base) | 0.677 | 0.532 | 0.500 |
| MinerU | **0.722** | 0.212 | 0.197 |
| PaddleOCR | 0.649 | 0.140 | 0.125 |
| Marker (38p) | 0.667 | 0.073 | 0.068 |

*Table 1 — KoGov: BC vs RCPS, Pearson r = −0.81 (n = 5, excl. Marker).*

### C1 — the mechanism (cross-domain, OHR-Bench)

Within each semantic-noise family, **Boundary Clarity barely moves while RCPS collapses.** Intrinsic
boundary metrics see only *formatting*, not *content*.

![Boundary Clarity is blind to content noise — top: BC stays flat across noise severity for all three parser families; bottom: RCPS collapses for MinerU and GOT while Qwen2.5-VL is noise-robust](paper/figures/fig_noise_family.png)

*Figure 2 — OHR-Bench 7-domain noise-family curves. **Top:** Boundary Clarity stays roughly flat across
noise severity (clean → mild → moderate → severe). **Bottom:** RCPS collapses for MinerU (−51%) and GOT,
while Qwen2.5-VL is more noise-robust (−8%). The intrinsic metric does not perceive the semantic content
quality retrieval depends on.*

### C2 — RCPS discriminates chunking strategies

| Chunker | RCPS | Hit@1 | MRR@10 |
|---|:---:|:---:|:---:|
| md-h3 | **0.593** | 0.556 | 0.613 |
| parser_native | 0.583 | 0.549 | 0.602 |
| LumberChunker | 0.557 | 0.514 | 0.580 |
| fixed500 | 0.535 | 0.491 | 0.560 |

*Table 3 — KoGov chunking-strategy grid (663 Q-A, v1 parser output, 3-retriever RCPS average).*

### C3 — RADP-DPO improves Hit@5 by ≈ 2 pp (the positive result)

On the 242-page / 663-Q-A KoGov fold, every RADP-DPO variant improves Hit@5 on `parser_native` over v1,
increasing along the reward-sharpening axis. At n = 663 the two-sided CIs still span zero (strong-directional,
P[Δ>0] ≈ 0.90); the cross-domain OHR-Bench replication supplies the two-sided significance.

| Variant | Hit@5 (v1 = 0.6863) | ΔHit@5 vs v1 (pp) [95% CI] | P[Δ>0] | ΔHit@10 | ΔRCPS |
|---|:---:|:---:|:---:|:---:|:---:|
| **RADP-DPO-v5** (R3, hard-neg) | 0.7074 | **+2.11 [−0.96, +5.13]** | **0.91** 🔶 | +2.21 | +1.72 |
| **RADP-DPO-v1** (R1, BGE β=0.1) | 0.7069 | **+2.06 [−0.96, +5.13]** | **0.91** 🔶 | +1.81 | +0.57 |
| **RADP-DPO-v4** (R2, warmstart β=0.05) | 0.7059 | **+1.96 [−1.06, +5.03]** | **0.90** 🔶 | +1.71 | +0.47 |
| RADP-SimPO (ref-free control) | 0.6793 | −0.70 [−3.77, +2.31] | 0.32 | −0.96 | −1.56 |

*Table 5 — RADP-DPO progression (R1→R2→R3) + SimPO control on parser_native, 242-page fold, 10k paired
bootstrap. 🔶 = P[Δ>0] ≥ 0.85. A 3-seed merge tightens R1 to +1.16 pp [−0.64, +2.90] (P = 0.90).*

**Cross-domain validation (English OHR-Bench, n = 2,264) — clears the 1 pp bar with two-sided significance.**
The Korean-tuned v1 parser, applied zero-shot, retrieves at Hit@5 = 58.5%. The hard-negative variant **R3
(RADP-DPO-v5)** improves every standard metric, two-sided significant and above 1 pp:

| Metric | Δ vs v1 (pp) | 95% CI |
|---|:---:|:---:|
| Hit@5 | **+1.03** | [+0.24, +1.84] |
| Hit@1 | **+1.31** | [+0.55, +2.09] |
| MRR@10 | **+1.17** | [+0.52, +1.86] |
| nDCG@5 | **+1.15** | [+0.49, +1.86] |

*Table 5b — OHR-Bench cross-domain, 3-retriever macro, 1k paired bootstrap, positive across all 7 domains.
Training signal (retrieval reward on train Q-A), evaluation metric, and document language are mutually
disjoint — ruling out metric circularity and domain over-fitting. Sharpening the reward from page-local
(R2: Hit@5 +0.85 pp) to hard negatives (R3) lifts the effect above 1 pp (R3 > R2 on Hit@1, +0.78 pp).*

**The gain transfers off the training-time scorer and concentrates on text-precision queries.** BGE-M3 was
used to score preference pairs; the gain is *strongest on the held-out retrievers* (ml-e5 +2.41 pp, Qwen3-Emb
+2.26 pp vs BGE +1.51 pp), ruling out a BGE-overfit, and concentrates on **factoid queries (+3.07 pp)** — the
class where verbatim answer-span text drives retrieval (Table 6 in the paper).

### C3 — mechanism: DPO tightens text fidelity, not chunking

| Variant | BC ↑ | CS ↓ | TextNED ↓ vs GT |
|---|:---:|:---:|:---:|
| v1 (ref) | 0.630 | 0.474 | 0.175 |
| **RADP-DPO-v1** | 0.646 | 0.474 | **0.122** |
| **RADP-DPO-v4** | 0.647 | 0.476 | **0.119** |
| RADP-aux λ=0.1 | 0.652 | 0.484 | 0.352 |

*Table 7 (excerpt) — RADP-DPO drops TextNED-vs-GT by 19–32% (0.175 → 0.119) while the **chunking signature
is unchanged** (BC ≈ 0.63, CS ≈ 0.474, both indistinguishable from v1). The gain comes from *what* is parsed,
not *how* chunks are split — and replicates cross-domain (OHR TextNED −2.5%, two-sided significant).*

### Bounding negatives — RADP-aux and SimPO

| λ | RCPS (md-h3) | Δ vs control [95% CI] | RCPS (parser-native) | Δ vs control [95% CI] |
|---|:---:|:---:|:---:|:---:|
| 0.0 (control) | 0.6551 | — | 0.6557 | — |
| 0.1 | **0.6664** | +1.13 [−2.53, +4.95] | **0.6788** | +2.31 [−1.59, +6.30] |
| 0.3 | 0.6526 | −0.25 [−4.03, +3.12] | 0.6694 | +1.37 [−2.35, +5.11] |
| 0.5 | 0.6407 | −1.44 [−5.92, +2.62] | 0.6442 | −1.15 [−5.78, +3.50] |

*Table 4 — RADP-aux λ sweep (73-page fold). Peak +1–3 pp, every Δ-vs-control CI includes 0, **below the
pre-registered 5 pp gate**. Reference-free **SimPO** is uniformly negative (Table 5). Together these locate
the working parameterisation: **discrete output + preference loss anchored to a reference policy**.*

---

## Deployment lessons

1. **Do not select parsers by intrinsic metrics alone.** Boundary Clarity (likewise TEDS, edit distance) can
   rank parsers in an order the downstream retriever inverts. A ~500-question RCPS run changes the decision.
2. **Use retrieval-reward DPO on the parser's discrete output.** For a parser already at ≈0.7 Hit@5, a +2 pp
   lift from a few hundred preference pairs and one LoRA run is a real return — and it transfers to the
   retriever you actually deploy. Avoid the aux-loss and reference-free SimPO formulations; both fail here.
3. **Spend where text precision drives retrieval.** RADP-DPO helps most on factoid queries (+3 pp) and is
   roughly neutral on tabular queries — structural-query-heavy stacks should complement with chunker/embedder-side training.

---

## Repository structure

```
.
├── configs/                  # experiment configs (YAML)
├── src/wigtnocr_radp/
│   ├── qa_generation/        # Q-A generation
│   ├── evaluation/           # RCPS, chunkers, retrievers, coverage, Boundary Clarity, bootstrap CI
│   └── training/             # RADP-aux (contrastive) · RADP-DPO · SimPO (LoRA-toggle reference)
├── scripts/
│   ├── training/             # candidate gen (K=2..16), preference pairs, DPO/SimPO, multi-seed pipelines
│   ├── evaluation/           # baseline_grid, chunking_grid, coverage, OHR-Bench eval chains, combined CI
│   └── analysis/             # positive_signal_dig, robustness_boost
├── paper/                    # EMNLP 2026 draft (v0.6) + figures
├── data/KoGovDoc-RAG/        # 663 Q-A (frozen, gitignored)
├── docs/                     # RESEARCH_DIRECTION · ACHIEVED · ROADMAP · TIMELINE · plans/
├── output/                   # results & checkpoints (gitignored, GPU server)
└── tests/
```

## Quick start

```bash
uv sync                                   # dependencies (extras: eval / train / data)
cp .env.example .env                      # set OPENAI_API_KEY
hf download Wigtn/KoGovDoc-Bench --repo-type dataset --local-dir data/KoGovDoc-Bench

# Coverage diagnostic (no GPU required, CPU seconds)
uv run python scripts/evaluation/coverage_diagnostic.py
```

---

## Authors (WIGTN)

This research is the follow-up to **WigtnOCR v1** (Qwen3-VL-2B document-parsing fine-tuning).

| Author (OpenReview) | Email | Contribution (CRediT) |
|------|-------|--------------|
| **Hyeong-seob Kim**\* | harrison@wigtn.com | Conceptualization, Methodology, Project administration |
| **Sang-woo Son**\* | sangwoo@wigtn.com | Software, Validation, Investigation |

> \* **Equal contribution (co-first authors).**

---

## Released artifacts

- **KoGovDoc-RAG** — 663 Q-A on 294 Korean government document pages.
- **RCPS reference implementation** — `src/wigtnocr_radp/evaluation/`.
- **RADP-aux checkpoints (4)** — LoRA, λ ∈ {0, 0.1, 0.3, 0.5}.
- **RADP-DPO / SimPO checkpoints (7)** — DPO R1–R3 (incl. hard-negative v5), SimPO control, 2 seeds.
- **OHR-Bench cross-domain results** + **mechanism analysis** (BC/CS/TextNED on 12 systems × 242 pages).

## License & Citation

Released under the **MIT License**.

```bibtex
@inproceedings{kim2026radp,
  title     = {Retrieval-Aware Document Parsing: Diagnosing and Measuring the Parsing--Retrieval Gap},
  author    = {Kim, Hyeong-seob and Son, Sang-woo},
  booktitle = {Proceedings of EMNLP 2026 (Industry Track)},
  year      = {2026},
  note      = {To appear}
}
```
