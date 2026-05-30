# WigtnOCR-RADP

**Retrieval-Aware Document Parsing — human-readable parsing ≠ retrievable parsing.**

> 🎯 EMNLP 2026 Industry Track submission (deadline 2026-06-16)
> 📦 Builds on [WigtnOCR v1](https://huggingface.co/Wigtn/Qwen3-VL-2B-WigtnOCR) + [KoGovDoc-Bench](https://huggingface.co/datasets/Wigtn/KoGovDoc-Bench)
> 🇰🇷 **[한국어 README](README.ko.md)** &nbsp;·&nbsp; 🧭 Research definition: [`docs/RESEARCH_DIRECTION.md`](docs/RESEARCH_DIRECTION.md) (KO) &nbsp;·&nbsp; progress: [`docs/ACHIEVED.md`](docs/ACHIEVED.md) / [`docs/ROADMAP.md`](docs/ROADMAP.md)

---

## TL;DR

Document parsers used in retrieval-augmented generation (RAG) are conventionally optimized
for *human-readability* metrics — TEDS, edit distance, Boundary Clarity — yet these metrics
**do not predict downstream retrieval**. On Korean government documents (6 parsers × 3 retrievers
× 663 Q-A), MoC Boundary Clarity *anti*-correlates with retrieval at **Pearson r = −0.81**: the
parser scoring highest on the intrinsic metric (MinerU) is the *worst* retriever.

We (C1) diagnose this disconnect cross-domain and expose its mechanism, (C2) propose **RCPS**
(Retrieval-Conditional Parsing Score), a retriever-agnostic task-oriented metric, and (C3) test
the natural parser-side fix — a chunk-boundary contrastive auxiliary loss (**RADP**) — at full
scale, and report a **rigorous negative** (+1–3 pp, below our pre-registered 5 pp gate). We release
**KoGovDoc-RAG**, the RCPS reference implementation, and the trained checkpoints.

---

## Motivation — parsing quality ≠ retrieval performance

A practitioner picking a parser for a RAG system runs MinerU on Korean government PDFs, confirms
it tops every intrinsic parsing-quality metric in our grid — highest MoC Boundary Clarity (0.72) —
and deploys it. Retrieval Hit@1 is **0.20, the worst of the six parsers evaluated.** The cleanest-looking
parser is the worst retriever.

This is not a one-off. The same direction is reported independently in English / enterprise settings
by OHR-Bench (ICCV 2025), EnterpriseDocBench (2026, r ≈ 0.14), and *When Good OCR Is Not Enough* (2026).
**Prior work either stops at diagnosis or trains a different pipeline layer (chunking → generation).
No prior work trains the L1 parser itself on a retrieval signal — that is our niche.**

---

## Core hypothesis — the causal chain we test

```
① train the parser on a retrieval signal  →  ② chunk boundaries shift from "human-friendly" to "retrieval-friendly"
                                           →  ③ those pieces score higher in retrieval (Hit@ / MRR)
```

The crux is showing ③ happens **because of** ②, and that it shows up **not only in our own metric but
in standard retrieval metrics**. (Full definitions & current status in [`docs/RESEARCH_DIRECTION.md`](docs/RESEARCH_DIRECTION.md).)

---

## Contributions

| | Contribution | Status |
|---|---|:---:|
| **C1** | A cross-domain **diagnostic** of the parsing↔retrieval disconnect, with a mechanism (noise-family curve, Figure 2) that makes the intrinsic-metric failure mode visible at a glance | ✅ |
| **C2** | **RCPS** (Retrieval-Conditional Parsing Score) — a retriever-agnostic, task-oriented metric to choose parsers/chunkers for production RAG, discriminating combinations intrinsic metrics conflate | ✅ |
| **C3** | A **rigorous negative** on the natural parser-side fix: a chunk-boundary contrastive auxiliary loss (**RADP**), at full scale and fair-compared with the production parser, yields +1–3 pp RCPS — below the pre-registered 5 pp gate. The aux-loss formulation is the wrong lever | ✅ |
| → next | Retrieval-reward training (DPO/RL) on the parser's **discrete output** — motivated by the C3 negative | 🔄 future work |

---

## Method

### RCPS — Retrieval-Conditional Parsing Score

Score a parser by what *downstream retrieval* can do with its output, not by how clean the output looks.
Given a parser `P`, a Q-A set `D = {(qᵢ, aᵢ, pageᵢ)}`, retrievers `R`, and cutoffs `K`:

```
RCPS(P, D, R, K) = (1 / |R||K|) · Σ_{r∈R} Σ_{k∈K}  MRR@k( r, chunks_P(D), {qᵢ} )
```

- `R = {BGE-M3, multilingual-e5-large, Qwen3-Embedding-8B}` (multilingual, varied architectures); `K = {1, 5, 10}`.
- A chunk is **relevant** for a query iff (i) its source page matches the answer's page, and (ii) the gold
  answer span is a substring of the chunk under whitespace/markdown-insensitive normalization.
- Averaging over retrievers makes the score **robust to embedder choice**. Reference implementation:
  [`src/wigtnocr_radp/evaluation/`](src/wigtnocr_radp/evaluation/).

### RADP — parser-side contrastive method

Jointly train the parser to (a) produce faithful markdown (standard parsing cross-entropy `L_parse`)
and (b) make its chunk-boundary representation close to the retriever's embedding space (a chunk-boundary
contrastive auxiliary loss `L_contrast`):

