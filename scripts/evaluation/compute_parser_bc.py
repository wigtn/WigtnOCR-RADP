"""MoC Boundary Clarity for ONE parser output dir — reproducible, resumable.

Companion to `scripts/evaluation/compute_moc_bc.py`, which computed BC for the
six v1 baseline-grid parsers in a single pass over a machine-local results root.
That script cannot be re-run here (its `V1_RESULTS_ROOT` is an absolute path on
another machine, and `data/KoGovDoc-Bench/val.jsonl` is not in this repo), so
this one scores a *single* in-repo parser directory instead — with the exact
same metric, chunker, LM and settings, so the number is directly comparable to
the ones already recorded in `output/baselines/moc_bc_correlation.json`.

Metric (unchanged, from `wigtnocr_radp.evaluation.boundary_clarity`):

    BC(q | d) = ppl(q | d) / ppl(q) = exp(NLL(q | d) - NLL(q))

`d` is a chunk, `q` is the chunk immediately after it *on the same page*. Only
within-page adjacent pairs are scored; page-crossing pairs are never formed.
The headline number is the unweighted mean over every valid boundary in the
corpus (NOT a mean of per-page means), and BC is never clamped to [0, 1].

Typical use (WSL, RTX 5070):

    CUDA_VISIBLE_DEVICES=0 HF_HUB_OFFLINE=0 uv run python \
      scripts/evaluation/compute_parser_bc.py \
      --parser-dir results/kogovdoc/mineru_val_tableon/predictions \
      --label MinerU-on \
      --model Qwen/Qwen3-VL-2B-Instruct \
      --device cuda \
      --max-tokens 1024 \
      --expected-pages 294 \
      --expected-chunks 903 \
      --out output/baselines/moc_bc_mineru_tableon.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
import os
import statistics
import subprocess
import sys
import tempfile
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("compute_parser_bc")

SCHEMA_VERSION = "1.0.0"
CHECKPOINT_SCHEMA_VERSION = "1.0.0"
REPO_ROOT_ENV = "WIGTNOCR_RADP_REPO_ROOT"
RUNNER_SOURCE_ID = "scripts/evaluation/compute_parser_bc.py"

METRIC_DEFINITION = (
    "MoC Boundary Clarity (arXiv:2503.09600). For a chunk d and the chunk q "
    "immediately following it on the same page, "
    "BC(q|d) = ppl(q|d) / ppl(q) = exp(NLL(q|d) - NLL(q)), where NLL is the "
    "mean token negative log-likelihood under the scoring LM. Higher BC = the "
    "next chunk is less predictable from the previous one = a cleaner, better "
    "separated boundary. Only within-page adjacent chunk pairs are scored; no "
    "boundary is formed across a page break. The corpus number is the "
    "unweighted mean over every valid boundary (not a mean of per-page means). "
    "BC is not clamped to [0, 1]."
)

AGGREGATION = "unweighted_mean_over_all_valid_adjacent_boundaries"

# Parsers whose BC is already recorded in moc_bc_correlation.json and whose
# output covers all 294 validation pages with measurable BC. Marker is partial
# (38 pages), while PaddleOCR has no measured BC in the stored source audit;
# both are excluded from the 4-point correlation.
COMPLETE_OUTPUT_REFERENCE_PARSERS = (
    "Qwen3-VL-30B (teacher)",
    "WigtnOCR-2B (ours, v1)",
    "Qwen3-VL-2B (base)",
)

# Named reference BC values pulled out of moc_bc_correlation.json for the
# `references` / `comparisons` blocks.
BC_REFERENCE_ALIASES = {
    "mineru_off": "MinerU",
    "prod": "WigtnOCR-2B (ours, v1)",
}


# --------------------------------------------------------------------------
# input discovery / manifest
# --------------------------------------------------------------------------


def repo_root() -> Path:
    """Repository root (this file lives at <root>/scripts/evaluation/)."""
    configured = os.environ.get(REPO_ROOT_ENV)
    if configured:
        return Path(configured).resolve()
    return Path(__file__).resolve().parents[2]


def as_repo_relative(path: Path, root: Path | None = None) -> str:
    """POSIX path relative to the repo root — never an absolute or home path."""
    root = root or repo_root()
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(root).as_posix()
    except ValueError:
        # Outside the repo: fall back to the bare name so no absolute path or
        # user home directory can leak into the result JSON.
        return resolved.name


def list_prediction_files(parser_dir: Path) -> list[Path]:
    """Every `*.md` under `parser_dir`, sorted by filename for determinism."""
    parser_dir = Path(parser_dir)
    if not parser_dir.is_dir():
        raise FileNotFoundError(f"parser_dir not found: {parser_dir}")
    return sorted(parser_dir.glob("*.md"), key=lambda p: p.name)


def manifest_sha256(files: Sequence[Path], root: Path | None = None) -> str:
    """SHA-256 over (repo-relative path, content) of every input file.

    Deterministic for a given set of files and contents, and independent of
    where the repo is checked out.
    """
    h = hashlib.sha256()
    for f in files:
        rel = as_repo_relative(f, root)
        content = Path(f).read_bytes()
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(hashlib.sha256(content).hexdigest().encode("ascii"))
        h.update(b"\n")
    return h.hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical_sha256(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_pages(files: Sequence[Path]) -> list[tuple[str, str]]:
    """`[(page_id, markdown)]` in sorted-filename order; page_id = file stem.

    The RCPS grid keys the same pages as `val_NNNN` via `val.jsonl`. That file
    is not in this repo, but the mapping is a bijection over the same 294
    files, and BC depends only on within-page chunk adjacency — so the page
    *labels* differ from the RCPS run while every chunk, boundary and the
    corpus mean are identical.
    """
    return [(f.stem, f.read_text(encoding="utf-8")) for f in files]


# --------------------------------------------------------------------------
# boundary enumeration
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Boundary:
    """One within-page adjacent chunk pair (d, q)."""

    page_id: str
    index: int  # boundary i sits between chunk i and chunk i+1 of this page
    prev_text: str
    next_text: str

    @property
    def key(self) -> str:
        return f"{self.page_id}#{self.index}"


def enumerate_boundaries(
    pages: Sequence[tuple[str, str]], chunker: Any
) -> tuple[list[Boundary], list[dict[str, Any]]]:
    """Chunk every page and form only the within-page adjacent boundaries.

    Returns `(boundaries, page_stats)`. A page with n chunks contributes
    exactly `max(n - 1, 0)` boundaries; consecutive pages are never joined.
    """
    boundaries: list[Boundary] = []
    page_stats: list[dict[str, Any]] = []
    for page_id, markdown in pages:
        chunks = chunker.chunk(page_id, markdown)
        texts = [c.text for c in chunks]
        n_bounds = max(len(texts) - 1, 0)
        for i in range(n_bounds):
            boundaries.append(
                Boundary(page_id=page_id, index=i, prev_text=texts[i], next_text=texts[i + 1])
            )
        page_stats.append(
            {
                "page_id": page_id,
                "num_chunks": len(texts),
                "num_boundaries_attempted": n_bounds,
                "num_boundaries_valid": 0,
                "mean_bc": None,
            }
        )
    return boundaries, page_stats


def boundary_manifest_sha256(boundaries: Sequence[Boundary]) -> str:
    """Hash boundary keys and both texts, in scoring order."""
    h = hashlib.sha256()
    for boundary in boundaries:
        for value in (boundary.key, boundary.prev_text, boundary.next_text):
            raw = value.encode("utf-8")
            h.update(len(raw).to_bytes(8, "big"))
            h.update(raw)
    return h.hexdigest()


def build_checkpoint_fingerprint(
    *,
    boundaries: Sequence[Boundary],
    input_manifest: str,
    model_id: str,
    model_revision: str | None,
    max_tokens: int,
    min_chars: int,
) -> dict[str, Any]:
    """Bind a resumable checkpoint to its complete scientific configuration."""
    scoring_source = repo_root() / "src/wigtnocr_radp/evaluation/boundary_clarity.py"
    components = {
        "input_manifest_sha256": input_manifest,
        "boundary_manifest_sha256": boundary_manifest_sha256(boundaries),
        "num_boundaries": len(boundaries),
        "model_id": model_id,
        "model_revision": model_revision,
        "dtype": "torch.bfloat16",
        "max_tokens": max_tokens,
        "chunker": {"name": "parser_native", "min_chars": min_chars},
        "metric_definition_sha256": hashlib.sha256(
            METRIC_DEFINITION.encode("utf-8")
        ).hexdigest(),
        "scoring_source_sha256": file_sha256(scoring_source),
        "runner_source_sha256": file_sha256(Path(__file__)),
    }
    return {
        "schema_version": CHECKPOINT_SCHEMA_VERSION,
        "sha256": canonical_sha256(components),
        "components": components,
    }


def validate_inputs(
    *,
    num_pages: int,
    num_chunks: int,
    expected_pages: int | None,
    expected_chunks: int | None,
) -> None:
    """Hard-fail on any page/chunk count mismatch before the LM is ever loaded."""
    if expected_pages is not None and num_pages != expected_pages:
        raise ValueError(
            f"prediction file count mismatch: found {num_pages}, expected {expected_pages}. "
            "Refusing to run — the input set is not the one this comparison is defined over."
        )
    if expected_chunks is not None and num_chunks != expected_chunks:
        raise ValueError(
            f"chunk count mismatch: ParserNativeChunker produced {num_chunks} chunks, "
            f"expected {expected_chunks} (the num_chunks of the matching RCPS run). "
            "Refusing to run — BC and RCPS would not be measured over the same chunking."
        )


def validate_reference_inputs(paths: Sequence[Path]) -> None:
    missing = [str(path) for path in paths if not Path(path).is_file()]
    if missing:
        raise FileNotFoundError(
            "reference files are missing; refusing to load the LM before this "
            f"preflight passes: {missing}"
        )


def cuda_preflight(device: str) -> None:
    """Initialise CUDA and allocate one scalar before the model is loaded."""
    if not device.startswith("cuda"):
        return
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA preflight failed: torch.cuda.is_available() is false")
    index = int(device.split(":", 1)[1]) if ":" in device else 0
    torch.cuda.set_device(index)
    probe = torch.ones(1, device=device)
    if probe.item() != 1.0:
        raise RuntimeError("CUDA preflight returned an unexpected allocation value")
    logger.info("CUDA preflight OK: %s", torch.cuda.get_device_name(index))


# --------------------------------------------------------------------------
# scoring + resumable checkpoint
# --------------------------------------------------------------------------


@dataclass
class BoundaryScore:
    key: str
    page_id: str
    index: int
    bc: float | None
    skip_reason: str | None


def _classify(bc: float | None) -> tuple[float | None, str | None]:
    if bc is None:
        return None, "scorer_returned_none"
    if math.isnan(bc):
        return None, "nan"
    if math.isinf(bc):
        return None, "inf"
    return float(bc), None


def load_checkpoint(path: Path | None) -> dict[str, BoundaryScore]:
    """Read a partial run back. Truncated/corrupt trailing lines are dropped."""
    done: dict[str, BoundaryScore] = {}
    if path is None or not Path(path).exists():
        return done
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            logger.warning("checkpoint: dropping unparseable line")
            continue
        done[d["key"]] = BoundaryScore(
            key=d["key"],
            page_id=d["page_id"],
            index=d["index"],
            bc=d.get("bc"),
            skip_reason=d.get("skip_reason"),
        )
    return done


def checkpoint_meta_path(path: Path) -> Path:
    return Path(f"{path}.meta.json")


def prepare_checkpoint(path: Path, fingerprint: dict[str, Any]) -> None:
    """Create or verify the checkpoint sidecar before cached scores are read."""
    path = Path(path)
    meta_path = checkpoint_meta_path(path)
    has_scores = path.exists() and path.stat().st_size > 0
    if has_scores and not meta_path.exists():
        raise RuntimeError(
            f"checkpoint {path} has no fingerprint sidecar {meta_path}; "
            "refusing to reuse unbound scores"
        )
    if meta_path.exists():
        try:
            stored = json.loads(meta_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise RuntimeError(f"checkpoint fingerprint is unreadable: {meta_path}") from exc
        if stored != fingerprint:
            raise RuntimeError(
                f"checkpoint fingerprint mismatch for {path}: "
                f"stored={stored.get('sha256')} current={fingerprint.get('sha256')}"
            )
    else:
        write_atomic(meta_path, dumps_strict(fingerprint))


def score_boundaries(
    boundaries: Sequence[Boundary],
    score_fn: Callable[[str, str], float | None],
    *,
    checkpoint_path: Path | None = None,
    checkpoint_fingerprint: dict[str, Any] | None = None,
    log_every: int = 50,
) -> list[BoundaryScore]:
    """Score every boundary, resuming from and appending to a checkpoint."""
    if checkpoint_path is not None:
        if checkpoint_fingerprint is None:
            raise ValueError("checkpoint_path requires checkpoint_fingerprint")
        prepare_checkpoint(checkpoint_path, checkpoint_fingerprint)
    done = load_checkpoint(checkpoint_path)
    if done:
        logger.info("checkpoint: resuming with %d boundaries already scored", len(done))

    fh = None
    if checkpoint_path is not None:
        Path(checkpoint_path).parent.mkdir(parents=True, exist_ok=True)
        fh = Path(checkpoint_path).open("a", encoding="utf-8")

    results: list[BoundaryScore] = []
    try:
        for n, b in enumerate(boundaries, start=1):
            if b.key in done:
                results.append(done[b.key])
                continue
            bc, reason = _classify(score_fn(b.prev_text, b.next_text))
            rec = BoundaryScore(key=b.key, page_id=b.page_id, index=b.index, bc=bc, skip_reason=reason)
            results.append(rec)
            if fh is not None:
                fh.write(
                    json.dumps(
                        {
                            "key": rec.key,
                            "page_id": rec.page_id,
                            "index": rec.index,
                            "bc": rec.bc,
                            "skip_reason": rec.skip_reason,
                        },
                        allow_nan=False,
                    )
                    + "\n"
                )
                fh.flush()
            if log_every and n % log_every == 0:
                valid = [r.bc for r in results if r.bc is not None]
                running = sum(valid) / len(valid) if valid else float("nan")
                logger.info(
                    "%d/%d boundaries — running mean BC=%.4f", n, len(boundaries), running
                )
    finally:
        if fh is not None:
            fh.close()
    return results


def summarize(
    scores: Sequence[BoundaryScore], page_stats: list[dict[str, Any]]
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, int]]:
    """Corpus summary + per-page rows + skip-reason histogram.

    `mean_bc` is the unweighted mean over all valid boundaries, so a page with
    more boundaries contributes proportionally more — it is NOT the mean of the
    per-page means.
    """
    by_page: dict[str, list[float]] = {}
    for s in scores:
        if s.bc is not None:
            by_page.setdefault(s.page_id, []).append(s.bc)

    for row in page_stats:
        vals = by_page.get(row["page_id"], [])
        row["num_boundaries_valid"] = len(vals)
        row["mean_bc"] = (sum(vals) / len(vals)) if vals else None

    valid = [s.bc for s in scores if s.bc is not None]
    skipped = [s for s in scores if s.bc is None]
    reasons: dict[str, int] = {}
    for s in skipped:
        reasons[s.skip_reason or "unknown"] = reasons.get(s.skip_reason or "unknown", 0) + 1

    summary = {
        "num_pages": len(page_stats),
        "pages_with_chunks": sum(1 for r in page_stats if r["num_chunks"] > 0),
        "num_chunks": sum(r["num_chunks"] for r in page_stats),
        "num_boundaries_attempted": len(scores),
        "num_boundaries_valid": len(valid),
        "num_boundaries_skipped": len(skipped),
        "skipped_by_reason": reasons,
        "mean_bc": (sum(valid) / len(valid)) if valid else None,
        "median_bc": statistics.median(valid) if valid else None,
        "std_bc": statistics.stdev(valid) if len(valid) > 1 else None,
        "min_bc": min(valid) if valid else None,
        "max_bc": max(valid) if valid else None,
    }
    return summary, page_stats, reasons


# --------------------------------------------------------------------------
# correlation (pure Python — scipy is not a project dependency)
# --------------------------------------------------------------------------


def _betacf(a: float, b: float, x: float) -> float:
    """Continued fraction for the incomplete beta function (Numerical Recipes)."""
    tiny, eps, itmax = 1e-30, 3e-16, 300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    h = d
    for m in range(1, itmax + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def regularized_incomplete_beta(a: float, b: float, x: float) -> float:
    """I_x(a, b) — regularized incomplete beta function."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    front = math.exp(lbeta + a * math.log(x) + b * math.log1p(-x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - math.exp(lbeta + b * math.log1p(-x) + a * math.log(x)) * _betacf(b, a, 1.0 - x) / b


