# MinerU tables-off parser outputs

This directory contains the 294 Markdown outputs used by the submitted-output
MinerU baseline. Table recognition was disabled in this historical run. The
camera-ready deployment comparison uses the separately released tables-on
outputs in `../mineru_val_tableon/`; the two runs also differ in software and
retrieval environment, so their difference is not interpreted as a controlled
table-recognition ablation.

The corresponding aggregate is the `MinerU` / `mineru_val` row in
`output/baselines/grid_v1_parser_native.json`: 294 pages, 1,050 chunks, RCPS
0.212040, and Hit@1 0.197084.

Run the deterministic release audit from the repository root:

```bash
python scripts/analysis/audit_mineru_output_release.py \
  --check output/results/mineru_output_release_audit.json
```

The audit requires all 294 page filenames to match the tables-on release,
checks the 229 KoGov / 65 arXiv composition and aggregate linkage, and binds the
prediction files to a canonical SHA-256 tree digest.
