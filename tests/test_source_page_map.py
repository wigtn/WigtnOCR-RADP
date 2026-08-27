"""CPU-only regression gate for the portable KoGovDoc-RAG page map."""

import json
from pathlib import Path

from scripts.analysis.source_page_map import EXPECTED_SOURCE_SHA256, ROOT, validate_map


MAP_PATH = ROOT / "data/KoGovDoc-RAG/source_page_map_v1.json"
def test_source_page_map_matches_release_inventories() -> None:
    report = json.loads(MAP_PATH.read_text(encoding="utf-8"))

    assert report["schema_version"] == 1
    assert report["source_metadata"]["sha256"] == EXPECTED_SOURCE_SHA256
    assert report["validation"] == validate_map(report)
    assert report["validation"]["num_pages"] == 294
    assert report["validation"]["num_evidence_pages"] == 242
    assert report["validation"]["num_distractor_pages"] == 52
    assert report["validation"]["domain_counts"] == {"arxiv": 65, "kogov": 229}

    for page in report["pages"]:
        filename = page["parser_output_file"]
        assert Path(filename).name == filename
        assert set(page) == {"page_id", "domain", "parser_output_file"}
