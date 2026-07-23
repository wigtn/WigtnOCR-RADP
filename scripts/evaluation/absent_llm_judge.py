"""LLM-judge semantic ceiling (L5) for the family-neutral absent diagnostic.

The matcher ladder (`absent_robustness.py`) is deterministic but still string-
based. This script closes the loop with a *cross-family* judge — OpenAI GPT
(NOT the Qwen family that produced the reference, the parsers, or the gold
spans) — so no same-family surface bias can survive.

For each parser, we take the answers it marks *absent* under the paper's L1
matcher and ask the judge, per answer: "does this page's text contain the
information needed to answer this question?" (wording/formatting may differ).
Each absent answer is then relabelled:

    genuine_absent  — judge says the content is not on the page (real parser loss)
    artifact        — judge says the content IS present (L1 missed it: surface form)

Reported per parser:

    semantic_absent_rate = (L1_absent - artifact) / total

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

SYSTEM = (
    "You are a strict evaluator checking whether a document page contains the "
    "information needed to answer a question. The page text was produced by an "
    "automatic document parser and may differ in wording, spacing, number "
    "formatting, or markdown from any reference. Judge CONTENT, not formatting.\n"
    "Answer present=true ONLY if the specific fact needed to answer the question "
    "is actually stated on the page (in any surface form). Answer present=false if "
    "that fact is missing, even if the page is on a related topic. Do not guess or "
    "use outside knowledge — decide solely from the page text provided."
)

USER_TEMPLATE = (
    "QUESTION:\n{question}\n\n"
    "EXPECTED ANSWER (from an independent reference):\n{answer}\n\n"
    "PARSER PAGE TEXT:\n---\n{page}\n---\n\n"
    "Is the information needed to answer the question present in the page text above?"
)

JUDGE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "presence_judgment",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "present": {"type": "boolean"},
                "evidence": {
                    "type": "string",
                    "description": "Verbatim quote from the page if present, else empty.",
                },
            },
            "required": ["present", "evidence"],
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
    ap.add_argument("--out_dir", type=Path, default=Path("output/diagnostics"))
    args = ap.parse_args()

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

            artifact = 0
            no_page = 0
            for qa in judged:
                page = pages.get(qa.page_id)
                if page is None:  # genuinely no output -> not an artifact
                    no_page += 1
                    continue
                key = (name, qa.qa_id)
                if key in cache:
                    verdict = cache[key]
                else:
                    v = _judge(client, args.model, qa.question, qa.answer_span, page)
                    verdict = {"parser": name, "qa_id": qa.qa_id,
                               "question_type": qa.question_type,
                               "present": bool(v["present"]), "evidence": v["evidence"]}
                    cache_f.write(json.dumps(verdict, ensure_ascii=False) + "\n")
                    cache_f.flush()
                    cache[key] = verdict
                if verdict["present"]:
                    artifact += 1

            l1_absent_n = len(l1_absent)
            genuine = l1_absent_n - artifact  # (judged subset; equal to full set when max=0)
            summary[name] = {
                "total_qa": total,
                "l1_absent": l1_absent_n,
                "l1_absent_rate": l1_absent_n / total,
                "judged": len(judged),
                "no_page": no_page,
                "artifact": artifact,
                "artifact_frac_of_absent": artifact / len(judged) if judged else 0.0,
                "genuine_absent": genuine,
                "semantic_absent_rate": genuine / total,
            }
            logger.info("%s: L1-absent=%.1f%% -> semantic-absent=%.1f%% (artifact %d/%d)",
                        name, summary[name]["l1_absent_rate"] * 100,
                        summary[name]["semantic_absent_rate"] * 100, artifact, len(judged))

    (args.out_dir / "absent_llm_judge.json").write_text(
        json.dumps({"config": {"model": args.model, "num_qa": total,
                              "note": "semantic_absent_rate assumes judged==all L1-absent; "
                                      "run with --max_per_parser 0 for the headline number"},
                   "parsers": summary}, ensure_ascii=False, indent=2))
    logger.info("wrote %s", args.out_dir / "absent_llm_judge.json")
    for name, s in summary.items():
        print(f"{name:12s}  L1-absent {s['l1_absent_rate']:.1%}  ->  "
              f"semantic-absent {s['semantic_absent_rate']:.1%}  "
              f"(artifact {s['artifact_frac_of_absent']:.0%} of absent)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
