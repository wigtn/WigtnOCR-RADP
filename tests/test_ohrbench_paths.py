"""Focused tests for OHR-Bench cross-release path resolution and coverage."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from wigtnocr_radp.ohrbench_paths import (
    EvidencePageCoverageError,
    build_document_index,
    ohr_page_id,
    require_evidence_page_coverage,
    resolve_document_files,
)


@dataclass(frozen=True)
class _QA:
    qa_id: str
    page_id: str


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
