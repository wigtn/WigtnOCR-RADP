# Findings — Boundary Clarity for MinerU table-ON (the missing Table 1 cell)

> Executed 2026-08-23 on WSL (RTX 5070). Closes the one gap left by
> `FINDINGS_tableon_rcps_and_prod_absent.md`: the table-ON MinerU re-run has
> RCPS/Hit@1 in the camera-ready grid, but its **BC cell is `---`**. Every other
> complete-output parser in Table~1 has a BC value, so MinerU-on could not be
> used in the C1 correlation and the "high BC, low retrieval" example had to be
> borrowed from the separate MinerU-off diagnostic row.
>
> **Answer: MinerU-on BC = 0.7132 — statistically indistinguishable from
> MinerU-off's 0.716 (−0.003), and the highest BC of any complete-output parser
> in the deployment pool, while its RCPS is the lowest. The 4-parser BC–RCPS
> Pearson is r = −0.7445, which rounds to the same −0.74 the paper already
> reports. The C1 claim holds with MinerU-on substituted for MinerU-off.**

Nothing in the paper, the READMEs, or any existing result file was modified by
this run. The only new artifacts are the script, its tests, this document, and
`output/baselines/moc_bc_mineru_tableon.json`.

## 1. Purpose

The camera-ready makes three BC-dependent statements:

- Table~1 (`tab:grid`): the deployment rows use MinerU-on, whose BC is `---`.
- §C1 L131: "Among four 294-page parsers with defined BC, its Pearson
  correlation with RCPS is $r=-0.74$."
- Figure `fig:disconnect` caption: same $r=-0.74$ / $-0.81$ pair, noting
  explicitly that **MinerU-off is used in this diagnostic**.

That last clause is the weak point. The deployment comparison is MinerU-on, but
the correlation that supports it is computed on MinerU-off. This run measures BC
for MinerU-on directly, under the identical definition and settings, so the two
analyses can be stated over one parser set.

## 2. What was run

```bash
CUDA_VISIBLE_DEVICES=0 HF_HUB_OFFLINE=0 uv run python \
  scripts/evaluation/compute_parser_bc.py \
  --parser-dir results/kogovdoc/mineru_val_tableon/predictions \
  --label MinerU-on \
  --model Qwen/Qwen3-VL-2B-Instruct \
  --device cuda \
  --max-tokens 1024 \
  --expected-pages 294 \
  --expected-chunks 903 \
  --out output/baselines/moc_bc_mineru_tableon.json
```

Metric, unchanged from `src/wigtnocr_radp/evaluation/boundary_clarity.py`:

    BC(q | d) = ppl(q | d) / ppl(q) = exp(NLL(q | d) − NLL(q))

`PerplexityLM` — its tokenisation, its left-truncation of the context, its
target cap of `max_tokens // 2`, and its NLL formula — was **not** touched. The
point of this run is comparability with the existing MinerU-off number, not a
better BC implementation. Likewise the table-ON `.md` files were consumed
verbatim: no HTML handling, no text normalisation, no re-parsing.

Only within-page adjacent chunk pairs are scored; no boundary is formed across a
page break. The headline number is the unweighted mean over **all** valid
boundaries, not a mean of per-page means. BC is not clamped to [0, 1] — the
observed maximum is 1.714.

## 3. Input verification — both gates passed

| Gate | Expected | Observed | Result |
|---|---|---|---|
| Prediction `.md` files (git-tracked) | 294 | **294** | pass |
| `ParserNativeChunker(min_chars=30)` chunks | 903 | **903** | pass |
| Pages yielding ≥1 chunk | 294 | **294** | pass |

The chunk gate is the load-bearing one: 903 is the `num_chunks` recorded in
`output/results/grid_MinerU-tableON_parser_native.json`, so BC and RCPS are
measured over the *same* chunking of the *same* bytes. The script hard-fails
before the LM is loaded if either count differs.

- Input manifest SHA-256: `1fd8559a1efc9653d956d012b453a236ffbeb7107de385d5b7875a3886867803`
  (over each `*.md` sorted by filename: repo-relative path + NUL + sha256(bytes) + LF).

**Page-id caveat.** The RCPS grid keys these pages `val_NNNN` via
`data/KoGovDoc-Bench/val.jsonl`, which is not in this repo (it has never been
git-tracked). This run therefore keys pages by sorted filename stem instead. The
mapping is a bijection over the same 294 files, and BC depends only on
within-page chunk adjacency, so every chunk, every boundary and the corpus mean
are identical — only the `per_page.page_id` labels differ. The 903-chunk match
confirms this empirically.

