# WigtnOCR-RADP

**Retrieval-Aware Document Parsing (RADP) — the parser that *looks* best is not the one retrieval wants.**

> ✅ **EMNLP 2026 Industry Track · Submission #384 · Accepted**
>
> 🖼️ OpenReview currently records **Accept (Poster)**. The presentation assignment is provisional;
> an oral assignment remains possible.
>
> ⏳ **Camera-ready deadline: August 30, 2026 (AoE)**
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
retrieves better. **It doesn't.** On the 294-page evaluation set (229 KoGov + 65 arXiv pages;
five full-set parsers, plus Marker on a 38-page subset, × 3 retrievers × 663 Q–A),
MoC Boundary Clarity is negatively associated with retrieval: **r = −0.74** among four comparable
full-set parsers, and **r = −0.81 (n = 5)** after adding Marker's 38-page subset. These small-sample
estimates are descriptive. In the separately audited tables-on comparison, choosing Prod instead of
MinerU changes **Hit@1 by +42.6 pp (0.123 → 0.549; 4.47× relative)**.

**Selection, not training, is the headline.** We make four contributions:

- **C1** — diagnose the parsing↔retrieval disconnect and its mechanism (intrinsic metrics see *formatting*, not *content*).
- **C2** — a **retriever-free coverage diagnostic** that identifies where to inspect first: under the stated exact-span normalization, **20.2%** of reference answers are *absent* from the parser output, constant across 8 chunkers.
- **C3** — **RCPS** (Retrieval-Conditional Parsing Score): a no-training, retriever-grounded **protocol** for choosing parsers *and* chunkers; an ablation shows it is not single-embedder MRR.
- **C4** — a bounded map of parser-side training. On a strict, source-page-aligned six-domain OHR
  compatibility subset (2,036 Q–A), two RADP-DPO checkpoints have Hit@5 point estimates **+0.95 pp**
  and **+1.15 pp** above Prod. The aligned RADP-Distill per-QA artifact is unavailable, so objective
  comparisons remain pending.

The repository currently contains the **KoGovDoc-RAG** evaluation files (663 Q–A over 294 pages:
229 KoGov + 65 arXiv), the RCPS implementation, and selected result artifacts. Items that are not yet
available—including checkpoints and several promised camera-ready artifacts—are listed explicitly below.

---

## Motivation — parsing quality ≠ retrieval performance

A practitioner picking a parser for a RAG system runs MinerU on Korean government PDFs, confirms that
its MoC Boundary Clarity is among the highest measured (0.72, essentially tied with Marker), and ships it.
Retrieval Hit@1 is **0.123** in the separately audited tables-on run, far below the 0.50–0.55
vision–language tier. A parser can therefore
look exceptionally clean while retrieving poorly.

This is not a one-off. The same direction is reported independently in English / enterprise settings by
OHR-Bench (ICCV 2025), EnterpriseDocBench (2026), and *When Good OCR Is Not Enough* (2026).
**Prior work either stops at diagnosis or trains a different pipeline layer (chunking → retriever →
generator). No prior work selects, or trains, the L1 parser itself on a retrieval signal — that is our niche.**

---

## Contributions

