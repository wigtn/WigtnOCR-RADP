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


class QAApiError(RuntimeError):
    """Raised when every attempt on a page failed with an API-level error.

    Distinct from a page that the model legitimately skipped or that produced
    no valid Q-A — those return an empty list. This signals an external fault
    (budget exhausted, auth, persistent rate limit) so the run can stop cleanly
    *without* marking the page done, leaving it for `--resume` to retry.
    """


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

    def generate_for_page(
        self, sample: dict[str, Any], val_idx: int, page_id_prefix: str = "val"
    ) -> list[dict[str, Any]]:
        """Generate Q-A records for a single page sample.

        `page_id_prefix` namespaces the page_id (e.g. "train" for the v1 train
        set) so train Q-A do not collide with the eval set's val_* ids.
        """
        gt_markdown = sample["messages"][2]["content"]
        image_path = sample["images"][0]
        page_id = f"{page_id_prefix}_{val_idx:04d}"
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
        api_ok = False
        for attempt in range(max_attempts):
            try:
                result = self.call_model(user_prompt)
            except Exception as exc:  # noqa: BLE001
                logger.error("[%s] API error (attempt %d): %s", page_id, attempt + 1, exc)
                continue
            api_ok = True

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

        if not api_ok:
            # Every attempt hit an API error — external fault, not an empty
            # page. Raise so the run stops without marking this page done.
            raise QAApiError(
                f"[{page_id}] all {max_attempts} attempts failed with API errors"
            )
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


def _read_done_indices(done_path: Path) -> set[int]:
    """Read the set of already-attempted page indices from a `.done` sidecar."""
    done: set[int] = set()
    if done_path.exists():
        for line in done_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                done.add(int(line))
    return done


def generate_for_config(
    config_path: str | Path,
    dry_run: bool = False,
    resume: bool = False,
) -> dict[str, Any]:
    """Run Q-A generation for a config file. Returns a summary dict.

    Args:
        config_path: Path to a Q-A generation config (configs/qa_generation/*.yaml).
        dry_run: If True, only prints the pages that would be processed; no API calls.
        resume: If True, skip pages already recorded in ``<output>.done`` and
            *append* new results. Each page is written to the output file the
            moment it finishes and its index is appended to the ``.done``
            sidecar — so a run can be stopped (e.g. to switch API keys) and
            continued without losing work or re-spending on done pages.
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
    done_path = output_path.parent / (output_path.name + ".done")
    page_id_prefix = config["output"].get("page_id_prefix", "val")

    done_indices = _read_done_indices(done_path) if resume else set()
    pending = [idx for idx in indices if idx not in done_indices]

    if dry_run:
        return {
            "dry_run": True,
            "resume": resume,
            "config_name": config.get("name"),
            "model": config["model"]["id"],
            "page_id_prefix": page_id_prefix,
            "num_pages_planned": len(indices),
            "num_already_done": len(done_indices),
            "num_pending": len(pending),
            "output_path": str(output_path),
        }

    generator = QAGenerator(config)
    skipped = 0

    # Incremental write: each page lands on disk immediately, so an interrupted
    # run keeps every completed page. `resume` decides append vs truncate.
    out_mode = "a" if (resume and output_path.exists()) else "w"
    done_mode = "a" if (resume and done_path.exists()) else "w"

    aborted = False
    start = time.time()
    with output_path.open(out_mode, encoding="utf-8") as out_f, \
            done_path.open(done_mode, encoding="utf-8") as done_f:
        for i, idx in enumerate(pending):
            sys.stdout.write(f"[{i+1}/{len(pending)}] {page_id_prefix}_idx={idx} ... ")
            sys.stdout.flush()
            try:
                recs = generator.generate_for_page(samples[idx], idx, page_id_prefix)
            except QAApiError as exc:
                # External fault — stop cleanly. This page is NOT marked done,
                # so `--resume` retries it after the key/budget is fixed.
                sys.stdout.write("API FAILURE — stopping\n")
                logger.error("run aborted: %s", exc)
                aborted = True
                break
            for r in recs:
                out_f.write(json.dumps(r, ensure_ascii=False) + "\n")
            out_f.flush()
            done_f.write(f"{idx}\n")
            done_f.flush()
            if not recs:
                skipped += 1
                sys.stdout.write("skipped/failed\n")
            else:
                sys.stdout.write(f"{len(recs)} Q-A\n")

    elapsed = time.time() - start

    # Totals are computed over the WHOLE output file so the summary is correct
    # across resumed runs, not just this invocation.
    all_records: list[dict[str, Any]] = []
    with output_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                all_records.append(json.loads(line))
    type_counter: Counter[str] = Counter(r["question_type"] for r in all_records)
    diff_counter: Counter[str] = Counter(r["difficulty"] for r in all_records)

    done_total = len(_read_done_indices(done_path))
    summary = {
        "config_name": config.get("name"),
        "model": config["model"]["id"],
        "resume": resume,
        "aborted_on_api_error": aborted,
        "pages_planned_total": len(indices),
        "pages_processed_this_run": done_total - len(done_indices),
        "pages_skipped_this_run": skipped,
        "pages_done_total": done_total,
        "pages_remaining": len(indices) - done_total,
        "qa_pairs_total": len(all_records),
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
