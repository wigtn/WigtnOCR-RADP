"""OHR-Bench cross-domain TextNED (text fidelity) — paper §4.5 replication.

Computes per-page normalised edit distance (NED) of each parser variant's
markdown against the OHR-Bench ground-truth page text, then a paired
percentile bootstrap of the per-page delta vs v1.

NED = character-level Levenshtein distance / max(len) via rapidfuzz, so
0 = identical, 1 = fully disjoint — the standard NED that OHR-Bench's
text-fidelity metric is based on (NOT difflib's Ratcliff-Obershelp ratio).

Inputs (all local, no GPU):
  - parses:  output/parses_ohrbench/{v1,dpo_v1,dpo_v4,v5}/{domain}/{docid}__p{N}.md
  - GT:      data/OHR-Bench/retrieval_extracted/gt/{domain}/{docid}.json  (array; [N]["text"])
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
from rapidfuzz.distance import Levenshtein

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] OHRNED: %(message)s")
log = logging.getLogger("ohrned")

ROOT = Path("/mnt/data1/work/WigtnOCR-RADP")
PARSES = ROOT / "output/parses_ohrbench"
GT_DIR = ROOT / "data/OHR-Bench/retrieval_extracted/gt"
VARIANTS = ["v1", "dpo_v1", "dpo_v4", "v5"]
N_BOOT = 1000
SEED = 20260603


def text_ned(a: str, b: str) -> float:
    return Levenshtein.normalized_distance(a, b)


def load_gt_page(cache: dict[Path, list], gt_path: Path, page_idx: int) -> str | None:
    if gt_path not in cache:
        try:
            cache[gt_path] = json.loads(gt_path.read_text())
        except FileNotFoundError:
            cache[gt_path] = []
    arr = cache[gt_path]
    if 0 <= page_idx < len(arr):
        return arr[page_idx].get("text", "")
    return None


def per_page_ned(variant: str, gt_cache: dict) -> dict[str, float]:
    """Return {page_key: ned} for one variant over all domains/pages."""
    out: dict[str, float] = {}
    vdir = PARSES / variant
    for md_file in sorted(vdir.rglob("*.md")):
        domain = md_file.parent.name
        stem = md_file.stem  # docid__pN
        if "__p" not in stem:
            continue
        docid, pstr = stem.rsplit("__p", 1)
        try:
            page_idx = int(pstr)
        except ValueError:
            continue
        gt_path = GT_DIR / domain / f"{docid}.json"
        gt_text = load_gt_page(gt_cache, gt_path, page_idx)
        if gt_text is None:
            continue
        out[f"{domain}/{stem}"] = text_ned(md_file.read_text(), gt_text)
    return out


def main() -> int:
    gt_cache: dict[Path, list] = {}
    neds = {v: per_page_ned(v, gt_cache) for v in VARIANTS}
    for v in VARIANTS:
        log.info("%s: %d pages, mean NED = %.4f", v, len(neds[v]), float(np.mean(list(neds[v].values()))))

    rng = np.random.default_rng(SEED)
    results: dict[str, dict] = {}
    v1 = neds["v1"]
    for v in VARIANTS:
        mean = round(float(np.mean(list(neds[v].values()))), 4)
        entry = {"n_pages": len(neds[v]), "mean_ned": mean}
        if v != "v1":
            # paired delta vs v1 on the shared page set
            keys = [k for k in neds[v] if k in v1]
            delta = np.array([neds[v][k] - v1[k] for k in keys])
            n = len(delta)
            boot = np.array([delta[rng.integers(0, n, n)].mean() for _ in range(N_BOOT)])
            lo, hi = np.percentile(boot, [2.5, 97.5])
            entry.update({
                "n_paired": n,
                "mean_delta_vs_v1": round(float(delta.mean()), 5),
                "ci95": [round(float(lo), 5), round(float(hi), 5)],
                "pct_change_vs_v1": round(100 * float(delta.mean()) / float(np.mean([v1[k] for k in keys])), 2),
                "two_sided_sig": bool(lo < 0 and hi < 0) or bool(lo > 0 and hi > 0),
            })
        results[v] = entry

    out_path = ROOT / "output/results/ohr_text_ned.json"
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    log.info("wrote %s", out_path)
    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