```
L_total = L_parse + λ · L_contrast
```

The contrastive anchor is the parser's pooled last-layer hidden state over the answer-chunk's token span,
projected to 1024-d; the InfoNCE positive is the BGE-M3 embedding of that same chunk; negatives are other
in-batch chunks plus a same-page hard negative. The retriever (BGE-M3) is frozen; only the parser (LoRA)
and the projection head are trained.

---

## Experiments

### Setup

- **KoGovDoc-RAG** — 663 Q-A over 294 pages of Korean government documents (GPT-5.4-generated,
  LLM-as-judge verified, 94/100 stratified accept). For RADP full-scale training we add 6,164 Q-A on
  the 2,667-page v1 train set; a held-out **73-page / 202-Q-A** fold is used for all RADP evaluation.
- **OHR-Bench** — cross-domain replication across 7 domains (Law, Manual, Finance, Newspaper, Textbook,
  Academic, Administration; 1,043 verbatim-answerable Q-A), 15 parser-output variants (3 real outputs +
  3 formatting-noise + 9 semantic-noise perturbations).
- **Model** — Qwen3-VL-2B-Instruct + LoRA (r = 8, α = 32), full v1 train set; λ ∈ {0, 0.1, 0.3, 0.5}
  (λ = 0 is a matched control reproducing the production parser v1).

### C1 — the parsing↔retrieval disconnect (Korean government docs)

RCPS spans 0.07–0.58 across six parsers; VLM-family parsers cluster at the top, OCR systems trail.
Intrinsic Boundary Clarity **anti-correlates** with RCPS at **Pearson r = −0.81** (n = 5, excl. the
38-page Marker subset). MinerU — cleanest boundaries (BC 0.72) — retrieves **worst**.

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

The headline finding: **within each semantic-noise family, Boundary Clarity barely moves while RCPS
collapses.** Intrinsic boundary metrics see only *formatting*, not *content* — semantic noise that
destroys retrievable content does not lower BC.

![Boundary Clarity is blind to content noise — top: BC stays flat across noise severity for all three parser families; bottom: RCPS collapses for MinerU and GOT while Qwen2.5-VL is noise-robust](paper/figures/fig_noise_family.png)

*Figure 2 — OHR-Bench 7-domain noise-family curves. **Top:** Boundary Clarity stays roughly flat across
noise severity (clean → mild → moderate → severe) for all three parser families. **Bottom:** RCPS collapses
for MinerU (−51%) and GOT, while Qwen2.5-VL is more noise-robust (−8%). The intrinsic metric does not
perceive the semantic content quality that retrieval depends on.*

| Family (n) | BC range | RCPS (clean → severe) | ΔRCPS |
|---|:---:|:---:|:---:|
| MinerU + semantic noise (4) | 0.708–0.735 | 0.50 → 0.24 | **−51%** |
| GOT + semantic noise (3) | 0.495–0.650 | (no clean) → 0.26 | — |
| Qwen2.5-VL + semantic noise (4) | 0.610–0.619 | 0.47 → 0.43 | −8% |

*Table 2 — OHR-Bench per-family noise-perturbation summary. The disconnect (BC flat, RCPS dropping under
semantic noise) is dramatic for MinerU and GOT; Qwen2.5-VL is more robust. The aggregate cross-variant
BC↔RCPS scalar is data-mix sensitive (−0.35 on Law+Manual, +0.25 on the full 7-domain corpus); the robust
finding is the per-family mechanism, which reproduces in every domain.*

### C2 — RCPS discriminates chunking strategies

A useful metric must separate alternatives a practitioner would compare. On the v1 parser's KoGov output,
RCPS cleanly ranks four chunking strategies — markdown-header (md-h3) > parser-native paragraphing >
LumberChunker > fixed-size — capturing *retrievability*, not surface appearance (intrinsic metrics would
rank fixed-size highest, since it has the cleanest boundaries by construction).

| Chunker | RCPS | Hit@1 | MRR@10 |
|---|:---:|:---:|:---:|
| md-h3 | **0.593** | 0.556 | 0.613 |
| parser_native | 0.583 | 0.549 | 0.602 |
| LumberChunker | 0.557 | 0.514 | 0.580 |
| fixed500 | 0.535 | 0.491 | 0.560 |

