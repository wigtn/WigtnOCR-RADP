"""Run the CPU-only camera-ready artifact gates from a clean checkout."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESULT_MANIFEST = ROOT / "output/results/MANIFEST.sha256"
MINERU_ON_BC = ROOT / "output/baselines/moc_bc_mineru_tableon.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_result_manifest() -> None:
    for line_number, raw in enumerate(
        RESULT_MANIFEST.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        expected, relative = line.split(maxsplit=1)
        path = (RESULT_MANIFEST.parent / relative).resolve()
        if _sha256(path) != expected:
            raise ValueError(f"manifest mismatch at line {line_number}: {relative}")


def verify_mineru_on_bc_evidence() -> None:
    report = json.loads(MINERU_ON_BC.read_text(encoding="utf-8"))
    primary = report["derived_correlations"]["BC_vs_RCPS"]
    sensitivity = report["derived_correlations"]["partial_marker_sensitivity"]
    if primary["n"] != 4 or primary["pearson_r"] != -0.7443:
        raise ValueError("MinerU-on complete-output BC correlation is stale")
    marker = sensitivity["BC_vs_RCPS"]
    if marker["n"] != 5 or marker["pearson_r"] != -0.8291:
        raise ValueError("MinerU-on + partial Marker BC sensitivity is stale")


def _run(*parts: str) -> None:
    subprocess.run(parts, cwd=ROOT, check=True)


def verify_fullgrid_aggregate(python: str) -> None:
    tracked = ROOT / "output/results/fullgrid_aggregate_audit.json"
    with tempfile.TemporaryDirectory(prefix="rcps-fullgrid-audit-") as directory:
        generated = Path(directory) / "fullgrid_aggregate_audit.json"
        _run(
            python,
            "scripts/analysis/fullgrid_aggregate_audit.py",
            "--out",
            str(generated),
        )
        if json.loads(generated.read_text(encoding="utf-8")) != json.loads(
            tracked.read_text(encoding="utf-8")
        ):
            raise ValueError("full-grid aggregate audit is stale")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--checkpoint-dir",
        type=Path,
        help="optional downloaded Wigtn checkpoint-release snapshot",
    )
    args = parser.parse_args()

    verify_result_manifest()
    verify_mineru_on_bc_evidence()
    python = sys.executable
    _run(
        python,
        "scripts/analysis/source_page_map.py",
        "--check",
        "data/KoGovDoc-RAG/source_page_map_v1.json",
    )
    _run(
        python,
        "scripts/analysis/audit_mineru_output_release.py",
        "--check",
        "output/results/mineru_output_release_audit.json",
    )
    _run(
        python,
        "scripts/analysis/audit_ohrbench_legacy_alignment.py",
        "--check",
        "output/results/ohrbench_alignment_audit.json",
    )
    _run(
        python,
        "scripts/analysis/audit_kogov_training_table.py",
        "--check",
        "output/results/kogov_training_table_10k_audit.json",
    )
    verify_fullgrid_aggregate(python)
    _run(
        python,
        "-c",
        "from tests.test_mineru_output_release import "
        "test_released_mineru_tables_off_outputs_match_submitted_aggregate as a; "
        "from tests.test_source_page_map import "
        "test_source_page_map_matches_release_inventories as b; "
        "from tests.test_checkpoint_release_manifest import "
        "test_checkpoint_release_manifest_matches_builder_inventory as c; "
        "a(); b(); c()",
    )
    if args.checkpoint_dir is not None:
        _run(
            python,
            "scripts/release/build_checkpoint_release.py",
            "--check",
            str(args.checkpoint_dir.resolve()),
        )
    print("OK: camera-ready artifact gates passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
