"""Audit the released 294-page MinerU tables-off parser outputs.

The tables-off directory is a recovered historical artifact.  This audit binds
it to the submitted-output aggregate grid without treating the tables-on/off
difference as a controlled table-recognition ablation.

Usage:
    python scripts/analysis/audit_mineru_output_release.py
    python scripts/analysis/audit_mineru_output_release.py \
        --check output/results/mineru_output_release_audit.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TABLES_OFF_ROOT = ROOT / "results/kogovdoc/mineru_val"
TABLES_ON_ROOT = ROOT / "results/kogovdoc/mineru_val_tableon"
GRID_PATH = ROOT / "output/baselines/grid_v1_parser_native.json"
DEFAULT_OUT = ROOT / "output/results/mineru_output_release_audit.json"

EXPECTED_TREE_SHA256 = "ebd32a84b8eabfe469223049d6ce9cee2027f971dc71dacdfe6a0c9949389fdb"
EXPECTED_NUM_PAGES = 294
EXPECTED_DOMAIN_COUNTS = {"arxiv": 65, "kogov": 229}
EXPECTED_AGGREGATE = {
    "dir": "mineru_val",
    "num_pages": 294,
    "num_chunks": 1050,
    "rcps": 0.21204022919709195,
    "hit@1": 0.19708396178984414,
    "hit@5": 0.25188536953242835,
    "hit@10": 0.2594268476621418,
    "mrr@10": 0.2200070626541215,
    "ndcg@10": 0.22970743291833093,
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _prediction_files(root: Path) -> list[Path]:
    return sorted((root / "predictions").glob("*.md"))


def _tree_sha256(root: Path, paths: list[Path]) -> str:
    """Hash canonical sha256sum-style records, including relative filenames."""

    digest = hashlib.sha256()
    for path in paths:
        relative = path.relative_to(root).as_posix()
        record = f"{_sha256(path)}  ./{relative}\n"
        digest.update(record.encode("utf-8"))
    return digest.hexdigest()


def _domain_counts(paths: list[Path]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for path in paths:
        domain = path.name.split("_", 1)[0]
        counts[domain] = counts.get(domain, 0) + 1
    return dict(sorted(counts.items()))


def _mineru_grid_row() -> dict[str, Any]:
    grid = json.loads(GRID_PATH.read_text(encoding="utf-8"))
    matches = [row for row in grid.get("parsers", []) if row.get("name") == "MinerU"]
    if len(matches) != 1:
        raise ValueError(f"expected one MinerU row in {GRID_PATH}, found {len(matches)}")
    row = matches[0]
    observed = {key: row.get(key) for key in EXPECTED_AGGREGATE}
    if observed != EXPECTED_AGGREGATE:
        raise ValueError(
            "MinerU aggregate does not match the submitted-output baseline: "
            f"got {observed}, expected {EXPECTED_AGGREGATE}"
        )
    return observed


def build_report() -> dict[str, Any]:
    off_files = _prediction_files(TABLES_OFF_ROOT)
    on_files = _prediction_files(TABLES_ON_ROOT)
    if len(off_files) != EXPECTED_NUM_PAGES:
        raise ValueError(f"expected {EXPECTED_NUM_PAGES} tables-off pages, got {len(off_files)}")
    if len(on_files) != EXPECTED_NUM_PAGES:
        raise ValueError(f"expected {EXPECTED_NUM_PAGES} tables-on pages, got {len(on_files)}")

    off_names = [path.name for path in off_files]
    on_names = [path.name for path in on_files]
    if off_names != on_names:
        raise ValueError("tables-off and tables-on prediction filename sets differ")

    counts = _domain_counts(off_files)
    if counts != EXPECTED_DOMAIN_COUNTS:
        raise ValueError(f"unexpected tables-off domain counts: {counts}")

    tree_sha256 = _tree_sha256(TABLES_OFF_ROOT, off_files)
    if tree_sha256 != EXPECTED_TREE_SHA256:
        raise ValueError(
            f"tables-off tree SHA-256 mismatch: got {tree_sha256}, "
            f"expected {EXPECTED_TREE_SHA256}"
        )

    sizes = [path.stat().st_size for path in off_files]
    if any(size == 0 for size in sizes):
        raise ValueError("tables-off release contains an empty prediction file")

    return {
        "schema_version": 1,
        "status": "audited_mineru_tables_off_release",
        "configuration_scope": {
            "label": "MinerU tables-off",
            "table_recognition": False,
            "interpretation": "submitted-output diagnostic, not a controlled tables-on/off ablation",
        },
        "predictions": {
            "path": TABLES_OFF_ROOT.relative_to(ROOT).as_posix() + "/predictions",
            "num_pages": len(off_files),
            "domain_counts": counts,
            "filename_set_matches_tables_on": True,
            "min_bytes": min(sizes),
            "max_bytes": max(sizes),
            "tree_sha256": tree_sha256,
        },
        "submitted_output_aggregate": {
            "source": GRID_PATH.relative_to(ROOT).as_posix(),
            "source_sha256": _sha256(GRID_PATH),
            **_mineru_grid_row(),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--check", type=Path)
    args = parser.parse_args()

    report = build_report()
    if args.check is not None:
        tracked = json.loads(args.check.read_text(encoding="utf-8"))
        if tracked != report:
            raise SystemExit(f"stale MinerU output release audit: {args.check}")
        print(f"OK: {args.check} matches the deterministic MinerU output audit")
        return 0

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
