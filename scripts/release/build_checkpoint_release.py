"""Build and verify the portable RCPS/RADP checkpoint release.

The training machine stores PEFT adapter configs with machine-local base-model
paths.  This tool verifies every evaluated final adapter by its original
SHA-256, copies only inference-relevant weights, rewrites the base-model field
to a public model ID, and emits a self-auditing release manifest.

The raw checkpoint root is expected to contain the repository-relative
``output/checkpoints`` tree.  No model weights are committed to this Git tree;
the generated directory is the source for the public checkpoint release.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


RELEASE_REPO = "https://github.com/wigtn/RCPS-RADP-Adapters"
RELEASE_ASSET = (
    "https://github.com/wigtn/RCPS-RADP-Adapters/releases/download/"
    "v1.0.0/RCPS-RADP-Adapters-v1.tar.gz"
)
PROD_BASE = "Wigtn/Qwen3-VL-2B-WigtnOCR"
AUX_TRAIN_BASE = "Qwen/Qwen3-VL-2B-Instruct"

COMMON_DPO = {
    "framework": "transformers+peft",
    "precision": "bfloat16",
    "per_device_batch_size": 1,
    "gradient_accumulation": 8,
    "lr_scheduler": "cosine",
    "warmup_ratio": 0.05,
    "max_sequence_length": 3072,
    "image_max_pixels": 1_048_576,
    "seed": 42,
    "lora": {"rank": 8, "alpha": 32, "dropout": 0.05},
}


def _dpo_config(**values: Any) -> dict[str, Any]:
    return {**COMMON_DPO, **values}


VARIANTS: tuple[dict[str, Any], ...] = (
    {
        "id": "radp-aux-lambda-0.0",
        "paper_label": "RADP-aux lambda=0.0",
        "method": "parse-loss control",
        "source": "output/checkpoints/radp_b_full_lambda00/final",
        "release": "radp-aux/lambda-0.0",
        "training_base": AUX_TRAIN_BASE,
        "evaluation_base": PROD_BASE,
        "adapter_sha256": "202e25d4a28ad0c1aedf46d9acb028445aaaf0e58447ec55e4a20de4b398ae3c",
        "config_sha256": "c9ef7194cf873f092175e9db134767f0d0f5eb75cc33941d1a2dc2f0f82788e1",
        "aux_manifest_sha256": "c7a054ef8dfd0de2d32657f6f0670d550e38b2cc364c66cec2e3ca1d4c65246b",
    },
    {
        "id": "radp-aux-lambda-0.1",
        "paper_label": "RADP-aux lambda=0.1",
        "method": "hidden-state auxiliary loss",
        "source": "output/checkpoints/radp_b_full_lambda01/final",
        "release": "radp-aux/lambda-0.1",
        "training_base": AUX_TRAIN_BASE,
        "evaluation_base": PROD_BASE,
        "adapter_sha256": "6a02cb0fb66dfe5c070d9c85d2fb49e5c30d2e138d4d9a01002f4e9534ae0113",
        "config_sha256": "18b546362fa485a5272355d841c3eea544dc8c5d2e53fd78efec6c4616ee7efe",
        "aux_manifest_sha256": "269af832a3323a0a402368db9c4387f4ae6c1cb4ca4543aed7bc30116344a37e",
    },
    {
        "id": "radp-aux-lambda-0.3",
        "paper_label": "RADP-aux lambda=0.3",
        "method": "hidden-state auxiliary loss",
        "source": "output/checkpoints/radp_b_full_lambda03/final",
        "release": "radp-aux/lambda-0.3",
        "training_base": AUX_TRAIN_BASE,
        "evaluation_base": PROD_BASE,
        "adapter_sha256": "67e4350932b81c0e2603bb825525698acf1c0590bb6d6ade634b8db54bea09e6",
        "config_sha256": "bfeced659213eb06465fc2b9f9d967f907ac74f5adb5b49f3d1d04c9dec6590c",
        "aux_manifest_sha256": "cdb457dd66e165bc29eda1ac515d2b5dcd88871128404ee95345de2528174c51",
    },
    {
        "id": "radp-aux-lambda-0.5",
        "paper_label": "RADP-aux lambda=0.5",
        "method": "hidden-state auxiliary loss",
        "source": "output/checkpoints/radp_b_full_lambda05/final",
        "release": "radp-aux/lambda-0.5",
        "training_base": AUX_TRAIN_BASE,
        "evaluation_base": PROD_BASE,
        "adapter_sha256": "81516a898405ce4d8808062ece2ebe9996c62c77b921688808b4a7a30441c8ed",
        "config_sha256": "c0dbe10dba5b836c953a44fa3392bc171b080b7f00731baffc3c888cf567e0fe",
        "aux_manifest_sha256": "c7e8f6ab98a0aea015bf7bfe7bb10db1cd4f4f063f29ca8ff1ca6a377d72780e",
    },
    {
        "id": "radp-dpo-r1",
        "paper_label": "RADP-DPO-R1",
        "method": "retrieval-reward DPO, first round",
        "source": "output/checkpoints/radp_dpo/final",
        "release": "radp-dpo/r1",
        "training_base": PROD_BASE,
        "evaluation_base": PROD_BASE,
        "adapter_sha256": "6b5ee58936c99d4f668ae31355d0e6fef5623182fce64b5fa0c59fafc7dd26e7",
        "config_sha256": "cb51560415859ef3a779613670d70d743c2fc70e9fe57b931ffe80e9b08aaafd",
        "trainer_state": "output/checkpoints/radp_dpo/checkpoint-232/trainer_state.json",
        "trainer_state_sha256": "16dc8d42a36f121235d138bf960e73b4736ed7ae52d1b0006a110b58bdd8f373",
        "source_log_sha256": "37d96513b5e824ee4db3c26d77d2c1d83ef4013e98d7e9119e5248d47fd20040",
        "executed_config": _dpo_config(
            objective="DPO",
            preference_pairs=922,
            beta=0.1,
            learning_rate=1e-5,
            epochs=2,
            initial_adapter=None,
            preference_source="output/preference/v1_pairs.jsonl",
        ),
    },
    {
        "id": "radp-dpo-r2",
        "paper_label": "RADP-DPO-R2",
        "method": "retrieval-reward DPO, warm-started second round",
        "source": "output/checkpoints/radp_dpo_v4/final",
        "release": "radp-dpo/r2",
        "training_base": PROD_BASE,
        "evaluation_base": PROD_BASE,
        "adapter_sha256": "1a78cbb03c899069fed3818743bd67f6c56f85548a508d08be9a7d58e37b6356",
        "config_sha256": "12ac353ba1fad18c6e3f6de960fae76c077fc315a63beb62788a689f6973194e",
        "trainer_state": "output/checkpoints/radp_dpo_v4/checkpoint-178/trainer_state.json",
        "trainer_state_sha256": "c6c40c217542f837dfe95b3bf4f303fa14c76b473917235653dbeb3cd495090f",
        "source_log_sha256": "772990e041de63e3fc72f5e4b452ff887dcecc651d1ac6534f81877f117c63e6",
        "executed_config": _dpo_config(
            objective="DPO",
            preference_pairs=705,
            beta=0.1,
            learning_rate=5e-6,
            epochs=2,
            initial_adapter="radp-dpo-r1",
            preference_source="output/preference/dpo_v1_round2_pairs_bge.jsonl",
            logging_steps=5,
            save_steps=50,
        ),
    },
    {
        "id": "radp-dpo-r3",
        "paper_label": "RADP-DPO-R3",
        "method": "retrieval-reward DPO with expanded candidates and hard negatives",
        "source": "output/checkpoints/radp_dpo_v5_hardneg/final",
        "release": "radp-dpo/r3",
        "training_base": PROD_BASE,
        "evaluation_base": PROD_BASE,
        "adapter_sha256": "ec798e0e889ea61db9865e51ccc9e4c5427013dc5d64d4a8b0db5a1ffc311c9c",
        "config_sha256": "28d6fc5fcddf0779326bb82ca893221687abcad67fe00523a2f1d4cafb8eb37b",
        "trainer_state": "output/checkpoints/radp_dpo_v5_hardneg/checkpoint-486/trainer_state.json",
        "trainer_state_sha256": "3defba0fbebba87d6a1e6b8763e69c98c067f56375bd1f3c6165f7f342b26c80",
        "source_log_sha256": "ee43b44ed0dc27bb4e106d5ff116b3961ded7e38735138093945528e072e8958",
        "executed_config": _dpo_config(
            objective="DPO",
            preference_pairs=1940,
            beta=0.05,
            learning_rate=1e-5,
            epochs=2,
            initial_adapter=None,
            preference_source="output/preference/v1_hardneg_pairs.jsonl",
            candidate_pool_size=16,
            hard_negatives=True,
        ),
    },
    {
        "id": "radp-distill",
        "paper_label": "RADP-Distill",
        "method": "edit-distance preference control",
        "source": "output/checkpoints/arm_b_textned/final",
        "release": "radp-distill",
        "training_base": PROD_BASE,
        "evaluation_base": PROD_BASE,
        "adapter_sha256": "2a00c8d7cf9a79fc14df1ce0bb64b5925bd7f391aacf7fe262f2c3926568c377",
        "config_sha256": "f2e81a947eaf97e1bd3efc943fa76047c3cf80ebbd54316b291b60dfaf6e7b9c",
        "trainer_state": "output/checkpoints/arm_b_textned/checkpoint-624/trainer_state.json",
        "trainer_state_sha256": "9e6560249670a4d529c0a54005c34fcaecc5288a464b8265ecfc86e019990ac4",
        "source_log_sha256": "eccda7c35518bee41d243fcf719ac5779b7f43d89d781a7ba6a73526a5df71fc",
        "executed_config": _dpo_config(
            objective="DPO with edit-distance-selected pairs",
            preference_pairs=2492,
            beta=0.1,
            learning_rate=1e-5,
            epochs=2,
            initial_adapter=None,
            preference_source="output/preference/arm_b_textned_pairs.jsonl",
        ),
    },
    {
        "id": "radp-simpo",
        "paper_label": "RADP-SimPO",
        "method": "reference-free SimPO control",
        "source": "output/checkpoints/radp_simpo/final",
        "release": "radp-simpo",
        "training_base": PROD_BASE,
        "evaluation_base": PROD_BASE,
        "adapter_sha256": "757325ec00d8057e6452c8306281f91e64a186c4d16372700160f2d341a45db7",
        "config_sha256": "c1eddbdc00f42ce6428e0057653fc2c3cdcf5cb67ee5b46aa879e9ab72db99b6",
        "trainer_state": "output/checkpoints/radp_simpo/checkpoint-232/trainer_state.json",
        "trainer_state_sha256": "dcf0085c24886ed9598cc9a34e2e45f1e969c377f12200acdfad51c2b0bd164e",
        "source_log_sha256": "ad671b027c9c307357cb1402f67280613583ba5683500d9bb8b3bb3dcf91f4ce",
        "executed_config": _dpo_config(
            objective="SimPO",
            preference_pairs=922,
            beta=2.0,
            gamma=1.0,
            learning_rate=1e-6,
            epochs=2,
            preference_source="output/preference/v1_pairs.jsonl",
        ),
    },
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _verify_hash(path: Path, expected: str) -> None:
    observed = _sha256(path)
    if observed != expected:
        raise ValueError(f"SHA-256 mismatch for {path}: {observed} != {expected}")


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _model_card() -> str:
    return f"""# RCPS/RADP parser-training adapters

