# WigtnOCR-RADP

**RCPS for retrieval-based selection, coverage for diagnosis, and RADP only for optional parser training.**

> ✅ **EMNLP 2026 Industry Track · Submission #384 · Accepted**
>
> 🖼️ OpenReview currently records **Accept (Poster)**. The presentation assignment is provisional;
> an oral assignment remains possible.
>
> ⏳ **Camera-ready deadline: August 30, 2026 (AoE)**
>
> 📄 Title: *Retrieval-Conditional Parsing Score (RCPS): Choosing Document Parsers by Retrieval, Not by Appearance* · [camera-ready working PDF](paper/latex/main_camera_ready.pdf)
>
> 📦 Builds on [WigtnOCR v1](https://huggingface.co/Wigtn/Qwen3-VL-2B-WigtnOCR) + [KoGovDoc-Bench](https://huggingface.co/datasets/Wigtn/KoGovDoc-Bench)
>
> 🇰🇷 **[한국어 README](README.ko.md)** · 🧭 [`docs/PAPER_READABILITY_REVIEW_AUDIT.md`](docs/PAPER_READABILITY_REVIEW_AUDIT.md) (current audit) · 🗓️ [`docs/CAMERA_READY_PLAN.md`](docs/CAMERA_READY_PLAN.md)

---

## TL;DR

Document RAG retrieves from parser outputs, yet parsers are often selected by intrinsic measures such as
edit distance or Boundary Clarity (BC), rather than by retrieval performance. **RCPS instead ranks
parser–chunker combinations on a fixed held-out retrieval probe, without training.** The resulting workflow is:

1. **Select with RCPS.** Five complete parser configurations span **0.137–0.584 RCPS**. Audited
   MinerU-on has higher BC than Prod (**0.713 vs 0.610**) but a **42.6-point** lower Hit@1
   (**0.123 vs 0.549; Prod is 4.47× as high**). MinerU-off is retained only as a submitted-output diagnostic.
2. **Diagnose with coverage.** In Prod output, **20.2%** of reference spans have no normalised exact match
   before chunking, while no tested chunker splits more than **2.3%**.
3. **Act or train only if needed.** For *absent* spans, inspect or switch the parser; for *split* spans,
   change overlap or chunking. The 73-page parser-training pilot misses its target, and two RADP-DPO
   checkpoints are only **+0.95** and **+1.15 Hit@5 points** above Prod on a separate, post-audit OHR
   compatibility subset.
4. **Re-evaluate changed configurations.** If `P` or `C` changes, run the resulting corpus through the
   same RCPS protocol before deployment. A covered configuration proceeds without redundant re-evaluation.

The denominators are not interchangeable:

| Analysis | Evaluation frame | Role |
|---|---|---|
| Parser/chunker selection | 663 Q–A retrieved against **294 pages** | 242 evidence pages + 52 Q–A-free distractors |
| Training/mechanism | The same 663 Q–A against **242 pages** | Evidence-bearing pages only |
| Pre-specified pilot | **202 Q–A / 73 pages** | Held-out training gate |
| OHR perturbations | **1,043 Law–Manual Q–A** | Source-aligned cross-domain diagnostic |
| OHR training audit | **2,036 Q–A / six domains** | Post-audit compatibility subset; not a full v2 rerun |

The repository currently contains the frozen **663-Q–A KoGovDoc-RAG probe** (whose evidence spans
242 pages), its 169/73 evidence-page split, the RCPS implementation, and selected result artifacts.
The main selection run adds 52 Q–A-free distractor pages to form its 294-page index; the complete source
corpus and mapping for a fresh-clone rerun are not yet packaged. All remaining release gaps are listed below.

<p align="center">
  <img src="paper/figures/fig_overview.png" width="100%" alt="RCPS workflow from the fixed evaluation frame through candidate generation, retrieval-based selection, coverage diagnosis, optional intervention, and deployment">
</p>

*Figure 1 — RCPS workflow.* A fixed 294-page / 663-Q–A frame evaluates every parser–chunker candidate.
RCPS selects a provisional `P* + C*`; coverage then distinguishes covered, absent, and split spans. Any
changed parser or chunker is evaluated again before final deployment. ([vector PDF](paper/figures/fig_overview.pdf) ·
[editable PPTX](paper/figures/fig_overview_camera_ready.pptx))

---

## Motivation — parsing quality ≠ retrieval performance

In the audited deployment comparison, MinerU-on has higher BC than Prod (**0.713 vs 0.610**) but much
lower Hit@1 (**0.123 vs 0.549**). The separately retained submitted-output MinerU-off diagnostic has BC
**0.716** and Hit@1 **0.197**. These configurations are not a causal table-recognition ablation; together,
they show the operational risk of choosing a parser by boundary appearance alone.

OHR-Bench, EnterpriseDocBench, and concurrent OCR-for-RAG studies report related mismatches in English
and enterprise settings. Our contribution is to turn that observation into a deployment workflow:
**select with RCPS, diagnose with coverage, change or train only if needed, and re-evaluate changed
configurations**. We are unaware of prior work that combines a reusable parser-selection protocol with a
diagnostic that separates exact-span absence from chunk-boundary splitting.

---

## Contributions

| | Contribution | Headline result |
|---|---|---|
| **C1** | The parsing↔retrieval **disconnect**. On an aligned English OHR-Bench subset, semantic-noise perturbations lower retrieval while BC is stable or changes non-monotonically. | Audited 294-page BC↔RCPS **r = −0.74** (descriptive); MinerU-on and Prod differ by **42.6 Hit@1 points** (0.123→0.549; 4.47×) |
| **C2** | **RCPS** — a retriever-averaged, format-normalised, held-out-Q–A **protocol** for choosing parsers/chunkers with no training. | Complete 294-page parsers span **0.137–0.584**; with Prod fixed, four chunkers span **0.535–0.593** |
| **C3** | A **retriever-free coverage diagnostic** — classify each reference span as *covered / split across chunks / absent from the normalised parser output*; a rule computable *before* any retriever runs. | **20.2% exact-span absent**, constant across 8 chunkers; split varies up to 2.3% ⇒ inspect parser output first |
| **C4** | A **bounded** map of parser-side training; the pilot misses its target, and the matched Distill comparison remains unavailable. | Post-audit six-domain OHR compatibility subset: **R2 +0.95 pp**, **R3 +1.15 pp** Hit@5 vs Prod (n=2,036) |

---

## Method

### RCPS — Retrieval-Conditional Parsing Score (C2)

Score a parser by what *downstream retrieval* does with its output, not by how clean the output looks.
RCPS is **not a new similarity function** but a protocol wrapping ordinary retrieval MRR in three choices:
**(i) extrinsic** (score on a held-out Q–A probe rather than parser text alone),
**(ii) retriever-averaged** (over specified embedders), and **(iii) format-normalised relevance**
(a relevant chunk must come from the source page and contain the normalised answer span).

```
RCPS(P, C; D, R, K) = (1 / |R||K|) · Σ_{r∈R} Σ_{k∈K} MRR@k(r, C(P), D)
```

Here, `P` is a parser, `C` is a chunker, and `D` is the fixed held-out Q–A probe.
`R = {BGE-M3, multilingual-e5-large, Qwen3-Embedding-8B}` and `K = {1, 5, 10}`. A chunk is **relevant**
iff its source page matches the answer's page and contains the reference span after shared whitespace and
Markdown normalisation. For each query, MRR@`k` is `1/j` when the first relevant chunk appears at rank
`j ≤ k`, and zero when no relevant chunk appears in the top `k`; the values are then averaged over queries.
Evaluation requires **no training**. Reference implementation:
[`src/wigtnocr_radp/evaluation/`](src/wigtnocr_radp/evaluation/).

<p align="center">
  <img src="paper/figures/fig_rcps_protocol.png" width="62%" alt="RCPS protocol: build each parser-chunker index, retrieve a fixed probe, apply reference-page and normalised-span relevance, average MRR, and rank candidates">
</p>

*Figure 2 — RCPS evaluation protocol.* Every candidate uses the same probe, retriever/retrieval-depth specification,
and reference-page plus normalised-span relevance rule. RCPS averages standard MRR and requires no
training. ([vector PDF](paper/figures/fig_rcps_protocol.pdf))

### Coverage diagnostic — parser vs chunker (C3)

RCPS scores parser + chunker + retriever jointly, so a low score does not say *which* layer is at fault.
Holding the parser output fixed and varying the chunker, classify each normalised reference span as **covered**,
**split** (present in the parsed page output but divided across chunks, and therefore potentially recoverable with overlap)
or **absent** (no exact match in the normalised parser output, so re-chunking cannot restore that exact span).
This diagnostic identifies the layer to inspect first; an absent match can reflect a genuine omission or a
surface-form mismatch, which requires case-level review to distinguish. Code:
[`scripts/evaluation/coverage_diagnostic.py`](scripts/evaluation/coverage_diagnostic.py).

<p align="center">
  <img src="paper/figures/fig_coverage.png" width="78%" alt="Coverage diagnostic showing a 20.2 percent pre-chunking no-match rate and a 0 to 2.3 percent chunk-boundary split rate across eight chunkers">
</p>

*Figure 3 — Coverage diagnostic with Prod fixed.* The pre-chunking exact-span no-match rate remains
**20.2%**; changing the chunker affects only splitting, which reaches at most **2.3%** across eight
chunkers. ([vector PDF](paper/figures/fig_coverage.pdf))

### Parser-side training — a secondary study (C4)

When the coverage diagnostic points to parser output, we test the following approaches and controls.

- **RADP-aux** *(hidden-state auxiliary loss — sub-threshold).* `L_total = L_parse + λ·L_contrast` uses
  InfoNCE between the parser's pooled answer-span hidden state and a frozen BGE-M3 embedding. Its best
  73-page pilot estimate remains below the pre-specified success criterion.
- **RADP-DPO** *(discrete-output retrieval-reward DPO).* Sample K parses from the production parser, score
  each by page-local BGE-M3 MRR averaged over `k = {1, 5, 10}`, form preference pairs, and train with a
  **LoRA-toggle reference** (`π_θ` = LoRA on, `π_ref` = LoRA off). The candidate pool and negatives expand
  across **R1 → R2 → R3**.
- **RADP-Distill** *(fidelity-based control).* Candidates are ranked by edit distance to reference Markdown
  instead of the page-local BGE-M3 MRR retrieval reward. Its aligned per-QA artifact is currently unavailable,
  so this README makes no quantitative Distill-versus-DPO claim.
- **SimPO** *(reference-free control).* Its 242-page Hit@5 point estimates are negative, but both confidence
  intervals cross zero; the runs do not isolate which optimization difference caused that result.

---

## Experiments

### Setup

- **KoGovDoc-RAG selection frame** — all **663 Q–A** retrieve against **294 pages**
  (**229 KoGov + 65 arXiv**). The answers occur on 242 of those pages; the remaining 52 pages are
  Q–A-free distractors. Q–A were generated with `gpt-5.4-2026-03-05`; a separate LLM-assisted check
  accepted 94/100 sampled pairs. This was not human verification of the complete probe.
- **KoGovDoc-RAG training frames** — DPO/SimPO and mechanism analyses retrieve the same 663 Q–A against
  only the **242 evidence-bearing pages**. The pre-specified pilot uses a held-out **73-page / 202-Q–A**
  fold. Preference data come from a separate, page-disjoint 2,667-page Prod corpus with 6,164 generated Q–A.
- **OHR-Bench frames** — C1 uses **1,043 source-aligned Law–Manual Q–A**, three benchmark outputs, and
  twelve dependent perturbations (three formatting and nine semantic); these are not 15 independent parsers.
  C4 uses a separate **2,036-Q–A / six-domain compatibility subset** after excluding 223 misaligned
  legacy `notes` rows and five Q–A whose evidence page is absent from the current parser bundle. Neither
  frame is a substitute for a full v2 rerun.
- **Model and scoring** — **Prod** is Qwen3-VL-2B fine-tuned for Korean document parsing; trained variants
  use LoRA (r=8, α=32). RCPS averages 3 retrievers × 3 retrieval depths. Reported uncertainty uses paired
  Q–A-level percentile bootstrap unless stated otherwise.

### C1 — the disconnect (KoGovDoc-RAG evaluation set)

The five candidates with complete outputs form the deployment comparison below. MinerU-on is the audited,
table-enabled configuration used in that comparison.

| Complete 294-page deployment comparison | BC | CS | RCPS | Hit@1 |
|---|:---:|:---:|:---:|:---:|
| Qwen3-VL-30B (teacher) | 0.623 | 3.38 | **0.584** | 0.545 |
| **Prod (ours, 2B)** | 0.610 | 3.07 | 0.583 | **0.549** |
| Qwen3-VL-2B (base) | 0.520 | 3.74 | 0.532 | 0.500 |
| PaddleOCR | — | 3.46 | 0.140 | 0.125 |
| MinerU-on | **0.713** | — | 0.137 | 0.123 |

Boundary Clarity is defined for four complete 294-page deployment configurations
(Qwen3-VL-30B, Prod, Qwen3-VL-2B, and MinerU-on). Their BC–RCPS correlation is
**Pearson r = −0.74**. Adding Marker's 38-page result gives **r = −0.83 (n = 5)**.
Both estimates are descriptive; PaddleOCR has no measured BC and Marker is not a complete-output result.

| Submitted/subset diagnostic | Scope | BC | CS | RCPS | Hit@1 |
|---|:---:|:---:|:---:|:---:|:---:|
| MinerU-off (submitted) | 294 pages | 0.716 | 2.81 | 0.212 | 0.197 |
| Marker | 38 pages | **0.717** | 3.41 | 0.073 | 0.068 |

MinerU-on and MinerU-off differ in more than table handling, so their scores do not estimate the causal
effect of table recognition. BC is Boundary Clarity (higher is better); CS is Chunk Stickiness (lower is better).

<p align="center">
  <img src="paper/figures/fig_disconnect.png" width="100%" alt="Boundary Clarity versus RCPS using MinerU-on in the audited deployment comparison, plus the MinerU-on versus Prod Hit at 1 gap">
</p>

*Figure 4 — Parsing quality can misrank retrieval candidates.* Panel (a) uses MinerU-on in the audited
294-page deployment comparison; panel (b) compares MinerU-on and Prod on Hit@1. MinerU-off remains a
separately labelled submitted-output diagnostic, not a causal table-recognition ablation.
([vector PDF](paper/figures/fig_disconnect.pdf))

### C1 — aligned perturbation diagnostic (cross-domain, OHR-Bench)

On the aligned Law–Manual subset, semantic noise lowers retrieval without a consistent BC response.
From clean to severe noise, MinerU RCPS falls **0.595 → 0.265** while BC changes non-monotonically
from **0.657 → 0.631**; Qwen2.5-VL RCPS falls **0.545 → 0.497** while BC stays near **0.563**.
GOT has no clean output, but from mild to severe noise its RCPS falls **0.461 → 0.298** while BC rises
**0.586 → 0.624**. The aggregate 15-row correlation is **r = −0.35**, reported descriptively because
variants within a family are dependent. This restricted subset does not establish broader domain generality.

### C2 — RCPS ranks parsers and chunkers

| Chunker | RCPS | Hit@1 | MRR@10 |
|---|:---:|:---:|:---:|
| md-h3 | **0.593** | 0.556 | 0.613 |
| parser_native | 0.583 | 0.549 | 0.602 |
| LumberChunker | 0.557 | 0.514 | 0.580 |
| fixed500 | 0.535 | 0.491 | 0.560 |

*KoGov chunking grid (663 Q–A, Prod output, 3-retriever RCPS average).* On the submitted-output aggregate
grid, which contains MinerU-off rather than the separate MinerU-on deployment row, the tracked audit finds
that using three-retriever **MRR@10 alone** instead of averaging MRR@{1,5,10} preserves the complete order
of the five 294-page parsers and all four chunkers. By contrast, dropping retriever-averaging and using only
BGE-M3 **inverts the top parser** (Prod first; full RCPS ranks the 30B teacher first); the five-parser rankings
otherwise agree (**Kendall τ = 0.80**). We do not report the format-sensitive ablation because the ranked
chunk lists required to reconstruct it were not persisted. Use the deployment retriever when it is fixed;
use the multi-retriever average as a hedge when the retriever is undecided or candidates are near-tied.
RCPS is an operational protocol, not a relabelled MRR.

In a separate three-parser end-to-end check, Prod also has the highest judged answer accuracy
(**72.5%**, versus **23.8%** for MinerU-on and **20.5%** for PaddleOCR). The lower pair reverses relative
to RCPS, and the same GPT-5.4 checkpoint generates and judges answers. We therefore treat this only as a
check of the top choice, not validation of the full ranking.

### C3 — coverage diagnostic separates output absence from chunk boundaries

On Prod's output (294 pages: **229 KoGov + 65 arXiv**; 663 Q–A, **no retriever**), **134/663 (20.2%)**
of normalised reference spans have no exact match in the parser output, while at most **15/663 (2.3%)**
are split across chunks.
The exact-span absence rate is constant across all eight chunkers, so re-chunking cannot make those cases
exact-span covered. This result points to parser-output inspection before chunker tuning; it does not, by
itself, show that the answer semantics are entirely missing rather than rendered in a different surface form.

We also test label robustness. GPT-5.4 reclassifies **56%** of Prod's exact-match-absent cases as
recoverable surface artefacts, although this judge is not independent of the GPT-family Q–A generator.
In a separate parser-masked, stratified sample of 100 absent cases, two authors independently agree on
81/100 cases (**κ = 0.615**) before adjudication. After adjudication, retrieval-unusable rates are
**42/50 (84.0%)** for MinerU-on, **12/30 (40.0%)** for Prod, and **19/20 (95.0%)** for PaddleOCR.
Different sampling fractions and MinerU configurations prevent a population-level replication claim.
The final per-case human labels are not yet packaged as a public artifact.

### C4 — parser-side training remains below the pilot target

On the held-out 73-page / 202-Q–A pilot, neither RADP-aux nor RADP-DPO meets the pre-specified target:
at least 5 RCPS points with a 95% confidence-interval lower bound above zero. A later OHR audit found that
the original result mixed benchmark releases. After removing 223 misaligned legacy `notes` rows and five
Q–A tied to a missing evidence page, the tracked arrays yield this strict six-domain compatibility result:

| Δ vs Prod (pp) | Hit@1 | Hit@5 | Hit@10 | MRR@10 | nDCG@5 |
|---|:---:|:---:|:---:|:---:|:---:|
| RADP-DPO R2 (retrieval reward) | +0.59 | +0.95 | +0.90 | +0.78 | +0.82 |
| RADP-DPO R3 (hard-negative) | +1.46 | +1.15 | +0.90 | +1.30 | +1.28 |

*Post-audit legacy compatibility subset, n=2,036, three-retriever macro, 1,000 Q–A-level paired-bootstrap
resamples (seed 42). Hit@5 95% CIs: R2 **[+0.33,+1.54]**, R3 **[+0.31,+2.05]**. This subset was defined
after the version audit; it is neither the original confirmatory analysis nor a full OHR-Bench v2 evaluation.*

On the exploratory KoGov fold (242 pages, n = 663), the RADP-DPO milestones reach +1.96 to +2.11 pp Hit@5
(P[Δ>0] ≈ 0.90; all two-sided intervals cross zero). SimPO Hit@5 point estimates are **−0.85 pp** with
md-h3 and **−0.70 pp** with parser-native chunking; both confidence intervals cross zero.
This pooled analysis combines the 169 development and 73 held-out evidence pages, so it is not a new
independent holdout. RADP-Distill quantitative results remain omitted until its per-QA artifact is restored
on the same subset.

### C4 — available measurements do not identify a training mechanism

| Variant | BC ↑ | TextNED ↓ vs reference |
|---|:---:|:---:|
| Prod (ref) | 0.630 | 0.240 |
| RADP-DPO R2 | 0.647 | **0.163** |
| RADP-DPO R3 | — | 0.185 |
| RADP-aux λ=0.1 | 0.652 | 0.423 |

*Selected 242-page mechanism measurements. Available R1–R3 measurements have lower TextNED and positive
Hit@5 point estimates relative to Prod; the compact table shows R2 and R3, but TextNED does not reproduce
their retrieval order. R3 BC and
uncertainty estimates for these structural metrics are unavailable. The co-occurrence is post hoc and
does not establish that fidelity or boundary changes caused the retrieval differences.*

---

## Deployment playbook

1. **Evaluate parsers with RCPS, not intrinsic metrics alone.** Boundary Clarity can rank candidates in an
   order the downstream retriever does not preserve. In the audited MinerU-on–Prod comparison, selecting
   Prod corresponds to Hit@1 **0.123 → 0.549** on the fixed KoGovDoc-RAG probe; this candidate-pool result
   is not a universal effect size.
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
│   └── training/             # RADP-aux (contrastive) · RADP-DPO · SimPO (LoRA-toggle ref)
├── scripts/
│   ├── training/             # candidate gen, preference / edit-distance pairs, DPO/Distill/SimPO pipelines
│   ├── evaluation/           # baseline_grid, chunking_grid, coverage_diagnostic, rcps_protocol_ablation, OHR chains
│   └── figures/              # paper figure generators (disconnect, RCPS protocol, overview PPTX)
├── experiments/              # RADP-Distill training/evaluation harness
├── paper/                    # frozen submission + camera-ready working LaTeX + figures
├── data/KoGovDoc-RAG/        # frozen 663-Q–A probe + 169/73 evidence-page split
├── docs/                     # RESEARCH_DIRECTION · TIMELINE · ROADMAP · plans/ · literature_review/
├── output/                   # selected result JSONs; see artifact status below
└── tests/
```

> **Figure source note:** the canonical camera-ready assets are
> `paper/figures/fig_overview.pdf`, `fig_rcps_protocol.pdf`, `fig_coverage.pdf`, and `fig_disconnect.pdf`;
> the PNG files displayed in this README are their web previews. Figure 1's canonical editable source is
> `paper/figures/fig_overview_camera_ready.pptx`; its RCPS badge is C2 and its coverage badge is C3.
> `scripts/figures/make_fig_overview.py` is a non-canonical alternative renderer and must not overwrite the
> approved PPTX-derived PDF.

## Local code check (Linux/WSL CUDA environment)

```bash
uv sync --extra dev
uv run pytest
uv run python scripts/evaluation/coverage_diagnostic.py --out_dir /tmp/rcps-coverage-check
```

These commands assume the Linux/WSL CUDA 12.8 dependency source encoded in `pyproject.toml` and `uv.lock`;
a clean macOS/CPU installation path has not yet been packaged or validated. `pytest` exercises the tracked
unit and alignment-gate tests. The coverage calculation itself is CPU-only. Its default Prod outputs under
`results/kogovdoc/v1_val/predictions/` and the 663-Q–A probe are tracked, but the source-page mapping
`data/KoGovDoc-Bench/val.jsonl` is gitignored and not packaged. The command is therefore **not fresh-clone
complete**; it can use equivalent local inputs through `--parser_dir` and `--val_jsonl`.

These commands are not a reproduction of every paper experiment. Full reruns still depend on external
parser outputs, embedding caches, checkpoints, and executed-configuration provenance. The missing pieces are
listed explicitly below.

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

- **KoGovDoc-RAG probe files** — 663 Q–A whose evidence spans **242 pages**, plus the frozen
  169-development / 73-held-out evidence-page split. The paper's selection frame indexes these 242 pages
  together with 52 Q–A-free distractors (**294 pages = 229 KoGov + 65 arXiv**); that full source-page
  corpus and mapping are not packaged here. A separate LLM-assisted 100-pair Q–A quality-check sample
  and its aggregate 94/100 result are tracked; the sample's blank `verification` fields are not human annotations.
- **RCPS reference implementation** — [`src/wigtnocr_radp/evaluation/`](src/wigtnocr_radp/evaluation/).
- **Selected evaluation artifacts** — aggregate parser/chunker grids, per-Q–A arrays for audited training
  comparisons, coverage and end-to-end diagnostics, and complete 294-page outputs for Prod, PaddleOCR,
  and MinerU-on.
- **Aligned OHR audit artifacts** — the 1,043-Q–A Law–Manual C1 result and a deterministic derivation of
  the strict 2,036-Q–A legacy compatibility subset. Older seven-domain outputs remain in the tree for
  provenance and are listed in
  [`MANIFEST.legacy-invalid.sha256`](output/results/MANIFEST.legacy-invalid.sha256); they are not valid
  camera-ready evidence.
- **Aggregate human-check results** — the paper records the parser-masked 100-case absent-label study
  (κ = 0.615, raw agreement 81/100, and post-adjudication parser-specific rates).
- **Camera-ready figure assets** — Figures 1–4 are stored as vector PDFs with PNG README previews;
  Figure 1 also includes its canonical editable PPTX. The compiled paper was checked with embedded fonts
  and no Type 3 fonts.

### Camera-ready pending — not currently available

- The source-page mapping that links `val_####` Q–A IDs to tracked parser-output filenames
  (`data/KoGovDoc-Bench/val.jsonl`), or an equivalent portable manifest.
- MinerU **table-OFF**, Qwen3-VL-30B, and Qwen3-VL-2B-base parser outputs, plus exact rerun commands.
- Per-Q–A arrays for the complete 294-page parser/chunker grid and the corresponding probe-resampling
  **ranking-stability** artifact. The tracked aggregate-grid audit and end-to-end stability check are
  different analyses and are already present.
- Final per-case labels and adjudications from the separate parser-masked, two-author 100-case absent-label
  study. Its aggregate results are reported in the paper, but the per-case artifact is not currently in Git;
  release and packaging remain pending. This is distinct from the tracked 100-pair Q–A quality check.
- A full OHR-Bench v2 rerun and clean-checkout validation of the current/quarantine workflow; legacy
  seven-domain / combined-CI / OHR-TextNED artifacts are already separated in the quarantine manifest.
- RADP-Distill per-QA and confidence-interval artifacts evaluated on the same aligned subset; until then,
  no quantitative Distill-versus-DPO comparison is supported.
- Complete BC/CS mechanism data and aligned uncertainty estimates.
- Complete executed-configuration/log provenance and model checkpoints for RADP-Distill, RADP-aux,
  RADP-DPO, and SimPO. In particular, the executed R2 `beta` requires confirmation from the original
  checkpoint or log.
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
