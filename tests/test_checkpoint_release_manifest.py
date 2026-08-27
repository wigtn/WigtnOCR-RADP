"""CPU-only checks for the tracked checkpoint-release provenance."""

import json
from pathlib import Path

from scripts.release.build_checkpoint_release import RELEASE_REPO, VARIANTS


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/provenance/checkpoint_release_manifest.json"


def test_checkpoint_release_manifest_matches_builder_inventory() -> None:
    report = json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected = {variant["id"]: variant for variant in VARIANTS}

    assert report["status"] == "portable_checkpoint_release"
    assert report["release_repository"] == RELEASE_REPO
    assert report["num_variants"] == 9
    assert {variant["id"] for variant in report["variants"]} == set(expected)

    for released in report["variants"]:
        source = expected[released["id"]]
        assert released["source_adapter_sha256"] == source["adapter_sha256"]
        assert released["source_adapter_config_sha256"] == source["config_sha256"]
        assert released["training_base_model"] == source["training_base"]
        assert released["evaluation_base_model"] == source["evaluation_base"]
        assert released["files"]["adapter_model.safetensors"]["sha256"] == source["adapter_sha256"]

    text = MANIFEST.read_text(encoding="utf-8")
    assert "/mnt/" not in text
    assert "/home/" not in text
