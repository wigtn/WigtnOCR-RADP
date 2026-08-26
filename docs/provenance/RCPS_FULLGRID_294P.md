# RCPS 294-page full-grid provenance

Verified on 2026-08-27. This run uses the selection frame only: 294 pages
(229 Korean-government and 65 arXiv), 663 Q–A, three retrievers, and
`k = {1, 5, 10}`. It does not mix in the 242-page training-analysis fold.

## Evaluated systems

- Parser-native: Qwen3-VL-30B teacher, Prod, Qwen3-VL-2B base, MinerU-off,
  MinerU-on, and PaddleOCR.
- Prod chunkers: `md_h3`, `parser_native`, `lumberchunker`, and `fixed500`.
- Marker is excluded because only a 38-page output is available.

The exporter loads the three embedders once and evaluates all nine unique
systems in one process. It writes aligned per-QA MRR vectors under both the
paper's format-normalised relevance rule and a case-sensitive raw-substring
control. Input file and parser-directory tree hashes are embedded in the JSON.

## Runtime and command

- GPU: NVIDIA RTX PRO 6000 Blackwell Server Edition
- NVIDIA driver: 575.64.03 (open kernel module)
- Python: 3.13.5
- PyTorch: 2.8.0+cu128
- sentence-transformers: 5.5.0
- transformers: 5.8.1

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 CUDA_VISIBLE_DEVICES=0 \
  .venv/bin/python scripts/analysis/export_fullgrid_perqa.py \
  --v1-root /path/to/kogovdoc-parser-outputs \
  --device cuda:0 \
  --out output/results/fullgrid_perqa_294p.json
```

For the audited run, `--v1-root` pointed to the existing directory containing
the five original full-page parser outputs; MinerU-on used the repository-local
`results/kogovdoc/mineru_val_tableon/predictions` default. The placeholder above
keeps the public command portable and avoids publishing a host-specific path.

On the execution host, repeated short-lived CUDA processes sometimes returned
`cuInit(0)=3`. Kernel logs identified an NVIDIA host-memory allocation failure
while registering the non-replayable-fault shadow buffer, despite idle VRAM.
No driver, CUDA, kernel, module, or persistence setting was changed. The audited
run used the existing `.venv/bin/python` directly, passed a CUDA allocation
preflight, and kept one process alive through all nine systems. Both GPUs were
idle again after normal process exit.

The two bootstrap files are CPU-only and can be regenerated from the exported
JSON. The exact system mappings and pairwise checks are recorded in
`rank_stability_parser_rcps_294p.json` and
`rank_stability_chunker_rcps_294p.json`; both use 1,000 iterations, a subset of
500 Q--A, sampling without replacement, and seed 42. A local rerun reproduced
every rank, ordering rate, and reported decimal. Python 3.9 and 3.13 differ only
in unreported floating-point tails (below $10^{-15}$).

## Results

| System | Normalised RCPS | Raw RCPS | Difference |
|---|---:|---:|---:|
| Qwen3-VL-30B teacher / parser-native | 0.584401 | 0.558717 | +0.025684 |
| Prod / parser-native | 0.582573 | 0.558649 | +0.023924 |
| Qwen3-VL-2B base / parser-native | 0.532109 | 0.503075 | +0.029035 |
| MinerU-off / parser-native | 0.212040 | 0.183491 | +0.028550 |
| MinerU-on / parser-native | 0.137508 | 0.096603 | +0.040905 |
| PaddleOCR / parser-native | 0.139741 | 0.115173 | +0.024568 |
| Prod / md-h3 | 0.592874 | 0.564093 | +0.028781 |
| Prod / LumberChunker | 0.557051 | 0.530151 | +0.026900 |
| Prod / fixed-500 | 0.535376 | 0.508733 | +0.026643 |

Raw matching lowers RCPS by 0.024–0.041 and does not reorder either the
six-parser pool or the four-chunker pool. The response-period provisional
description “0.02–0.03” is therefore too narrow because MinerU-on shifts by
0.041.

For the fixed-seed probe bootstrap, each of 1,000 iterations samples 500 of 663
Q–A without replacement:

- Six-parser mean Kendall tau-a is 0.902; the complete order is unchanged in
  39.4% of draws. The variation is confined to the near-tied teacher–Prod and
  PaddleOCR–MinerU-on pairs. Prod remains above Base, MinerU-off, PaddleOCR,
  and MinerU-on in 100% of draws.
- The complete four-chunker order is unchanged in 96.1% of draws (mean
  Kendall tau-a 0.987). `md_h3` remains above `parser_native` in 96.5%,
  `parser_native` above LumberChunker in 99.9%, and LumberChunker above
  `fixed500` in 99.7%.

## Public artifact hashes

The retrieved execution artifact had SHA-256
`6d534f6e0b4bd4885a4e2e8d2e2fe6baeaecd0c9c9bfc1d2fcfe0ac5ea23428e`.
The public copy removes only machine-specific parser-directory paths; its
scientific arrays, input tree hashes, runtime metadata, and summaries are
unchanged.

- `output/results/fullgrid_perqa_294p.json`:
  `f99b684a7b3219ac836aca2edabf5523c366b6f37ae639a2e08058cdf8c15fb0`
- `output/results/rank_stability_parser_rcps_294p.json`:
  `12304f959805a87b686ad6b15d5f3ece7c24ff9673a5df566d597826a52523f2`
- `output/results/rank_stability_chunker_rcps_294p.json`:
  `1023a729a99ff9c61c70d97cb70c0445531896397ac532ce332faf77faf853b8`
