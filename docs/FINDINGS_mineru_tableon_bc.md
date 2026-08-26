# MinerU table-ON Boundary Clarity: audited camera-ready artifact

> Final audit: 2026-08-27 KST. MinerU-on BC is **0.713123** over all
> **609/609** within-page boundaries. The four-parser BC--RCPS Pearson
> correlation is **r = -0.7443**. These values support the camera-ready
> rounded values **0.713** and **-0.74**.

This artifact fills the previously missing MinerU-on BC cell. The current
camera-ready paper, figure, and READMEs already use MinerU-on--rather than the
separate MinerU-off diagnostic--in the four-parser deployment correlation.

## 1. Scope and result

The run evaluates the 294-page table-enabled MinerU output with the same
Boundary Clarity definition, language model, parser-native chunker, and token
limit used for the stored baseline audit:

```text
BC(q | d) = ppl(q | d) / ppl(q) = exp(NLL(q | d) - NLL(q))
```

Only adjacent chunks on the same page form a boundary. The corpus score is the
unweighted mean across every valid boundary; it is not a mean of page means and
is not clamped to `[0, 1]`.

| Quantity | Audited value |
|---|---:|
| Pages | 294 |
| Parser-native chunks | 903 |
| Boundaries attempted / valid | 609 / 609 |
| Skipped boundaries | 0 |
| Mean BC | **0.7131232508982984** |
| Median BC | 0.7268471243986776 |
| Sample standard deviation | 0.25583351119563696 |
| Min / max | 0.05230371461529283 / 1.6889491022575358 |

The identity `609 = 903 - 294` confirms that every page yields at least one
chunk and every within-page adjacent boundary was evaluated.

## 2. Input and execution gates

| Gate | Expected | Observed |
|---|---:|---:|
| Prediction Markdown files | 294 | 294 |
| `ParserNativeChunker(min_chars=30)` chunks | 903 | 903 |
| Pages with at least one chunk | 294 | 294 |

- Prediction manifest SHA-256:
  `1fd8559a1efc9653d956d012b453a236ffbeb7107de385d5b7875a3886867803`
- Boundary manifest SHA-256:
  `077882792aa4b94df6a202168a038e822e6ba8694c6136c92bee21d1837a5d15`
- Scoring fingerprint:
  `9fe594ef2ff0f34609c27ed2f93c10f48249646c82023fd02e216d7784de712b`
- Final artifact SHA-256:
  `42876dd617fdcdc26518f7e5fc4702582b9b9f8796aea359f365df43e177bab4`

The page IDs in this run are sorted prediction filename stems. The RCPS grid
uses `val_NNNN` IDs from the unavailable portable page map. This does not alter
BC: the metric uses only adjacency within each of the same 294 Markdown files,
and the 903-chunk gate binds the BC run to the matching RCPS chunking.

## 3. Clean rerun and provenance

The original WSL artifact recorded a dirty checkout and reused an
unfingerprinted checkpoint. It produced BC `0.7132110997071613`. The final
artifact replaces it with a fresh run that:

- used no checkpoint (`enabled=false`, `resumed_records=0`);
- recorded the exact runner SHA-256 and model revision;
- ran from a checkout with no tracked modifications;
- hashed every input file and every scored boundary; and
- wrote all 609 boundary results without a skip.

The clean rerun produced `0.7131232508982984`, only `0.00008785` below the WSL
value. This is a numerical repeat, not a statistical equivalence claim; no
paired uncertainty estimate was defined for the two hardware environments.

Execution environment:

| Field | Value |
|---|---|
| Executed UTC | 2026-08-26T19:14:36Z |
| GPU | NVIDIA RTX PRO 6000 Blackwell Server Edition |
| Python | 3.13.5 |
| PyTorch / CUDA | 2.8.0+cu128 / 12.8 |
| Transformers | 5.8.1 |
| Model | `Qwen/Qwen3-VL-2B-Instruct` |
| Model revision | `89644892e4d85e24eaac8bacfd4f463576704203` |
| Runner SHA-256 | `a4a4945c5e63da076d1bc8be513baa6e80baf88780735aeda5f18d13823173c8` |

