"""Build or validate the portable KoGovDoc-RAG source-page map.

The private training-format ``val.jsonl`` contains absolute image paths and
reference Markdown.  The public map derived here retains only the stable
``val_####`` page ID, domain, and parser-output filename.

Usage:
    python scripts/analysis/source_page_map.py \
        --source /path/to/KoGovDoc-Bench/val.jsonl \
        --out data/KoGovDoc-RAG/source_page_map_v1.json
    python scripts/analysis/source_page_map.py \
        --check data/KoGovDoc-RAG/source_page_map_v1.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "data/KoGovDoc-RAG/source_page_map_v1.json"
SOURCE_LABEL = "KoGovDoc-Bench/val.jsonl"
EXPECTED_SOURCE_SHA256 = "7b0fc3606951ccf08a338d62c983976f9e8609ec38d668b6db51056d07fa5213"
QA_PATH = ROOT / "data/KoGovDoc-RAG/qa_pairs_v1.jsonl"
SPLIT_PATH = ROOT / "data/KoGovDoc-RAG/page_split_v1.json"
PARSER_OUTPUT_DIRS = (
    ROOT / "results/kogovdoc/v1_val/predictions",
    ROOT / "results/kogovdoc/paddleocr_val/predictions",
    ROOT / "results/kogovdoc/mineru_val/predictions",
    ROOT / "results/kogovdoc/mineru_val_tableon/predictions",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def derive_map(source: Path) -> dict[str, Any]:
    source_sha256 = _sha256(source)
    if source_sha256 != EXPECTED_SOURCE_SHA256:
        raise ValueError(
            f"unexpected source SHA-256: {source_sha256}; expected {EXPECTED_SOURCE_SHA256}"
        )
    rows = [
        json.loads(line)
        for line in source.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    pages: list[dict[str, str]] = []
    for index, row in enumerate(rows):
        images = row.get("images")
        if not isinstance(images, list) or len(images) != 1:
            raise ValueError(f"source row {index} must contain exactly one image path")
        image = PurePosixPath(str(images[0]))
        if "papers" in image.parts:
            domain = "arxiv"
        elif "documents" in image.parts:
            domain = "kogov"
        else:
            raise ValueError(f"source row {index} has an unknown image domain: {image}")
        pages.append(
            {
                "page_id": f"val_{index:04d}",
                "domain": domain,
                "parser_output_file": f"{image.parent.name}_{image.stem}.md",
            }
        )

    return {
        "schema_version": 1,
        "status": "portable_source_page_map",
        "source_metadata": {
            "source_label": SOURCE_LABEL,
            "sha256": source_sha256,
            "excluded_fields": [
                "absolute image path",
                "system prompt",
                "user prompt",
                "reference Markdown",
            ],
        },
        "pages": pages,
    }


def _qa_page_ids() -> set[str]:
    return {
        str(json.loads(line)["page_id"])
        for line in QA_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


def validate_map(report: dict[str, Any]) -> dict[str, Any]:
    if report.get("status") != "portable_source_page_map":
        raise ValueError("unsupported source-page map status")
    pages = report.get("pages")
    if not isinstance(pages, list) or len(pages) != 294:
        raise ValueError(f"source-page map must contain 294 pages, got {len(pages or [])}")

    source_metadata = report.get("source_metadata")
    if not isinstance(source_metadata, dict):
        raise ValueError("source-page map is missing source metadata")
    if source_metadata.get("source_label") != SOURCE_LABEL:
        raise ValueError("source-page map has an unexpected source label")
    if source_metadata.get("sha256") != EXPECTED_SOURCE_SHA256:
        raise ValueError("source-page map has an unexpected source SHA-256")

    expected_page_keys = {"page_id", "domain", "parser_output_file"}
    for index, row in enumerate(pages):
        if not isinstance(row, dict) or set(row) != expected_page_keys:
            raise ValueError(f"source-page map row {index} has an unexpected schema")

    page_ids = [str(row["page_id"]) for row in pages]
    filenames = [str(row["parser_output_file"]) for row in pages]
    if page_ids != [f"val_{index:04d}" for index in range(294)]:
        raise ValueError("source-page map page IDs are not the canonical ordered val_0000..val_0293")
    if len(set(filenames)) != len(filenames):
        raise ValueError("source-page map contains duplicate parser-output filenames")
    if any(PurePosixPath(name).name != name or "\\" in name for name in filenames):
        raise ValueError("source-page map parser-output values must be portable basenames")

    domain_counts = dict(sorted(Counter(str(row["domain"]) for row in pages).items()))
    if domain_counts != {"arxiv": 65, "kogov": 229}:
        raise ValueError(f"unexpected source-page map domain counts: {domain_counts}")

    expected_files = set(filenames)
    parser_sets: dict[str, bool] = {}
    for directory in PARSER_OUTPUT_DIRS:
        observed = {path.name for path in directory.glob("*.md")}
        if observed != expected_files:
            raise ValueError(
                f"parser output set does not match source-page map: {directory} "
                f"missing={len(expected_files - observed)} extra={len(observed - expected_files)}"
            )
        parser_sets[str(directory.relative_to(ROOT))] = True

    qa_pages = _qa_page_ids()
    split = json.loads(SPLIT_PATH.read_text(encoding="utf-8"))
    train_pages = set(split["train_pages"])
    eval_pages = set(split["eval_pages"])
    if train_pages & eval_pages:
        raise ValueError("page-level train/eval split overlaps")
    if train_pages | eval_pages != qa_pages:
        raise ValueError("page split does not exactly cover the Q-A evidence pages")
    if not qa_pages <= set(page_ids):
        raise ValueError("Q-A evidence page is absent from the source-page map")

    return {
        "num_pages": len(pages),
        "domain_counts": domain_counts,
        "num_evidence_pages": len(qa_pages),
        "num_distractor_pages": len(pages) - len(qa_pages),
        "parser_output_sets_match": parser_sets,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--check", type=Path)
    args = parser.parse_args()

    if args.source is None and args.check is None:
        parser.error("provide --source to build or --check to validate")

    if args.source is not None:
        report = derive_map(args.source)
        validation = validate_map(report)
        report["validation"] = validation
        if args.check is not None:
            tracked = json.loads(args.check.read_text(encoding="utf-8"))
            if tracked != report:
                raise SystemExit(f"tracked source-page map differs from source: {args.check}")
            print(f"OK: {args.check} matches source and parser inventories")
            return 0
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"wrote {args.out}")
        return 0

    report = json.loads(args.check.read_text(encoding="utf-8"))
    validation = validate_map(report)
    if report.get("validation") != validation:
        raise SystemExit(f"stale source-page map validation summary: {args.check}")
    print(f"OK: {args.check} matches Q-A, split, and parser inventories")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
