"""Compute Pearson r between v1 BC/CS scores and our RCPS — H1 verification.

Hypothesis H1 (RADP_RESEARCH_PROPOSAL §2):
    parsing↔retrieval correlation Pearson r < 0.5
    (reproduce EnterpriseDocBench's r=0.14 in Korean domain)

Sources:
    - BC/CS: v1's `bccs_eval_all/bccs_summary.json` (semantic strategy, doc-level)
    - RCPS:  `output/baselines/grid_v1_<chunker>.json`

Output: `output/baselines/correlation_v1.json` + markdown table.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

V1_BCCS = Path("/mnt/data1/work/wigtnOCR-v1/results/kogovdoc/bccs_eval_all/bccs_summary.json")
GRID = Path("output/baselines/grid_v1_parser_native.json")
OUT_DIR = Path("output/baselines")


# Maps v1 BC/CS keys -> grid parser display names
PARSER_MAP = {
    "marker_semantic": "Marker",
    "mineru_semantic": "MinerU",
    "paddleocr_semantic": "PaddleOCR",
    "qwen3vl2b_semantic": "Qwen3-VL-2B (base)",
    "qwen3vl30b_semantic": "Qwen3-VL-30B (teacher)",
    "wigtnocr_semantic": "WigtnOCR-2B (ours, v1)",
}


def pearson_r(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return float("nan")
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True))
    denom = math.sqrt(sxx * syy)
    if denom == 0:
        return float("nan")
    return sxy / denom


def spearman_r(xs: list[float], ys: list[float]) -> float:
    def rank(v: list[float]) -> list[float]:
        s = sorted((x, i) for i, x in enumerate(v))
        out = [0.0] * len(v)
        i = 0
        while i < len(s):
            j = i
            while j + 1 < len(s) and s[j + 1][0] == s[i][0]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                out[s[k][1]] = avg
            i = j + 1
        return out

    return pearson_r(rank(xs), rank(ys))


def main() -> None:
    bccs = json.loads(V1_BCCS.read_text())
    grid = json.loads(GRID.read_text())
    rcps_by_name = {p["name"]: p for p in grid["parsers"]}

    rows: list[dict[str, float | str | int]] = []
    for key, name in PARSER_MAP.items():
        if key not in bccs or name not in rcps_by_name:
            continue
        rows.append(
            {
                "parser": name,
                "bc": bccs[key]["bc_avg"],
                "cs": bccs[key]["cs_avg"],
                "rcps": rcps_by_name[name]["rcps"],
                "hit@1": rcps_by_name[name]["hit@1"],
                "mrr@10": rcps_by_name[name]["mrr@10"],
                "num_pages": rcps_by_name[name]["num_pages"],
            }
        )

    # Full set (all 6) — Marker is page-coverage-partial (38/294)
    full_bc = [r["bc"] for r in rows]
    full_cs = [r["cs"] for r in rows]
    full_rcps = [r["rcps"] for r in rows]
    full_hit = [r["hit@1"] for r in rows]

    # Subset excluding Marker (apples-to-apples 294-page comparison)
    sub = [r for r in rows if r["parser"] != "Marker"]
    sub_bc = [r["bc"] for r in sub]
    sub_cs = [r["cs"] for r in sub]
    sub_rcps = [r["rcps"] for r in sub]
    sub_hit = [r["hit@1"] for r in sub]

    correlations = {
        "all_6_parsers": {
            "n": len(full_bc),
            "pearson_BC_vs_RCPS": pearson_r(full_bc, full_rcps),
            "pearson_BC_vs_Hit1": pearson_r(full_bc, full_hit),
            "pearson_CS_vs_RCPS": pearson_r(full_cs, full_rcps),  # CS lower=better
            "spearman_BC_vs_RCPS": spearman_r(full_bc, full_rcps),
        },
        "excluding_marker_5_parsers": {
            "n": len(sub_bc),
            "pearson_BC_vs_RCPS": pearson_r(sub_bc, sub_rcps),
            "pearson_BC_vs_Hit1": pearson_r(sub_bc, sub_hit),
            "pearson_CS_vs_RCPS": pearson_r(sub_cs, sub_rcps),
            "spearman_BC_vs_RCPS": spearman_r(sub_bc, sub_rcps),
        },
    }

    summary = {"parsers": rows, "correlations": correlations}

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "correlation_v1.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2)
    )

    # Markdown
    lines: list[str] = []
    lines.append("# Parsing↔Retrieval Correlation (H1 verification)")
    lines.append("")
    lines.append("Sources: v1 BC/CS (semantic chunker, doc-level), our RCPS (parser_native, BGE-M3).")
    lines.append("")
    lines.append("| Parser | pages | BC | CS | RCPS | Hit@1 |")
    lines.append("|--------|:----:|:----:|:----:|:----:|:----:|")
    for r in sorted(rows, key=lambda x: x["rcps"], reverse=True):
        lines.append(
            f"| {r['parser']} | {r['num_pages']} | {r['bc']:.4f} | {r['cs']:.4f} "
            f"| {r['rcps']:.4f} | {r['hit@1']:.4f} |"
        )
    lines.append("")
    lines.append("## Correlation tests")
    lines.append("")
    for label, c in correlations.items():
        lines.append(f"### {label} (n={c['n']})")
        lines.append("")
        lines.append("| Pair | Pearson r | (H1 target: r < 0.5) |")
        lines.append("|------|:---------:|:--------------------:|")
        for k, v in c.items():
            if k == "n":
                continue
            verdict = "✅" if abs(v) < 0.5 else "⚠️"
            lines.append(f"| {k} | {v:+.4f} | {verdict} |")
        lines.append("")

    (OUT_DIR / "correlation_v1.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