def _two_sided_p_from_r(r: float, n: int) -> float:
    """Two-sided p for a correlation coefficient via the t-approximation.

    This is the same approximation `scipy.stats.pearsonr` /
    `scipy.stats.spearmanr` use by default. At n=4 it is a formality, not
    evidence — see the caveats in docs/FINDINGS_mineru_tableon_bc.md.
    """
    df = n - 2
    if df <= 0:
        return float("nan")
    if abs(r) >= 1.0:
        return 0.0
    t2 = (r * r) * df / (1.0 - r * r)
    return regularized_incomplete_beta(df / 2.0, 0.5, df / (df + t2))


def pearson(xs: Sequence[float], ys: Sequence[float]) -> tuple[float, float]:
    n = len(xs)
    if n != len(ys) or n < 2:
        raise ValueError("pearson needs two equal-length sequences of length >= 2")
    mx, my = sum(xs) / n, sum(ys) / n
    dx = [x - mx for x in xs]
    dy = [y - my for y in ys]
    num = sum(a * b for a, b in zip(dx, dy, strict=True))
    den = math.sqrt(sum(a * a for a in dx) * sum(b * b for b in dy))
    if den == 0.0:
        return float("nan"), float("nan")
    r = max(-1.0, min(1.0, num / den))
    return r, _two_sided_p_from_r(r, n)


