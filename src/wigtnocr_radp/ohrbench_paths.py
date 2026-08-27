"""Path and coverage helpers for versioned OHR-Bench releases.

The original Q-A parquet and the expanded v2 document release do not always
store the same document under the same domain directory.  Document basenames,
however, are stable and globally unique in the v2 release.  These helpers make
that identity explicit and prevent a missing evidence page from being scored as
an ordinary retrieval miss.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Protocol


# Historical OHR artifacts are immutable provenance.  Some are deterministic
# audit inputs and others are explicitly quarantined mixed-release summaries.
# Protect by basename as well as path so redirecting an old producer to a new
# directory cannot create a deceptively named replacement.
PROTECTED_OHR_RESULT_BASENAMES = frozenset(
    {
        "combined_kogov_ohr_ci.json",
        "ohr_text_ned.json",
        "ohr_v5_ci.json",
        "ohr_v5_perqa.json",
        "ohrbench_7dom_bc.json",
        "ohrbench_7dom_rcps.json",
        "ohrbench_alignment_audit.json",
        "ohrbench_bc_noise.json",
        "ohrbench_crossdomain.json",
        "ohrbench_noise.json",
        "ohrbench_per_domain.json",
        "ohrbench_v1dpo_ci.json",
        "ohrbench_v1dpo_perqa.json",
    }
)

COMPATIBILITY_OUTPUT_MARKERS = ("compat", "strict")

LEGACY_OHR_ALIGNMENT_AUDIT_STATUS = (
    "corrected_legacy_compatibility_subset_not_full_v2"
)
ALIGNED_DISTILL_OHR_ALIGNMENT_AUDIT_STATUS = (
    "audited_legacy_compatibility_subset_with_aligned_distill_not_full_v2"
)
SUPPORTED_OHR_ALIGNMENT_AUDIT_STATUSES = frozenset(
    {
        LEGACY_OHR_ALIGNMENT_AUDIT_STATUS,
        ALIGNED_DISTILL_OHR_ALIGNMENT_AUDIT_STATUS,
    }
)


class EvidencePair(Protocol):
    """Minimal Q-A shape required by the evidence-page coverage gate."""

    @property
    def qa_id(self) -> str:
        ...

    @property
    def page_id(self) -> str:
        ...


class EvidencePageCoverageError(RuntimeError):
    """Raised when an evaluation corpus omits a Q-A evidence page."""


def require_supported_ohr_alignment_audit(
    audit: Mapping[str, object],
    *,
    path: Path,
) -> None:
    """Accept the legacy audit and its schema-2 aligned-Distill successor."""

    if audit.get("status") not in SUPPORTED_OHR_ALIGNMENT_AUDIT_STATUSES:
        raise ValueError(f"unsupported OHR alignment audit status: {path}")


def require_compatibility_output_path(path: Path) -> None:
    """Reject legacy artifact names and ambiguous OHR result filenames.

    Corrected legacy-QA runs must advertise ``compat`` or ``strict`` in every
    result filename.  This prevents an otherwise valid rerun from silently
    replacing either a quarantined summary or one of the immutable arrays used
    by the tracked alignment audit.
    """

    if path.suffix.lower() not in {".json", ".md"}:
        raise ValueError(f"OHR compatibility output must be JSON or Markdown: {path}")
    if path.name in PROTECTED_OHR_RESULT_BASENAMES:
        raise ValueError(f"refusing to overwrite protected OHR artifact: {path}")
    lowered = path.name.lower()
    if not any(marker in lowered for marker in COMPATIBILITY_OUTPUT_MARKERS):
        raise ValueError(
            f"corrected legacy OHR output must include one of "
            f"{COMPATIBILITY_OUTPUT_MARKERS} in its filename: {path}"
        )


def require_compatibility_cache_path(path: Path) -> None:
    """Keep corrected parser/PNG caches separate from legacy mixed-release caches."""

    lowered_parts = {part.lower() for part in path.parts}
    if "parses_ohrbench" in lowered_parts or "ohrbench_pngs" in lowered_parts:
        raise ValueError(f"refusing to write corrected data into a legacy OHR cache: {path}")
    if not any("compat" in part or "strict" in part for part in lowered_parts):
        raise ValueError(f"corrected OHR cache path must be explicitly compat/strict: {path}")


def document_basename(doc_name: str) -> str:
    """Return the stable document identifier, ignoring its release-specific domain."""

    return str(doc_name).rsplit("/", 1)[-1]


def ohr_page_id(doc_name: str, page_idx: int) -> str:
    """Canonical OHR page ID shared by parquet rows, PDFs, JSON, and parses."""

    return f"{document_basename(doc_name)}__p{int(page_idx)}"


def build_document_index(root: Path, suffix: str) -> dict[str, Path]:
    """Index document files below ``root`` by globally unique basename.

    Domain directories are deliberately ignored.  Ambiguous basenames fail
    closed because silently choosing one release copy would corrupt relevance
    labels in exactly the same way as a missing page.
    """

    if not suffix.startswith("."):
        raise ValueError(f"suffix must start with '.': {suffix!r}")
    if not root.is_dir():
        raise FileNotFoundError(f"document root does not exist: {root}")

    index: dict[str, Path] = {}
    for path in sorted(root.rglob(f"*{suffix}")):
        if not path.is_file():
            continue
        basename = path.name[: -len(suffix)]
        previous = index.get(basename)
        if previous is not None and previous != path:
            raise ValueError(
                f"ambiguous OHR document basename {basename!r}: {previous} and {path}"
            )
        index[basename] = path
    return index


def resolve_document_files(
    root: Path,
    document_names: Iterable[str],
    *,
    suffix: str,
) -> tuple[dict[str, Path], tuple[str, ...]]:
    """Resolve logical document names across every physical domain folder.

    Returns ``(resolved, missing)`` so callers that prepare a cache can report
    source gaps, while the evaluation-time evidence gate remains responsible
    for deciding whether a gap invalidates a Q-A score.
    """

    index = build_document_index(root, suffix)
    basenames = sorted(
        {
            base[: -len(suffix)] if base.endswith(suffix) else base
            for name in document_names
            for base in (document_basename(name),)
        }
    )
    resolved = {name: index[name] for name in basenames if name in index}
    missing = tuple(name for name in basenames if name not in index)
    return resolved, missing


def require_evidence_page_coverage(
    qa_pairs: Iterable[EvidencePair],
    parsed_pages: Mapping[str, object] | Iterable[str],
    *,
    label: str,
) -> None:
    """Fail before retrieval if any Q-A evidence page has no parsed page.

    Missing parser *content* is a legitimate model error.  Missing parser
    *pages* are an evaluation-integrity error and must never be converted into
    zero-valued retrieval observations.
    """

    qa_list = list(qa_pairs)
    parsed_ids = set(parsed_pages.keys() if isinstance(parsed_pages, Mapping) else parsed_pages)
    expected_ids = {qa.page_id for qa in qa_list}
    missing_ids = sorted(expected_ids - parsed_ids)
    if not missing_ids:
        return

    missing_set = set(missing_ids)
    affected_qas = [qa.qa_id for qa in qa_list if qa.page_id in missing_set]
    sample_pages = ", ".join(missing_ids[:5])
    sample_qas = ", ".join(affected_qas[:5])
    raise EvidencePageCoverageError(
        f"{label}: missing {len(missing_ids)}/{len(expected_ids)} evidence pages "
        f"affecting {len(affected_qas)}/{len(qa_list)} Q-A; "
        f"page sample=[{sample_pages}]; qa sample=[{sample_qas}]"
    )
