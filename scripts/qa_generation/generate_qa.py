"""CLI entry point for Q-A pair generation.

Usage:
    export OPENAI_API_KEY=sk-...
    uv run python scripts/qa_generation/generate_qa.py \
        --config configs/qa_generation/diverse_5.yaml

    # Dry run (no API calls; just prints planned execution)
    uv run python scripts/qa_generation/generate_qa.py \
        --config configs/qa_generation/diverse_5.yaml --dry-run
"""

from __future__ import annotations

import argparse
import json
import logging
import sys

from wigtnocr_radp.qa_generation import generate_for_config


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Q-A pairs from KoGovDoc-Bench.")
    parser.add_argument(
        "--config",
        required=True,
        help="Path to Q-A generation config (configs/qa_generation/*.yaml)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned execution without API calls",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help=(
            "Resume: skip pages already in <output>.done and append new results. "
            "Each page is flushed to disk as it finishes, so the run can be "
            "stopped (e.g. to switch API keys) and continued without rework."
        ),
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable DEBUG logging",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    try:
        summary = generate_for_config(
            args.config, dry_run=args.dry_run, resume=args.resume
        )
    except RuntimeError as exc:
        sys.stderr.write(f"ERROR: {exc}\n")
        return 1

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