This release contains the nine final LoRA adapters evaluated in *Retrieval-Conditional
Parsing Score (RCPS): Choosing Document Parsers by Retrieval, Not by Appearance*.
It includes the RADP-aux lambda sweep, RADP-DPO R1--R3,
RADP-Distill, and the SimPO control. These checkpoints support the paper's
secondary negative-result study; they are not a new production recommendation.

The main evaluation base is [`{PROD_BASE}`](https://huggingface.co/{PROD_BASE}).
RADP-DPO, RADP-Distill, and SimPO were trained from that base. RADP-aux was
trained from [`{AUX_TRAIN_BASE}`](https://huggingface.co/{AUX_TRAIN_BASE}) and
then evaluated in the paper by applying its adapter to the Prod base. The
per-variant `adapter_config.json` records the training base, while `manifest.json`
records both training and evaluation bases.

## Variants

| Paper label | Subfolder |
|---|---|
| RADP-aux lambda=0.0 | `radp-aux/lambda-0.0` |
| RADP-aux lambda=0.1 | `radp-aux/lambda-0.1` |
| RADP-aux lambda=0.3 | `radp-aux/lambda-0.3` |
| RADP-aux lambda=0.5 | `radp-aux/lambda-0.5` |
| RADP-DPO-R1 | `radp-dpo/r1` |
| RADP-DPO-R2 | `radp-dpo/r2` |
| RADP-DPO-R3 | `radp-dpo/r3` |
| RADP-Distill | `radp-distill` |
| RADP-SimPO | `radp-simpo` |

## Loading an evaluated adapter

Download and extract the audited release first:

```bash
curl -L -o RCPS-RADP-Adapters-v1.tar.gz "{RELEASE_ASSET}"
tar -xzf RCPS-RADP-Adapters-v1.tar.gz -C /path/to/RCPS-RADP-Adapters
```

```python
from peft import PeftModel
from transformers import Qwen3VLForConditionalGeneration

base = Qwen3VLForConditionalGeneration.from_pretrained(
    "{PROD_BASE}", torch_dtype="auto", device_map="auto"
)
model = PeftModel.from_pretrained(
    base,
    "/path/to/RCPS-RADP-Adapters/radp-dpo/r2",
)
```

`manifest.json` gives original and release hashes, executed hyperparameters,
source-log hashes, and the source repository paths for every variant. Structured
`trainer_state.json` files are included where the Transformers trainer produced
them. Optimizer states, training images, and preference-pair text are excluded.
The repository release builder verifies the original weights before staging.
"""


def build_release(source_root: Path, output_root: Path) -> dict[str, Any]:
    if output_root.exists() and any(output_root.iterdir()):
        raise ValueError(f"release output must be empty: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)

    released: list[dict[str, Any]] = []
    for variant in VARIANTS:
        source_dir = source_root / variant["source"]
        source_adapter = source_dir / "adapter_model.safetensors"
        source_config = source_dir / "adapter_config.json"
        _verify_hash(source_adapter, variant["adapter_sha256"])
        _verify_hash(source_config, variant["config_sha256"])

        destination = output_root / variant["release"]
        destination.mkdir(parents=True, exist_ok=True)
        release_adapter = destination / "adapter_model.safetensors"
        shutil.copy2(source_adapter, release_adapter)

        config = json.loads(source_config.read_text(encoding="utf-8"))
        config["base_model_name_or_path"] = variant["training_base"]
        release_config = destination / "adapter_config.json"
        _write_json(release_config, config)

        if "aux_manifest_sha256" in variant:
            source_manifest = source_dir / "radp_b_manifest.json"
            _verify_hash(source_manifest, variant["aux_manifest_sha256"])
            executed_config = json.loads(source_manifest.read_text(encoding="utf-8"))
            executed_config["training_base_model"] = variant["training_base"]
            executed_config["evaluation_base_model"] = variant["evaluation_base"]
        else:
            executed_config = dict(variant["executed_config"])
            executed_config["training_base_model"] = variant["training_base"]
            executed_config["evaluation_base_model"] = variant["evaluation_base"]
        executed_path = destination / "executed_config.json"
        _write_json(executed_path, executed_config)

        files = {
            "adapter_model.safetensors": {
                "sha256": _sha256(release_adapter),
                "bytes": release_adapter.stat().st_size,
            },
            "adapter_config.json": {
                "sha256": _sha256(release_config),
                "bytes": release_config.stat().st_size,
            },
            "executed_config.json": {
                "sha256": _sha256(executed_path),
                "bytes": executed_path.stat().st_size,
            },
        }

        if "trainer_state" in variant:
            source_state = source_root / variant["trainer_state"]
            _verify_hash(source_state, variant["trainer_state_sha256"])
            release_state = destination / "trainer_state.json"
            shutil.copy2(source_state, release_state)
            files["trainer_state.json"] = {
                "sha256": _sha256(release_state),
                "bytes": release_state.stat().st_size,
            }

        released.append(
            {
                "id": variant["id"],
                "paper_label": variant["paper_label"],
                "method": variant["method"],
                "subfolder": variant["release"],
                "training_base_model": variant["training_base"],
                "evaluation_base_model": variant["evaluation_base"],
                "source_checkpoint": variant["source"],
                "source_adapter_sha256": variant["adapter_sha256"],
                "source_adapter_config_sha256": variant["config_sha256"],
                "source_log_sha256": variant.get("source_log_sha256"),
                "files": files,
            }
        )

    manifest = {
        "schema_version": 1,
        "status": "portable_checkpoint_release",
        "release_repository": RELEASE_REPO,
        "release_asset": RELEASE_ASSET,
        "num_variants": len(released),
        "scope": {
            "includes": "final PEFT adapters, portable configs, executed configs, and available trainer states",
            "excludes": "optimizer states, training images, preference-pair text, tokenizers duplicated from public bases, and RADP-aux projection heads unused for parser inference",
        },
        "variants": released,
    }
    _write_json(output_root / "manifest.json", manifest)
    (output_root / "README.md").write_text(_model_card(), encoding="utf-8")
    validate_release(output_root)
    return manifest


def validate_release(output_root: Path) -> dict[str, Any]:
    manifest_path = output_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "portable_checkpoint_release":
        raise ValueError("unsupported checkpoint release status")
    if manifest.get("num_variants") != len(VARIANTS):
        raise ValueError("checkpoint release has an unexpected variant count")

    seen: set[str] = set()
    for variant in manifest["variants"]:
        variant_id = str(variant["id"])
        if variant_id in seen:
            raise ValueError(f"duplicate release variant: {variant_id}")
        seen.add(variant_id)
        directory = output_root / variant["subfolder"]
        for name, expected in variant["files"].items():
            path = directory / name
            _verify_hash(path, expected["sha256"])
            if path.stat().st_size != expected["bytes"]:
                raise ValueError(f"size mismatch for {path}")

    text_files = [output_root / "README.md", manifest_path]
    text_files.extend(output_root.glob("**/*.json"))
    for path in text_files:
        text = path.read_text(encoding="utf-8")
        if "/mnt/" in text or "/home/" in text:
            raise ValueError(f"machine-local path leaked into release: {path}")
    return {"num_variants": len(seen), "status": "ok"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--check", type=Path)
    args = parser.parse_args()

    if args.check is not None:
        result = validate_release(args.check)
        print(f"OK: {args.check} ({result['num_variants']} variants)")
        return 0
    if args.source is None or args.out is None:
        parser.error("provide --source and --out, or --check")
    manifest = build_release(args.source, args.out)
    print(f"wrote {args.out} ({manifest['num_variants']} variants)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
