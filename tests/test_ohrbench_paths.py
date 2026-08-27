"""Focused tests for OHR-Bench cross-release path resolution and coverage."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from wigtnocr_radp.ohrbench_paths import (
    ALIGNED_DISTILL_OHR_ALIGNMENT_AUDIT_STATUS,
    EvidencePageCoverageError,
    LEGACY_OHR_ALIGNMENT_AUDIT_STATUS,
    PROTECTED_OHR_RESULT_BASENAMES,
    build_document_index,
    ohr_page_id,
    require_compatibility_cache_path,
    require_compatibility_output_path,
    require_evidence_page_coverage,
    require_supported_ohr_alignment_audit,
    resolve_document_files,
)


@dataclass(frozen=True)
class _QA:
    qa_id: str
    page_id: str


@pytest.mark.parametrize(
    "status",
    [
        LEGACY_OHR_ALIGNMENT_AUDIT_STATUS,
        ALIGNED_DISTILL_OHR_ALIGNMENT_AUDIT_STATUS,
    ],
)
def test_alignment_audit_accepts_legacy_and_aligned_distill_statuses(status: str) -> None:
    require_supported_ohr_alignment_audit(
        {"status": status},
        path=Path("output/results/ohrbench_alignment_audit.json"),
    )


def test_alignment_audit_rejects_unknown_status() -> None:
    with pytest.raises(ValueError, match="unsupported OHR alignment audit status"):
        require_supported_ohr_alignment_audit(
            {"status": "full_v2_unverified"},
            path=Path("output/results/ohrbench_alignment_audit.json"),
        )


def _touch(path: Path, text: str = "[]") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_resolves_old_notes_document_from_v2_textbook_folder(tmp_path: Path) -> None:
    expected = tmp_path / "textbook" / "GNHK_eng_AF_004.json"
    _touch(expected)
    _touch(tmp_path / "administration" / "DUDE_022e4264.json")

    resolved, missing = resolve_document_files(
        tmp_path,
        ["notes/GNHK_eng_AF_004"],
        suffix=".json",
    )

    assert resolved == {"GNHK_eng_AF_004": expected}
    assert missing == ()


def test_resolves_document_name_that_already_has_suffix(tmp_path: Path) -> None:
    expected = tmp_path / "law" / "manual.pdf"
    _touch(expected)

    resolved, missing = resolve_document_files(
        tmp_path,
        ["law/manual.pdf"],
        suffix=".pdf",
    )

    assert resolved == {"manual": expected}
    assert missing == ()


def test_document_index_rejects_ambiguous_basename(tmp_path: Path) -> None:
    _touch(tmp_path / "textbook" / "same.json")
    _touch(tmp_path / "administration" / "same.json")

    with pytest.raises(ValueError, match="ambiguous OHR document basename"):
        build_document_index(tmp_path, ".json")


def test_page_id_ignores_release_specific_domain() -> None:
    assert ohr_page_id("notes/GNHK_eng_AF_004", 0) == "GNHK_eng_AF_004__p0"
    assert ohr_page_id("textbook/GNHK_eng_AF_004", 0) == "GNHK_eng_AF_004__p0"


def test_coverage_gate_accepts_complete_evidence_pages() -> None:
    qa = [_QA("q1", "doc_a__p0"), _QA("q2", "doc_b__p3")]
    require_evidence_page_coverage(
        qa,
        {"doc_a__p0": "text", "doc_b__p3": ""},
        label="parser=v1",
    )


def test_coverage_gate_fails_with_page_and_qa_counts() -> None:
    qa = [
        _QA("q1", "doc_a__p0"),
        _QA("q2", "missing__p0"),
        _QA("q3", "missing__p0"),
    ]

    with pytest.raises(EvidencePageCoverageError) as exc:
        require_evidence_page_coverage(qa, {"doc_a__p0": "text"}, label="parser=R2")

    message = str(exc.value)
    assert "parser=R2" in message
    assert "missing 1/2 evidence pages" in message
    assert "affecting 2/3 Q-A" in message
    assert "missing__p0" in message
    assert "q2" in message


@pytest.mark.parametrize("basename", sorted(PROTECTED_OHR_RESULT_BASENAMES))
def test_output_gate_rejects_every_protected_result_basename(basename: str) -> None:
    with pytest.raises(ValueError, match="protected OHR artifact"):
        require_compatibility_output_path(Path("some/new/directory") / basename)


def test_output_gate_requires_explicit_compatibility_marker() -> None:
    with pytest.raises(ValueError, match="must include"):
        require_compatibility_output_path(Path("output/results/ohrbench_new.json"))

    require_compatibility_output_path(
        Path("output/results/ohrbench_law_manual_compat_rcps.json")
    )
    require_compatibility_output_path(
        Path("output/results/ohrbench_v1dpo_strict2036_ci.json")
    )


def test_cache_gate_separates_compatibility_and_legacy_cache_roots() -> None:
    with pytest.raises(ValueError, match="legacy OHR cache"):
        require_compatibility_cache_path(Path("output/parses_ohrbench"))
    with pytest.raises(ValueError, match="explicitly compat/strict"):
        require_compatibility_cache_path(Path("output/new_ohr_parses"))

    require_compatibility_cache_path(Path("output/parses_ohrbench_compat2036"))