def _average_ranks(vals: Sequence[float]) -> list[float]:
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    ranks = [0.0] * len(vals)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def spearman(xs: Sequence[float], ys: Sequence[float]) -> tuple[float, float]:
    return pearson(_average_ranks(xs), _average_ranks(ys))


def corr_block(label: str, xs: Sequence[float], ys: Sequence[float]) -> dict[str, Any]:
    pr, pp = pearson(xs, ys)
    sr, sp = spearman(xs, ys)
    return {
        "label": label,
        "n": len(xs),
        "pearson_r": round(pr, 4),
        "pearson_p": round(pp, 4),
        "spearman_r": round(sr, 4),
        "spearman_p": round(sp, 4),
    }


# --------------------------------------------------------------------------
# provenance
# --------------------------------------------------------------------------


def git_commit() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root(),
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout.strip() or None
    except (subprocess.CalledProcessError, OSError):
        return None


def git_is_dirty() -> bool | None:
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_root(),
            capture_output=True,
            text=True,
            check=True,
        )
        return bool(out.stdout.strip())
    except (subprocess.CalledProcessError, OSError):
        return None


def git_tracked_is_dirty() -> bool | None:
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            cwd=repo_root(),
            capture_output=True,
            text=True,
            check=True,
        )
        return bool(out.stdout.strip())
    except (subprocess.CalledProcessError, OSError):
        return None


