"""Bootstrap CIs for RCPS and its components.

RCPS = (1/|R||K|) Σ_{r, k} (1/N) Σ_i MRR@k(r, qa_i)
     = (1/N) Σ_i per_qa_score_i,   where per_qa_score_i = (1/|R||K|) Σ_{r,k} mrr[r,k,i]

So percentile bootstrap over Q-A indices just resamples `per_qa_score` with
replacement and takes percentiles of the resampled means. The per-Q-A score
array is the only thing the bootstrap needs once the eval has been run.

For paired comparisons (λ=0.1 vs λ=0, etc.) we keep the same resample indices
across systems, so the CI is on the *paired* delta, not the marginal difference.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


@dataclass(frozen=True)
class CI:
    """A bootstrap mean estimate with a percentile CI."""

    mean: float
    lo: float
    hi: float

    def fmt(self, decimals: int = 4) -> str:
        return f"{self.mean:.{decimals}f} [{self.lo:.{decimals}f}, {self.hi:.{decimals}f}]"

    def to_dict(self) -> dict[str, float]:
        return {"mean": self.mean, "lo": self.lo, "hi": self.hi}


def bootstrap_mean(
    per_qa: np.ndarray,
    *,
    n_boot: int = 1000,
    alpha: float = 0.05,
    seed: int = 42,
) -> CI:
    """Percentile bootstrap CI of the mean of `per_qa`.

    Args:
        per_qa: shape (N,). One score per Q-A (already averaged over retriever/k).
        n_boot: number of bootstrap resamples.
        alpha: 1 - confidence level (0.05 → 95% CI).
    """
    arr = np.asarray(per_qa, dtype=float)
    n = arr.shape[0]
    if n == 0:
        return CI(0.0, 0.0, 0.0)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(n_boot, n))
    boot_means = arr[idx].mean(axis=1)
    lo = float(np.percentile(boot_means, 100 * alpha / 2))
    hi = float(np.percentile(boot_means, 100 * (1 - alpha / 2)))
    return CI(mean=float(arr.mean()), lo=lo, hi=hi)


def bootstrap_paired_delta(
    per_qa_treated: np.ndarray,
    per_qa_control: np.ndarray,
    *,
    n_boot: int = 1000,
    alpha: float = 0.05,
    seed: int = 42,
) -> CI:
    """Percentile bootstrap CI of the *paired* mean delta (treated − control).

    The two arrays must share Q-A index ordering — the bootstrap draws one set
    of indices and applies it to both, preserving the pairing. This is tighter
    than the unpaired CI and reflects what we actually claim ("λ=0.1 beats λ=0
    on the same eval set by X").
    """
    t = np.asarray(per_qa_treated, dtype=float)
    c = np.asarray(per_qa_control, dtype=float)
    assert t.shape == c.shape, f"shape mismatch: treated {t.shape} vs control {c.shape}"
    n = t.shape[0]
    if n == 0:
        return CI(0.0, 0.0, 0.0)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(n_boot, n))
    diffs = t[idx].mean(axis=1) - c[idx].mean(axis=1)
    lo = float(np.percentile(diffs, 100 * alpha / 2))
    hi = float(np.percentile(diffs, 100 * (1 - alpha / 2)))
    return CI(mean=float((t - c).mean()), lo=lo, hi=hi)


def per_qa_rcps(per_qa_mrr: dict[tuple[str, int], np.ndarray]) -> np.ndarray:
    """Average per-Q-A MRR across all (retriever, k) combinations → per-Q-A RCPS.

    Args:
        per_qa_mrr: keys are (retriever_name, k), values are length-N arrays of
            MRR@k for each Q-A.
    """
    arrs = list(per_qa_mrr.values())
    assert all(a.shape == arrs[0].shape for a in arrs), "all arrays must share shape"
    return np.stack(arrs, axis=0).mean(axis=0)


def save_per_qa_arrays(
    path: str | Path,
    per_qa: dict[str, dict[tuple[str, int], np.ndarray]],
    *,
    extra_meta: dict[str, Any] | None = None,
) -> None:
    """Save per-Q-A score arrays for later bootstrap analysis.

    Structure on disk:
        {
          "meta": {...},
          "systems": {
            "<label>": {
              "<retriever>__mrr@<k>": [floats, ...],
              ...
            }
          }
        }
    """
    out: dict[str, Any] = {"meta": extra_meta or {}, "systems": {}}
    for label, per_rk in per_qa.items():
        out["systems"][label] = {
            f"{rname}__mrr@{k}": arr.tolist() for (rname, k), arr in per_rk.items()
        }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(out, ensure_ascii=False))


def load_per_qa_arrays(
    path: str | Path,
) -> tuple[dict[str, dict[tuple[str, int], np.ndarray]], dict[str, Any]]:
    """Reverse of save_per_qa_arrays."""
    raw = json.loads(Path(path).read_text())
    systems: dict[str, dict[tuple[str, int], np.ndarray]] = {}
    for label, rk_map in raw["systems"].items():
        per_rk: dict[tuple[str, int], np.ndarray] = {}
        for key, vals in rk_map.items():
            rname, suffix = key.rsplit("__", 1)
            k = int(suffix.removeprefix("mrr@"))
            per_rk[(rname, k)] = np.asarray(vals, dtype=float)
        systems[label] = per_rk
    return systems, raw.get("meta", {})
