"""Probe-subset bootstrap for ranking stability (reviewer bXGg, Q1).

Draws `--subset-size` of the 663 probe questions without replacement,
`--iters` times (fixed seed), recomputes the system ranking on every subset,
and reports:

  (a) how often each system ranks first (headline: does Prod stay top-1);
  (b) the mean Kendall tau between the subset ranking and the full-probe
      ranking, plus the fraction of resamples whose ranking is unchanged;
  (c) the per-system rank distribution.
  (d) optional pairwise ordering rates requested with `--pair LEFT>RIGHT`.

Two input modes (mixable is not supported — pick one):

  --perqa       per-QA retrieval dumps written by `grid_single_parser.py` or the
                training-eval harness (`FULL_HF_perqa_242p.json`), schema
                  systems["<label>__<chunker>"]["<retriever>__mrr@<k>"] = [floats]
                aligned to meta.qa_ids. Select/rename systems with repeated
                `--system "<raw key>=<display name>"`.
  --e2e-detail  the end-to-end per-QA log (`e2e_rag_detail.jsonl`, one row per
                (parser, qa_id) with a boolean `correct`); systems = parsers and
                the metric is answer accuracy.

Per-QA metric for --perqa mode:
  rcps   = elementwise mean over every <retriever>__mrr@<k> series
           (the paper's retriever-and-cutoff-averaged RCPS)
  hit@1  = elementwise mean over the three <retriever>__mrr@1 series
  mrr@10 = elementwise mean over the three <retriever>__mrr@10 series

`--expect NAME=VALUE` asserts the full-probe mean for NAME (sanity gate against
the committed aggregate artefacts) before any bootstrap runs.

Usage:
    .venv/bin/python scripts/analysis/rank_stability_bootstrap.py \
        --perqa output/results/FULL_HF_perqa_242p.json \
                output/results/perqa_MinerU-tableON_parser_native.json \
        --system "v1 (ref)__parser_native=Prod" \
        --system "MinerU-tableON__parser_native=MinerU-tableON" \
        --metric rcps --top Prod --expect Prod=0.582573 \
        --out output/results/rank_stability_parser_rcps.json
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

METRIC_SERIES = {
    "rcps": lambda key: "__mrr@" in key,
    "hit@1": lambda key: key.endswith("__mrr@1"),
    "mrr@10": lambda key: key.endswith("__mrr@10"),
}


def load_perqa(paths: list[str], selections: dict[str, str], metric: str) -> dict[str, list[float]]:
    """Return {display name: per-QA score vector}, validating qa_id alignment."""
    want = METRIC_SERIES[metric]
    scores: dict[str, list[float]] = {}
    ref_ids: list[str] | None = None
    for path in paths:
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        ids = d["meta"]["qa_ids"]
        if ref_ids is None:
            ref_ids = ids
        elif ids != ref_ids:
            raise SystemExit(f"{path}: meta.qa_ids differs from the first file — cannot align")
        for raw, name in selections.items():
            if raw not in d["systems"]:
                continue
            series = [v for k, v in d["systems"][raw].items() if want(k)]
            if not series:
                raise SystemExit(f"{path}: {raw} has no series for metric {metric}")
            n = len(series[0])
            scores[name] = [sum(s[i] for s in series) / len(series) for i in range(n)]
    missing = set(selections.values()) - set(scores)
    if missing:
        raise SystemExit(f"systems not found in any --perqa file: {sorted(missing)}")
    return scores


def load_e2e(path: str) -> dict[str, list[float]]:
    """Return {parser: per-QA correct(0/1)} aligned on the shared qa_id order."""
    rows: dict[str, dict[str, float]] = defaultdict(dict)
    order: list[str] = []
    seen: set[str] = set()
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                rows[r["parser"]][r["qa_id"]] = 1.0 if r["correct"] else 0.0
                if r["qa_id"] not in seen:
                    seen.add(r["qa_id"])
                    order.append(r["qa_id"])
    parsers = sorted(rows)
    for p in parsers:
        if set(rows[p]) != seen:
            raise SystemExit(f"{path}: parser {p} covers {len(rows[p])}/{len(seen)} qa_ids")
    return {p: [rows[p][q] for q in order] for p in parsers}


def ranking(means: dict[str, float]) -> list[str]:
    """Systems best-first; deterministic name tie-break."""
    return sorted(means, key=lambda s: (-means[s], s))


def kendall_tau(full: list[str], sub: list[str]) -> float:
    """Kendall tau-a between two orderings of the same systems."""
    pos_f = {s: i for i, s in enumerate(full)}
    pos_s = {s: i for i, s in enumerate(sub)}
    items = list(full)
    conc = disc = 0
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a, b = items[i], items[j]
            agree = (pos_f[a] - pos_f[b]) * (pos_s[a] - pos_s[b])
            if agree > 0:
                conc += 1
            elif agree < 0:
                disc += 1
    n_pairs = len(items) * (len(items) - 1) // 2
    return (conc - disc) / n_pairs if n_pairs else 1.0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--perqa", nargs="+", default=[], help="per-QA JSON dumps")
    ap.add_argument("--system", action="append", default=[],
                    help='"<raw systems key>=<display name>" (repeatable)')
    ap.add_argument("--e2e-detail", default=None, help="e2e_rag_detail.jsonl")
    ap.add_argument("--metric", choices=sorted(METRIC_SERIES), default="rcps")
    ap.add_argument("--subset-size", type=int, default=500)
    ap.add_argument("--iters", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--top", default="Prod", help="system for the headline top-1 rate")
    ap.add_argument(
        "--pair", action="append", default=[],
        help='pairwise stability as "LEFT>RIGHT" using display names (repeatable)',
    )
    ap.add_argument("--expect", action="append", default=[],
                    help='"NAME=VALUE" full-probe mean sanity check (abs tol 1e-6)')
    ap.add_argument("--out", default=None, help="write the result JSON here")
    args = ap.parse_args()

    if bool(args.perqa) == bool(args.e2e_detail):
        raise SystemExit("use exactly one of --perqa ... or --e2e-detail")
    if args.e2e_detail:
        scores = load_e2e(args.e2e_detail)
        metric = "answer_accuracy"
    else:
        if not args.system:
            raise SystemExit("--perqa mode needs at least one --system mapping")
        selections = dict(s.split("=", 1) for s in args.system)
        scores = load_perqa(args.perqa, selections, args.metric)
        metric = args.metric

    n_qa = {len(v) for v in scores.values()}
    if len(n_qa) != 1:
        raise SystemExit(f"per-QA vectors disagree in length: {sorted(n_qa)}")
    n = n_qa.pop()
    if not 0 < args.subset_size <= n:
        raise SystemExit(f"--subset-size must be in 1..{n}")

    full_means = {s: sum(v) / n for s, v in scores.items()}
    for spec in args.expect:
        name, val = spec.split("=", 1)
        if name not in full_means:
            raise SystemExit(f"--expect {name}: unknown system")
        if abs(full_means[name] - float(val)) > 1e-6:
            raise SystemExit(
                f"sanity FAIL {name}: full mean {full_means[name]:.6f} != expected {val}"
            )
    full_rank = ranking(full_means)
    if args.top not in full_means:
        raise SystemExit(f"--top {args.top!r} not among systems {sorted(full_means)}")
    pairs: list[tuple[str, str]] = []
    for spec in args.pair:
        if ">" not in spec:
            raise SystemExit(f"--pair {spec!r}: expected LEFT>RIGHT")
        left, right = (part.strip() for part in spec.split(">", 1))
        if left not in full_means or right not in full_means:
            raise SystemExit(
                f"--pair {spec!r}: names must be among {sorted(full_means)}"
            )
        if left == right:
            raise SystemExit(f"--pair {spec!r}: LEFT and RIGHT must differ")
        pairs.append((left, right))

    rng = random.Random(args.seed)
    idx_all = range(n)
    top1 = Counter()
    rank_dist: dict[str, Counter] = {s: Counter() for s in scores}
    taus: list[float] = []
    unchanged = 0
    pair_counts = {pair: Counter() for pair in pairs}
    for _ in range(args.iters):
        idx = rng.sample(idx_all, args.subset_size)
        means = {s: sum(v[i] for i in idx) / args.subset_size for s, v in scores.items()}
        sub_rank = ranking(means)
        top1[sub_rank[0]] += 1
        for r, s in enumerate(sub_rank, start=1):
            rank_dist[s][r] += 1
        taus.append(kendall_tau(full_rank, sub_rank))
        unchanged += sub_rank == full_rank
        for left, right in pairs:
            if means[left] > means[right]:
                pair_counts[(left, right)]["left_above"] += 1
            elif means[left] < means[right]:
                pair_counts[(left, right)]["right_above"] += 1
            else:
                pair_counts[(left, right)]["tie"] += 1

    result = {
        "config": {
            "metric": metric, "n_qa": n, "subset_size": args.subset_size,
            "iters": args.iters, "seed": args.seed, "sampling": "without replacement",
            "inputs": args.perqa or [args.e2e_detail],
        },
        "full_probe": {"means": full_means, "ranking": full_rank},
        "top1_rate": {s: top1.get(s, 0) / args.iters for s in full_rank},
        "kendall_tau": {"mean": sum(taus) / len(taus), "min": min(taus)},
        "ranking_unchanged_rate": unchanged / args.iters,
        "rank_distribution": {s: {str(r): c / args.iters for r, c in sorted(rank_dist[s].items())}
                              for s in full_rank},
        "pairwise_ordering": {
            f"{left}>{right}": {
                "full_probe_delta": full_means[left] - full_means[right],
                "left_above_rate": pair_counts[(left, right)]["left_above"] / args.iters,
                "tie_rate": pair_counts[(left, right)]["tie"] / args.iters,
                "right_above_rate": pair_counts[(left, right)]["right_above"] / args.iters,
            }
            for left, right in pairs
        },
    }

    print(f"metric={metric}  n={n}  subset={args.subset_size}x{args.iters}  seed={args.seed}")
    print(f"full ranking: {' > '.join(full_rank)}  "
          f"(means: {', '.join(f'{s}={full_means[s]:.4f}' for s in full_rank)})")
    print(f"(a) top-1 rate [{args.top}]: {result['top1_rate'].get(args.top, 0.0):.1%}")
    print(
        f"(b) Kendall tau: mean={result['kendall_tau']['mean']:.4f} "
        f"min={result['kendall_tau']['min']:.2f}  "
        f"ranking unchanged: {result['ranking_unchanged_rate']:.1%}"
    )
    print("(c) rank distribution:")
    for s in full_rank:
        cells = "  ".join(f"r{r}:{result['rank_distribution'][s].get(str(r), 0.0):.1%}"
                          for r in range(1, len(full_rank) + 1))
        print(f"    {s:<18} {cells}")
    if pairs:
        print("(d) pairwise ordering:")
        for left, right in pairs:
            stats = result["pairwise_ordering"][f"{left}>{right}"]
            print(
                f"    {left} > {right}: {stats['left_above_rate']:.1%} "
                f"(tie {stats['tie_rate']:.1%}, reversed {stats['right_above_rate']:.1%}; "
                f"full delta={stats['full_probe_delta']:.6f})"
            )

    if args.out:
        Path(args.out).write_text(
            json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
