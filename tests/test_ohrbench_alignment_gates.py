"""CPU-only tests for the legacy OHR compatibility lineage gates."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.evaluation.ohrbench_combined_ci import load_ohr_perqa
from scripts.evaluation.ohrbench_v1dpo_full import (
    apply_strict_compatibility_mask,
    require_non_destructive_output,
)
from wigtnocr_radp.evaluation.types import QAPair


def _qa(qa_id: str, domain: str) -> QAPair:
    return QAPair(
        qa_id=qa_id,
        page_id=f"{qa_id}__p0",
        doc_id=qa_id,
        language="en",
        domain=domain,
        question=f"question {qa_id}",
        answer_span=f"answer {qa_id}",
        answer_chunk="",
        question_type="text",
        difficulty="medium",
    )


def _audit(source_path: Path, digest: str) -> dict:
    return {
        "status": "corrected_legacy_compatibility_subset_not_full_v2",
        "source_artifacts": {source_path.name: digest},
        "c4_strict_compatibility_subset": {
            "source_num_qa": 4,
            "num_qa": 2,
            "domain_counts": {"law": 1, "manual": 1},
            "excluded": {
                "legacy_notes_zero_rows": 1,
                "missing_v2_page": "missing__p0",
                "missing_v2_page_num_qa": 1,
                "missing_v2_page_qa_ids": ["q-missing"],
            },
        },
    }


def _write_source(path: Path, *, short_metric: bool = False) -> dict:
    artifact = {
        "qa_ids": ["q-law", "q-notes", "q-missing", "q-manual"],
        "domains": ["law", "notes", "textbook", "manual"],
        "meta": {"n_qa": 4, "retrievers": ["r"], "k_values": [1]},
        "models": {"v1": {"mrr@1__r": [0.1, 0.2, 0.3, 0.4]}},
    }
    if short_metric:
        artifact["models"]["v1"]["mrr@1__r"].pop()
    path.write_text(json.dumps(artifact), encoding="utf-8")
    return artifact


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_combined_ci_binds_source_hash_and_qa_order(tmp_path: Path) -> None:
    source = tmp_path / "source.json"
    _write_source(source)
    audit_path = tmp_path / "audit.json"
    audit_path.write_text(json.dumps(_audit(source, _digest(source))), encoding="utf-8")

    loaded = load_ohr_perqa(source, audit_path)

    assert loaded["v1"][("mrr", "r", 1)].tolist() == [0.1, 0.4]

    source.write_text(source.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="SHA-256 does not match"):
        load_ohr_perqa(source, audit_path)


def test_combined_ci_rejects_metric_array_not_in_qa_order(tmp_path: Path) -> None:
    source = tmp_path / "source.json"
    _write_source(source, short_metric=True)
    audit_path = tmp_path / "audit.json"
    audit_path.write_text(json.dumps(_audit(source, _digest(source))), encoding="utf-8")

    with pytest.raises(ValueError, match="expected 4 in qa_ids order"):
        load_ohr_perqa(source, audit_path)


def test_strict_regeneration_filter_and_overwrite_guard(tmp_path: Path) -> None:
    source = tmp_path / "source.json"
    audit = _audit(source, "unused")
    pairs = [
        _qa("q-law", "law"),
        _qa("q-notes", "notes"),
        _qa("q-missing", "textbook"),
        _qa("q-manual", "manual"),
    ]

    filtered = apply_strict_compatibility_mask(pairs, audit)

    assert [qa.qa_id for qa in filtered] == ["q-law", "q-manual"]
    with pytest.raises(ValueError, match="refusing to overwrite"):
        require_non_destructive_output(tmp_path / "source.json", audit)