| | Contribution | Headline result |
|---|---|---|
| **C1** | The parsing↔retrieval **disconnect** and its mechanism. Under controlled semantic-noise perturbations on an aligned English OHR-Bench subset, retrieval declines while Boundary Clarity is nearly fixed or changes non-monotonically. | Full-set BC↔RCPS **r = −0.74** (descriptive); tables-on parser comparison moves **Hit@1 by +42.6 pp** (0.123→0.549; 4.47×) |
| **C2** | A **retriever-free coverage diagnostic** — classify each reference span as *covered / split across chunks / absent from the normalized parser output*; a rule computable *before* any retriever runs. | **20.2% exact-span absent** vs ≤2.3% split, constant across 8 chunkers ⇒ inspect parser output first |
| **C3** | **RCPS** — a retriever-averaged, format-normalised, held-out-Q–A **protocol** for choosing parsers/chunkers with no training. Ablation: it is **not** single-embedder MRR. | retriever-averaging flips the top parser; **Kendall τ = 0.80** vs naive MRR |
| **C4** | A **bounded** map of parser-side training, with objective comparisons deferred until aligned artifacts are available. | Strict six-domain OHR subset: **R2 +0.95 pp**, **R3 +1.15 pp** Hit@5 vs Prod (n=2,036) |

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
its source page matches the answer's page and the reference span is a substring of the chunk (whitespace- and
markdown-insensitive). Run on a few hundred held-out Q–A with **no training**. Reference implementation:
[`src/wigtnocr_radp/evaluation/`](src/wigtnocr_radp/evaluation/).

### Coverage diagnostic — parser vs chunker (C2)

RCPS scores parser + chunker + retriever jointly, so a low score does not say *which* layer is at fault.
Holding the parser output fixed and varying the chunker, classify each normalized reference span as **covered**,
**split** (present on the page but divided across chunks, and therefore potentially recoverable with overlap)
or **absent** (no exact match in the normalized parser output, so re-chunking cannot restore that exact span).
This diagnostic identifies the layer to inspect first; an absent match can reflect a genuine omission or a
surface-form mismatch, which requires case-level review to distinguish. Code:
[`scripts/evaluation/coverage_diagnostic.py`](scripts/evaluation/coverage_diagnostic.py).

### Parser-side training — what works, and what doesn't (C4)

When the coverage diagnostic points to the parser, we test parser-side training from both natural directions.

