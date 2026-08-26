# RADP-DPO R2 executed configuration

The R2 training configuration was verified on 2026-08-27 against the original
`v4_train.log` retained on the training machine. This record distinguishes the
executed value from defaults and earlier draft prose.

## Verified run

- Paper milestone: `RADP-DPO-R2`
- Checkpoint directory: `output/checkpoints/radp_dpo_v4/final`
- Initial adapter: `output/checkpoints/radp_dpo/final` (R1)
- Preference data: `output/preference/dpo_v1_round2_pairs_bge.jsonl`
- Preference pairs loaded: 705
- DPO beta: **0.1**
- Learning rate: `5e-6`
- Epochs: 2
- Per-device batch size: 1
- Gradient accumulation: 8
- Logging interval: 5 steps
- Checkpoint interval: 50 steps

Sanitised executed command:

```bash
uv run python scripts/training/train_radp_dpo.py \
  --pairs output/preference/dpo_v1_round2_pairs_bge.jsonl \
  --init_adapter output/checkpoints/radp_dpo/final \
  --output_dir output/checkpoints/radp_dpo_v4 \
  --epochs 2 \
  --per_device_batch_size 1 \
  --grad_accum 8 \
  --beta 0.1 \
  --lr 5e-6 \
  --logging_steps 5 \
  --save_steps 50
```

## Source-log audit

- Start record: `2026-05-27 16:10:20,724`, reporting 705 pairs,
  `beta=0.10`, `lr=5e-06`, and 2 epochs.
- Final-adapter record: `2026-05-27 16:45:31,147`.
- Original log SHA-256:
  `772990e041de63e3fc72f5e4b452ff887dcecc651d1ac6534f81877f117c63e6`.

The full raw log contains machine-specific absolute paths and progress output;
this portable record preserves the executed scientific configuration and the
hash of the retained audit source.
