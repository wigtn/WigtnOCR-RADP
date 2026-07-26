"""Score human P/D/A verdicts from the blind absent-verification sheet.

The evidence for the rebuttal is the HUMAN verdicts — the ladder and the LLM
judge are automated and cannot answer the reviewer's human-verification ask.
This scorer turns grader downloads (`absent_blind_<name>.json`, produced by
`verification_sheet.html`) plus the private `answer_key.json` into the numbers
the rebuttal reports, per `docs/ADJUDICATION_absent_criteria.md`:

  - per-parser P/D/A counts, artefact rate (= P / judged) with Wilson 95% CI,
    genuine-absent rate (= (D+A) / judged) with Wilson 95% CI;
  - with 2+ graders: Cohen's kappa (3-way) on co-judged cases + the disagreement
    list for third-party adjudication (final label = agreed label; disagreements
    stay unresolved until an `--adjudicated` file settles them);
  - optionally, agreement vs the WSL LLM-judge cache (human vs GPT), 3-way and
    binary (P vs D+A).

Usage:
    .venv/bin/python scripts/analysis/score_absent_blind.py \
        --results output/human_verify/absent_blind_harrison.json \
                  output/human_verify/absent_blind_sangwoo.json \
        [--adjudicated output/human_verify/adjudicated.json] \
        [--judge-cache output/diagnostics/absent_llm_judge_cache.jsonl]

`--adjudicated`: {"<case_id>": "P"|"D"|"A"} for cases the two graders disagreed on.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

LABELS = ("P", "D", "A")
LABEL_TO_JUDGE = {"P": "present", "D": "degraded", "A": "absent"}


def wilson_ci(k: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def cohens_kappa(pairs: list[tuple[str, str]]) -> float:
    """Cohen's kappa for two raters over categorical labels."""
    n = len(pairs)
    if n == 0:
        return float("nan")
    po = sum(1 for a, b in pairs if a == b) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum(ca[l] * cb[l] for l in LABELS) / (n * n)
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", nargs="+", required=True)
    ap.add_argument("--key", default="output/human_verify/answer_key.json")
    ap.add_argument("--adjudicated", default=None,
                    help='{"case_id": "P|D|A"} settling grader disagreements')
    ap.add_argument("--judge-cache", default=None,
                    help="WSL absent_llm_judge_cache.jsonl for human-vs-LLM agreement")
    args = ap.parse_args()

    key = json.loads(Path(args.key).read_text())["key"]

    # grader -> {case_id: judgment}
    by_grader: dict[str, dict[str, str]] = {}
    for path in args.results:
        for row in json.loads(Path(path).read_text()):
            if row.get("judgment") in LABELS:
                by_grader.setdefault(row["grader"], {})[str(row["case_id"])] = row["judgment"]
    graders = sorted(by_grader)
    print(f"graders: {graders}  "
          f"(judged: {', '.join(str(len(by_grader[g])) for g in graders)})\n")

    adjudicated: dict[str, str] = {}
    if args.adjudicated:
        adjudicated = json.loads(Path(args.adjudicated).read_text())
        bad = {k: v for k, v in adjudicated.items() if v not in LABELS}
        if bad:
            raise SystemExit(f"--adjudicated labels must be P/D/A; invalid: {bad}")

    # -- final label per case: unanimous, else adjudicated, else unresolved ---
    final: dict[str, str] = {}
    disagreements: list[str] = []
    for cid in key:
        votes = [by_grader[g][cid] for g in graders if cid in by_grader[g]]
        if not votes:
            continue
        if len(set(votes)) == 1:
            final[cid] = votes[0]
        elif cid in adjudicated:
            final[cid] = adjudicated[cid]
        else:
            disagreements.append(cid)

    # -- per-parser table ------------------------------------------------------
    per_parser: dict[str, Counter] = defaultdict(Counter)
    for cid, label in final.items():
        per_parser[key[cid]["parser"]][label] += 1

    print("| parser | judged | P | D | A | artefact (P) [95% CI] | genuine absent (D+A) [95% CI] |")
    print("|--------|-------:|--:|--:|--:|----------------------|-------------------------------|")
    for parser in sorted(per_parser):
        c = per_parser[parser]
        n = sum(c.values())
        art_lo, art_hi = wilson_ci(c["P"], n)
        gen_lo, gen_hi = wilson_ci(c["D"] + c["A"], n)
        print(f"| {parser} | {n} | {c['P']} | {c['D']} | {c['A']} "
              f"| {c['P'] / n:.3f} [{art_lo:.3f}, {art_hi:.3f}] "
              f"| {(c['D'] + c['A']) / n:.3f} [{gen_lo:.3f}, {gen_hi:.3f}] |")
    print()

    # -- inter-grader agreement -----------------------------------------------
    if len(graders) >= 2:
        for i in range(len(graders)):
            for j in range(i + 1, len(graders)):
                a, b = graders[i], graders[j]
                common = sorted(set(by_grader[a]) & set(by_grader[b]), key=int)
                pairs = [(by_grader[a][c], by_grader[b][c]) for c in common]
                agree = sum(1 for x, y in pairs if x == y)
                print(f"human-human [{a} vs {b}]: n={len(pairs)} "
                      f"agree={agree}/{len(pairs)} kappa={cohens_kappa(pairs):.3f}")
        if disagreements:
            print(f"UNRESOLVED disagreements (need 3rd adjudicator): "
                  f"{len(disagreements)} cases -> {', '.join(sorted(disagreements, key=int))}")
        print()

    # -- human vs LLM judge ----------------------------------------------------
    if args.judge_cache:
        llm: dict[tuple[str, str], str] = {}
        for line in Path(args.judge_cache).read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                llm[(r["parser"], r["qa_id"])] = r["label"]
        # key parser names -> judge cache parser names (MinerU-tableON judged as MinerU)
        alias = {"MinerU-tableON": "MinerU"}
        pairs3, pairs2 = [], []
        for cid, label in final.items():
            meta = key[cid]
            jl = llm.get((alias.get(meta["parser"], meta["parser"]), meta["qa_id"]))
            if jl is None:
                continue
            pairs3.append((LABEL_TO_JUDGE[label], jl))
            pairs2.append((label != "P", jl != "present"))  # binary: genuine-absent?
        if pairs3:
            agree3 = sum(1 for a, b in pairs3 if a == b)
            agree2 = sum(1 for a, b in pairs2 if a == b)
            print(f"human-vs-LLM: n={len(pairs3)} 3-way agree={agree3 / len(pairs3):.3f} "
                  f"binary(P vs D+A) agree={agree2 / len(pairs2):.3f}")
        else:
            print("human-vs-LLM: no overlapping (parser, qa_id) — check cache/alias")

    unresolved_note = f", unresolved={len(disagreements)}" if disagreements else ""
    print(f"\nfinal labels: {len(final)}{unresolved_note} "
          f"(정본 산출은 disagreement 0이 된 뒤에만 rebuttal에 인용)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
