"""LLM-judge semantic ceiling (L5) for the family-neutral absent diagnostic.

The matcher ladder (`absent_robustness.py`) is deterministic but still string-
based. This script closes the loop with a *cross-family* judge — OpenAI GPT
(NOT the Qwen family that produced the reference, the parsers, or the gold
spans) — so no same-family surface bias can survive.

For each parser, we take the answers it marks *absent* under the paper's L1
matcher and ask the judge, per answer, a three-way retriever-recoverability
label (criterion in docs/ADJUDICATION_absent_criteria.md):

    present   — the fact is stated and a retriever could recover it -> artifact
                (a surface/notation mismatch, NOT a parser loss)
    degraded  — characters physically present but not retriever-recoverable
                (value detached from its header, OCR-corrupted digits, fragmented)
                -> true-absent
    absent    — content not on the page at all -> true-absent

    genuine_absent = degraded + absent ; artifact = present
    semantic_absent_rate = genuine_absent / total = (L1_absent - artifact) / total

Judging recoverability (not mere string existence) keeps the label coherent with
the paper's own relevance rule: a chunk is relevant iff a retriever can surface
it, so present-but-unrecoverable content scores zero and is absent by that rule.
Running the judge on Prod's own absent set (the default includes Prod) makes the
check symmetric — any pro-Qwen bias in L1 would show as a *higher* artifact
fraction for the OCR parsers, and we subtract it out.

The rebuttal claim holds if MinerU/PaddleOCR keep a large semantic_absent gap
over Prod: their content is genuinely missing, not mismatched. Running the judge
on Prod's own absent set (the default includes Prod) makes the check symmetric —
we report each parser's artifact fraction, so any pro-Qwen bias in L1 would show
up as a *higher* artifact fraction for the OCR parsers, and we subtract it out.

Cost control: results are cached to a jsonl keyed by (parser, qa_id) so re-runs
resume. Use --max_per_parser to cap calls while piloting.

Usage:
    export OPENAI_API_KEY=sk-...
    uv run python scripts/evaluation/absent_llm_judge.py
    uv run python scripts/evaluation/absent_llm_judge.py --parsers Prod MinerU PaddleOCR --max_per_parser 60
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from wigtnocr_radp.evaluation.absent_matchers import l1_normalized
from wigtnocr_radp.evaluation.parser_outputs import load_parser_outputs
from wigtnocr_radp.evaluation.rcps import load_qa_pairs

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("absent_llm_judge")

# Cross-family judge. NOT a Qwen model — that is the whole point.
DEFAULT_MODEL = "gpt-5.4-2026-03-05"

# Parser output roots (keep in sync with absent_robustness.py / baseline_grid.py).
KOGOV_ROOT = Path("/mnt/data1/work/wigtnOCR-v1/results/kogovdoc")
VAL_JSONL = Path("data/KoGovDoc-Bench/val.jsonl")
PARSERS: dict[str, str] = {
    "Prod": "v1_val/predictions",
    "Qwen3-VL-30B": "30b_val/predictions",
    "Qwen3-VL-2B-base": "2b_base_val/predictions",
    "MinerU": "mineru_val/predictions",
    "PaddleOCR": "paddleocr_val/predictions",
    "Marker": "marker_val/predictions",
}

# Three-way, retriever-recoverability criterion (see docs/ADJUDICATION_absent_criteria.md).
# The object of this paper is retrieval, not string existence: content present only as
# OCR-mangled fragments a retriever cannot surface is Degraded and counts as true-absent.
SYSTEM = (
    "You judge whether a document page lets a RETRIEVER answer a question. The page "
    "was produced by an automatic parser and may differ in wording, spacing, number "
    "formatting, or markdown from any reference — judge CONTENT and RECOVERABILITY, "
    "not surface formatting. Decide solely from the page text; no outside knowledge, "
    "no guessing. Assign exactly one label:\n"
    "- present: the specific fact the question asks for is stated on the page AND a "
    "reader could locate it from the query terms (its row/column label or context and "
    "its value both survive, even if numbers/units/whitespace/markdown are formatted "
    "differently).\n"
    "- degraded: the fact's characters are physically on the page but a retriever "
    "could not recover it — e.g. the value is detached from the row/header that "
    "identifies it, OCR corruption alters a digit/character of a numeric/spec answer, "
    "or it is fragmented across non-adjacent lines.\n"
    "- absent: the content is not on the page at all (e.g. a table rendered as an "
    "image reference, a missing row/section).\n"
    "Tie-break: if unsure between present and degraded, choose present."
)

USER_TEMPLATE = (
    "QUESTION:\n{question}\n\n"
    "EXPECTED ANSWER (from an independent reference):\n{answer}\n\n"
    "PARSER PAGE TEXT:\n---\n{page}\n---\n\n"
    "Label whether a retriever could recover the answer from the page text above "
    "(present / degraded / absent)."
)

JUDGE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "recoverability_judgment",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "label": {"type": "string", "enum": ["present", "degraded", "absent"]},
                "evidence": {
                    "type": "string",
                    "description": "Verbatim quote from the page if present/degraded, else empty.",
                },
            },
            "required": ["label", "evidence"],
        },
    },
}


def _judge(client: OpenAI, model: str, question: str, answer: str, page: str) -> dict[str, Any]:
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": USER_TEMPLATE.format(
                question=question, answer=answer, page=page[:12000])},
        ],
        response_format=JUDGE_SCHEMA,
    )
    return json.loads(resp.choices[0].message.content)


def _load_cache(path: Path) -> dict[tuple[str, str], dict[str, Any]]:
    cache: dict[tuple[str, str], dict[str, Any]] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                cache[(r["parser"], r["qa_id"])] = r
    return cache


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--qa", default="data/KoGovDoc-RAG/qa_pairs_v1.jsonl")
    ap.add_argument("--root", type=Path, default=KOGOV_ROOT)
    ap.add_argument("--val_jsonl", type=Path, default=VAL_JSONL)
    ap.add_argument("--parsers", nargs="*", default=["Prod", "MinerU", "PaddleOCR"])
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--max_per_parser", type=int, default=0, help="0 = judge all L1-absent")
    ap.add_argument("--override", nargs="*", default=[], metavar="NAME=SUBDIR",
                    help="override a parser's output subdir, e.g. "
                         "MinerU=mineru_val_tableon/predictions")
    ap.add_argument("--out_dir", type=Path, default=Path("output/diagnostics"))
    args = ap.parse_args()

    for ov in args.override:
        name, _, sub = ov.partition("=")
        if name in PARSERS and sub:
            PARSERS[name] = sub
            logger.info("override: %s -> %s", name, sub)

    load_dotenv()
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY not set")
    client = OpenAI()

    qa_pairs = load_qa_pairs(args.qa)
    total = len(qa_pairs)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    cache_path = args.out_dir / "absent_llm_judge_cache.jsonl"
    cache = _load_cache(cache_path)

    summary: dict[str, Any] = {}
    with cache_path.open("a", encoding="utf-8") as cache_f:
        for name in args.parsers:
            subdir = PARSERS.get(name)
            if subdir is None:
                logger.warning("unknown parser %s (known: %s)", name, list(PARSERS))
                continue
            pdir = Path(subdir) if Path(subdir).is_absolute() else args.root / subdir
            if not pdir.is_dir():
                logger.warning("skip %s: %s not found", name, pdir)
                continue
            pages = load_parser_outputs(pdir, args.val_jsonl)

            l1_absent = [qa for qa in qa_pairs
                         if not l1_normalized(qa.answer_span, pages.get(qa.page_id, ""))]
            judged = l1_absent if args.max_per_parser <= 0 else l1_absent[: args.max_per_parser]

            labels = {"present": 0, "degraded": 0, "absent": 0}
            no_page = 0
            for qa in judged:
                page = pages.get(qa.page_id)
                if page is None:  # genuinely no output -> absent (not an artifact)
                    no_page += 1
                    labels["absent"] += 1
                    continue
                key = (name, qa.qa_id)
                if key in cache:
                    verdict = cache[key]
                else:
                    v = _judge(client, args.model, qa.question, qa.answer_span, page)
                    verdict = {"parser": name, "qa_id": qa.qa_id,
                               "question_type": qa.question_type,
                               "label": v["label"], "evidence": v["evidence"]}
                    cache_f.write(json.dumps(verdict, ensure_ascii=False) + "\n")
                    cache_f.flush()
                    cache[key] = verdict
                labels[verdict["label"]] += 1

            # artifact = judged present (a surface mismatch, not a parser loss).
            # genuine-absent = degraded + absent (both non-recoverable by a retriever).
            artifact = labels["present"]
            l1_absent_n = len(l1_absent)
            with_page = len(judged) - no_page  # items actually sent to the judge
            complete = len(judged) == l1_absent_n  # whole L1-absent set judged (not capped)
            genuine = l1_absent_n - artifact
            # semantic_absent_rate is only valid when the whole L1-absent set was
            # judged; a capped (--max_per_parser) pilot would overstate it, so gate it.
            sem_rate = genuine / total if complete else None
            summary[name] = {
                "total_qa": total,
                "l1_absent": l1_absent_n,
                "l1_absent_rate": l1_absent_n / total,
                "judged": len(judged),
                "judged_with_page": with_page,
                "no_page": no_page,
                "complete": complete,
                "labels": dict(labels),  # present / degraded / absent
                "artifact": artifact,
                "artifact_frac_of_absent": artifact / with_page if with_page else 0.0,
                "degraded_frac_of_absent": labels["degraded"] / with_page if with_page else 0.0,
                "genuine_absent": genuine if complete else None,
                "semantic_absent_rate": sem_rate,
            }
            logger.info("%s: L1-absent=%.1f%% -> semantic-absent=%s (artifact %d/%d)",
                        name, summary[name]["l1_absent_rate"] * 100,
                        f"{sem_rate * 100:.1f}%" if sem_rate is not None else "n/a (capped run)",
                        artifact, with_page)

    (args.out_dir / "absent_llm_judge.json").write_text(
        json.dumps({"config": {"model": args.model, "num_qa": total,
                              "note": "semantic_absent_rate is null unless the whole "
                                      "L1-absent set was judged (complete=true); use "
                                      "--max_per_parser 0 for the headline number"},
                   "parsers": summary}, ensure_ascii=False, indent=2))
    logger.info("wrote %s", args.out_dir / "absent_llm_judge.json")
    for name, s in summary.items():
        sem = f"{s['semantic_absent_rate']:.1%}" if s["semantic_absent_rate"] is not None else "n/a (capped)"
        lb = s["labels"]
        print(f"{name:12s}  L1-absent {s['l1_absent_rate']:.1%}  ->  "
              f"semantic-absent {sem}  "
              f"(present/degraded/absent = {lb['present']}/{lb['degraded']}/{lb['absent']}; "
              f"artifact {s['artifact_frac_of_absent']:.0%})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
