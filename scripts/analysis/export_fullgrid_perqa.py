"""Export the aligned 294-page RCPS full grid at per-QA resolution.

This closes the camera-ready probe-resampling audit without mixing in the
242-page training fold.  It evaluates nine unique systems over the same 663
questions, three retrievers, and k={1,5,10}:

* six parser-native corpora: Teacher, Prod, Base, MinerU-off, MinerU-on, Paddle;
* Prod with md_h3, LumberChunker, and fixed500 (parser-native is shared above).

The ranked chunks are reused to evaluate both the paper's format-normalised
relevance rule and a raw-substring sensitivity control.  Models are loaded once
and kept in one process so GPU-driver initialisation occurs only once.

Typical ml35 invocation (from the repository root):

    HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 CUDA_VISIBLE_DEVICES=0 \
      .venv/bin/python scripts/analysis/export_fullgrid_perqa.py \
      --v1-root /path/to/kogovdoc-parser-outputs \
      --device cuda:0 --out output/results/fullgrid_perqa_294p.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import platform
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("export_fullgrid_perqa")

K_VALUES = (1, 5, 10)
PARSER_NATIVE_LABELS = (
    "Qwen3-VL-30B (teacher)",
    "Prod",
    "Qwen3-VL-2B (base)",
    "MinerU-off",
    "MinerU-on",
    "PaddleOCR",
)
CHUNKER_LABELS = ("Prod__md_h3", "Prod__parser_native", "Prod__lumberchunker", "Prod__fixed500")


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def tree_sha256(root: Path) -> str:
    """Hash file names and contents in a parser-output directory."""
    h = hashlib.sha256()
    files = sorted(p for p in root.rglob("*") if p.is_file())
    for path in files:
        rel = path.relative_to(root).as_posix().encode("utf-8")
        h.update(len(rel).to_bytes(8, "big"))
        h.update(rel)
        with path.open("rb") as f:
            for block in iter(lambda: f.read(1024 * 1024), b""):
                h.update(block)
    return h.hexdigest()


def mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def driver_version() -> str | None:
    try:
        return subprocess.check_output(
            ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).splitlines()[0].strip()
    except (OSError, subprocess.CalledProcessError, IndexError):
        return None


def first_relevant_rank(
    ranked: Sequence[tuple[Any, float]], qa: Any, *, normalised: bool, normalize_for_match: Any
) -> int | None:
    answer = normalize_for_match(qa.answer_span) if normalised else qa.answer_span
    for rank, (chunk, _) in enumerate(ranked, start=1):
        if chunk.page_id != qa.page_id:
            continue
        text = normalize_for_match(chunk.text) if normalised else chunk.text
        if answer and answer in text:
            return rank
    return None


def metric_vectors(
    results: Sequence[Any], qa_pairs: Sequence[Any], normalize_for_match: Any
) -> tuple[dict[str, list[float]], dict[str, list[float]]]:
    normalised: dict[str, list[float]] = {f"mrr@{k}": [] for k in K_VALUES}
    raw: dict[str, list[float]] = {f"mrr@{k}": [] for k in K_VALUES}
    for result, qa in zip(results, qa_pairs, strict=True):
        norm_rank = first_relevant_rank(
            result.ranked, qa, normalised=True, normalize_for_match=normalize_for_match
        )
        raw_rank = first_relevant_rank(
            result.ranked, qa, normalised=False, normalize_for_match=normalize_for_match
        )
        for k in K_VALUES:
            normalised[f"mrr@{k}"].append(
                0.0 if norm_rank is None or norm_rank > k else 1.0 / norm_rank
            )
            raw[f"mrr@{k}"].append(
                0.0 if raw_rank is None or raw_rank > k else 1.0 / raw_rank
            )
    return normalised, raw


def ranking(
    summary: Mapping[str, Mapping[str, float]], keys: Sequence[str], field: str
) -> list[str]:
    return sorted(keys, key=lambda key: (-summary[key][field], key))


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--qa", type=Path, default=Path("data/KoGovDoc-RAG/qa_pairs_v1.jsonl"))
    ap.add_argument("--val", type=Path, default=Path("data/KoGovDoc-Bench/val.jsonl"))
    ap.add_argument(
        "--v1-root",
        type=Path,
        required=True,
        metavar="PATH",
        help="root containing 30b_val, v1_val, 2b_base_val, mineru_val, and paddleocr_val",
    )
    ap.add_argument(
        "--mineru-on-dir", type=Path,
        default=Path("results/kogovdoc/mineru_val_tableon/predictions"),
    )
    ap.add_argument(
        "--lumber-chunks", type=Path,
        default=Path("output/chunks/lumberchunker_v1.jsonl"),
    )
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--expected-pages", type=int, default=294)
    ap.add_argument("--expected-qa", type=int, default=663)
    ap.add_argument("--out", type=Path, default=Path("output/results/fullgrid_perqa_294p.json"))
    ap.add_argument("--resume", action="store_true")
    return ap.parse_args()


def main() -> int:
    args = parse_args()

    import torch
    from sentence_transformers import __version__ as sentence_transformers_version
    from transformers import __version__ as transformers_version

    from wigtnocr_radp.evaluation.chunkers import (
        FixedSizeChunker,
        MarkdownHeaderChunker,
        ParserNativeChunker,
    )
    from wigtnocr_radp.evaluation.llm_chunkers import PrecomputedChunker
    from wigtnocr_radp.evaluation.parser_outputs import load_parser_outputs
    from wigtnocr_radp.evaluation.rcps import load_qa_pairs
    from wigtnocr_radp.evaluation.retrievers import (
        BgeM3Retriever,
        MultilingualE5LargeRetriever,
        Qwen3EmbeddingRetriever,
    )
    from wigtnocr_radp.evaluation.types import normalize_for_match

    if args.device.startswith("cuda"):
        if not torch.cuda.is_available():
            raise RuntimeError(
                "CUDA initialisation failed before model loading. Re-run this same process; "
                "do not alter the server driver or CUDA installation."
            )
        device_index = int(args.device.split(":", 1)[1]) if ":" in args.device else 0
        torch.cuda.set_device(device_index)
        probe = torch.ones(1, device=args.device)
        if probe.item() != 1.0:
            raise RuntimeError("CUDA allocation preflight returned an unexpected value")
        logger.info("CUDA preflight OK: %s", torch.cuda.get_device_name(device_index))

    qa_pairs = load_qa_pairs(args.qa)
    if len(qa_pairs) != args.expected_qa:
        raise RuntimeError(f"expected {args.expected_qa} Q-A, found {len(qa_pairs)}")

    parser_dirs = {
        "Qwen3-VL-30B (teacher)": args.v1_root / "30b_val/predictions",
        "Prod": args.v1_root / "v1_val/predictions",
        "Qwen3-VL-2B (base)": args.v1_root / "2b_base_val/predictions",
        "MinerU-off": args.v1_root / "mineru_val/predictions",
        "MinerU-on": args.mineru_on_dir,
        "PaddleOCR": args.v1_root / "paddleocr_val/predictions",
    }
    pages: dict[str, dict[str, str]] = {}
    for label, parser_dir in parser_dirs.items():
        if not parser_dir.is_dir():
            raise FileNotFoundError(f"{label}: parser output directory not found: {parser_dir}")
        loaded = dict(load_parser_outputs(parser_dir, args.val))
        if len(loaded) != args.expected_pages:
            raise RuntimeError(
                f"{label}: expected {args.expected_pages} pages, found {len(loaded)}"
            )
        pages[label] = loaded

    prod_pages = pages["Prod"]
    systems: list[tuple[str, dict[str, str], Any]] = [
        (f"{label}__parser_native", pages[label], ParserNativeChunker(min_chars=30))
        for label in PARSER_NATIVE_LABELS
    ]
    systems.extend([
        ("Prod__md_h3", prod_pages, MarkdownHeaderChunker(max_level=3)),
        ("Prod__lumberchunker", prod_pages, PrecomputedChunker(args.lumber_chunks)),
        ("Prod__fixed500", prod_pages, FixedSizeChunker(size=500)),
    ])

    retrievers = [
        BgeM3Retriever(device=args.device, batch_size=32),
        MultilingualE5LargeRetriever(device=args.device, batch_size=32),
        Qwen3EmbeddingRetriever(device=args.device, batch_size=8),
    ]
    retriever_names = [retriever.name for retriever in retrievers]

    source_hashes = {
        "qa": {"path": str(args.qa), "sha256": file_sha256(args.qa)},
        "val": {"path": str(args.val), "sha256": file_sha256(args.val)},
        "lumber_chunks": {
            "path": str(args.lumber_chunks), "sha256": file_sha256(args.lumber_chunks)
        },
        "parser_outputs": {
            label: {
                "source_id": f"{label} full 294-page parser output",
                "tree_sha256": tree_sha256(path),
            }
            for label, path in parser_dirs.items()
        },
    }
    payload: dict[str, Any] = {
        "meta": {
            "schema": "rcps-fullgrid-perqa-v1",
            "qa_ids": [qa.qa_id for qa in qa_pairs],
            "n_qa": len(qa_pairs),
            "n_pages": args.expected_pages,
            "retrievers": retriever_names,
            "k_values": list(K_VALUES),
            "systems": [label for label, _, _ in systems],
            "parser_pool": [f"{label}__parser_native" for label in PARSER_NATIVE_LABELS],
            "chunker_pool": list(CHUNKER_LABELS),
            "relevance": {
                "normalised": (
                    "reference page + NFKC/lowercase/whitespace-and-Markdown-stripped "
                    "answer substring"
                ),
                "raw": "reference page + case-sensitive raw answer substring",
            },
            "runtime": {
                "python": sys.version.split()[0],
                "platform": platform.platform(),
                "torch": torch.__version__,
                "torch_cuda": torch.version.cuda,
                "cuda_device": (
                    torch.cuda.get_device_name(torch.cuda.current_device())
                    if torch.cuda.is_available() else None
                ),
                "nvidia_driver": driver_version(),
                "sentence_transformers": sentence_transformers_version,
                "transformers": transformers_version,
            },
            "source_hashes": source_hashes,
        },
        "systems": {},
        "systems_raw": {},
        "summary": {},
    }
    if args.resume and args.out.exists():
        existing = json.loads(args.out.read_text(encoding="utf-8"))
        if existing.get("meta", {}).get("qa_ids") != payload["meta"]["qa_ids"]:
            raise RuntimeError("resume file has different qa_ids")
        for key in ("systems", "systems_raw", "summary"):
            payload[key].update(existing.get(key, {}))

    for system_label, system_pages, chunker in systems:
        if system_label in payload["systems"]:
            logger.info("resume: skipping completed system %s", system_label)
            continue
        chunks = chunker.chunk_corpus(dict(system_pages))
        if not chunks:
            raise RuntimeError(f"{system_label}: chunker produced no chunks")
        logger.info("%s: %d pages -> %d chunks", system_label, len(system_pages), len(chunks))

        norm_series: dict[str, list[float]] = {}
        raw_series: dict[str, list[float]] = {}
        for retriever in retrievers:
            logger.info("%s: index/search with %s", system_label, retriever.name)
            retriever.index(chunks)
            results = retriever.search(qa_pairs, top_k=max(K_VALUES))
            norm, raw = metric_vectors(results, qa_pairs, normalize_for_match)
            for k in K_VALUES:
                norm_series[f"{retriever.name}__mrr@{k}"] = norm[f"mrr@{k}"]
                raw_series[f"{retriever.name}__mrr@{k}"] = raw[f"mrr@{k}"]

        norm_rcps = mean([mean(values) for values in norm_series.values()])
        raw_rcps = mean([mean(values) for values in raw_series.values()])
        payload["systems"][system_label] = norm_series
        payload["systems_raw"][system_label] = raw_series
        payload["summary"][system_label] = {
            "num_pages": len(system_pages),
            "num_chunks": len(chunks),
            "rcps_normalised": norm_rcps,
            "rcps_raw": raw_rcps,
            "normalised_minus_raw": norm_rcps - raw_rcps,
        }
        atomic_write_json(args.out, payload)
        logger.info(
            "%s complete: RCPS normalised=%.6f raw=%.6f shift=%.6f",
            system_label, norm_rcps, raw_rcps, norm_rcps - raw_rcps,
        )

    parser_keys = payload["meta"]["parser_pool"]
    chunker_keys = payload["meta"]["chunker_pool"]
    payload["rankings"] = {
        "parser_normalised": ranking(payload["summary"], parser_keys, "rcps_normalised"),
        "parser_raw": ranking(payload["summary"], parser_keys, "rcps_raw"),
        "chunker_normalised": ranking(payload["summary"], chunker_keys, "rcps_normalised"),
        "chunker_raw": ranking(payload["summary"], chunker_keys, "rcps_raw"),
    }
    payload["complete"] = True
    atomic_write_json(args.out, payload)
    logger.info("wrote complete full-grid artifact: %s", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
