"""CPU-only regression gate for the released MinerU tables-off outputs."""

from scripts.analysis.audit_mineru_output_release import (
    EXPECTED_TREE_SHA256,
    build_report,
)


def test_released_mineru_tables_off_outputs_match_submitted_aggregate() -> None:
    report = build_report()

    assert report["status"] == "audited_mineru_tables_off_release"
    assert report["configuration_scope"]["table_recognition"] is False
    assert report["predictions"] == {
        "path": "results/kogovdoc/mineru_val/predictions",
        "num_pages": 294,
        "domain_counts": {"arxiv": 65, "kogov": 229},
        "filename_set_matches_tables_on": True,
        "min_bytes": 6,
        "max_bytes": 7453,
        "tree_sha256": EXPECTED_TREE_SHA256,
    }
    assert report["submitted_output_aggregate"]["dir"] == "mineru_val"
    assert report["submitted_output_aggregate"]["num_pages"] == 294
    assert report["submitted_output_aggregate"]["num_chunks"] == 1050
    assert report["submitted_output_aggregate"]["rcps"] == 0.21204022919709195
    assert report["submitted_output_aggregate"]["hit@1"] == 0.19708396178984414
