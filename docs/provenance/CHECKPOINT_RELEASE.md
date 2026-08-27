# RCPS/RADP checkpoint release

The camera-ready checkpoint release is published at
[`wigtn/RCPS-RADP-Adapters`](https://github.com/wigtn/RCPS-RADP-Adapters),
with the audited weights in the
[`v1.0.0` release asset](https://github.com/wigtn/RCPS-RADP-Adapters/releases/download/v1.0.0/RCPS-RADP-Adapters-v1.tar.gz).
It contains the nine final PEFT adapters evaluated in the paper:

- RADP-aux with lambda 0.0, 0.1, 0.3, and 0.5;
- RADP-DPO R1, R2, and R3;
- RADP-Distill; and
- the RADP-SimPO control.

The tracked [`checkpoint_release_manifest.json`](checkpoint_release_manifest.json)
records, for every variant, its paper label, source checkpoint, original adapter
and config hashes, portable release hashes, executed configuration, source-log
hash where available, training base, and evaluation base. The original adapter
weights were recovered from the training machine and verified before staging.

## Base-model lineage

RADP-DPO, RADP-Distill, and SimPO were trained from and evaluated on the public
Prod base, [`Wigtn/Qwen3-VL-2B-WigtnOCR`](https://huggingface.co/Wigtn/Qwen3-VL-2B-WigtnOCR).
The RADP-aux sweep was trained from
[`Qwen/Qwen3-VL-2B-Instruct`](https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct)
and evaluated by applying each resulting adapter to Prod. The camera-ready
appendix states this executed cross-base setup explicitly.

## Deterministic staging and validation

Given a private raw checkpoint root that contains `output/checkpoints`, build a
portable release directory with:

```bash
python scripts/release/build_checkpoint_release.py \
  --source /path/to/raw-checkpoint-root \
  --out /path/to/empty-release-directory
```

The builder rejects any weight, adapter config, or trainer state whose SHA-256
does not match the audited source. It rewrites machine-local base-model paths to
public Hugging Face IDs and rejects machine-local paths in the resulting text
metadata. Validate a staged or downloaded snapshot with:

```bash
python scripts/release/build_checkpoint_release.py \
  --check /path/to/release-directory
```

The release intentionally omits optimizer states, training images,
preference-pair text, tokenizers duplicated from the public bases, and RADP-aux
projection heads that are unused for parser inference. Structured trainer
states are included for R1--R3, Distill, and SimPO.

## Public-download verification

The published tarball is 358,728,348 bytes with SHA-256
`22b4a0d4f5560f4d7c31633a1c885bbe3568a2bef841bfd94bf2407c339f08c6`.
After publication, it was downloaded without repository credentials, extracted
to a new directory, and checked against both the tracked manifest and the
builder's nine-variant inventory. A clean checkout can repeat the complete
CPU-only artifact gate with:

```bash
python3 scripts/release/verify_camera_ready_artifacts.py \
  --checkpoint-dir /path/to/extracted/RCPS-RADP-Adapters
```
