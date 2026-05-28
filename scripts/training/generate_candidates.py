"""Stage 1a — Generate per-page markdown candidates from v1 with temperature sampling.

For each of the 2,667 v1 train pages, generate N candidates (different sampling
temperatures) so we can score them with page-local RCPS and build preference
pairs for DPO training (see `score_candidates.py` → `build_preference_pairs.py`).

Uses the merged v1 model (`wigtnocr-2b-merged`) so no LoRA adapter dance is
needed. Outputs one jsonl line per (page, candidate) into `--out`.

Usage:
    CUDA_VISIBLE_DEVICES=1 uv run python scripts/training/generate_candidates.py \
        --temperatures 0.7 1.2 --batch_size 8
"""

from __future__ import annotations

import os

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

import argparse  # noqa: E402
import json  # noqa: E402
import logging  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import torch  # noqa: E402
from PIL import Image  # noqa: E402
from transformers import AutoProcessor, Qwen3VLForConditionalGeneration  # noqa: E402

from wigtnocr_radp.training.data import remap_train_image_path  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("generate_candidates")

V1_MERGED = Path("/mnt/data1/work/wigtnOCR-v1/output/wigtnocr-2b-merged")
V1_DATASETS = Path("/mnt/data1/work/wigtnOCR-v1/datasets")


def load_image(path: Path, max_pixels: int) -> Image.Image:
    img = Image.open(path).convert("RGB")
    w, h = img.size
    if w * h > max_pixels:
        scale = (max_pixels / (w * h)) ** 0.5
        img = img.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)
    return img


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model_dir", type=Path, default=V1_MERGED)
    ap.add_argument("--adapter", type=Path, default=None,
                    help="optional LoRA adapter on top of --model_dir (e.g. DPO checkpoint)")
    ap.add_argument("--train_jsonl", type=Path, default=Path("data/KoGovDoc-RAG/train_2667.jsonl"))
    ap.add_argument("--train_images_root", type=Path, default=V1_DATASETS)
    ap.add_argument("--out", type=Path, default=Path("output/candidates/v1_train_candidates.jsonl"))
    ap.add_argument("--temperatures", type=float, nargs="+", default=[0.7, 1.2])
    ap.add_argument("--batch_size", type=int, default=8)
    ap.add_argument("--max_new_tokens", type=int, default=2048)
    ap.add_argument("--image_max_pixels", type=int, default=1_048_576)
    ap.add_argument("--limit", type=int, default=None, help="restrict to first N pages (smoke test)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--resume", action="store_true", help="skip (page_id, temperature) pairs already in --out")
    args = ap.parse_args()

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA not available")
    torch.manual_seed(args.seed)

    logger.info("loading merged base model: %s", args.model_dir)
    model = Qwen3VLForConditionalGeneration.from_pretrained(
        args.model_dir, dtype=torch.bfloat16, attn_implementation="sdpa", device_map="cuda"
    )
    if args.adapter:
        from peft import PeftModel
        logger.info("loading LoRA adapter on top: %s", args.adapter)
        model = PeftModel.from_pretrained(model, str(args.adapter))
    model.eval()
    processor = AutoProcessor.from_pretrained(args.model_dir)
    processor.tokenizer.padding_side = "left"

    rows = [json.loads(line) for line in args.train_jsonl.read_text().splitlines() if line.strip()]
    if args.limit:
        rows = rows[: args.limit]
    pages: list[tuple[str, dict]] = [(f"train_{i:04d}", row) for i, row in enumerate(rows)]
    logger.info("loaded %d train pages", len(pages))

    # Resume support: skip (page_id, temperature) pairs already written.
    args.out.parent.mkdir(parents=True, exist_ok=True)
    seen: set[tuple[str, float]] = set()
    if args.resume and args.out.exists():
        for line in args.out.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            seen.add((r["page_id"], float(r["temperature"])))
        logger.info("resume: skipping %d existing (page, temp) pairs", len(seen))

    # Open output file in append mode so resume preserves history.
    fout = args.out.open("a", encoding="utf-8")

    total_done = 0
    for temp_idx, temperature in enumerate(args.temperatures):
        logger.info("=== candidate %d/%d  temperature=%.2f ===",
                    temp_idx + 1, len(args.temperatures), temperature)
        pages_to_do = [(pid, row) for pid, row in pages if (pid, temperature) not in seen]
        logger.info("temp=%.2f: %d pages to generate (%d already done)",
                    temperature, len(pages_to_do), len(pages) - len(pages_to_do))

        t0 = time.time()
        for start in range(0, len(pages_to_do), args.batch_size):
            batch = pages_to_do[start : start + args.batch_size]
            images, texts = [], []
            for _pid, row in batch:
                system = row["messages"][0]["content"]
                user = row["messages"][1]["content"].replace("<image>", "", 1).lstrip()
                messages = [
                    {"role": "system", "content": system},
                    {"role": "user", "content": [{"type": "image"}, {"type": "text", "text": user}]},
                ]
                texts.append(processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True))
                images.append(load_image(remap_train_image_path(row["images"][0], args.train_images_root),
                                         args.image_max_pixels))

            inputs = processor(text=texts, images=images, return_tensors="pt", padding=True).to("cuda")
            gen_kwargs = {"max_new_tokens": args.max_new_tokens, "do_sample": True,
                          "temperature": temperature, "top_p": 0.95}
            with torch.inference_mode():
                out = model.generate(**inputs, **gen_kwargs)
            gen = out[:, inputs["input_ids"].shape[1] :]
            decoded = processor.batch_decode(gen, skip_special_tokens=True)

            for (pid, row), md in zip(batch, decoded):
                fout.write(json.dumps({
                    "page_id": pid, "doc_id": row["images"][0].split("/")[-2],
                    "candidate_idx": temp_idx, "temperature": temperature,
                    "markdown": md.strip(),
                }, ensure_ascii=False) + "\n")
            fout.flush()
            total_done += len(batch)
            if (total_done % 80 == 0) or total_done == len(pages_to_do):
                elapsed = time.time() - t0
                rate = total_done / max(elapsed, 1e-6)
                logger.info("[temp=%.1f] %d/%d  (%.1f pages/s, %.1f min elapsed)",
                            temperature, total_done % len(pages_to_do) or len(pages_to_do),
                            len(pages_to_do), rate, elapsed / 60)

    fout.close()
    logger.info("wrote %d candidates to %s", total_done, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
