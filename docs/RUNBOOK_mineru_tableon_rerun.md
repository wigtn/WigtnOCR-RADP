# Runbook — fair MinerU re-run (tables ON) + re-measure the absent gap

> Do this on the machine that HAS the KoGov data. It answers the one open
> question from the MinerU-config finding ([[mineru-table-config-bug]]): is the
> +50 pp MinerU−Prod absent gap a real content gap, or an artifact of running
> MinerU with `table-config.enable:false`? Everything here is in PR #10.

## Background (why)

The MinerU baseline was parsed with table recognition DISABLED (global
`magic-pdf.json`: `table-config.enable:false`). Result: 0 markdown tables over 294
KoGov pages, 31% image-only pages. So MinerU's KoGov RCPS 0.212 / 70.4% absent /
87.9% tabular-absent are all measured on a crippled run (on OHR-Bench, table-on,
MinerU scores 0.595 — competitive). The honest fix is to re-parse with tables ON
and recompute.

## What PR #10 gives you vs what you add

- ✅ In PR #10: the analysis code — `absent_robustness.py` (deterministic ladder,
  CPU-only), `absent_llm_judge.py` (3-way recoverability judge, OpenAI API),
  `baseline_grid.py` (RCPS, needs embedders/GPU), all now accepting
  `--override MinerU=<newdir>`.
- ➕ You add: the MinerU re-parse itself (was run outside the repo originally).
  `scripts/evaluation/run_mineru_tableon.py` (new) does it.

## Step 0 — environment

```bash
git fetch && git checkout rebuttal/family-neutral-absent && git pull
uv pip install "magic-pdf>=1.0,<2"     # same 1.x family that made the models
# models already on disk; magic-pdf.json points to them (models-dir)
```

## Step 1 — PILOT (de-risk: does tables-on actually parse tables?)

Parse just a few pages first. The melted-table page is `kogov_008/page_0544.png`
(= val_0000). Confirm it now yields a markdown table before committing hours.

```bash
uv run python scripts/evaluation/run_mineru_tableon.py \
    --images_root <IMAGES>/documents \
    --out /tmp/mineru_pilot --device cpu --limit 5
# the log ends with ".../5 pages have a markdown table" — expect > 0.
# eyeball: grep -c '|' /tmp/mineru_pilot/kogov_008_page_0544.md   (should be many)
```

- **Tables appear → go to Step 2.**
- **Still 0 tables** → version/model mismatch. Try a different magic-pdf version,
  or check the temp config actually set `table-config.enable:true` (the script
  prints its path — inspect it). Do not proceed to the full run until the pilot
  shows tables.

`<IMAGES>` = the dir whose children are `kogov_001/`, `kogov_008/`, … Each holds
`page_XXXX.png`. (On the old server this was
`.../wigtnOCR-v1/datasets/training/images/documents`.)

## Step 2 — full re-parse (tables ON) to a NEW dir

```bash
uv run python scripts/evaluation/run_mineru_tableon.py \
    --images_root <IMAGES>/documents \
    --val_jsonl data/KoGovDoc-Bench/val.jsonl \
    --out <RESULTS>/kogovdoc/mineru_val_tableon/predictions \
    --device cpu           # cuda if a GPU is free; CPU ~1-3h for 294 pages
```

Does NOT touch the original `mineru_val/` — new dir `mineru_val_tableon/`.

## Step 3 — recompute the absent gap (CPU only, no embedder)

This is the decisive number. `--root` points at your results root; `--override`
swaps MinerU to the table-on dir.

```bash
uv run python scripts/evaluation/absent_robustness.py \
    --root <RESULTS>/kogovdoc \
    --override MinerU=mineru_val_tableon/predictions --ref Prod
# reads output/diagnostics/absent_robustness.{json,md}
```

Compare MinerU's absent row + the MinerU−Prod gap to the table-off numbers
(L1 70.4% / gap +50.2 pp). Then the 3-way judge (needs OPENAI_API_KEY):

```bash
export OPENAI_API_KEY=...
uv run python scripts/evaluation/absent_llm_judge.py \
    --parsers Prod MinerU --override MinerU=mineru_val_tableon/predictions
```

## Step 4 (optional, needs GPU) — recompute RCPS

RCPS needs the 3 embedders (BGE-M3, e5-large, Qwen3-Embedding-8B). Point
`baseline_grid.py` at the new MinerU dir (edit its parser map or add the dir) and
re-run to get MinerU's fair RCPS / Hit@1.

## How to read the outcome

| Result | Meaning | Paper action |
|---|---|---|
| MinerU absent stays high (gap still ~+50 pp) | content genuinely lost even with tables on | **Bulletproof.** Report table-on numbers; the finding survives. Keep C1/C2 as-is with the fair config stated. |
| MinerU absent drops a lot (gap shrinks) | the gap was mostly the disabled-table config | **Reframe.** MinerU is no longer the clean-but-empty poster child; lean C1 on the config-independent OHR noise-insensitivity, state MinerU's fair number, drop/soften the KoGov MinerU-BC anti-correlation headline. |

Either way, state MinerU's config explicitly in Setup/Limitations (honesty), and
update `tab:grid` / the family-neutral appendix with the table-on MinerU numbers.
The worked example was already removed from the paper (config-exposure risk); if
the table-on run still shows a genuine table loss, a re-caveated version can go
back in.
