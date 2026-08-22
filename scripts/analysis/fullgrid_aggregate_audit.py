"""Audit claims recoverable from the stored 294-page aggregate grids.

This script does not load an embedding model.  It verifies the stored RCPS and
MRR@10 aggregates, compares their induced rankings, and records the important
coverage limitation that Marker has outputs for only 38 of the 294 pages.

It deliberately does *not* perform probe resampling: the baseline grid stores
aggregate metrics, not the per-Q--A vectors required for a bootstrap.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PARSER_GRID = ROOT / "output/baselines/grid_v1_parser_native.json"
DEFAULT_CHUNKER_GRID = ROOT / "output/baselines/chunking_grid_v1.json"
DEFAULT_OUT = ROOT / "output/results/fullgrid_aggregate_audit.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ranking(rows: list[dict[str, Any]], name_key: str, metric: str) -> list[str]:
    return [
        str(row[name_key])
        for row in sorted(rows, key=lambda row: (-float(row[metric]), str(row[name_key])))
    ]


def inversion_pairs(reference: list[str], candidate: list[str]) -> list[list[str]]:
    pos = {name: idx for idx, name in enumerate(candidate)}
    pairs: list[list[str]] = []
    for i, left in enumerate(reference):
        for right in reference[i + 1 :]:
            if pos[left] > pos[right]:
                pairs.append([left, right])
    return pairs


def compare_rankings(rows: list[dict[str, Any]], name_key: str) -> dict[str, Any]:
    rcps = ranking(rows, name_key, "rcps")
    mrr10 = ranking(rows, name_key, "mrr@10")
    inversions = inversion_pairs(rcps, mrr10)
    n = len(rcps)
    n_pairs = n * (n - 1) // 2
    tau = 1.0 if n_pairs == 0 else 1.0 - 2.0 * len(inversions) / n_pairs
    return {
        "n_candidates": n,
        "rcps_ranking": rcps,
        "mrr_at_10_only_ranking": mrr10,
        "same_order": rcps == mrr10,
        "inversions": inversions,
        "kendall_tau_a": tau,
        "scores": {
            str(row[name_key]): {
                "rcps": float(row["rcps"]),
                "mrr_at_10_only": float(row["mrr@10"]),
            }
            for row in rows
        },
    }


def validate_parser_grid(grid: dict[str, Any]) -> list[str]:
    retrievers = grid["config"]["retrievers"]
    checks: list[str] = []
    for row in grid["parsers"]:
        by_retriever = row["by_retriever"]
        reconstructed_rcps = sum(
            float(by_retriever[retriever]["mrr"][str(k)])
            for retriever in retrievers
            for k in (1, 5, 10)
        ) / (len(retrievers) * 3)
        reconstructed_mrr10 = sum(
            float(by_retriever[retriever]["mrr"]["10"]) for retriever in retrievers
        ) / len(retrievers)
        if abs(reconstructed_rcps - float(row["rcps"])) > 1e-12:
            raise ValueError(f"{row['name']}: stored RCPS fails reconstruction")
        if abs(reconstructed_mrr10 - float(row["mrr@10"])) > 1e-12:
            raise ValueError(f"{row['name']}: stored MRR@10 fails reconstruction")
        checks.append(str(row["name"]))
    return checks


def validate_chunker_grid(grid: dict[str, Any]) -> list[str]:
    retrievers = grid["config"]["retrievers"]
    checks: list[str] = []
    for row in grid["chunkers"]:
        by_retriever = row["by_retriever"]
        reconstructed_rcps = sum(
            float(by_retriever[retriever]["mrr"][str(k)])
            for retriever in retrievers
            for k in (1, 5, 10)
        ) / (len(retrievers) * 3)
        reconstructed_mrr10 = sum(
            float(by_retriever[retriever]["mrr"]["10"]) for retriever in retrievers
        ) / len(retrievers)
        if abs(reconstructed_rcps - float(row["rcps"])) > 1e-12:
            raise ValueError(f"{row['chunker']}: stored RCPS fails reconstruction")
        if abs(reconstructed_mrr10 - float(row["mrr@10"])) > 1e-12:
            raise ValueError(f"{row['chunker']}: stored MRR@10 fails reconstruction")
        checks.append(str(row["chunker"]))
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--parser-grid", type=Path, default=DEFAULT_PARSER_GRID)
    parser.add_argument("--chunker-grid", type=Path, default=DEFAULT_CHUNKER_GRID)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    parser_grid = json.loads(args.parser_grid.read_text(encoding="utf-8"))
    chunker_grid = json.loads(args.chunker_grid.read_text(encoding="utf-8"))
    checked_parsers = validate_parser_grid(parser_grid)
    checked_chunkers = validate_chunker_grid(chunker_grid)

    parser_rows = parser_grid["parsers"]
    full_page_rows = [row for row in parser_rows if int(row["num_pages"]) == 294]
    partial_rows = [row for row in parser_rows if int(row["num_pages"]) != 294]

    if int(parser_grid["config"]["num_qa"]) != 663:
        raise ValueError("parser grid is not the frozen 663-Q--A probe")
    if int(chunker_grid["config"]["num_qa"]) != 663:
        raise ValueError("chunker grid is not the frozen 663-Q--A probe")
    if int(chunker_grid["config"]["num_pages"]) != 294:
        raise ValueError("chunker grid is not the 294-page corpus")
    if parser_grid["config"]["retrievers"] != chunker_grid["config"]["retrievers"]:
        raise ValueError("parser and chunker grids use different retrievers")

    report = {
        "scope": {
            "num_qa": 663,
            "num_pages": 294,
            "retrievers": parser_grid["config"]["retrievers"],
            "rcps_definition": "mean MRR over 3 retrievers and k={1,5,10}",
            "mrr_at_10_only_definition": "mean MRR@10 over the same 3 retrievers",
        },
        "inputs": {
            "parser_grid": {
                "path": str(args.parser_grid.relative_to(ROOT)),
                "sha256": sha256(args.parser_grid),
            },
            "chunker_grid": {
                "path": str(args.chunker_grid.relative_to(ROOT)),
                "sha256": sha256(args.chunker_grid),
            },
        },
        "reconstruction_checks": {
            "parsers": checked_parsers,
            "chunkers": checked_chunkers,
            "status": "passed",
        },
        "parser_ranking_all_stored_rows": compare_rankings(parser_rows, "name"),
        "parser_ranking_294_page_rows_only": compare_rankings(full_page_rows, "name"),
        "chunker_ranking": compare_rankings(chunker_grid["chunkers"], "chunker"),
        "coverage": {
            "full_294_page_parsers": [str(row["name"]) for row in full_page_rows],
            "partial_parsers": {
                str(row["name"]): int(row["num_pages"]) for row in partial_rows
            },
        },
        "verdict": {
            "mrr_at_10_only_order_unchanged_for_all_stored_parser_rows": compare_rankings(
                parser_rows, "name"
            )["same_order"],
            "mrr_at_10_only_order_unchanged_for_294_page_parsers": compare_rankings(
                full_page_rows, "name"
            )["same_order"],
            "mrr_at_10_only_order_unchanged_for_chunkers": compare_rankings(
                chunker_grid["chunkers"], "chunker"
            )["same_order"],
        },
        "limitations": [
            "The stored baseline grids contain aggregate metrics, not aligned per-Q--A vectors; this report cannot establish probe-resampling stability.",
            "Marker has outputs for 38 pages, so the five-parser 294-page ranking is the coverage-comparable parser result.",
            "The stored metrics use format-normalised relevance; format-sensitive relevance cannot be reconstructed without ranked chunk lists or re-indexing.",
        ],
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.out}")
    print("parser all same order:", report["verdict"]["mrr_at_10_only_order_unchanged_for_all_stored_parser_rows"])
    print("parser 294p same order:", report["verdict"]["mrr_at_10_only_order_unchanged_for_294_page_parsers"])
    print("chunker same order:", report["verdict"]["mrr_at_10_only_order_unchanged_for_chunkers"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