## 4. Result

| Quantity | Value |
|---|---|
| Boundaries attempted | 609 |
| Boundaries valid | **609** |
| Boundaries skipped | **0** (no None, no NaN, no Inf) |
| **Mean BC** | **0.7132** (0.7132110997071613) |
| Median BC | 0.7289 |
| Std BC (sample, n−1) | 0.2567 |
| Min / Max BC | 0.0530 / 1.7137 |

609 = 903 chunks − 294 pages, as expected when every page yields at least one
chunk. The same identity holds for all six parsers in the existing BC file
(e.g. MinerU-off: 1050 − 294 = 756), which is an independent check that this run
enumerates boundaries exactly the way the original did.

Nothing was silently discarded: the skip histogram is empty.

### Comparison to the existing BC values

| Parser | BC | RCPS | Hit@1 |
|---|---|---|---|
| Marker (38p, partial) | 0.7168 | 0.073 | 0.068 |
| MinerU-off | 0.7161 | 0.212 | 0.197 |
| **MinerU-on (this run)** | **0.7132** | **0.1365** | **0.1227** |
| Qwen3-VL-30B (teacher) | 0.6232 | 0.5844 | 0.5445 |
| Prod / WigtnOCR-2B (ours, v1) | 0.6100 | 0.5826 | 0.5485 |
| Qwen3-VL-2B (base) | 0.5199 | 0.5321 | 0.4997 |

- **MinerU-on BC − MinerU-off BC = −0.0029.** Turning table recognition on moved
  BC by three thousandths — nothing, against a within-corpus std of 0.257.
- **MinerU-on BC − Prod BC = +0.1032.** MinerU-on has clearly *cleaner*
  boundaries than the production parser, and 4.7× worse Hit@1.

This is the C1 pattern in its sharpest form so far, and it now lives entirely
inside the deployment pool: among the parsers with complete 294-page output,
**MinerU-on has the highest BC and the lowest RCPS.** Previously that example
required the separately-scoped MinerU-off row.

## 5. New 4-parser correlation

Complete-output parsers only. BC for the first three is read from
`output/baselines/moc_bc_correlation.json`; their RCPS/Hit@1 come from the
current grid `output/baselines/grid_v1_parser_native.json`; MinerU-on pairs this
run's BC with `output/results/grid_MinerU-tableON_parser_native.json`. Marker
(38 pages) and PaddleOCR (0 boundaries) stay excluded, as in the original
analysis. MinerU-off is *replaced by* MinerU-on rather than added — they are the
same 294 pages re-parsed, so including both would double-count one parser.

| Pair | Pearson r | p | Spearman ρ | p |
|---|---|---|---|---|
| BC vs RCPS | **−0.7445** | 0.2555 | −0.20 | 0.80 |
| BC vs Hit@1 | −0.7484 | 0.2516 | −0.40 | 0.60 |

For reference, the same 4-parser correlation computed with **MinerU-off** BC and
the same current-grid RCPS gives Pearson **−0.7357**, Spearman −0.20 — i.e. the
paper's reported $r=-0.74$. Swapping in MinerU-on moves it to −0.7445, which
still rounds to **−0.74**.

The p-values use the standard t-approximation (identical to `scipy.stats`
defaults). At n = 4 they are a formality, not evidence; the paper already calls
these correlations descriptive and should keep doing so.

Spearman is only −0.20 because the BC and RCPS orderings agree on nothing except
that MinerU is last: the 30B teacher outranks Prod on RCPS but the reverse on
BC. A near-zero rank correlation alongside a strongly negative Pearson is itself
consistent with the C1 claim — BC carries no usable monotone information about
retrieval utility in this pool.

`scipy` is not installed in this project's venv, so Pearson/Spearman are
implemented in pure Python inside the script. They are pinned by unit test
against the committed scipy-produced numbers in `moc_bc_correlation.json`
(−0.8137/0.0938 and −0.7/0.1881 for the n=5 set, −0.8178/0.0908 for Hit@1),
which they reproduce to 4 decimal places.

## 6. Environment

| | |
|---|---|
| Git commit | `b563327c3c7d417f3e6500869be148c545fff6cb` |
| Executed (UTC) | 2026-08-23T14:36:37Z |
| Model | `Qwen/Qwen3-VL-2B-Instruct` |
| Model revision | `89644892e4d85e24eaac8bacfd4f463576704203` |
| dtype / device | `torch.bfloat16` / `cuda` |
| GPU | NVIDIA GeForce RTX 5070 |
| Python / torch | 3.13.13 / 2.8.0+cu128 |
| transformers / CUDA | 5.8.1 / 12.8 |

