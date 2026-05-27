"""Generate per-page Markdown parses with a Qwen3-VL parser (base + optional LoRA).

Writes one `<doc_id>_<page_stem>.md` file per page into `--out_dir`, using the
same filename convention as `wigtnocr_radp.evaluation.parser_outputs` so the
output drops straight into `load_parser_outputs` / `compute_rcps`.

Usage:
    # RADP-B (λ=0.3) parses for the held-out eval fold
    CUDA_VISIBLE_DEVICES=1 uv run python scripts/evaluation/generate_parses.py \
        --adapter output/checkpoints/radp_b_base/final \
        --fold eval --out_dir output/parses/radp_b_base_eval
"""

from __future__ import annotations

import os

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

import argparse  # noqa: E402
import json  # noqa: E402
import logging  # noqa: E402
from pathlib import Path  # noqa: E402

import torch  # noqa: E402
from PIL import Image  # noqa: E402
from transformers import AutoProcessor, Qwen3VLForConditionalGeneration  # noqa: E402

from wigtnocr_radp.evaluation.parser_outputs import build_page_id_index  # noqa: E402
from wigtnocr_radp.training.data import remap_image_path  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("generate_parses")


def load_image(path: Path, max_pixels: int) -> Image.Image:
    img = Image.open(path).convert("RGB")
    w, h = img.size
    if w * h > max_pixels:
        scale = (max_pixels / (w * h)) ** 0.5
        img = img.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)
    return img


def fold_page_ids(split_path: Path, fold: str) -> set[str]:
    split = json.loads(split_path.read_text())
    if fold == "all":
        return set(split["train_pages"]) | set(split["eval_pages"])
    return set(split[{"train": "train_pages", "eval": "eval_pages"}[fold]])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", default="Qwen/Qwen3-VL-2B-Instruct")
    ap.add_argument("--adapter", default=None, help="LoRA adapter dir; omit for the base model")
    ap.add_argument("--val_jsonl", type=Path, default=Path("data/KoGovDoc-Bench/val.jsonl"))
    ap.add_argument("--split", type=Path, default=Path("data/KoGovDoc-RAG/page_split_v1.json"))
    ap.add_argument("--fold", choices=("train", "eval", "all"), default="eval")
    ap.add_argument("--out_dir", type=Path, required=True)
    ap.add_argument("--batch_size", type=int, default=8)
    ap.add_argument("--max_new_tokens", type=int, default=2048)
    ap.add_argument("--image_max_pixels", type=int, default=1_048_576)
    args = ap.parse_args()

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA not available")

    logger.info("loading base model: %s", args.base)
    model = Qwen3VLForConditionalGeneration.from_pretrained(
        args.base, dtype=torch.bfloat16, attn_implementation="sdpa", device_map="cuda"
    )
    if args.adapter:
        from peft import PeftModel

        logger.info("loading LoRA adapter: %s", args.adapter)
        model = PeftModel.from_pretrained(model, args.adapter)
    model.eval()

    processor = AutoProcessor.from_pretrained(args.base)
    processor.tokenizer.padding_side = "left"  # left padding for batched generation

    # Pages to parse, with their val.jsonl rows and output filename stems.
    page_stems = build_page_id_index(args.val_jsonl)
    want = fold_page_ids(args.split, args.fold)
    val_rows = [json.loads(line) for line in args.val_jsonl.read_text().splitlines() if line.strip()]

    jobs: list[tuple[str, str, dict]] = []  # (page_id, stem, row)
    for i, row in enumerate(val_rows):
        page_id = f"val_{i:04d}"
        if page_id in want:
            jobs.append((page_id, page_stems[page_id], row))
    logger.info("fold=%s: %d pages to parse", args.fold, len(jobs))

    args.out_dir.mkdir(parents=True, exist_ok=True)
    done = 0
    for start in range(0, len(jobs), args.batch_size):
        batch = jobs[start : start + args.batch_size]
        images, texts = [], []
        for _pid, _stem, row in batch:
            system = row["messages"][0]["content"]
            user = row["messages"][1]["content"].replace("<image>", "", 1).lstrip()
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": [{"type": "image"}, {"type": "text", "text": user}]},
            ]
            texts.append(processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True))
            images.append(load_image(remap_image_path(row["images"][0]), args.image_max_pixels))

        inputs = processor(text=texts, images=images, return_tensors="pt", padding=True).to("cuda")
        with torch.inference_mode():
            out = model.generate(**inputs, max_new_tokens=args.max_new_tokens, do_sample=False)
        gen = out[:, inputs["input_ids"].shape[1] :]
        decoded = processor.batch_decode(gen, skip_special_tokens=True)

        for (_pid, stem, _row), md in zip(batch, decoded):
            (args.out_dir / f"{stem}.md").write_text(md.strip() + "\n", encoding="utf-8")
        done += len(batch)
        logger.info("parsed %d/%d pages", done, len(jobs))

    logger.info("wrote %d markdown files to %s", done, args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