def build_provenance(
    *, model_id: str, model_revision: str | None, dtype: str, device: str, gpu: str | None
) -> dict[str, Any]:
    import torch  # local import: keeps this module importable without a GPU stack
    import transformers

    return {
        "git_commit": git_commit(),
        "git_commit_role": (
            "execution checkout supplying package and input files; "
            "runner_source_sha256 identifies the executed runner"
        ),
        "git_dirty": git_is_dirty(),
        "git_tracked_dirty": git_tracked_is_dirty(),
        "executed_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "runner_source": RUNNER_SOURCE_ID,
        "runner_source_sha256": file_sha256(Path(__file__)),
        "model_id": model_id,
        "model_revision": model_revision,
        "dtype": dtype,
        "device": device,
        "gpu": gpu,
        "python_version": sys.version.split()[0],
        "torch_version": torch.__version__,
        "transformers_version": transformers.__version__,
        "cuda_version": torch.version.cuda,
    }


def model_revision_of(model: Any) -> str | None:
    """Hugging Face commit hash, if the loaded config carries one."""
    cfg = getattr(model, "config", None)
    for attr in ("_commit_hash", "commit_hash"):
        v = getattr(cfg, attr, None)
        if isinstance(v, str) and v:
            return v
    return None


# --------------------------------------------------------------------------
# references / comparisons
# --------------------------------------------------------------------------


