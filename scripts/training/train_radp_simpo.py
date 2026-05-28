"""SimPO training driver — Simple Preference Optimization on parser outputs.

Reuses the DPO data pipeline (preference pairs, collator) but with SimPO loss:
no reference model, length-normalized log-prob, explicit γ margin.

Usage:
    CUDA_VISIBLE_DEVICES=1 uv run python scripts/training/train_radp_simpo.py \
        --pairs output/preference/v1_pairs.jsonl \
        --output_dir output/checkpoints/radp_simpo \
        --beta 2.0 --gamma 1.0 --lr 1e-6 --epochs 2
"""

from __future__ import annotations

import os

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

import argparse  # noqa: E402
import logging  # noqa: E402
from pathlib import Path  # noqa: E402

import torch  # noqa: E402
from peft import LoraConfig, get_peft_model  # noqa: E402
from transformers import AutoProcessor, Qwen3VLForConditionalGeneration, TrainingArguments  # noqa: E402

from wigtnocr_radp.training.dpo_data import DPOPreferenceDataset, Qwen3VLDPOCollator  # noqa: E402
from wigtnocr_radp.training.simpo_trainer import RadpSimpoTrainer  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("train_radp_simpo")

V1_MERGED = Path("/mnt/data1/work/wigtnOCR-v1/output/wigtnocr-2b-merged")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", type=Path, default=V1_MERGED,
                    help="merged v1 model — SimPO is reference-free, no toggle needed")
    ap.add_argument("--pairs", type=Path, default=Path("output/preference/v1_pairs.jsonl"))
    ap.add_argument("--output_dir", type=Path, default=Path("output/checkpoints/radp_simpo"))
    ap.add_argument("--beta", type=float, default=2.0,
                    help="SimPO β (per-token reward scale, SimPO paper default ≈ 2.0)")
    ap.add_argument("--gamma", type=float, default=1.0,
                    help="SimPO γ target margin (paper sweep 0.3-1.6)")
    ap.add_argument("--lr", type=float, default=1e-6,
                    help="SimPO LR (paper default ≈ 5e-7, ~10x lower than DPO due to β=2)")
    ap.add_argument("--epochs", type=float, default=2.0)
    ap.add_argument("--per_device_batch_size", type=int, default=1)
    ap.add_argument("--grad_accum", type=int, default=8)
    ap.add_argument("--lora_r", type=int, default=8)
    ap.add_argument("--lora_alpha", type=int, default=32)
    ap.add_argument("--max_seq_length", type=int, default=3072)
    ap.add_argument("--image_max_pixels", type=int, default=1_048_576)
    ap.add_argument("--save_steps", type=int, default=200)
    ap.add_argument("--logging_steps", type=int, default=10)
    ap.add_argument("--warmup_ratio", type=float, default=0.05)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA not available")

    logger.info("loading base (merged v1): %s", args.base)
    model = Qwen3VLForConditionalGeneration.from_pretrained(
        args.base, dtype=torch.bfloat16, attn_implementation="sdpa", device_map="cuda"
    )
    processor = AutoProcessor.from_pretrained(args.base)
    processor.tokenizer.padding_side = "right"

    # Fresh LoRA — SimPO doesn't need π_ref/π_init alignment trick.
    lora_cfg = LoraConfig(
        r=args.lora_r, lora_alpha=args.lora_alpha, lora_dropout=0.05,
        bias="none", task_type="CAUSAL_LM",
        target_modules="all-linear",
    )
    model = get_peft_model(model, lora_cfg)
    model.gradient_checkpointing_enable()
    model.enable_input_require_grads()
    model.print_trainable_parameters()

    dataset = DPOPreferenceDataset.from_jsonl(args.pairs)
    collator = Qwen3VLDPOCollator(processor,
                                   max_seq_length=args.max_seq_length,
                                   image_max_pixels=args.image_max_pixels)

    training_args = TrainingArguments(
        output_dir=str(args.output_dir),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.per_device_batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        warmup_ratio=args.warmup_ratio,
        bf16=True,
        gradient_checkpointing=True,
        logging_steps=args.logging_steps,
        save_steps=args.save_steps,
        save_total_limit=2,
        report_to=["none"],
        remove_unused_columns=False,
        seed=args.seed,
        dataloader_num_workers=0,
        dataloader_pin_memory=False,
    )

    trainer = RadpSimpoTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        data_collator=collator,
        beta=args.beta,
        gamma=args.gamma,
    )

    logger.info("starting SimPO training: %d pairs, β=%.2f, γ=%.2f, lr=%.0e, epochs=%g",
                len(dataset), args.beta, args.gamma, args.lr, args.epochs)
    trainer.train()

    final_dir = args.output_dir / "final"
    final_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(final_dir))
    processor.save_pretrained(str(final_dir))
    logger.info("saved final adapter to %s", final_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
