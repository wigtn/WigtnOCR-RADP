"""Q-A pair generator: orchestrates OpenAI structured-output calls and validation."""

from __future__ import annotations

import json
import logging
import os
import random
import sys
import time
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from wigtnocr_radp.qa_generation.schema import (
    QA_RESPONSE_SCHEMA,
    SYSTEM_PROMPT,
    USER_TEMPLATE,
    expand_to_chunk,
    validate_qa,
)
from wigtnocr_radp.utils.config import load_yaml_config, resolve_config_path
from wigtnocr_radp.utils.language import (
    derive_doc_id,
    detect_language,
    infer_domain,
)


logger = logging.getLogger("wigtnocr_radp.qa_generation")


class QAGenerator:
    """Generate Q-A pairs for a single page using a configured OpenAI model."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        model_cfg = config["model"]
        load_dotenv()  # auto-load .env at repo root if present
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY environment variable is not set. "
                "Set it with: export OPENAI_API_KEY=sk-..."
            )
        self.client = OpenAI(
            api_key=api_key,
            timeout=model_cfg.get("request_timeout_seconds", 60),
            max_retries=model_cfg.get("max_retries", 2),
        )
        self.model_id: str = model_cfg["id"]
        self.temperature: float = model_cfg.get("temperature", 0.7)
        self.validation_rules: dict[str, Any] = config.get("validation", {})

    def call_model(self, user_prompt: str) -> dict[str, Any]:
        resp = self.client.chat.completions.create(
            model=self.model_id,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format=QA_RESPONSE_SCHEMA,
            temperature=self.temperature,
        )
        return json.loads(resp.choices[0].message.content)

    def generate_for_page(self, sample: dict[str, Any], val_idx: int) -> list[dict[str, Any]]:
        """Generate Q-A records for a single validation sample."""
        gt_markdown = sample["messages"][2]["content"]
        image_path = sample["images"][0]
        page_id = f"val_{val_idx:04d}"
        doc_id = derive_doc_id(image_path)
        domain = infer_domain(image_path)
        language = detect_language(gt_markdown)

        user_prompt = USER_TEMPLATE.format(
            page_id=page_id,
            domain=domain,
            language=language,
            ground_truth_markdown=gt_markdown,
        )

        max_attempts = 1 + self.validation_rules.get("retry_on_invalid", 1)
        for attempt in range(max_attempts):
            try:
                result = self.call_model(user_prompt)
            except Exception as exc:  # noqa: BLE001
                logger.error("[%s] API error (attempt %d): %s", page_id, attempt + 1, exc)
                continue

            if result.get("skip"):
                logger.info("[%s] SKIPPED: %s", page_id, result.get("reason"))
                return []

            records: list[dict[str, Any]] = []
            invalid_seen = False
            chunk_cfg = self.config.get("chunk_expansion", {})
            target_min = chunk_cfg.get("target_min", 200)
            target_max = chunk_cfg.get("target_max", 800)
            for qa in result.get("qa_pairs", []):
                ok, msg = validate_qa(qa, gt_markdown, self.validation_rules)
                if not ok:
                    logger.warning(
                        "[%s] INVALID QA: %s | q=%r",
                        page_id,
                        msg,
                        qa.get("question", "")[:60],
                    )
                    invalid_seen = True
                    continue
                # Auto-expand chunk
                chunk = expand_to_chunk(qa["answer_span"], gt_markdown, target_min, target_max)
                if chunk is None:
                    logger.warning(
                        "[%s] chunk auto-expand failed for span=%r",
                        page_id,
                        qa["answer_span"][:60],
                    )
                    invalid_seen = True
                    continue
                qa["answer_chunk"] = chunk
                records.append(
                    self._to_record(qa, page_id, doc_id, language, domain)
                )

            if records and not invalid_seen:
                return records
            if records and attempt == max_attempts - 1:
                return records

        return []

    def _to_record(
        self,
        qa: dict[str, Any],
        page_id: str,
        doc_id: str,
        language: str,
        domain: str,
    ) -> dict[str, Any]:
        return {
            "qa_id": str(uuid.uuid4()),
            "page_id": page_id,
            "doc_id": doc_id,
            "language": language,
            "domain": domain,
            "question": qa["question"],
            "answer_span": qa["answer_span"],
            "answer_chunk": qa["answer_chunk"],
            "question_type": qa["question_type"],
            "difficulty": qa["difficulty"],
            "multi_page": False,
            "referenced_pages": [page_id],
            "metadata": {
                "generator_model": self.model_id,
                "generator_temperature": self.temperature,
                "generation_timestamp": datetime.now(timezone.utc).isoformat(),
                "human_verified": False,
                "verification_notes": None,
                "rationale": qa.get("rationale", ""),
            },
        }


def _select_indices(num_samples: int, sampling_cfg: dict[str, Any]) -> list[int]:
    """Pick val_idx list per config."""
    if sampling_cfg.get("page_indices"):
        return list(sampling_cfg["page_indices"])
    num = min(sampling_cfg.get("num_pages", 5), num_samples)
    mode = sampling_cfg.get("mode", "first")
    if mode == "random":
        rng = random.Random(sampling_cfg.get("seed", 42))
        return rng.sample(range(num_samples), num)
    return list(range(num))


def generate_for_config(
    config_path: str | Path,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Run Q-A generation for a config file. Returns a summary dict.

    Args:
        config_path: Path to a Q-A generation config (configs/qa_generation/*.yaml).
        dry_run: If True, only prints the pages that would be processed; no API calls.
    """
    config = load_yaml_config(config_path)
    data_cfg_path = config["dataset"]["config"]
    data_cfg = load_yaml_config(resolve_config_path(data_cfg_path))

    split = config["dataset"].get("split", "validation")
    jsonl_path = resolve_config_path(data_cfg["paths"]["validation_jsonl"])
    if split != "validation":
        raise NotImplementedError(f"Only 'validation' split is supported; got {split!r}")

    with jsonl_path.open("r", encoding="utf-8") as f:
        samples = [json.loads(line) for line in f]

    indices = _select_indices(len(samples), config["sampling"])

    output_path = resolve_config_path(config["output"]["path"])
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if dry_run:
        return {
            "dry_run": True,
            "config_name": config.get("name"),
            "model": config["model"]["id"],
            "num_pages_planned": len(indices),
            "indices": indices,
            "output_path": str(output_path),
        }

    generator = QAGenerator(config)
    all_records: list[dict[str, Any]] = []
    skipped = 0
    type_counter: Counter[str] = Counter()
    diff_counter: Counter[str] = Counter()

    start = time.time()
    for i, idx in enumerate(indices):
        sys.stdout.write(f"[{i+1}/{len(indices)}] val_idx={idx} ... ")
        sys.stdout.flush()
        recs = generator.generate_for_page(samples[idx], idx)
        if not recs:
            skipped += 1
            sys.stdout.write("skipped/failed\n")
            continue
        all_records.extend(recs)
        for r in recs:
            type_counter[r["question_type"]] += 1
            diff_counter[r["difficulty"]] += 1
        sys.stdout.write(f"{len(recs)} Q-A\n")

    elapsed = time.time() - start

    with output_path.open("w", encoding="utf-8") as f:
        for r in all_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    summary = {
        "config_name": config.get("name"),
        "model": config["model"]["id"],
        "pages_processed": len(indices),
        "pages_skipped": skipped,
        "qa_pairs_generated": len(all_records),
        "question_type_distribution": dict(type_counter),
        "difficulty_distribution": dict(diff_counter),
        "elapsed_seconds": round(elapsed, 1),
        "output_path": str(output_path),
    }

    log_path = resolve_config_path(config["output"]["pretty_log_path"])
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    return summary