def _find_parser(rows: Iterable[dict[str, Any]], key: str, name: str) -> dict[str, Any] | None:
    for r in rows:
        if r.get(key) == name:
            return r
    return None


def build_references(
    *, bc_ref_path: Path, rcps_ref_path: Path, rcps_current_path: Path
) -> dict[str, Any]:
    """Reference BC/RCPS values, each tagged with its source path and SHA-256."""
    bc_doc = json.loads(Path(bc_ref_path).read_text(encoding="utf-8"))
    cur_doc = json.loads(Path(rcps_current_path).read_text(encoding="utf-8"))

    bc_src = {
        "path": as_repo_relative(bc_ref_path),
        "sha256": file_sha256(bc_ref_path),
        "note": "mean_bc values here are stored rounded to 4 decimal places",
    }
    rcps_src = {"path": as_repo_relative(rcps_ref_path), "sha256": file_sha256(rcps_ref_path)}
    cur_src = {"path": as_repo_relative(rcps_current_path), "sha256": file_sha256(rcps_current_path)}

    refs: dict[str, Any] = {"sources": {"bc": bc_src, "rcps": rcps_src, "rcps_current": cur_src}}

    for alias, name in BC_REFERENCE_ALIASES.items():
        row = _find_parser(bc_doc["parsers"], "parser", name)
        if row is None:
            raise KeyError(f"{bc_ref_path}: no parser named {name!r}")
        refs[f"{alias}_bc"] = {
            "parser": name,
            "mean_bc": row["mean_bc"],
            "num_pages": row["num_pages"],
            "num_boundaries": row["num_boundaries"],
            "source": "bc",
        }

    refs["mineru_on_rcps"] = {
        "label": cur_doc["label"],
        "rcps": cur_doc["rcps"],
        "hit@1": cur_doc["hit@1"],
        "num_pages": cur_doc["num_pages"],
        "num_chunks": cur_doc["num_chunks"],
        "chunker": cur_doc["chunker"],
        "source": "rcps_current",
    }
    return refs


