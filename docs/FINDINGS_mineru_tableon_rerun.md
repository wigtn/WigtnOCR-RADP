# Findings — MinerU table-ON re-run + fair absent re-measurement

> Executed 2026-07-24 on the fresh WSL machine (RTX 5070). Answers the open
> question from [[mineru-table-config-bug]] / the runbook
> `RUNBOOK_mineru_tableon_rerun.md`: is the +50 pp MinerU−Prod absent gap a real
> content gap, or an artifact of running MinerU with `table-config.enable:false`?
>
> **Answer: mostly real. The gap PERSISTS at ~+46 pp with tables ON — it does not
> collapse. But the paper's specific *tabular* absent figure (87.9%) was
> materially config-inflated and must be corrected to ~42%.**

## What was actually run

The runbook assumed "models already on disk" — false on this machine. Full
bootstrap was needed and done (non-destructive, new dir only):

- `magic-pdf 1.3.12` (`[full]`) in a dedicated py3.12 venv (`~/mineru-venv`).
- Models: `opendatalab/PDF-Extract-Kit-1.0` + `hantian/layoutreader`. The current
  HF snapshot dropped the v3 OCR files magic-pdf 1.3.12 references
  (`ch_PP-OCRv3_det_infer.pth` etc.); back-filled 13 files from revision
  `a4f6a8d29a4d` (last before the 2025-10-24 v3 deletion).
- `transformers` pinned to **4.49.0** — 4.57 crashes UnimerNet MFR with
  `UnimerMBartForCausalLM.forward() got an unexpected keyword argument 'cache_position'`.
- `magic-pdf.json`: `device-mode: cuda`, `table-config.enable:true`,
  `formula-config.enable:true`.
- Parsed **all 294 val pages** (229 KoGov + 65 arxiv) tables-ON, HTML tables
  stripped to spaces (fair vs markdown parsers). 0 failed. **140/229 KoGov pages
  now contain a table** (was **0** with the config bug).
- Output: `results/kogovdoc/mineru_val_tableon/predictions/` (294 `.md`).

Concrete proof the config bug is real: the melted page `kogov_008/page_0544`
(val_0000), previously dumped as an image → counted absent, now transcribes the
full pipe-diameter price table as text (`D500mm … 26,358 … 208,362 …`).

## The decisive numbers (full 663-QA basis = the paper's `absent_robustness` basis)

Absent = gold answer not recoverable from the parser's page output.

| MinerU absent | L0 | L1 | L2 | L3 | L4 |
|---|---|---|---|---|---|
| table-OFF (paper) | 74.8 | **70.4** | 68.0 | 73.0 | 68.6 |
| **table-ON (re-run)** | 73.3 | **66.1** | 63.2 | 63.0 | 62.1 |
| Prod (paper, table-OFF) | 24.1 | 20.2 | 19.6 | 24.1 | 16.9 |

**MinerU − Prod gap:**

| | L1 | L4 |
|---|---|---|
| table-OFF | +50.2 | +51.7 |
| **table-ON** | **+45.9** | **+45.2** |

→ Turning tables on trims the overall gap by only ~4–6 pp. **The gap does not
close; it stays ~+46 pp.** The same-family-artifact objection is not what drives
it — the content is genuinely missing.

### Tabular questions — the paper's headline "dropped-table-cell" mechanism

| KoGov tabular (n=144) | MinerU | Prod | gap |
|---|---|---|---|
| table-OFF (paper) | **87.9%** | 13.9% | +74.0 pp |
| **table-ON (re-run)** | **41.7%** | 13.9% | **+27.8 pp** |

Tabular absent is **halved (87.9 → 41.7)**. This is the config effect and it is
large. **But +27.8 pp of tabular gap survives** — even reading tables, MinerU
loses ~3× more table answers than Prod.

### Per-domain (table-ON)

| domain | L1 | L4 |
|---|---|---|
| KoGov (Korean gov, n=527) | 74.0% | 71.7% |
| arxiv (English papers, n=136) | 35.3% | 25.0% |

MinerU does far better on clean English (consistent with its OHR-Bench 0.595).
The absent gap is a Korean-gov-document phenomenon, not general incompetence.

## Verdict

**Finding survives, with one number corrected.** Per the runbook's decision table
this is the "gap stays high" row, not the "gap collapses" row:

1. **Keep C1/C2.** The MinerU−Prod absent gap is real content loss (+46 pp,
   config-independent direction; survives to L4; confirmed on OHR by construction
   elsewhere). Not a same-family matching artifact.
2. **Correct the tabular figure.** The paper's **87.9% tabular absent is
   config-inflated**; the fair (tables-ON) number is **41.7%**, gap **+27.8 pp**
   not +74 pp. Re-caveat the "dropped-table-cell" claim: MinerU *does* transcribe
   tables, but still drops ~40% of table answers and 3× Prod's rate.
3. **State the config explicitly** in Setup/Limitations (honesty): the original
   MinerU baseline ran `table-config.enable:false`; a tables-ON re-run recovers
   ~half the tabular gap but leaves the overall gap ~+46 pp.

This is exactly the "A안" close (caveat + keep C1), but now **evidence-backed**:
we know the gap holds (so we're not softening a live finding), and we caught that
the 87.9% headline specifically needed correcting — which a blind caveat would
have missed.

## Caveats to report with the numbers

1. **Version fidelity.** The re-run env (magic-pdf 1.3.12, 2026 PDF-Extract-Kit
   models, transformers 4.49) is *not* guaranteed identical to the original
   `mineru_val` env. So the table-ON vs table-OFF delta is not a perfectly
   controlled A/B. The **parseability conclusion is robust to this** (tables now
   parse; the melted table is recovered), and the effect sizes (tabular −46 pp,
   gap persisting +46 pp) are far larger than any plausible version noise.
2. **Prod/PaddleOCR not re-run here.** Only MinerU was re-parsed on this machine;
   Prod's absent (20.2/16.9) and tabular (13.9) are the paper's fixed numbers.
   Prod predictions don't change, so the gap arithmetic is valid on the same
   663-QA / same-matcher basis.
3. **HTML tables.** MinerU emits `<table><td>`, not markdown pipes. Left raw the
   tags penalise cross-cell spans; the re-run strips tags to spaces for a fair
   match (single-cell values unaffected either way).

## Artifacts

- Predictions: `results/kogovdoc/mineru_val_tableon/predictions/` (294 `.md`)
- Official ladder: `output/diagnostics/absent_robustness.{json,md}` (MinerU
  table-ON, 294/294 pages)
- Re-run env: `~/mineru-venv`, `~/magic-pdf.json` (cuda, tables+formula ON)
