# WigtnOCR-RADP

**Retrieval-Aware Document Parsing (RADP) — the parser that *looks* best is not the one retrieval wants.**

> 🎯 **EMNLP 2026 Industry Track** submission · paper draft **v0.8** (2026-06-07) · deadline 2026-06-16
>
> 📄 Title: *Retrieval-Conditional Parsing Score (RCPS): Choosing Document Parsers by Retrieval, Not by Appearance*
>
> 📦 Builds on [WigtnOCR v1](https://huggingface.co/Wigtn/Qwen3-VL-2B-WigtnOCR) + [KoGovDoc-Bench](https://huggingface.co/datasets/Wigtn/KoGovDoc-Bench)
>
> 🇰🇷 **[한국어 README](README.ko.md)** · 🧭 [`docs/RESEARCH_DIRECTION.md`](docs/RESEARCH_DIRECTION.md) (KO) · 🗓️ [`docs/TIMELINE.md`](docs/TIMELINE.md)

---

## TL;DR

Document parsers used in retrieval-augmented generation (RAG) are conventionally chosen by *intrinsic*
"clean output" metrics — edit distance, Boundary Clarity — on the assumption that cleaner parser output
retrieves better. **It doesn't.** On Korean government documents (6 parsers × 3 retrievers × 663 Q–A),
MoC Boundary Clarity **anti-correlates** with retrieval at **Pearson r = −0.81 (n = 5)**: the
cleanest-boundary parser (MinerU) is the *worst* retriever, and choosing the parser by retrieval rather
than by appearance changes **Hit@1 by +35.1 pp (0.197 → 0.549; 2.8× relative)**.

**Selection, not training, is the headline.** We make four contributions:

- **C1** — diagnose the parsing↔retrieval disconnect and its mechanism (intrinsic metrics see *formatting*, not *content*).
- **C2** — a **retriever-free coverage diagnostic** that localizes the fault to a pipeline layer: **20.2%** of answers are *absent* from the parser output (a parser fault), constant across 8 chunkers.
- **C3** — **RCPS** (Retrieval-Conditional Parsing Score): a no-training, retriever-grounded **protocol** for choosing parsers *and* chunkers; an ablation shows it is not single-embedder MRR.
- **C4** — a bounded map of parser-side training: best-of-K **fidelity distillation (RADP-Distill)** gives **+1.22 pp OHR-Bench Hit@5**, and a matched control shows **no evidence the retrieval reward improves over fidelity-based selection** (substantially overlapping CIs). A hidden-state auxiliary loss (RADP-aux) is sub-threshold and reference-free SimPO is negative.

We release **KoGovDoc-RAG** (663 Q–A over 294 Korean government pages) with a reference implementation of RCPS and the RADP-Distill checkpoint.

---

## Motivation — parsing quality ≠ retrieval performance

A practitioner picking a parser for a RAG system runs MinerU on Korean government PDFs, confirms it tops
the intrinsic parsing-quality grid — highest MoC Boundary Clarity (0.72), matched only by Marker — and
ships it. Retrieval Hit@1 is **0.20, the worst of the six parsers evaluated.** The cleanest-looking parser
is the worst retriever.

This is not a one-off. The same direction is reported independently in English / enterprise settings by
OHR-Bench (ICCV 2025), EnterpriseDocBench (2026), and *When Good OCR Is Not Enough* (2026).
**Prior work either stops at diagnosis or trains a different pipeline layer (chunking → retriever →
generator). No prior work selects, or trains, the L1 parser itself on a retrieval signal — that is our niche.**

---

## Contributions

| | Contribution | Headline result |
|---|---|---|
| **C1** | The parsing↔retrieval **disconnect** and its mechanism. Under controlled semantic-noise perturbations on English OHR-Bench, Boundary Clarity stays flat while retrieval collapses — intrinsic boundary metrics track *formatting*, not *content*. | BC↔RCPS **r = −0.81** (n=5); parser choice alone moves **Hit@1 by +35.1 pp** (0.197→0.549; 2.8×) |
| **C2** | A **retriever-free coverage diagnostic** — classify each answer *covered / split (chunker fault) / absent (parser fault)*; a rule computable *before* any retriever runs. | **20.2% absent** vs ≤2.3% split, constant across 8 chunkers ⇒ fix the parser |
| **C3** | **RCPS** — a retriever-averaged, format-normalised, held-out-Q–A **protocol** for choosing parsers/chunkers with no training. Ablation: it is **not** single-embedder MRR. | retriever-averaging flips the top parser; **Kendall τ = 0.87** vs naive MRR |
| **C4** | A **bounded** map of parser-side training. Best-of-K **fidelity distillation** is the lever; the retrieval-reward apparatus adds nothing over it. RADP-aux sub-threshold, SimPO negative. | **RADP-Distill +1.22 pp** OHR-Bench Hit@5 [+0.35, +2.15] (n=2,264) |

---

## Method

### RCPS — Retrieval-Conditional Parsing Score (C3)

Score a parser by what *downstream retrieval* does with its output, not by how clean the output looks.
RCPS is **not a new similarity function** but a protocol wrapping ordinary retrieval MRR in three choices:
**(i) extrinsic** (score on a held-out Q–A probe, not on the text), **(ii) retriever-averaged** (over
several embedders, so the ranking does not hinge on the production one), **(iii) format-normalised**
relevance (a chunk is relevant iff its text contains the answer span, however formatted).

```
RCPS(P, D, R, K) = (1 / |R||K|) · Σ_{r∈R} Σ_{k∈K}  MRR@k( r, chunks_P(D), {qᵢ} )
```

`R = {BGE-M3, multilingual-e5-large, Qwen3-Embedding-8B}`; `K = {1, 5, 10}`. A chunk is **relevant** iff
its source page matches the answer's page and the gold span is a substring of the chunk (whitespace- and
markdown-insensitive). Run on a few hundred held-out Q–A with **no training**. Reference implementation:
[`src/wigtnocr_radp/evaluation/`](src/wigtnocr_radp/evaluation/).