def build_derived_correlations(
    *, mean_bc: float, bc_ref_path: Path, rcps_ref_path: Path, rcps_current_path: Path
) -> dict[str, Any]:
    """Pearson/Spearman over the 4 complete-output parsers.

    BC for the three existing parsers comes from moc_bc_correlation.json; their
    RCPS/Hit@1 come from the *current* baseline grid
    (grid_v1_parser_native.json), not from the RCPS snapshot embedded in the BC
    file — those two disagree, and the task specifies the current grid. The
    fourth point is this run's BC paired with the table-ON RCPS.
    """
    bc_doc = json.loads(Path(bc_ref_path).read_text(encoding="utf-8"))
    rcps_doc = json.loads(Path(rcps_ref_path).read_text(encoding="utf-8"))
    cur_doc = json.loads(Path(rcps_current_path).read_text(encoding="utf-8"))

    points: list[dict[str, Any]] = []
    for name in COMPLETE_OUTPUT_REFERENCE_PARSERS:
        bc_row = _find_parser(bc_doc["parsers"], "parser", name)
        rc_row = _find_parser(rcps_doc["parsers"], "name", name)
        if bc_row is None or rc_row is None:
            raise KeyError(f"missing reference row for {name!r}")
        points.append(
            {
                "parser": name,
                "bc": bc_row["mean_bc"],
                "bc_source": "existing",
                "rcps": rc_row["rcps"],
                "hit@1": rc_row["hit@1"],
                "rcps_source": "grid_v1_parser_native",
            }
        )
    points.append(
        {
            "parser": cur_doc["label"],
            "bc": mean_bc,
            "bc_source": "this_run",
            "rcps": cur_doc["rcps"],
            "hit@1": cur_doc["hit@1"],
            "rcps_source": "grid_MinerU-tableON_parser_native",
        }
    )

    marker_bc = _find_parser(bc_doc["parsers"], "parser", "Marker")
    marker_rcps = _find_parser(rcps_doc["parsers"], "name", "Marker")
    if marker_bc is None or marker_rcps is None:
        raise KeyError("missing reference row for the partial Marker sensitivity point")
    marker_point = {
        "parser": "Marker",
        "bc": marker_bc["mean_bc"],
        "bc_source": "existing_partial_38_pages",
        "rcps": marker_rcps["rcps"],
        "hit@1": marker_rcps["hit@1"],
        "rcps_source": "grid_v1_parser_native_partial_38_pages",
        "num_pages": marker_bc["num_pages"],
    }

    bcs = [p["bc"] for p in points]
    sensitivity_points = [*points, marker_point]
    sensitivity_bcs = [p["bc"] for p in sensitivity_points]
    return {
        "label": "complete_output_parsers_with_mineru_on",
        "note": (
            "4 parsers with complete 294-page output and measured BC. Marker "
            "is partial (38 pages), and PaddleOCR has no measured BC in the "
            "stored source audit; both are excluded. "
            "MinerU-off is replaced by MinerU-on: they are the same 294 pages "
            "parsed under two configurations, so including both would double-count "
            "one parser family/configuration comparison."
        ),
        "points": points,
        "BC_vs_RCPS": corr_block("complete_output_4", bcs, [p["rcps"] for p in points]),
        "BC_vs_Hit1": corr_block("complete_output_4", bcs, [p["hit@1"] for p in points]),
        "partial_marker_sensitivity": {
            "note": (
                "Sensitivity analysis only: Marker covers 38 pages rather than "
                "the complete 294-page frame and remains excluded from the "
                "primary comparison."
            ),
            "points": sensitivity_points,
            "BC_vs_RCPS": corr_block(
                "complete_output_4_plus_partial_marker",
                sensitivity_bcs,
                [p["rcps"] for p in sensitivity_points],
            ),
            "BC_vs_Hit1": corr_block(
                "complete_output_4_plus_partial_marker",
                sensitivity_bcs,
                [p["hit@1"] for p in sensitivity_points],
            ),
        },
    }


