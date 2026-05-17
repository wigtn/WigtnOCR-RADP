"""Language and metadata heuristics for KoGovDoc-Bench pages."""

from __future__ import annotations


def detect_language(text: str) -> str:
    """Heuristic language detection over a piece of text.

    Returns one of: 'ko', 'en', 'mixed'.
    """
    ko = sum(1 for c in text if "가" <= c <= "힯")
    en = sum(1 for c in text if "a" <= c.lower() <= "z")
    if ko > en:
        return "ko"
    if en > ko * 2:
        return "en"
    return "mixed"


def infer_domain(image_path: str) -> str:
    """Infer source domain from a KoGovDoc-Bench image path."""
    if "documents" in image_path:
        return "kogov"
    if "papers" in image_path:
        return "arxiv"
    return "unknown"


def derive_doc_id(image_path: str) -> str:
    """Derive a stable document identifier from a KoGovDoc-Bench image path.

    Example:
        '/.../images/documents/kogov_008/page_0544.png' -> 'kogov_008'
    """
    parts = image_path.split("/")
    for i, p in enumerate(parts):
        if p in ("documents", "papers") and i + 1 < len(parts):
            return parts[i + 1]
    return "unknown"