### Coverage diagnostic — parser vs chunker (C2)

RCPS scores parser + chunker + retriever jointly, so a low score does not say *which* layer is at fault.
Holding the parser output fixed and varying the chunker, classify each gold answer as **covered**, **split**
(a boundary cut through it — a chunker fault, recoverable with overlap) or **absent** (not in the parser
output at all — a parser fault, unrecoverable by any chunking). The rule: *if absent dominates, fix the
parser; if split dominates, fix the chunker.* Code: [`scripts/evaluation/coverage_diagnostic.py`](scripts/evaluation/coverage_diagnostic.py).

### Parser-side training — what works, and what doesn't (C4)

When the coverage diagnostic points to the parser, we test parser-side training from both natural directions.

- **RADP-aux** *(hidden-state auxiliary loss — sub-threshold).* `L_total = L_parse + λ·L_contrast` (InfoNCE
  between the parser's pooled answer-span hidden state and the frozen BGE-M3 embedding). The signal reaches
  the deployed markdown only via diffuse gradient back-flow; **below threshold**.
- **RADP-DPO** *(discrete-output retrieval-reward DPO).* Sample K parses from the production parser, score
  each by a page-local RCPS, form preference pairs, and train with a **LoRA-toggle reference** (`π_θ` = LoRA
  on, `π_ref` = LoRA off — one accelerator, no model copy). Reward sharpened across milestones **R1 → R2 → R3**.
- **RADP-Distill** *(reward-agnostic control — the recommended lever).* The **identical** best-of-K pipeline,
  but candidates are ranked by **edit-distance to the ground-truth markdown** instead of page-local RCPS.
  Its CI substantially overlaps RADP-DPO's ⇒ **no evidence the retrieval reward helps**; the lever is fidelity distillation.
- **SimPO** *(reference-free control — negative).* Removing the reference policy is uniformly negative,
  confirming the reference anchoring is load-bearing.

---

## Experiments

### Setup

- **KoGovDoc-RAG** — 663 Q–A / 294 pages of Korean government documents (`gpt-5.4` generated, LLM-as-judge
  94/100 accept). DPO/SimPO + mechanism use the combined **242-page / 663-Q–A** fold; RADP-aux uses a 73-page
  held-out fold; +6,164 train Q–A on the 2,667-page Prod train set.
- **OHR-Bench** — cross-domain English replication, 7 domains, **2,264 verbatim-answerable Q–A**; 15
  parser-output variants (3 real + 3 formatting-noise + 9 semantic-noise) drive the C1 mechanism.
- **Model** — **Prod** = Qwen3-VL-2B fine-tuned for Korean document parsing; LoRA (r=8, α=32). All RCPS uses
  3 retrievers × 3 cutoffs; deltas use paired percentile bootstrap.

### C1 — the disconnect (Korean government docs)

Boundary Clarity **anti-correlates** with RCPS at **Pearson r = −0.81 (n = 5**, excl. PaddleOCR whose BC is
undefined). The cleanest-boundary parsers (MinerU, Marker; BC ≈ 0.72) retrieve worst. Chunk Stickiness is
likewise uninformative (CS↔RCPS r = +0.26).

| Parser | BC | CS | RCPS | Hit@1 |
|---|:---:|:---:|:---:|:---:|
| Qwen3-VL-30B (teacher) | 0.623 | 3.38 | **0.584** | 0.545 |
| **Prod (ours, 2B)** | 0.610 | 3.07 | 0.583 | 0.549 |
| Qwen3-VL-2B (base) | 0.520 | 3.74 | 0.532 | 0.500 |
| MinerU | 0.716 | 2.81 | 0.212 | 0.197 |
| PaddleOCR | — | 3.46 | 0.140 | 0.125 |
| Marker (38p) | **0.717** | 3.41 | 0.073 | 0.068 |

*KoGov parser grid (Appendix D). BC vs RCPS, r = −0.81 (n = 5, excl. PaddleOCR; dropping Marker → n = 4, r = −0.74).*

### C1 — the mechanism (cross-domain, OHR-Bench)

Within each semantic-noise family, **Boundary Clarity barely moves while RCPS collapses** — MinerU RCPS
0.50 → 0.24 (−51%) with BC flat at 0.71–0.74; GOT 0.38 → 0.26; Qwen2.5-VL noise-robust (0.47 → 0.43, −8%).
Intrinsic boundary metrics see *formatting*, not the *content* retrieval depends on. (The aggregate
cross-variant scalar is document-mix sensitive — we report the per-family mechanism, which replicates in
every domain, as the robust finding.)

![Boundary Clarity is blind to content noise](paper/figures/fig_noise_family.png)

### C2 — coverage diagnostic localizes the fault to the parser

On Prod's output (294 pages, 663 Q–A, **no retriever**), **20.2% of answers are absent** and at most **2.3%
are split**, with the absent rate **constant across all eight chunkers** — exactly the boundary-independence
a parser fault must show. One answer in five is never produced, so no re-chunking can recover it: the gap is
a **parser** problem, which licenses the parser-side intervention in C4.

### C3 — RCPS discriminates chunkers, and is not single-embedder MRR

| Chunker | RCPS | Hit@1 | MRR@10 |
|---|:---:|:---:|:---:|
| md-h3 | **0.593** | 0.556 | 0.613 |
| parser_native | 0.583 | 0.549 | 0.602 |
| LumberChunker | 0.557 | 0.514 | 0.580 |
| fixed500 | 0.535 | 0.491 | 0.560 |

*KoGov chunking grid (663 Q–A, Prod output, 3-retriever RCPS average).* **Ablation:** dropping
retriever-averaging (single embedder BGE-M3) **inverts the top parser** (ranks Prod first; full RCPS ranks
the 30B teacher first), while format-invariance shifts scores but not order. The ordering disagreement
(**Kendall τ = 0.87**) shows RCPS is a protocol, not a relabelled MRR.

### C4 — parser-side training: a bounded, reward-agnostic lever

The pre-specified confirmatory test is the cross-domain **OHR-Bench** replication (training signal,
evaluation metric, and document language mutually disjoint). **RADP-Distill** (edit-distance distillation,
**no retrieval reward**) is the headline and the recommended recipe:

| Δ vs Prod (pp) | Hit@1 | Hit@5 | Hit@10 | MRR@10 | nDCG@5 |
|---|:---:|:---:|:---:|:---:|:---:|
| **RADP-Distill** (headline) | **+0.88** | **+1.22** | **+1.32** | **+1.01** | **+1.05** |
| RADP-DPO R2 (retrieval reward) | +0.53 | +0.85 | +0.81 | +0.70 | +0.74 |
| RADP-DPO R3 (hard-negative) | +1.31 | +1.03 | +0.81 | +1.17 | +1.15 |

*OHR-Bench cross-domain, 3-retriever macro, 1k paired bootstrap. Hit@5 two-sided significant (95% CIs:
Distill [+0.35, +2.15], R2 [+0.35, +1.43], R3 [+0.24, +1.84]). RADP-Distill matches/leads RADP-DPO at the
primary metric Hit@5 ⇒ the retrieval reward buys nothing over plain fidelity distillation.*

On the exploratory KoGov fold (242 pages, n = 663) the RADP-DPO milestones reach +1.96 to +2.11 pp Hit@5
(P[Δ>0] ≈ 0.90, two-sided non-significant at this fold size); RADP-Distill reaches **+2.61 pp** (P = 0.95).
SimPO is uniformly negative (−0.7 to −1.7 pp).

### C4 — mechanism: training tightens text fidelity, not chunking

| Variant | BC ↑ | CS ↓ | TextNED ↓ vs GT |
|---|:---:|:---:|:---:|
| Prod (ref) | 0.630 | 0.474 | 0.240 |
| **RADP-Distill** | 0.641 | — | **0.158** |
| RADP-DPO R2 | 0.647 | 0.476 | **0.163** |
| RADP-DPO R3 | 0.656 | 0.485 | 0.185 |
| RADP-aux λ=0.1 | 0.652 | 0.484 | 0.423 |

*Chunk-level mechanism (242-page fold). RADP-Distill drops TextNED-vs-GT furthest (0.240 → 0.158) while the
**chunking signature is unchanged** (BC ≈ 0.63, CS ≈ 0.474). The gain comes from *what* is parsed, not *how*
chunks are split — the same fact as C1's intrinsic-metric blindness, seen from the training side. RADP-aux
instead *increases* TextNED (its hidden-state objective degrades surface text).*

---

## Deployment playbook

1. **Evaluate parsers with RCPS, not intrinsic metrics alone.** Boundary Clarity (likewise edit distance) can
   rank parsers in an order the downstream retriever inverts. A few hundred held-out Q–A, scored with no
   training, is a 0.20 → 0.55 Hit@1 decision. *This is the highest-leverage takeaway.*
2. **Run the coverage diagnostic first.** If *absent* dominates, fix the parser; if *split* dominates, fix the chunker.
3. **If you train the parser, distil its discrete output toward clean ground-truth text.** Expect ≈ +1 pp Hit@5
   cross-domain, largest on retrievers *not* used for scoring. A retrieval reward showed no gain over this control; avoid the
   hidden-state auxiliary loss and reference-free SimPO (both fail).
4. **Spend where text precision drives retrieval.** The gain concentrates on factoid queries (+3 pp) and is
   roughly neutral on tabular ones — layout-heavy stacks should look to the chunker or embedder.

---

## Repository structure

```
.
├── configs/                  # experiment configs (YAML)
├── src/wigtnocr_radp/
│   ├── qa_generation/        # Q-A generation
│   ├── evaluation/           # RCPS, chunkers, retrievers, coverage, Boundary Clarity, bootstrap CI
│   └── training/             # RADP-aux (contrastive) · RADP-DPO · RADP-Distill · SimPO (LoRA-toggle ref)
├── scripts/
│   ├── training/             # candidate gen, preference / edit-distance pairs, DPO/Distill/SimPO pipelines
│   ├── evaluation/           # baseline_grid, chunking_grid, coverage_diagnostic, rcps_protocol_ablation, OHR chains
│   └── figures/              # paper figure generators (disconnect, RCPS protocol, overview PPTX)
├── experiments/              # arm_b_textned_distill = RADP-Distill runs
├── paper/                    # EMNLP 2026 draft v0.8 (paper.md) + LaTeX (paper/latex) + figures
├── data/KoGovDoc-RAG/        # 663 Q-A (frozen, gitignored)
├── docs/                     # RESEARCH_DIRECTION · TIMELINE · ROADMAP · plans/ · literature_review/
├── output/                   # results & checkpoints (gitignored, GPU server)
└── tests/
```

## Quick start

```bash
uv sync                                   # dependencies (extras: eval / train / data)
cp .env.example .env                      # set OPENAI_API_KEY
hf download Wigtn/KoGovDoc-Bench --repo-type dataset --local-dir data/KoGovDoc-Bench

# Coverage diagnostic (no GPU, CPU seconds) — the C2 result, reproducible first
uv run python scripts/evaluation/coverage_diagnostic.py
```

---

## Authors (WIGTN)

Follow-up to **WigtnOCR v1** (Qwen3-VL-2B document-parsing fine-tuning).

| Author (OpenReview) | Email | Contribution (CRediT) |
|------|-------|--------------|
| **Hyeong-seob Kim**\* | harrison@wigtn.com | Conceptualization, Methodology, Project administration |
| **Sang-woo Son**\* | sangwoo@wigtn.com | Software, Validation, Investigation |

> \* **Equal contribution (co-first authors).**

---

## Released artifacts

- **KoGovDoc-RAG** — 663 Q–A over 294 Korean government document pages.
- **RCPS reference implementation** — [`src/wigtnocr_radp/evaluation/`](src/wigtnocr_radp/evaluation/).
- **RADP-Distill checkpoint** — the recommended deployable parser-side lever (best-of-K, edit-distance ranked, no retrieval reward).
- **RADP-aux (λ ∈ {0, 0.1, 0.3, 0.5}) + RADP-DPO (R1–R3) + SimPO checkpoints** — released for reproducibility as the negative / controlled comparisons.
- **OHR-Bench cross-domain results + mechanism analysis** (BC / CS / TextNED on 12 systems × 242 pages).

## License & Citation

Released under the **MIT License**.

```bibtex
@inproceedings{kim2026rcps,
  title     = {Retrieval-Conditional Parsing Score (RCPS): Choosing Document Parsers by Retrieval, Not by Appearance},
  author    = {Kim, Hyeong-seob and Son, Sang-woo},
  booktitle = {Proceedings of EMNLP 2026 (Industry Track)},
  year      = {2026},
  note      = {To appear}
}
```
