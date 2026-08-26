"""Unit tests for scripts/evaluation/compute_parser_bc.py.

Everything here runs on CPU with no model download: the LM is replaced by a
deterministic fake scorer, so the tests pin the *bookkeeping* — boundary
enumeration, aggregation, input validation, manifest hashing and JSON
strictness — which is what has to stay identical to the original BC run.
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import pytest

from wigtnocr_radp.evaluation.chunkers import ParserNativeChunker

# scripts/ is not an importable package, so load the script by path. It must be
# registered in sys.modules before exec_module or its @dataclass fails.
_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "evaluation" / "compute_parser_bc.py"
_spec = importlib.util.spec_from_file_location("compute_parser_bc", _SCRIPT)
assert _spec is not None and _spec.loader is not None
cpb = importlib.util.module_from_spec(_spec)
sys.modules["compute_parser_bc"] = cpb
_spec.loader.exec_module(cpb)


CHUNK_A = "A" * 40
CHUNK_B = "B" * 40
CHUNK_C = "C" * 40
CHUNK_D = "D" * 40


def _chunker() -> ParserNativeChunker:
    return ParserNativeChunker(min_chars=30)


def _page(*chunks: str) -> str:
    return "\n\n".join(chunks)


# --------------------------------------------------------------------------
# boundary enumeration: within-page adjacency only
# --------------------------------------------------------------------------


def test_only_adjacent_within_page_pairs_are_formed():
    pages = [("p1", _page(CHUNK_A, CHUNK_B, CHUNK_C))]
    bounds, stats = cpb.enumerate_boundaries(pages, _chunker())

    assert [(b.page_id, b.index) for b in bounds] == [("p1", 0), ("p1", 1)]
    # each boundary joins chunk i to chunk i+1 — never i to i+2
    assert (bounds[0].prev_text, bounds[0].next_text) == (CHUNK_A, CHUNK_B)
    assert (bounds[1].prev_text, bounds[1].next_text) == (CHUNK_B, CHUNK_C)
    assert stats[0]["num_chunks"] == 3
    assert stats[0]["num_boundaries_attempted"] == 2


def test_no_boundary_is_formed_across_a_page_break():
    pages = [("p1", _page(CHUNK_A, CHUNK_B)), ("p2", _page(CHUNK_C, CHUNK_D))]
    bounds, _ = cpb.enumerate_boundaries(pages, _chunker())

    pairs = [(b.page_id, b.prev_text, b.next_text) for b in bounds]
    assert pairs == [("p1", CHUNK_A, CHUNK_B), ("p2", CHUNK_C, CHUNK_D)]
    # the p1-last -> p2-first pair must not exist
    assert (CHUNK_B, CHUNK_C) not in [(b.prev_text, b.next_text) for b in bounds]


def test_single_chunk_page_contributes_no_boundary():
    pages = [("p1", CHUNK_A), ("p2", _page(CHUNK_B, CHUNK_C))]
    bounds, stats = cpb.enumerate_boundaries(pages, _chunker())

    assert len(bounds) == 1
    assert bounds[0].page_id == "p2"
    assert stats[0]["num_boundaries_attempted"] == 0


def test_boundary_count_equals_chunks_minus_pages_with_chunks():
    pages = [
        ("p1", _page(CHUNK_A, CHUNK_B, CHUNK_C)),
        ("p2", CHUNK_A),
        ("p3", _page(CHUNK_A, CHUNK_B)),
    ]
    bounds, stats = cpb.enumerate_boundaries(pages, _chunker())
    num_chunks = sum(r["num_chunks"] for r in stats)
    pages_with_chunks = sum(1 for r in stats if r["num_chunks"] > 0)

    assert num_chunks == 6
    assert len(bounds) == num_chunks - pages_with_chunks == 3


# --------------------------------------------------------------------------
# aggregation: unweighted mean over boundaries, not mean of per-page means
# --------------------------------------------------------------------------


def _scores(spec: list[tuple[str, int, float | None]]) -> list[cpb.BoundaryScore]:
    return [
        cpb.BoundaryScore(key=f"{p}#{i}", page_id=p, index=i, bc=v, skip_reason=None if v is not None else "nan")
        for p, i, v in spec
    ]


def test_mean_is_weighted_by_boundary_count_not_by_page():
    # p1 has 3 boundaries at 0.9, p2 has 1 boundary at 0.1.
    # boundary-weighted mean = (0.9*3 + 0.1) / 4 = 0.70
    # mean-of-page-means     = (0.9 + 0.1) / 2   = 0.50   <- must NOT be this
    scores = _scores([("p1", 0, 0.9), ("p1", 1, 0.9), ("p1", 2, 0.9), ("p2", 0, 0.1)])
    page_stats = [
        {"page_id": "p1", "num_chunks": 4, "num_boundaries_attempted": 3, "num_boundaries_valid": 0, "mean_bc": None},
        {"page_id": "p2", "num_chunks": 2, "num_boundaries_attempted": 1, "num_boundaries_valid": 0, "mean_bc": None},
    ]
    summary, per_page, _ = cpb.summarize(scores, page_stats)

    assert summary["mean_bc"] == pytest.approx(0.70)
    assert summary["mean_bc"] != pytest.approx(0.50)
    assert per_page[0]["mean_bc"] == pytest.approx(0.9)
    assert per_page[1]["mean_bc"] == pytest.approx(0.1)
    assert summary["num_boundaries_valid"] == 4


def test_bc_is_not_clamped_to_unit_interval():
    scores = _scores([("p1", 0, 1.8), ("p1", 1, 0.2)])
    page_stats = [
        {"page_id": "p1", "num_chunks": 3, "num_boundaries_attempted": 2, "num_boundaries_valid": 0, "mean_bc": None}
    ]
    summary, _, _ = cpb.summarize(scores, page_stats)

    assert summary["max_bc"] == pytest.approx(1.8)
    assert summary["mean_bc"] == pytest.approx(1.0)


def test_invalid_values_are_counted_with_a_reason_not_silently_dropped():
    scores = [
        cpb.BoundaryScore("p1#0", "p1", 0, 0.5, None),
        cpb.BoundaryScore("p1#1", "p1", 1, None, "scorer_returned_none"),
        cpb.BoundaryScore("p1#2", "p1", 2, None, "nan"),
    ]
    page_stats = [
        {"page_id": "p1", "num_chunks": 4, "num_boundaries_attempted": 3, "num_boundaries_valid": 0, "mean_bc": None}
    ]
    summary, _, reasons = cpb.summarize(scores, page_stats)

    assert summary["num_boundaries_attempted"] == 3
    assert summary["num_boundaries_valid"] == 1
    assert summary["num_boundaries_skipped"] == 2
    assert reasons == {"scorer_returned_none": 1, "nan": 1}
    assert summary["mean_bc"] == pytest.approx(0.5)


def test_classify_rejects_nan_and_inf():
    assert cpb._classify(float("nan")) == (None, "nan")
    assert cpb._classify(float("inf")) == (None, "inf")
    assert cpb._classify(None) == (None, "scorer_returned_none")
    assert cpb._classify(0.42) == (0.42, None)


# --------------------------------------------------------------------------
# input validation
# --------------------------------------------------------------------------


def test_validate_inputs_accepts_matching_counts():
    cpb.validate_inputs(num_pages=294, num_chunks=903, expected_pages=294, expected_chunks=903)


def test_validate_inputs_fails_on_page_count_mismatch():
    with pytest.raises(ValueError, match="prediction file count mismatch"):
        cpb.validate_inputs(num_pages=293, num_chunks=903, expected_pages=294, expected_chunks=903)


def test_validate_inputs_fails_on_chunk_count_mismatch():
    with pytest.raises(ValueError, match="chunk count mismatch"):
        cpb.validate_inputs(num_pages=294, num_chunks=902, expected_pages=294, expected_chunks=903)


def test_validate_inputs_skips_checks_when_expectations_are_absent():
    cpb.validate_inputs(num_pages=7, num_chunks=9, expected_pages=None, expected_chunks=None)


def test_validate_reference_inputs_fails_before_model_load(tmp_path):
    missing = tmp_path / "missing.json"
    with pytest.raises(FileNotFoundError, match="reference files are missing"):
        cpb.validate_reference_inputs([missing])


# --------------------------------------------------------------------------
# manifest hashing
# --------------------------------------------------------------------------


def _write_pages(root: Path, contents: dict[str, str]) -> Path:
    d = root / "predictions"
    d.mkdir(parents=True, exist_ok=True)
    for name, text in contents.items():
        (d / name).write_text(text, encoding="utf-8")
    return d


def test_manifest_hash_is_deterministic_for_identical_input(tmp_path):
    contents = {"b.md": "beta\n\n" + CHUNK_B, "a.md": "alpha\n\n" + CHUNK_A}
    d1 = _write_pages(tmp_path / "one", contents)
    d2 = _write_pages(tmp_path / "two", contents)

    h1 = cpb.manifest_sha256(cpb.list_prediction_files(d1), root=tmp_path / "one")
    h2 = cpb.manifest_sha256(cpb.list_prediction_files(d2), root=tmp_path / "two")
    h1_again = cpb.manifest_sha256(cpb.list_prediction_files(d1), root=tmp_path / "one")

    assert h1 == h1_again
    assert h1 == h2  # same relative paths + same bytes -> same hash


def test_manifest_hash_changes_when_content_changes(tmp_path):
    d = _write_pages(tmp_path, {"a.md": "alpha"})
    before = cpb.manifest_sha256(cpb.list_prediction_files(d), root=tmp_path)
    (d / "a.md").write_text("alpha!", encoding="utf-8")
    after = cpb.manifest_sha256(cpb.list_prediction_files(d), root=tmp_path)

    assert before != after


def test_prediction_files_are_sorted_and_hash_ignores_input_order(tmp_path):
    d = _write_pages(tmp_path, {"z.md": "z", "a.md": "a", "m.md": "m"})
    files = cpb.list_prediction_files(d)

    # discovery always sorts, whatever order the filesystem hands back
    assert [f.name for f in files] == ["a.md", "m.md", "z.md"]
    # and hashing a shuffled list re-sorted gives the same digest
    shuffled = [files[2], files[0], files[1]]
    assert cpb.manifest_sha256(files, root=tmp_path) == cpb.manifest_sha256(
        sorted(shuffled, key=lambda f: f.name), root=tmp_path
    )


def test_as_repo_relative_never_leaks_an_absolute_path(tmp_path):
    outside = tmp_path / "somewhere" / "x.md"
    outside.parent.mkdir(parents=True)
    outside.write_text("x", encoding="utf-8")

    rel = cpb.as_repo_relative(outside)
    assert not rel.startswith("/")
    assert "home" not in rel


# --------------------------------------------------------------------------
# JSON strictness
# --------------------------------------------------------------------------


def test_dumps_strict_rejects_nan():
    with pytest.raises(ValueError):
        cpb.dumps_strict({"mean_bc": float("nan")})


def test_dumps_strict_rejects_infinity():
    with pytest.raises(ValueError):
        cpb.dumps_strict({"mean_bc": float("inf")})


def test_dumps_strict_round_trips_normal_values():
    text = cpb.dumps_strict({"mean_bc": 0.7161, "skipped": None, "label": "MinerU-on"})
    assert "NaN" not in text and "Infinity" not in text
    assert json.loads(text)["mean_bc"] == pytest.approx(0.7161)


def test_write_atomic_leaves_no_temp_file(tmp_path):
    out = tmp_path / "nested" / "result.json"
    cpb.write_atomic(out, cpb.dumps_strict({"ok": True}))

    assert json.loads(out.read_text(encoding="utf-8")) == {"ok": True}
    assert [p.name for p in out.parent.iterdir()] == ["result.json"]


# --------------------------------------------------------------------------
# end-to-end bookkeeping with a fake scorer (no model, no GPU)
# --------------------------------------------------------------------------


def test_end_to_end_with_fake_scorer_and_checkpoint_resume(tmp_path):
    d = _write_pages(
        tmp_path,
        {
            "p1.md": _page(CHUNK_A, CHUNK_B, CHUNK_C),
            "p2.md": CHUNK_A,
            "p3.md": _page(CHUNK_A, CHUNK_B),
        },
    )
    files = cpb.list_prediction_files(d)
    pages = cpb.load_pages(files)
    bounds, page_stats = cpb.enumerate_boundaries(pages, _chunker())
    assert len(bounds) == 3

    calls: list[tuple[str, str]] = []

    def fake(prev: str, nxt: str) -> float:
        calls.append((prev, nxt))
        return 0.5 + 0.1 * len(calls)

    ckpt = tmp_path / "scratch" / "ckpt.jsonl"
    fingerprint = {
        "schema_version": cpb.CHECKPOINT_SCHEMA_VERSION,
        "sha256": "test-fingerprint",
        "components": {"fixture": "stable"},
    }
    first = cpb.score_boundaries(
        bounds,
        fake,
        checkpoint_path=ckpt,
        checkpoint_fingerprint=fingerprint,
        log_every=0,
    )
    assert len(calls) == 3
    assert json.loads(cpb.checkpoint_meta_path(ckpt).read_text()) == fingerprint

    # resuming must reuse the checkpoint and not re-invoke the scorer
    def exploding(prev: str, nxt: str) -> float:
        raise AssertionError("scorer must not be called on a fully-checkpointed resume")

    second = cpb.score_boundaries(
        bounds,
        exploding,
        checkpoint_path=ckpt,
        checkpoint_fingerprint=fingerprint,
        log_every=0,
    )
    assert [s.bc for s in second] == [s.bc for s in first]

    summary, per_page, _ = cpb.summarize(second, page_stats)
    assert summary["num_pages"] == 3
    assert summary["pages_with_chunks"] == 3
    assert summary["num_chunks"] == 6
    assert summary["num_boundaries_attempted"] == 3
    assert summary["num_boundaries_valid"] == 3
    assert summary["mean_bc"] == pytest.approx((0.6 + 0.7 + 0.8) / 3)
    assert {r["page_id"] for r in per_page} == {"p1", "p2", "p3"}
    assert next(r for r in per_page if r["page_id"] == "p2")["mean_bc"] is None

    text = cpb.dumps_strict({"summary": summary, "per_page": per_page})
    assert "NaN" not in text


def test_checkpoint_rejects_missing_or_mismatched_fingerprint(tmp_path):
    ckpt = tmp_path / "checkpoint.jsonl"
    ckpt.write_text('{"key":"p1#0","page_id":"p1","index":0,"bc":0.5}\n')
    fingerprint = {
        "schema_version": cpb.CHECKPOINT_SCHEMA_VERSION,
        "sha256": "expected",
        "components": {},
    }

    with pytest.raises(RuntimeError, match="no fingerprint sidecar"):
        cpb.prepare_checkpoint(ckpt, fingerprint)

    cpb.write_atomic(
        cpb.checkpoint_meta_path(ckpt),
        cpb.dumps_strict({**fingerprint, "sha256": "different"}),
    )
    with pytest.raises(RuntimeError, match="fingerprint mismatch"):
        cpb.prepare_checkpoint(ckpt, fingerprint)


def test_checkpoint_fingerprint_binds_inputs_model_and_boundaries():
    boundaries = [cpb.Boundary("p1", 0, CHUNK_A, CHUNK_B)]
    common = {
        "boundaries": boundaries,
        "input_manifest": "input-a",
        "model_id": "model-a",
        "model_revision": "revision-a",
        "max_tokens": 1024,
        "min_chars": 30,
    }
    first = cpb.build_checkpoint_fingerprint(**common)
    assert first == cpb.build_checkpoint_fingerprint(**common)
    assert first["sha256"] != cpb.build_checkpoint_fingerprint(
        **{**common, "input_manifest": "input-b"}
    )["sha256"]
    assert first["sha256"] != cpb.build_checkpoint_fingerprint(
        **{**common, "model_revision": "revision-b"}
    )["sha256"]
    changed = [cpb.Boundary("p1", 0, CHUNK_A, CHUNK_C)]
    assert first["sha256"] != cpb.build_checkpoint_fingerprint(
        **{**common, "boundaries": changed}
    )["sha256"]


def test_attach_reference_blocks_uses_hashed_repository_sources():
    root = cpb.repo_root()
    report = {"summary": {"mean_bc": 0.7131232508982984}}
    result = cpb.attach_reference_blocks(
        report,
        bc_ref_path=root / "output/baselines/moc_bc_correlation.json",
        rcps_ref_path=root / "output/baselines/grid_v1_parser_native.json",
        rcps_current_path=root / "output/results/grid_MinerU-tableON_parser_native.json",
    )

    assert result["references"]["mineru_on_rcps"]["num_chunks"] == 903
    assert result["derived_correlations"]["BC_vs_RCPS"]["n"] == 4
    assert result["derived_correlations"]["points"][-1]["bc"] == pytest.approx(
        0.7131232508982984
    )
    for source in result["references"]["sources"].values():
        assert len(source["sha256"]) == 64


# --------------------------------------------------------------------------
# correlation helpers — pinned against the scipy-produced numbers already in
# output/baselines/moc_bc_correlation.json (scipy is not a project dependency)
# --------------------------------------------------------------------------

_EXISTING_BC = [0.61, 0.6232, 0.5199, 0.7161, 0.7168]
_EXISTING_RCPS = [
    0.5516964335591786,
    0.5446395652278005,
    0.493276512884356,
    0.17607456087848247,
    0.06795290765879002,
]
_EXISTING_HIT1 = [
    0.521870286576169,
    0.5082956259426847,
    0.4660633484162896,
    0.16289592760180996,
    0.06334841628959276,
]


def test_pearson_reproduces_the_committed_scipy_result():
    r, p = cpb.pearson(_EXISTING_BC, _EXISTING_RCPS)
    assert round(r, 4) == -0.8137
    assert round(p, 4) == 0.0938


def test_spearman_reproduces_the_committed_scipy_result():
    r, p = cpb.spearman(_EXISTING_BC, _EXISTING_RCPS)
    assert round(r, 4) == -0.7
    assert round(p, 4) == 0.1881


def test_correlation_helpers_reproduce_the_committed_hit1_result():
    assert round(cpb.pearson(_EXISTING_BC, _EXISTING_HIT1)[0], 4) == -0.8178
    assert round(cpb.pearson(_EXISTING_BC, _EXISTING_HIT1)[1], 4) == 0.0908
    assert round(cpb.spearman(_EXISTING_BC, _EXISTING_HIT1)[0], 4) == -0.7


def test_perfect_correlation_is_exactly_one():
    r, p = cpb.pearson([1.0, 2.0, 3.0, 4.0], [2.0, 4.0, 6.0, 8.0])
    assert r == pytest.approx(1.0)
    assert p == pytest.approx(0.0, abs=1e-9)


def test_spearman_uses_average_ranks_for_ties():
    assert cpb._average_ranks([10.0, 20.0, 20.0, 30.0]) == [1.0, 2.5, 2.5, 4.0]


def test_corr_block_emits_json_safe_finite_numbers():
    block = cpb.corr_block("t", _EXISTING_BC[:4], _EXISTING_RCPS[:4])
    assert block["n"] == 4
    for k in ("pearson_r", "pearson_p", "spearman_r", "spearman_p"):
        assert math.isfinite(block[k])
    assert "NaN" not in cpb.dumps_strict(block)
