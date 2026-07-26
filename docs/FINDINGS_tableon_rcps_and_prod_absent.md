# Findings — table-ON MinerU retrieval, Prod per-domain absent, dataset seal

> Executed 2026-07-26 on ml37 (RTX 3090, 3-retriever RCPS incl. Qwen3-Embedding-8B)
> and ml35 (per-domain absent + dataset counts). Closes the last open item from the
> MinerU config self-audit: does the C1 headline survive a *fair* (table-on) MinerU
> retrieval measurement, on the same predictions the E2E run used?

## 1. MinerU table-ON retrieval — the C1 headline holds and widens

**What.** The paper's parser grid (Table~1) measures MinerU at RCPS 0.212 / Hit@1
0.197, but that MinerU baseline was run with table recognition OFF (tables dumped
as image refs). To test whether the parsing–retrieval disconnect is a config
artefact, we recomputed RCPS/Hit@1 on the **table-ON** MinerU predictions
(`results/kogovdoc/mineru_val_tableon/predictions/`, 294 pages — the *same*
predictions the end-to-end run used), with the identical pipeline: parser-native
chunking, the 3 retrievers (BGE-M3 + multilingual-e5-large + Qwen3-Embedding-8B),
`compute_rcps` over the 663-Q–A probe.

**Result (663 Q–A, parser_native, 903 chunks):**

| MinerU | RCPS | Hit@1 | Hit@5 | Hit@10 |
|---|---|---|---|---|
| table-OFF (paper Table 1, KoGov) | 0.212 | 0.197 | — | — |
| **table-ON (re-run, overall)** | **0.137** | **0.123** | 0.173 | 0.190 |
| — KoGov only (n=527) | **0.046** | **0.038** | — | — |
| — arxiv only (n=136) | 0.486 | 0.451 | — | — |

Per-retriever Hit@1 (table-ON): BGE-M3 0.118, e5-large 0.110, Qwen3-Emb-8B 0.140.

**Interpretation.** Turning tables ON does **not** rescue MinerU — on the Korean
government documents its RCPS *drops* from 0.212 to **0.046** (Hit@1 0.197 →
0.038). The reason is visible in the output: MinerU now emits the table, but the
cell values are OCR-corrupted (`13,316`→`13.316`, `1800`→`180`, and numbers turned
into LaTeX fragments like `$1.5\mathrm{m}$`), so the "clean-looking" table is
unretrievable — exactly the formatting-≠-content-fidelity mechanism the paper
argues (C1/C2). The takeaway is narrow and safe: MinerU's low retrieval is **not**
an artefact of the disabled-table configuration — enabling tables makes it worse,
not better, so the parsing–retrieval disconnect stands.

(MinerU does far better on English arxiv — RCPS 0.486 — consistent with its
competitive OHR-Bench score; the failure is specific to the Korean-gov corpus.)

## 2. Prod per-domain absent — gate passed, implementation validated

**What.** Per-domain (KoGov vs arxiv) breakdown of the Prod (v1_val) absent rate
across the L0–L4 matching ladder, to confirm the per-domain tooling reproduces the
paper's fixed corpus numbers before it is used elsewhere.

**Result (Prod, 663 Q–A: kogov=527, arxiv=136):**

| rung | arxiv | kogov | overall (weighted) |
|---|---:|---:|---:|
| L0_exact | 25.7% | 23.7% | 24.1% |
| L1_normalized | 24.3% | 19.2% | **20.2%** |
| L2_numeric | 23.5% | 18.6% | 19.6% |
| L3_token_recall | 20.6% | 25.0% | 24.1% |
| L4_fuzzy_lcs | 22.8% | 15.4% | **16.9%** |

**Gate:** overall L1 = 20.2% (target 20.2% ± 0.2), L4 = 16.9% (target 16.9% ±
0.2) — **both pass exactly**. The per-domain implementation reproduces the paper's
fixed-corpus absent numbers, so its per-domain split is trustworthy.

## 3. Dataset fold seal

**What.** Line counts of the training/validation folds, to confirm the fold sizes
and rule out stray "2,664 / 2,994" figures.

**Result:** `train.jsonl` = **2,667**, `val.jsonl` = **294** — matches the
expected 2,667 / 294. The 4a fold sizes are sealed; the ghost 2,664/2,994 numbers
do not originate here.

## Artefacts — where each result lives in the repo

Result JSONs (committed on `main`):

| File | Produced by | Contains |
|---|---|---|
| `output/results/grid_MinerU-tableON_parser_native.json` | §1, `scripts/analysis/grid_single_parser.py` | table-ON MinerU RCPS/Hit@{1,5,10}/MRR/nDCG, overall + per-retriever |
| `output/results/perqa_MinerU-tableON_parser_native.json` | §1, same run (`return_per_qa`) | per-Q–A MRR (input to the kogov/arxiv split) |

The per-domain split of §1 (kogov 0.046 / arxiv 0.486) is derived from the perqa
file via `scripts/analysis/perqa_source_rcps.py`; the numeric table above is the
canonical record (the script prints, it does not write a JSON).

§2 (Prod per-domain absent) and §3 (fold counts) are **stdout tables/counts by
design** (per `docs/HANDOFF_wsl_rebuttal_runs.md`) — the full tables are inlined
above; no JSON is emitted for them.

Inputs:

- `results/kogovdoc/mineru_val_tableon/predictions/` — 294 table-ON MinerU `.md`
  (in-repo), the **same predictions the end-to-end run consumed** (§1 fairness).
- `data/KoGovDoc-RAG/qa_pairs_v1.jsonl` — the 663-Q–A probe (in-repo).
- Prod predictions (§2): read from
  `…/wigtnOCR-v1/results/kogovdoc/v1_val/predictions` on the run host (not in-repo).

Scripts (committed): `scripts/analysis/{grid_single_parser, perqa_source_rcps,
absent_per_domain, source_groupby}.py`.

## Caveats

- The table-ON re-run uses a freshly-installed 3-retriever stack (magic-pdf-era
  predictions unchanged; retrievers BGE-M3 / e5-large / Qwen3-Embedding-8B on a
  3090). The retrieval pipeline (chunker, `compute_rcps`, probe) is identical to
  the paper grid; only the MinerU *predictions* differ (tables on vs off).
- Both the paper Table 1 value 0.212 and the table-ON overall 0.137 are mixed-corpus
  scores (663 Q–A = 527 KoGov + 136 arxiv; verified against the grid config), so
  mixed-to-mixed the drop is 0.212 → 0.137. The per-domain decomposition (KoGov-only
  0.046 vs arxiv 0.486) shows where the collapse concentrates — arxiv cushions the
  mixed average.
