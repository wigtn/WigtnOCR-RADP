"""Score human verification vs the LLM verdict, and vs itself if 2 graders.

Consumes the JSONL(s) downloaded from verify_sheet.html and the original LLM
verification sample, and reports the numbers for the R1/R3 construct-validity reply:
  - human accept rate (+ Wilson 95% CI), overall and by question_type,
  - human vs LLM agreement (% and Cohen's kappa) on the accept label,
  - if two grader files are given, human-human agreement (kappa) too.

Usage:
  python scripts/evaluation/score_human_verify.py \
      --human output/human_verify/verify_human_*.jsonl \
      --llm output/human_verify/qa_verification_sample_v1.jsonl
"""

from __future__ import annotations

import argparse
import glob
import json
import math
from collections import Counter, defaultdict
from pathlib import Path


def _wilson(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    z = 1.96
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def _kappa(a: list[bool], b: list[bool]) -> float:
    n = len(a)
    if n == 0:
        return float("nan")
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pa1 = sum(a) / n
    pb1 = sum(b) / n
    pe = pa1 * pb1 + (1 - pa1) * (1 - pb1)
    return (po - pe) / (1 - pe) if pe != 1 else 1.0


def _load_human(paths: list[str]) -> dict[str, list[dict]]:
    by_id: dict[str, list[dict]] = defaultdict(list)
    for p in paths:
        for line in Path(p).read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                by_id[r["qa_id"]].append(r)
    return by_id


def _llm_accept(sample_path: str) -> dict[str, bool]:
    out = {}
    for line in Path(sample_path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        v = r.get("verification") or {}
        acc = v.get("accept")
        # the LLM sample may store accept=null but have a separate results file;
        # fall back to True unless explicitly rejected.
        out[r["qa_id"]] = bool(acc) if acc is not None else None
        out[r["qa_id"] + "__type"] = r.get("question_type", "")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--human", nargs="+", required=True, help="grader JSONL(s) (globs ok)")
    ap.add_argument("--llm", default="output/human_verify/qa_verification_sample_v1.jsonl")
    ap.add_argument("--results", default="output/human_verify/qa_verification_results_v1.json",
                    help="LLM results json with the rejected list (for accept labels)")
    ap.add_argument("--out", default="output/human_verify/human_vs_llm.json")
    args = ap.parse_args()

    paths = [f for g in args.human for f in glob.glob(g)]
    if not paths:
        raise SystemExit("no human files matched")
    human = _load_human(paths)

    # LLM accept labels: prefer the results json's `rejected` list.
    llm_reject = set()
    rp = Path(args.results)
    if rp.exists():
        res = json.loads(rp.read_text())
        llm_reject = {r["qa_id"] for r in res.get("rejected", [])}
    qtype = {}
    for line in Path(args.llm).read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            qtype[r["qa_id"]] = r.get("question_type", "")

    # majority-vote human accept per qa
    ids = [q for q in human if not q.endswith("__type")]
    h_accept, l_accept, types = {}, {}, {}
    graders = defaultdict(dict)
    for q in ids:
        votes = [x.get("accept") for x in human[q] if x.get("accept") is not None]
        if not votes:
            continue
        h_accept[q] = sum(1 for v in votes if v) >= (len(votes) / 2)
        # short qa_id in reject list may be prefix; match by prefix
        l_accept[q] = not any(q.startswith(rj) or rj.startswith(q[:8]) for rj in llm_reject)
        types[q] = qtype.get(q, "")
        for x in human[q]:
            graders[x.get("grader", "anon")][q] = x.get("accept")

    common = [q for q in h_accept if q in l_accept]
    hk = sum(1 for q in common if h_accept[q])
    lo, hi = _wilson(hk, len(common))
    agree = sum(1 for q in common if h_accept[q] == l_accept[q]) / len(common) if common else 0
    kap = _kappa([h_accept[q] for q in common], [l_accept[q] for q in common])

    # by type
    bt = defaultdict(lambda: [0, 0])
    for q in common:
        bt[types[q]][1] += 1
        if h_accept[q]:
            bt[types[q]][0] += 1

    # human-human kappa if 2 graders
    hh = None
    gk = list(graders)
    if len(gk) >= 2:
        a, b = graders[gk[0]], graders[gk[1]]
        both = [q for q in a if q in b and a[q] is not None and b[q] is not None]
        if both:
            hh = {"graders": gk[:2], "n": len(both),
                  "kappa": _kappa([bool(a[q]) for q in both], [bool(b[q]) for q in both])}

    out = {
        "n": len(common),
        "human_accept_rate": hk / len(common) if common else 0,
        "human_accept_ci95": [lo, hi],
        "llm_accept_rate": sum(l_accept[q] for q in common) / len(common) if common else 0,
        "human_vs_llm_agreement": agree,
        "human_vs_llm_kappa": kap,
        "by_question_type": {t: {"accept": k, "n": n, "rate": k / n} for t, (k, n) in bt.items()},
        "human_human": hh,
    }
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"\nHeadline: human accept {out['human_accept_rate']:.0%} "
          f"[{lo:.0%},{hi:.0%}], vs LLM agreement {agree:.0%}, kappa {kap:.2f} (n={len(common)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