`provenance.git_dirty` is `true` in the result JSON: the working tree held the
new script, its tests and this document when the run executed. No tracked input
file was modified — the input manifest hash in §3 covers the 294 predictions and
is reproducible from the committed tree.

Runtime was about 5 minutes for 609 boundaries (1,218 forward passes) after a
one-off model download. The script checkpoints to `scratch/bc/<label>/` and
resumes from it; `scratch/` is gitignored, so no checkpoint, model cache or log
is committed. The final JSON is written to a temp file and `os.replace`d, so an
interrupted run can never leave a truncated result.

The committed JSON was regenerated by re-running the finished script against the
checkpoint after some lint-only edits (import order, `zip(strict=True)`,
`datetime.UTC`). It came back **identical to the first run in every field except
`executed_at_utc`**, which is why the timestamp above is 14:36:37Z rather than
the 14:31:07Z of the original scoring pass.

## 7. Caveats — read before quoting any of this

1. **The reference BC values were recorded without a model revision.**
   `moc_bc_correlation.json` stores `ppl_model` but no Hugging Face commit hash,
   no dtype, no torch/transformers versions, and no GPU. This run pins revision
   `89644892…`, but there is no way to prove the 2026-07 run used the same
   snapshot. The MinerU-on − MinerU-off gap of −0.0029 is *within* the range that
   environment drift alone could explain. Treat the two numbers as "the same to
   within measurement noise", not as a measured 0.003 decrease.

2. **The reference BC values are stored rounded to 4 decimals**, so every
   difference in §4 carries at most 4-decimal precision.

3. **MinerU-on vs MinerU-off is not a table-recognition ablation.** As
   `FINDINGS_mineru_tableon_rerun.md` records, the two runs differ in parsing
   software environment, not only in `table-config.enable`. The paper already
   states this ("the two MinerU runs differ in more than table handling"). The
   BC result must not be reported as "enabling table recognition changes BC by
   −0.003"; it is "two MinerU configurations, differing in more than tables,
   land at the same BC".

4. **n = 4.** Both correlations are descriptive. The Pearson coefficient is
   dominated by the single MinerU point being far from the other three on the
   RCPS axis; dropping it collapses the sample to 3.

5. **BC is LM-relative.** It is defined against Qwen3-VL-2B-Instruct's text
   path. That is fine for a cross-parser comparison — every parser is scored by
   the same LM — but the absolute value is not a property of the parser alone.

## 8. Camera-ready implication (conditional — no paper text was changed)

Stated as options, not as edits. The decision is deferred to the main PC.

**If the MinerU-on BC cell is filled in:** Table~1's `MinerU-on` BC becomes
`0.713`, and it is then the highest BC among the five complete-output deployment
rows while holding the lowest RCPS. That is a strictly stronger presentation of
C1 than the current `---`, because the misranking no longer has to be imported
from the separately-scoped MinerU-off diagnostic row.

**If §C1 L131 and the `fig:disconnect` caption are re-based on MinerU-on:** the
quoted $r=-0.74$ is unchanged at two decimals (−0.7445 vs −0.7357), and the
sentence "MinerU-off is used in this diagnostic" in the figure caption could be
dropped, removing the one place where the deployment pool and the correlation
pool disagree. Note the n=5 variant ($r=-0.81$) is a *different* set — it adds
Marker and uses the RCPS snapshot embedded in `moc_bc_correlation.json`, not the
current grid — so it is not automatically re-based by this run.

**If nothing is changed:** nothing in the paper becomes wrong. Every claim above
survives; the MinerU-on BC cell simply stays empty and the caveat sentence stays
in the caption.

**What this run does not license.** It gives no basis for a causal
table-recognition statement (caveat 3), no basis for strengthening the
correlation's statistical language (caveat 4), and no basis for dropping the
"descriptive" hedging.

## 9. Reproduce

```bash
uv run pytest tests/test_compute_parser_bc.py tests/test_chunkers.py
# input gates only, no model load:
uv run python scripts/evaluation/compute_parser_bc.py \
  --parser-dir results/kogovdoc/mineru_val_tableon/predictions \
  --label MinerU-on --expected-pages 294 --expected-chunks 903 \
  --out output/baselines/moc_bc_mineru_tableon.json --dry-run
```

Related: [[mineru-table-config-bug]], `FINDINGS_mineru_tableon_rerun.md`,
`FINDINGS_tableon_rcps_and_prod_absent.md`,
`FINDINGS_tableon_local_verification.md`.