- **RADP-aux** *(hidden-state auxiliary loss — sub-threshold).* `L_total = L_parse + λ·L_contrast` (InfoNCE
  between the parser's pooled answer-span hidden state and the frozen BGE-M3 embedding). The signal reaches
  the deployed markdown only via diffuse gradient back-flow; **below threshold**.
- **RADP-DPO** *(discrete-output retrieval-reward DPO).* Sample K parses from the production parser, score
  each by a page-local RCPS, form preference pairs, and train with a **LoRA-toggle reference** (`π_θ` = LoRA
  on, `π_ref` = LoRA off — one accelerator, no model copy). Reward sharpened across milestones **R1 → R2 → R3**.
- **RADP-Distill** *(fidelity-based control).* Candidates are ranked by edit distance to reference Markdown
  instead of page-local RCPS. Its aligned per-QA artifact is currently unavailable, so this README makes no
  quantitative Distill-versus-DPO claim.
- **SimPO** *(reference-free control).* Its evaluated point estimates are negative; the runs do not isolate
  which optimization difference caused that result.

---

## Experiments

### Setup

- **KoGovDoc-RAG** — 663 Q–A / 294 evaluation pages (**229 KoGov + 65 arXiv**) (`gpt-5.4` generated, LLM-as-judge
  94/100 accept). DPO/SimPO + mechanism use the combined **242-page / 663-Q–A** fold; RADP-aux uses a 73-page
  held-out fold; +6,164 train Q–A on the 2,667-page Prod train set.
- **OHR-Bench** — two audited compatibility subsets. C1 uses **1,043 Law–Manual Q–A** and 15
  parser-output variants. C4 uses a strict **2,036-Q–A / six-domain** subset after excluding 223 corrupted
  legacy `notes` rows and five Q–A whose evidence page is absent from the current parser bundle. This is
  not a substitute for a full v2 rerun.
- **Model** — **Prod** = Qwen3-VL-2B fine-tuned for Korean document parsing; LoRA (r=8, α=32). All RCPS uses
  3 retrievers × 3 cutoffs; deltas use paired percentile bootstrap.

### C1 — the disconnect (KoGovDoc-RAG evaluation set)

Among the four comparable full-set parsers with defined Boundary Clarity, BC and RCPS have
**Pearson r = −0.74**. Adding Marker on its 38-page subset gives **r = −0.81 (n = 5)**; PaddleOCR is
excluded because BC is undefined. Both estimates are descriptive.

| Parser | BC | CS | RCPS | Hit@1 |
|---|:---:|:---:|:---:|:---:|
| Qwen3-VL-30B (teacher) | 0.623 | 3.38 | **0.584** | 0.545 |
| **Prod (ours, 2B)** | 0.610 | 3.07 | 0.583 | 0.549 |
| Qwen3-VL-2B (base) | 0.520 | 3.74 | 0.532 | 0.500 |
| MinerU (tables-on, separate run) | — | — | 0.137 | 0.123 |
| MinerU (submitted tables-off) | 0.716 | 2.81 | 0.212 | 0.197 |
| PaddleOCR | — | 3.46 | 0.140 | 0.125 |
| Marker (38p) | **0.717** | 3.41 | 0.073 | 0.068 |

*KoGov parser grid (paper §4.3, Table 1). The BC correlation uses the submitted tables-off grid; the
tables-on MinerU row is a separately audited configuration. Marker is excluded from full-set rank comparisons.*

### C1 — the mechanism (cross-domain, OHR-Bench)

On the aligned Law–Manual subset, semantic noise lowers retrieval without a consistent BC response.
MinerU RCPS falls **0.595 → 0.265 (−55%)** while BC varies **0.657 → 0.631** non-monotonically;
Qwen2.5-VL RCPS falls **0.545 → 0.497 (−9%)** while BC stays near **0.563**; and GOT RCPS falls
**0.461 → 0.298** while BC rises **0.586 → 0.624**. The aggregate 15-variant correlation is
**r = −0.35**, reported descriptively because variants within a family are not independent parsers.
The stale seven-domain figure has been removed from this README until it is regenerated from this aligned subset.

### C2 — coverage diagnostic separates output absence from chunk boundaries

On Prod's output (294 pages: **229 KoGov + 65 arXiv**; 663 Q–A, **no retriever**), **20.2% of normalized
reference spans have no exact match in the parser output**, while at most **2.3% are split** across chunks.
The exact-span absence rate is constant across all eight chunkers, so re-chunking cannot make those cases
exact-span covered. This result points to parser-output inspection before chunker tuning; it does not, by
itself, show that the answer semantics are entirely missing rather than rendered in a different surface form.

### C3 — RCPS discriminates chunkers, and is not single-embedder MRR

| Chunker | RCPS | Hit@1 | MRR@10 |
|---|:---:|:---:|:---:|
| md-h3 | **0.593** | 0.556 | 0.613 |
| parser_native | 0.583 | 0.549 | 0.602 |
| LumberChunker | 0.557 | 0.514 | 0.580 |
| fixed500 | 0.535 | 0.491 | 0.560 |

*KoGov chunking grid (663 Q–A, Prod output, 3-retriever RCPS average).* The tracked aggregate audit finds
that using three-retriever **MRR@10 alone** instead of averaging MRR@{1,5,10} preserves the complete order
of the five 294-page parsers and all four chunkers. By contrast, dropping retriever-averaging and using only
BGE-M3 **inverts the top parser** (Prod first; full RCPS ranks the 30B teacher first); the five-parser rankings
otherwise agree (**Kendall τ = 0.80**). We do not report the format-sensitive ablation because the ranked
chunk lists required to reconstruct it were not persisted. RCPS is an operational protocol, not a relabelled MRR.

### C4 — parser-side training: corrected compatibility-subset results

The original OHR result mixed benchmark releases. After removing the 223 corrupted legacy `notes` rows
and five Q–A tied to a missing evidence page, the tracked audit yields this strict six-domain result:

| Δ vs Prod (pp) | Hit@1 | Hit@5 | Hit@10 | MRR@10 | nDCG@5 |
|---|:---:|:---:|:---:|:---:|:---:|
| RADP-DPO R2 (retrieval reward) | +0.59 | +0.95 | +0.90 | +0.78 | +0.82 |
| RADP-DPO R3 (hard-negative) | +1.46 | +1.15 | +0.90 | +1.30 | +1.28 |

*Corrected legacy compatibility subset, n=2,036, three-retriever macro, 1,000 paired-bootstrap resamples
(seed 42). Hit@5 95% CIs: R2 **[+0.33,+1.54]**, R3 **[+0.31,+2.05]**. This post-audit subset is not the
original confirmatory analysis and is not a full OHR-Bench v2 evaluation.*

On the exploratory KoGov fold (242 pages, n = 663), the RADP-DPO milestones reach +1.96 to +2.11 pp Hit@5
(P[Δ>0] ≈ 0.90; all two-sided intervals cross zero). SimPO point estimates range from −1.7 to −0.7 pp.
RADP-Distill quantitative results remain omitted until its per-QA artifact is restored on the same subset.

### C4 — mechanism: training tightens text fidelity, not chunking

| Variant | BC ↑ | TextNED ↓ vs reference |
|---|:---:|:---:|
| Prod (ref) | 0.630 | 0.240 |
| RADP-DPO R2 | 0.647 | **0.163** |
| RADP-DPO R3 | — | 0.185 |
| RADP-aux λ=0.1 | 0.652 | 0.423 |

*Available 242-page mechanism measurements. All DPO checkpoints have lower TextNED and higher Hit@5
point estimates than Prod, but TextNED does not order the checkpoints. R3 BC/CS and uncertainty estimates
are unavailable, so the data do not establish a systematic boundary-change mechanism.*

---

## Deployment playbook

1. **Evaluate parsers with RCPS, not intrinsic metrics alone.** Boundary Clarity (likewise edit distance) can
   rank parsers in an order the downstream retriever inverts. A few hundred held-out Q–A, scored with no
   training, is a 0.12 → 0.55 Hit@1 decision in the separately audited tables-on comparison.
   *This is the highest-leverage takeaway.*
2. **Run the coverage diagnostic first.** If exact-span *absence* dominates, inspect those parser outputs and
   change the parser when content is genuinely missing; if *split* dominates, tune the chunker or overlap.
3. **If you train the parser, measure it on an untouched subset and include a fidelity-based baseline.** The
   audited DPO checkpoints have Hit@5 point estimates about one point above Prod, but the Distill comparison
   is not recoverable from the current per-QA artifacts.
4. **Keep conclusions tied to available evidence.** The current mechanism results associate DPO with lower
   TextNED than Prod; they do not identify a causal mechanism or establish an evidence-type advantage.

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
├── experiments/              # RADP-Distill training/evaluation harness
├── paper/                    # accepted EMNLP 2026 manuscript + LaTeX + figures
├── data/KoGovDoc-RAG/        # frozen 663-Q–A evaluation files and page split
├── docs/                     # RESEARCH_DIRECTION · TIMELINE · ROADMAP · plans/ · literature_review/
├── output/                   # selected result JSONs; see artifact status below
└── tests/
```

> **Note (figure logos):** `scripts/figures/make_fig_overview_pptx.py` expects third-party brand logos under
> `scripts/figures/icons/logos/` (`qwen.png`, `mineru.png`, `marker_datalab.png`, `paddle.png`, `bge_baai.png`, `me5_ms.png`).
> These are **not committed** for licensing reasons — download them from each project's official site/repo before regenerating Figure 1.
> Figure regeneration is deferred to the final camera-ready visual pass. Several current exports and one
> generator still contain stale table-off or mixed-version OHR values; see the camera-ready plan before use.

## Local code check

```bash
uv sync --extra dev
uv run pytest
uv run python scripts/evaluation/coverage_diagnostic.py --out_dir /tmp/rcps-coverage-check
```

The last command runs the CPU-only 294-page / 663-Q–A coverage diagnostic when the local,
gitignored source-page mapping `data/KoGovDoc-Bench/val.jsonl` is present. The Q–A and parser outputs
are tracked, but this mapping file is not yet packaged, so the command is not currently fresh-clone complete.
These commands are **not** a fresh-clone reproduction of every paper experiment.
The full pipeline still depends on external parser outputs, caches, and checkpoints. Portable end-to-end
instructions and the remaining release artifacts are camera-ready work listed below.

---

## Authors (OpenReview order)

Follow-up to **WigtnOCR v1** (Qwen3-VL-2B document-parsing fine-tuning).

1. Sang-Woo Son
2. Hyeong-seob Kim
3. Hyeonsang Kim
4. Hyun-woo Cho
5. Jinmo Kim

The author list and order will remain exactly as submitted. The request to designate Hyeong-seob Kim as
corresponding author is awaiting written confirmation from the Industry Track chairs, so no
corresponding-author marker is applied yet. Affiliations and emails will be added only from confirmed metadata.

---

## Artifact and reproducibility status

### Current repository

- **KoGovDoc-RAG evaluation files** — 663 Q–A over 294 pages (**229 KoGov + 65 arXiv**) and the frozen page
  split, plus a separate LLM-assisted 100-pair Q–A quality-check sample and its aggregate 94/100 result.
  The sample's blank `verification` fields are not human labels.
- **RCPS reference implementation** — [`src/wigtnocr_radp/evaluation/`](src/wigtnocr_radp/evaluation/).
- **Selected evaluation artifacts** — tracked result JSONs and the 294-page MinerU table-ON parser output
  used by the current analysis.
- **Aligned OHR audit artifacts** — the 1,043-Q–A Law–Manual C1 result and a deterministic derivation of
  the strict 2,036-Q–A legacy compatibility subset. Older seven-domain outputs remain in the tree for
  provenance but are not valid camera-ready evidence.

### Camera-ready pending — not currently available

- MinerU **table-OFF** parser outputs and the exact rerun commands.
- Per-Q–A arrays for the complete 294-page parser/chunker grid and the corresponding probe-resampling
  **ranking-stability** artifact. The tracked aggregate-grid audit and end-to-end stability check are
  different analyses and are already present.
- Final per-case labels and adjudications from the separate two-author 100-case absent-label study; they
  are not currently in Git, and the release decision and packaging are still pending.
- A full OHR-Bench v2 rerun and clean-machine validation of the new current/quarantine manifests; legacy
  seven-domain / combined-CI / OHR-TextNED artifacts are already separated in the quarantine manifest.
- RADP-Distill per-QA and confidence-interval artifacts evaluated on the same aligned subset; until then,
  no quantitative Distill-versus-DPO comparison is supported.
- Complete BC/CS mechanism data and regenerated figures using only aligned, current values.
- Complete executed-configuration/log provenance and model checkpoints for RADP-Distill, RADP-aux,
  RADP-DPO, and SimPO.
- A portable **fresh-clone, end-to-end reproduction path**, including external data, parser outputs,
  embedding caches, checkpoint acquisition, and removal of machine-specific runtime assumptions.

## License & Citation

Repository code is released under the **MIT License**. Third-party datasets and model assets retain
their original licenses and terms.

```bibtex
@inproceedings{son2026rcps,
  title     = {Retrieval-Conditional Parsing Score (RCPS): Choosing Document Parsers by Retrieval, Not by Appearance},
  author    = {Son, Sang-Woo and Kim, Hyeong-seob and Kim, Hyeonsang and Cho, Hyun-woo and Kim, Jinmo},
  booktitle = {Proceedings of EMNLP 2026 (Industry Track)},
  year      = {2026},
  note      = {Accepted; camera-ready pending}
}
```
