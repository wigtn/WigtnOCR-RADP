"""Train RADP-B: Qwen3-VL parser + chunk-boundary contrastive auxiliary loss.

    L_total = L_parse + λ · L_contrast

L_parse is the standard VLM parsing cross-entropy (image -> markdown); L_contrast
is an InfoNCE term that pulls the parser's pooled hidden state toward the frozen
BGE-M3 embedding of the answer chunk. See docs/RADP_RESEARCH_PROPOSAL.md §4.1.

Stack: transformers + peft (HF-native). ms-swift was dropped on 2026-05-20 — the
pinned env (transformers 5.8, cu128) is incompatible with ms-swift 4.2.

Usage:
    # default: GPU 1 (GPU 0 is usually occupied)
    CUDA_VISIBLE_DEVICES=1 uv run python scripts/training/train_radp_b.py

    # fast end-to-end pipeline check (4 steps, no save/eval)
    CUDA_VISIBLE_DEVICES=1 uv run python scripts/training/train_radp_b.py --smoke
"""

from __future__ import annotations

import os

# Pin to GPU 1 by default (GPU 0 typically hosts other jobs). Must run before
# torch initialises CUDA. Override by exporting CUDA_VISIBLE_DEVICES yourself.
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "1")
# Base model, processor and BGE cache are all local — stay offline to avoid
# network round-trips (and the ~/.cache permission noise they trigger).
os.environ.setdefault("HF_HUB_OFFLINE", "1")
# Reduce fragmentation from the variable sequence lengths across batches.
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

import argparse  # noqa: E402
import json  # noqa: E402
import logging  # noqa: E402
import subprocess  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Any  # noqa: E402

import torch  # noqa: E402
from peft import LoraConfig, get_peft_model  # noqa: E402
from transformers import (  # noqa: E402
    AutoProcessor,
    Qwen3VLForConditionalGeneration,
    TrainerCallback,
    TrainingArguments,
)

from wigtnocr_radp.training.contrastive import (  # noqa: E402
    BgeM3EmbeddingCache,
    ContrastiveProjectionHead,
    RadpBLoss,
    SamplingStrategy,
)
from wigtnocr_radp.training.data import (  # noqa: E402
    Qwen3VLContrastiveCollator,
    RadpBDataset,
)
from wigtnocr_radp.training.trainer import RadpBTrainer, attach_radp_loss  # noqa: E402
from wigtnocr_radp.utils.config import load_yaml_config, resolve_config_path  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("train_radp_b")


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True
        ).strip()
    except Exception:  # noqa: BLE001
        return "unknown"


class ProjectionHeadSaveCallback(TrainerCallback):
    """Persist the projection head alongside each PEFT adapter checkpoint."""

    def __init__(self, radp_loss: RadpBLoss) -> None:
        self.radp_loss = radp_loss

    def on_save(self, args: TrainingArguments, state: Any, control: Any, **kwargs: Any) -> None:
        ckpt = Path(args.output_dir) / f"checkpoint-{state.global_step}"
        if ckpt.is_dir():
            torch.save(self.radp_loss.projection_head.state_dict(), ckpt / "projection_head.pt")