`provenance.git_dirty` remains `true` because the execution checkout contained
an unrelated untracked `configs/data/` directory. The more specific
`git_tracked_dirty=false` records the relevant fact: tracked package and input
files were unchanged. The executed runner lived in `/tmp`; its canonical public
source ID and exact SHA are recorded in the JSON.

## 4. Reproduction commands

The GPU step writes the scientific result without comparison files. This keeps
the expensive measurement independent of optional local reporting artifacts:

```bash
WIGTNOCR_RADP_REPO_ROOT=/path/to/WigtnOCR-RADP \
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 CUDA_VISIBLE_DEVICES=0 \
.venv/bin/python scripts/evaluation/compute_parser_bc.py \
  --parser-dir results/kogovdoc/mineru_val_tableon/predictions \
  --label MinerU-on \
  --model Qwen/Qwen3-VL-2B-Instruct \
  --device cuda --max-tokens 1024 \
  --expected-pages 294 --expected-chunks 903 \
  --no-checkpoint --no-references \
  --out /tmp/moc_bc_mineru_tableon_core.json
```

The CPU-only augmentation step attaches source hashes, comparisons, and the
descriptive correlation:

```bash
.venv/bin/python scripts/evaluation/compute_parser_bc.py \
  --augment-existing /tmp/moc_bc_mineru_tableon_core.json \
  --out output/baselines/moc_bc_mineru_tableon.json
```

For future resumed runs, the script now requires a sidecar fingerprint that
binds cached scores to the input manifest, boundary texts, model revision,
chunker settings, metric definition, and runner/scorer source hashes. It refuses
legacy or mismatched checkpoints.

## 5. Camera-ready comparison

| Parser/configuration | BC | RCPS | Hit@1 |
|---|---:|---:|---:|
| Marker (38 pages; partial) | 0.7168 | 0.073 | 0.068 |
| MinerU-off (submitted diagnostic) | 0.7161 | 0.212 | 0.197 |
| **MinerU-on (audited)** | **0.7131** | **0.1365** | **0.1227** |
| Qwen3-VL-30B teacher | 0.6232 | 0.5844 | 0.5445 |
| Prod / WigtnOCR-2B | 0.6100 | 0.5826 | 0.5485 |
| Qwen3-VL-2B base | 0.5199 | 0.5321 | 0.4997 |

- MinerU-on minus MinerU-off BC: `-0.00297675`. The two configurations also
  differ in software and retrieval environments, so this is not a causal
  table-recognition ablation.
- MinerU-on minus Prod BC: `+0.10312325`.
- Prod Hit@1 is `4.47x` as high as MinerU-on (`0.5485` versus `0.1227`).

MinerU-on therefore has the highest **measured** BC among the four complete
294-page outputs with defined BC, but the lowest RCPS among all five complete
outputs. PaddleOCR is a complete output but has no measured BC in the stored
source audit.

## 6. Descriptive four-parser correlation

The four points are Qwen3-VL-30B, Prod, Qwen3-VL-2B base, and MinerU-on. Marker
is partial and PaddleOCR has no measured BC. MinerU-off is a separately scoped
configuration and is not added as another independent parser.

| Pair | Pearson r | p | Spearman rho | p |
|---|---:|---:|---:|---:|
| BC vs RCPS | **-0.7443** | 0.2557 | -0.20 | 0.80 |
| BC vs Hit@1 | -0.7481 | 0.2519 | -0.40 | 0.60 |

At `n=4`, these coefficients describe this candidate pool only. The p-values
are recorded for audit completeness and are not evidence of a population-level
relationship. The paper therefore retains `r=-0.74` and its descriptive
small-sample qualification.

## 7. Remaining caveats

1. The older reference BC file records its values to four decimals and does not
   contain a model revision or full environment fingerprint. Differences from
   MinerU-off and Prod inherit that limitation.
2. MinerU-on and MinerU-off differ in more than table recognition. Their score
   difference must not be interpreted causally.
3. BC is relative to the Qwen3-VL-2B-Instruct text-scoring path. The absolute
   value is not a parser-only property.
4. The correlation contains only four complete outputs with measurable BC and
   is dominated by the distant MinerU-on retrieval point.

Related records: `FINDINGS_mineru_tableon_rerun.md`,
`FINDINGS_tableon_rcps_and_prod_absent.md`, and
`FINDINGS_tableon_local_verification.md`.
