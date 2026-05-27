"""PHASE_1 §1.2 — sample 100 Q-A for verification, stratified by domain/language/type.

Writes the sample to data/KoGovDoc-RAG/qa_verification_sample_v1.jsonl with a
blank `verification` block per record (axes: question naturalness, answer
correctness, span-location correctness) for the reviewer to fill in.
"""

from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path

QA_PATH = Path("data/KoGovDoc-RAG/qa_pairs_v1.jsonl")
OUT_PATH = Path("data/KoGovDoc-RAG/qa_verification_sample_v1.jsonl")
N_SAMPLE = 100
SEED = 42


def main() -> int:
    rows = [json.loads(line) for line in QA_PATH.read_text().splitlines() if line.strip()]
    rng = random.Random(SEED)

    # Stratify by (domain, language, question_type); allocate proportionally.
    strata: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for r in rows:
        strata[(r["domain"], r["language"], r["question_type"])] = strata[
            (r["domain"], r["language"], r["question_type"])
        ] + [r]

    sample: list[dict] = []
    for key, group in strata.items():
        share = round(N_SAMPLE * len(group) / len(rows))
        share = min(share, len(group))
        sample.extend(rng.sample(group, share) if share else [])
    # Top up / trim to exactly N_SAMPLE.
    remaining = [r for r in rows if r not in sample]
    rng.shuffle(remaining)
    while len(sample) < N_SAMPLE and remaining:
        sample.append(remaining.pop())
    sample = sample[:N_SAMPLE]
    rng.shuffle(sample)

    with OUT_PATH.open("w", encoding="utf-8") as f:
        for r in sample:
            f.write(json.dumps({
                "qa_id": r["qa_id"],
                "page_id": r["page_id"],
                "domain": r["domain"],
                "language": r["language"],
                "question_type": r["question_type"],
                "difficulty": r["difficulty"],
                "question": r["question"],
                "answer_span": r["answer_span"],
                "answer_chunk": r["answer_chunk"],
                "verification": {
                    "question_natural": None,   # bool — natural & answerable
                    "answer_correct": None,     # bool — answer_span answers the question
                    "span_located": None,       # bool — span sits correctly in answer_chunk
                    "accept": None,             # bool — overall accept
                    "notes": "",
                },
            }, ensure_ascii=False) + "\n")

    # Report the realised stratification.
    from collections import Counter
    dist = Counter((r["domain"], r["language"], r["question_type"]) for r in sample)
    print(f"sampled {len(sample)} Q-A → {OUT_PATH}")
    print("strata (domain, lang, type): count")
    for k, v in sorted(dist.items()):
        print(f"  {k}: {v}")
    print("difficulty:", dict(Counter(r["difficulty"] for r in sample)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