def attach_reference_blocks(
    report: dict[str, Any],
    *,
    bc_ref_path: Path,
    rcps_ref_path: Path,
    rcps_current_path: Path,
) -> dict[str, Any]:
    """Attach deterministic comparison blocks to a core GPU result."""
    refs = build_references(
        bc_ref_path=bc_ref_path,
        rcps_ref_path=rcps_ref_path,
        rcps_current_path=rcps_current_path,
    )
    mean_bc = report["summary"]["mean_bc"]
    if not isinstance(mean_bc, (int, float)) or not math.isfinite(mean_bc):
        raise ValueError("core result has no finite summary.mean_bc")
    report["references"] = refs
    report["comparisons"] = {
        "bc_minus_mineru_off_bc": mean_bc - refs["mineru_off_bc"]["mean_bc"],
        "bc_minus_prod_bc": mean_bc - refs["prod_bc"]["mean_bc"],
        "note": (
            "Reference BC values are stored rounded to 4 decimal places, so "
            "these differences carry at most 4-decimal precision. The "
            "reference run also recorded no model revision — see the caveats "
            "in docs/FINDINGS_mineru_tableon_bc.md."
        ),
    }
    report["derived_correlations"] = build_derived_correlations(
        mean_bc=mean_bc,
        bc_ref_path=bc_ref_path,
        rcps_ref_path=rcps_ref_path,
        rcps_current_path=rcps_current_path,
    )
    return report


# --------------------------------------------------------------------------
# output
# --------------------------------------------------------------------------


def dumps_strict(report: dict[str, Any]) -> str:
    """Serialize with `allow_nan=False` so NaN/Infinity can never be emitted."""
    return json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"