*Table 3 — KoGov chunking-strategy grid (663 Q-A, v1 parser output, 3-retriever RCPS average).*

### C3 — the parser-side fix does *not* close the gap (the negative)

RADP trained at full scale (2,667 pages), evaluated on the 73-page / 202-Q-A held-out fold. The contrastive
loss yields a **sub-threshold** gain: λ = 0.1 is the peak (+1.1 pp md-h3 / +2.3 pp parser-native), and RCPS
declines monotonically beyond it while `parseSim` drops in lockstep — the two objectives **compete over the
same LoRA parameters.** The pre-registered **5 pp gate fails.**

| λ | RCPS (md-h3) | RCPS (parser-native) | parseSim |
|---|:---:|:---:|:---:|
| 0.0 (control) | 0.6551 | 0.6557 | 0.872 |
| **0.1** | **0.6664** | **0.6788** | 0.874 |
| 0.3 | 0.6526 | 0.6694 | 0.862 |
| 0.5 | 0.6407 | 0.6442 | 0.851 |
| v1 (ref) | 0.6724 | 0.6569 | 0.789 |

*Table 4 — full-scale λ sweep, 73-page eval fold. Best vs matched control: +1.13 pp (md-h3) / +2.31 pp
(parser-native) — gate (≥ 5 pp) fails. The control reproduces v1, confirming the data-scale confound is removed.*

**Why it fails (and the C1 connection).** The parser's `L_parse` target is itself human-readable markdown —
exactly the structure whose intrinsic boundary metrics anti-correlate with retrieval (Figure 2). An auxiliary
objective on the parser's *hidden* representations cannot escape the prior its primary objective embeds. To
overcome the human-readability prior, the training signal has to enter through the parser's **discrete output**,
not its hidden states — which motivates retrieval-reward (DPO/RL) training as the principled next step (future work).

---

## Deployment lessons

1. **Do not select parsers by intrinsic metrics alone.** Boundary Clarity (likewise TEDS, edit distance)
   can rank parsers in an order the downstream retriever inverts. A ~500-question RCPS evaluation on a
   domain-representative held-out set takes hours and changes the decision.
2. **Auxiliary losses on parser hidden states are the wrong lever.** At full scale, fair-compared with a
   production parser, the gain is sub-threshold (+1–3 pp). The investment does not pay off.
3. **The disconnect is mechanistic, not stochastic.** Intrinsic structure can look pristine while content
   is destroyed (Figure 2) — monitor retrieval directly, not the parser's surface quality.

---

## Repository structure

```
.
├── configs/                  # experiment configs (YAML)
├── src/wigtnocr_radp/
│   ├── qa_generation/        # Q-A generation
│   ├── evaluation/           # RCPS, chunkers, retrievers, coverage diagnostic, Boundary Clarity
│   └── training/             # RADP (contrastive) / DPO components
├── scripts/
│   ├── qa_generation/
│   ├── training/             # train_radp_b, DPO generate/score/build/train
│   └── evaluation/           # baseline_grid, chunking_grid, coverage_diagnostic, bootstrap
├── paper/                    # EMNLP 2026 draft + figures
├── data/KoGovDoc-RAG/        # 663 Q-A (frozen, gitignored)
├── docs/                     # see below
├── output/                   # results & checkpoints (gitignored, GPU server)
└── tests/
```

## Documentation

| Doc | Contents |
|-----|----------|
| [`docs/RESEARCH_DIRECTION.md`](docs/RESEARCH_DIRECTION.md) | **Research definition** — hypothesis, proof chain, current position, completion criteria ★ (KO) |
| [`docs/ACHIEVED.md`](docs/ACHIEVED.md) | What's done (C1/C2/C3 + infra, with evidence links) (KO) |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | What's next (priorities, timeline, gates) (KO) |
| [`docs/plans/`](docs/plans/) | Per-task detailed plans (PLAN-01–05) |
| [`paper/draft/paper.md`](paper/draft/paper.md) | EMNLP 2026 Industry Track draft |

---

## Quick start

```bash
uv sync                                   # dependencies
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

> \* **Equal contribution (co-first authors).** See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## License & Citation

Released under the [MIT License](LICENSE). *(Upstream WigtnOCR v1 is Apache-2.0.)*

```bibtex
@inproceedings{kim2026radp,
  title     = {Retrieval-Aware Document Parsing: Diagnosing and Measuring the Parsing--Retrieval Gap},
  author    = {Kim, Hyeong-seob and Son, Sang-woo},
  booktitle = {Proceedings of EMNLP 2026 (Industry Track)},
  year      = {2026},
  note      = {To appear}
}
```