def build_lora(model: torch.nn.Module, lora_cfg: dict[str, Any]) -> torch.nn.Module:
    """Wrap the parser in a LoRA adapter targeting only the language-model linears.

    Targeting the LLM attention/MLP projection names (q/k/v/o/gate/up/down_proj)
    naturally excludes the vision tower and the vision->LLM merger, so the
    `freeze_vit` / `freeze_aligner` v1 protocol is satisfied by construction.
    """
    config = LoraConfig(
        r=int(lora_cfg["rank"]),
        lora_alpha=int(lora_cfg["alpha"]),
        lora_dropout=float(lora_cfg["dropout"]),
        target_modules=list(lora_cfg["target_modules"]),
        bias="none",
        task_type="CAUSAL_LM",
    )
    peft_model = get_peft_model(model, config)

    leaked = [n for n, _ in peft_model.named_modules() if "lora_" in n and "visual" in n]
    if leaked:
        raise RuntimeError(f"LoRA leaked into the vision tower ({len(leaked)} modules)")
    return peft_model


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", type=Path, default=Path("configs/training/radp_b_base.yaml"))
    ap.add_argument("--output_dir", type=Path, default=None, help="override logging.output_dir")
    ap.add_argument("--contrastive_lambda", type=float, default=None,
                    help="override contrastive.loss_coefficient_lambda (λ sweep); 0 = control")
    ap.add_argument("--smoke", action="store_true", help="4-step pipeline check, no save/eval")
    ap.add_argument("--no_eval", action="store_true", help="skip the eval fold")
    args = ap.parse_args()

    cfg = load_yaml_config(args.config)
    repo_root = resolve_config_path(Path("pyproject.toml")).parent
    os.chdir(repo_root)
    logger.info("repo root: %s | git: %s | CUDA_VISIBLE_DEVICES=%s",
                repo_root, git_commit(), os.environ.get("CUDA_VISIBLE_DEVICES"))

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA not available — RADP-B training needs a GPU")

    base_id = cfg["base_model"]["base_id"]
    train_cfg = cfg["training"]
    con_cfg = cfg["contrastive"]
    data_cfg = cfg["data"]
    log_cfg = cfg["logging"]

    if not (train_cfg.get("freeze_vit") and train_cfg.get("freeze_aligner")):
        raise ValueError("v1 protocol requires freeze_vit and freeze_aligner = true")

    # --- Model + processor ---------------------------------------------------
    logger.info("loading base model: %s", base_id)
    model = Qwen3VLForConditionalGeneration.from_pretrained(
        base_id, dtype=torch.bfloat16, attn_implementation="sdpa"
    )
    processor = AutoProcessor.from_pretrained(base_id)
    hidden_dim = int(model.config.text_config.hidden_size)
    logger.info("parser text hidden_size = %d", hidden_dim)

    model = build_lora(model, cfg["lora"])

    # Final hidden layer for the contrastive anchor — captured via a forward
    # hook so we avoid `output_hidden_states=True` (which materialises every
    # layer and OOMs on full-page document images).
    hidden_module = next(
        (m for n, m in model.named_modules() if n.endswith("language_model.norm")), None
    )
    if hidden_module is None:
        raise RuntimeError("could not locate language_model.norm for hidden-state capture")

    use_grad_ckpt = bool(train_cfg.get("gradient_checkpointing", True))
    if use_grad_ckpt:
        model.enable_input_require_grads()  # required for grad flow through frozen embeddings

    # --- Contrastive head + loss --------------------------------------------
    proj_dim = int(con_cfg.get("proj_dim", 1024))
    head = ContrastiveProjectionHead(
        hidden_dim=hidden_dim,
        proj_dim=proj_dim,
        dropout=float(con_cfg.get("projection_dropout", 0.1)),
    )
    lambda_ = (args.contrastive_lambda if args.contrastive_lambda is not None
               else float(con_cfg["loss_coefficient_lambda"]))
    radp_loss = RadpBLoss(
        projection_head=head,
        lambda_=lambda_,
        temperature=float(con_cfg["temperature"]),
    )
    logger.info("contrastive λ = %.3f%s", lambda_, " (CONTROL)" if lambda_ == 0 else "")
    attach_radp_loss(model, radp_loss)

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    logger.info("trainable params: %d / %d (%.3f%%)", trainable, total, 100 * trainable / total)

    # --- Data ----------------------------------------------------------------
    # full-scale mode (data.train_qa present): train on the whole 2,667p v1 set;
    # eval stays the 73p held-out val fold — comparable to the pilot and to v1.
    full_scale = "train_qa" in data_cfg
    if full_scale:
        logger.info("FULL-SCALE mode: training on the 2,667p v1 train set")
        train_ds = RadpBDataset.from_qa_file(
            qa_path=data_cfg["train_qa"],
            pages_jsonl=data_cfg["train_pages_jsonl"],
            train_images_root=data_cfg["train_images_root"],
            page_id_prefix=data_cfg.get("train_page_id_prefix", "train"),
        )
    else:
        train_ds = RadpBDataset.from_fold(
            split_path=data_cfg["split"], qa_path=data_cfg["qa"],
            val_jsonl=data_cfg["val_jsonl"], fold="train",
            images_root=data_cfg["images_root"],
        )
    eval_ds = None
    if not args.no_eval and not args.smoke:
        eval_ds = RadpBDataset.from_fold(
            split_path=data_cfg["split"], qa_path=data_cfg["qa"],
            val_jsonl=data_cfg["val_jsonl"], fold="eval",
            images_root=data_cfg["images_root"],
        )
    if args.smoke:
        train_ds = RadpBDataset(train_ds.examples[:16])

    collator = Qwen3VLContrastiveCollator(
        processor,
        image_max_pixels=int(data_cfg.get("image_max_pixels", 1_048_576)),
        max_seq_length=int(data_cfg.get("max_seq_length", 3072)),
    )

    chunker = data_cfg["chunker"]
    if full_scale:
        train_cache = BgeM3EmbeddingCache.load(Path(data_cfg["train_cache_dir"]) / chunker)
    else:
        train_cache = BgeM3EmbeddingCache.load(Path(data_cfg["cache_dir"]) / "train" / chunker)
    eval_cache = (
        BgeM3EmbeddingCache.load(Path(data_cfg["cache_dir"]) / "eval" / chunker)
        if eval_ds is not None else train_cache
    )
    logger.info("BGE cache: train rows=%d, eval rows=%d",
                len(train_cache.metas), len(eval_cache.metas))

    sampler = SamplingStrategy(
        num_in_batch_neg=int(con_cfg["num_in_batch_neg"]),
        num_hard_neg=int(con_cfg["num_hard_neg"]),
    )

    # --- TrainingArguments ---------------------------------------------------
    batch_size = int(train_cfg["contrastive_batch_size"])
    if sampler.num_in_batch_neg > batch_size - 1:
        logger.warning(
            "num_in_batch_neg=%d > batch_size-1=%d — negatives will be resampled "
            "with replacement", sampler.num_in_batch_neg, batch_size - 1,
        )
    output_dir = Path(args.output_dir or log_cfg["output_dir"])

    targs = TrainingArguments(
        output_dir=str(output_dir),
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        gradient_accumulation_steps=int(train_cfg["grad_accum"]),
        num_train_epochs=float(train_cfg["epochs"]),
        learning_rate=float(train_cfg["learning_rate"]),
        lr_scheduler_type=train_cfg["scheduler"],
        warmup_ratio=float(train_cfg["warmup_ratio"]),
        bf16=True,
        gradient_checkpointing=use_grad_ckpt,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        dataloader_drop_last=True,  # keep every train batch full for in-batch negatives
        dataloader_num_workers=int(train_cfg.get("dataloader_num_workers", 2)),
        remove_unused_columns=False,
        label_names=["labels"],
        logging_steps=int(log_cfg["log_steps"]),
        eval_strategy="steps" if eval_ds is not None else "no",
        eval_steps=int(log_cfg["eval_steps"]),
        prediction_loss_only=True,
        save_strategy="no" if args.smoke else "steps",
        save_steps=int(log_cfg["save_steps"]),
        save_total_limit=int(log_cfg.get("save_total_limit", 2)),
        max_steps=4 if args.smoke else -1,
        seed=int(cfg.get("seed", 42)),
        report_to=[],
    )

    trainer = RadpBTrainer(
        model=model,
        args=targs,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        data_collator=collator,
        processing_class=processor,
        train_cache=train_cache,
        eval_cache=eval_cache,
        sampler=sampler,
        radp_loss=radp_loss,
        hidden_module=hidden_module,
        contrastive_seed=int(cfg.get("seed", 42)),
    )
    if not args.smoke:
        trainer.add_callback(ProjectionHeadSaveCallback(radp_loss))

    # --- Train ---------------------------------------------------------------
    logger.info("starting training: %d examples, batch=%d, %.0f epochs%s",
                len(train_ds), batch_size, float(train_cfg["epochs"]),
                " [SMOKE]" if args.smoke else "")
    result = trainer.train()
    logger.info("training done: %s", result.metrics)

    if args.smoke:
        logger.info("smoke run OK — pipeline verified, nothing saved")
        return 0

    # --- Save: adapter + projection head + processor + manifest -------------
    final_dir = output_dir / "final"
    final_dir.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(final_dir))
    processor.save_pretrained(str(final_dir))
    torch.save(radp_loss.projection_head.state_dict(), final_dir / "projection_head.pt")

    manifest = {
        "method": "RADP-B",
        "framework": "transformers+peft",
        "git_commit": git_commit(),
        "base_model": base_id,
        "hidden_dim": hidden_dim,
        "proj_dim": proj_dim,
        "lambda": radp_loss.lambda_,
        "temperature": radp_loss.temperature,
        "lora": cfg["lora"],
        "batch_size": batch_size,
        "grad_accum": int(train_cfg["grad_accum"]),
        "epochs": float(train_cfg["epochs"]),
        "num_train_examples": len(train_ds),
        "num_eval_examples": len(eval_ds) if eval_ds is not None else 0,
        "train_metrics": result.metrics,
    }
    (final_dir / "radp_b_manifest.json").write_text(json.dumps(manifest, indent=2))
    logger.info("saved RADP-B model to %s", final_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