def write_atomic(path: Path, text: str) -> None:
    """Write via a temp file in the same directory + `os.replace`.

    An interrupted run therefore leaves either the previous file or nothing —
    never a truncated JSON.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--parser-dir", type=Path)
    ap.add_argument("--label", help="system label, e.g. MinerU-on")
    ap.add_argument(
        "--augment-existing",
        type=Path,
        help="attach reference/correlation blocks to an existing core result; no LM load",
    )
    ap.add_argument("--model", default="Qwen/Qwen3-VL-2B-Instruct")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--max-tokens", type=int, default=1024)
    ap.add_argument("--min-chars", type=int, default=30, help="ParserNativeChunker min_chars")
    ap.add_argument("--expected-pages", type=int, default=None)
    ap.add_argument("--expected-chunks", type=int, default=None)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument(
        "--checkpoint",
        type=Path,
        default=None,
        help="resumable JSONL checkpoint (default: scratch/bc/<label>/checkpoint.jsonl)",
    )
    ap.add_argument("--no-checkpoint", action="store_true")
    ap.add_argument("--bc-reference", type=Path, default=Path("output/baselines/moc_bc_correlation.json"))
    ap.add_argument("--rcps-reference", type=Path, default=Path("output/baselines/grid_v1_parser_native.json"))
    ap.add_argument(
        "--rcps-current",
        type=Path,
        default=Path("output/results/grid_MinerU-tableON_parser_native.json"),
    )
    ap.add_argument("--no-references", action="store_true", help="skip references/comparisons/correlations")
    ap.add_argument("--dry-run", action="store_true", help="validate inputs and exit without loading the LM")
    args = ap.parse_args(argv)

    if args.augment_existing is not None:
        if args.no_references:
            ap.error("--augment-existing cannot be combined with --no-references")
        validate_reference_inputs(
            [args.bc_reference, args.rcps_reference, args.rcps_current]
        )
        report = json.loads(args.augment_existing.read_text(encoding="utf-8"))
        attach_reference_blocks(
            report,
            bc_ref_path=args.bc_reference,
            rcps_ref_path=args.rcps_reference,
            rcps_current_path=args.rcps_current,
        )
        write_atomic(args.out, dumps_strict(report))
        logger.info("augmented %s -> %s", args.augment_existing, args.out)
        return 0

    if args.parser_dir is None or args.label is None:
        ap.error("--parser-dir and --label are required unless --augment-existing is used")

    from wigtnocr_radp.evaluation.chunkers import ParserNativeChunker

    files = list_prediction_files(args.parser_dir)
    pages = load_pages(files)
    chunker = ParserNativeChunker(min_chars=args.min_chars)
    boundaries, page_stats = enumerate_boundaries(pages, chunker)
    num_chunks = sum(r["num_chunks"] for r in page_stats)

    logger.info(
        "%s: %d pages, %d chunks, %d within-page boundaries",
        args.label,
        len(pages),
        num_chunks,
        len(boundaries),
    )
    validate_inputs(
        num_pages=len(files),
        num_chunks=num_chunks,
        expected_pages=args.expected_pages,
        expected_chunks=args.expected_chunks,
    )
    if not args.no_references:
        validate_reference_inputs(
            [args.bc_reference, args.rcps_reference, args.rcps_current]
        )

    manifest = manifest_sha256(files)
    logger.info("input manifest sha256=%s", manifest)

    if args.dry_run:
        logger.info("--dry-run: inputs validated, exiting before LM load")
        return 0

    cuda_preflight(args.device)

    checkpoint = None
    if not args.no_checkpoint:
        checkpoint = args.checkpoint or (
            repo_root() / "scratch" / "bc" / args.label.replace("/", "_") / "checkpoint.jsonl"
        )

    import torch

    from wigtnocr_radp.evaluation.boundary_clarity import PerplexityLM

    ppl = PerplexityLM(model_id=args.model, device=args.device, max_tokens=args.max_tokens)
    gpu = (
        torch.cuda.get_device_name(0)
        if args.device.startswith("cuda") and torch.cuda.is_available()
        else None
    )
    model_revision = model_revision_of(ppl.model)
    fingerprint = build_checkpoint_fingerprint(
        boundaries=boundaries,
        input_manifest=manifest,
        model_id=args.model,
        model_revision=model_revision,
        max_tokens=args.max_tokens,
        min_chars=args.min_chars,
    )
    resumed_records = len(load_checkpoint(checkpoint)) if checkpoint is not None else 0
    scores = score_boundaries(
        boundaries,
        ppl.boundary_clarity,
        checkpoint_path=checkpoint,
        checkpoint_fingerprint=fingerprint if checkpoint is not None else None,
    )
    summary, per_page, reasons = summarize(scores, page_stats)

    if summary["mean_bc"] is None:
        raise RuntimeError("no valid boundaries scored — refusing to write a result")
    logger.info(
        "%s: mean BC=%.4f over %d/%d boundaries (%d skipped: %s)",
        args.label,
        summary["mean_bc"],
        summary["num_boundaries_valid"],
        summary["num_boundaries_attempted"],
        summary["num_boundaries_skipped"],
        reasons or "none",
    )

    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "label": args.label,
        "metric_definition": METRIC_DEFINITION,
        "provenance": build_provenance(
            model_id=args.model,
            model_revision=model_revision,
            dtype="torch.bfloat16",
            device=args.device,
            gpu=gpu,
        ),
        "input": {
            "parser_dir": as_repo_relative(args.parser_dir),
            "prediction_file_count": len(files),
            "prediction_manifest_sha256": manifest,
            "manifest_definition": (
                "sha256 over, for each *.md sorted by filename: "
                "repo-relative POSIX path + NUL + sha256(file bytes) hex + LF"
            ),
        },
        "chunker": {"name": "parser_native", "min_chars": args.min_chars},
        "scoring": {
            "max_tokens": args.max_tokens,
            "aggregation": AGGREGATION,
            "clamped": False,
            "boundaries": "within_page_adjacent_only",
            "std_bc_definition": "sample standard deviation (n-1)",
            "fingerprint": fingerprint,
        },
        "checkpoint": {
            "enabled": checkpoint is not None,
            "resumed_records": resumed_records,
            "fingerprint": fingerprint if checkpoint is not None else None,
            "note": (
                "When enabled, cached boundary scores are reused only after the "
                "sidecar fingerprint matches the input, boundary texts, model "
                "revision, chunker, metric, and scoring source hashes."
            ),
        },
        "summary": summary,
        "per_page": per_page,
    }

    if not args.no_references:
        attach_reference_blocks(
            report,
            bc_ref_path=args.bc_reference,
            rcps_ref_path=args.rcps_reference,
            rcps_current_path=args.rcps_current,
        )

    write_atomic(args.out, dumps_strict(report))
    logger.info("wrote %s", as_repo_relative(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
