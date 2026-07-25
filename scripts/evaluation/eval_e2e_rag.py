"""End-to-end RAG answer-quality evaluation (answers R3's scope question).

RCPS measures answer-span *retrievability*. R3 asks: does the RCPS parser ranking
predict end-to-end *answer* quality once a generator consumes the retrieved
context? This script builds the missing stage — retrieve → generate → score the
generated answer — and compares the parser ordering by answer accuracy against the
RCPS (span-retrieval) ordering.

Pipeline per parser P and question q:
  1. chunk P's pages (same chunker as RCPS), index with a retriever,
  2. retrieve top-k chunks for q,
  3. prompt a generator LLM to answer q from ONLY those chunks,
  4. score the answer vs the gold with (a) a cross-family LLM judge (correct=1/0)
     and (b) exact/substring match under the paper's normalisation.
Report per parser: answer accuracy (judge) + EM, and the Spearman/Kendall
agreement between the parser ranking by answer accuracy and by RCPS.

Reuses the repo's chunkers/retrievers/relevance so the retrieval half is identical
to RCPS; only generation + answer scoring are new. Needs an embedder (GPU) and an
OpenAI key (generator + judge). Runs on the machine that has the data.

Usage:
  export OPENAI_API_KEY=...
  uv run python scripts/evaluation/eval_e2e_rag.py \
      --qa data/KoGovDoc-RAG/qa_pairs_v1.jsonl \
      --root /path/to/results/kogovdoc --val_jsonl data/KoGovDoc-Bench/val.jsonl \
      --parsers Prod MinerU Qwen3-VL-30B --retriever bge-m3 --k 5 \
      --gen_model gpt-5.4-2026-03-05 --sample 200
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

from wigtnocr_radp.evaluation.chunkers import MarkdownHeaderChunker
from wigtnocr_radp.evaluation.parser_outputs import load_parser_outputs
from wigtnocr_radp.evaluation.rcps import load_qa_pairs
from wigtnocr_radp.evaluation.types import normalize_for_match

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("eval_e2e_rag")

KOGOV_ROOT = Path("/mnt/data1/work/wigtnOCR-v1/results/kogovdoc")
VAL_JSONL = Path("data/KoGovDoc-Bench/val.jsonl")
PARSERS: dict[str, str] = {
    "Prod": "v1_val/predictions",
    "Qwen3-VL-30B": "30b_val/predictions",
    "Qwen3-VL-2B-base": "2b_base_val/predictions",
    "MinerU": "mineru_val/predictions",
    "MinerU-tableon": "mineru_val_tableon/predictions",
    "PaddleOCR": "paddleocr_val/predictions",
}

GEN_SYSTEM = (
    "You answer a question using ONLY the provided context passages, which were "
    "produced by an automatic document parser and may be noisy. If the answer is "
    "present, reply with the exact answer as short as possible. If the context does "
    "not contain the answer, reply exactly: NO ANSWER. Do not use outside knowledge."
)
GEN_USER = "CONTEXT:\n{context}\n\nQUESTION: {question}\n\nANSWER:"

JUDGE_SYSTEM = (
    "You grade whether a predicted answer is correct for a question, given the gold "
    "answer. Accept paraphrases, different formatting, and extra words as long as the "
    "specific gold fact is stated. Mark incorrect if the fact is wrong, missing, or "
    "the prediction is 'NO ANSWER'. Judge only the fact, not style."
)
JUDGE_USER = "QUESTION: {q}\nGOLD: {gold}\nPREDICTED: {pred}\n\nIs the prediction correct?"
JUDGE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {"name": "answer_correct", "strict": True, "schema": {
        "type": "object", "additionalProperties": False,
        "properties": {"correct": {"type": "boolean"}},
        "required": ["correct"]}},
}


def _build_retriever(name: str):
    from wigtnocr_radp.evaluation.retrievers import (
        BgeM3Retriever, MultilingualE5LargeRetriever, Qwen3EmbeddingRetriever,
    )
    return {"bge-m3": BgeM3Retriever, "e5-large": MultilingualE5LargeRetriever,
            "qwen3-emb": Qwen3EmbeddingRetriever}[name]()


def _generate(client, model, question, context) -> str:
    r = client.chat.completions.create(model=model, messages=[
        {"role": "system", "content": GEN_SYSTEM},
        {"role": "user", "content": GEN_USER.format(context=context[:12000], question=question)}])
    return (r.choices[0].message.content or "").strip()


def _judge(client, model, q, gold, pred) -> bool:
    if normalize_for_match(gold) and normalize_for_match(gold) in normalize_for_match(pred):
        return True  # exact/substring match — no API call needed
    r = client.chat.completions.create(model=model, response_format=JUDGE_SCHEMA, messages=[
        {"role": "system", "content": JUDGE_SYSTEM},
        {"role": "user", "content": JUDGE_USER.format(q=q, gold=gold, pred=pred)}])
    return bool(json.loads(r.choices[0].message.content)["correct"])


def _spearman(a: list[float], b: list[float]) -> float:
    """Rank correlation without scipy (n is tiny)."""
    def ranks(x):
        order = sorted(range(len(x)), key=lambda i: x[i])
        rk = [0.0] * len(x)
        for pos, i in enumerate(order):
            rk[i] = pos
        return rk
    ra, rb = ranks(a), ranks(b)
    n = len(a)
    d2 = sum((ra[i] - rb[i]) ** 2 for i in range(n))
    return 1 - 6 * d2 / (n * (n * n - 1)) if n > 1 else 1.0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--qa", default="data/KoGovDoc-RAG/qa_pairs_v1.jsonl")
    ap.add_argument("--root", type=Path, default=KOGOV_ROOT)
    ap.add_argument("--val_jsonl", type=Path, default=VAL_JSONL)
    ap.add_argument("--parsers", nargs="*", default=["Prod", "MinerU", "Qwen3-VL-30B"])
    ap.add_argument("--retriever", default="bge-m3", choices=["bge-m3", "e5-large", "qwen3-emb"])
    ap.add_argument("--k", type=int, default=5, help="top-k chunks fed to the generator")
    ap.add_argument("--gen_model", default="gpt-5.4-2026-03-05")
    ap.add_argument("--judge_model", default="gpt-5.4-2026-03-05")
    ap.add_argument("--sample", type=int, default=0, help="first N QA only (0=all)")
    ap.add_argument("--rcps_json", type=Path, default=None,
                    help="baseline grid json with per-parser RCPS, for the ranking comparison")
    ap.add_argument("--rcps_map", nargs="*", default=[], metavar="GRIDNAME=OURNAME",
                    help="map grid parser names to --parsers names, e.g. "
                         "'WigtnOCR-2B (ours, v1)=Prod' 'MinerU=MinerU-tableon'")
    ap.add_argument("--out_dir", type=Path, default=Path("output/results"))
    args = ap.parse_args()

    load_dotenv()
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY not set")
    client = OpenAI()

    qa = load_qa_pairs(args.qa)
    if args.sample:
        qa = qa[: args.sample]
    chunker = MarkdownHeaderChunker(max_level=3)
    retriever = _build_retriever(args.retriever)

    summary: dict[str, Any] = {}
    args.out_dir.mkdir(parents=True, exist_ok=True)
    detail_path = args.out_dir / "e2e_rag_detail.jsonl"
    with detail_path.open("w", encoding="utf-8") as det:
        for name in args.parsers:
            sub = PARSERS.get(name)
            pdir = args.root / sub if sub else None
            if not pdir or not pdir.is_dir():
                logger.warning("skip %s: %s not found", name, pdir)
                continue
            pages = load_parser_outputs(pdir, args.val_jsonl)
            chunks = chunker.chunk_corpus(dict(pages))
            retriever.index(chunks)
            results = retriever.search(qa, top_k=args.k)

            correct = em = answered = 0
            for q, res in zip(qa, results):
                ctx = "\n\n---\n\n".join(c.text for c in res.top_k(args.k))
                pred = _generate(client, args.gen_model, q.question, ctx)
                is_em = bool(normalize_for_match(q.answer_span)
                             and normalize_for_match(q.answer_span) in normalize_for_match(pred))
                ok = _judge(client, args.judge_model, q.question, q.answer_span, pred)
                correct += int(ok); em += int(is_em)
                answered += int("NO ANSWER" not in pred.upper())
                det.write(json.dumps({"parser": name, "qa_id": q.qa_id, "q": q.question,
                                      "gold": q.answer_span, "pred": pred, "correct": ok,
                                      "em": is_em}, ensure_ascii=False) + "\n")
            n = len(qa)
            summary[name] = {"n": n, "answer_accuracy": correct / n, "em": em / n,
                             "answered_rate": answered / n}
            logger.info("%s: answer-acc %.1f%%  EM %.1f%%  (n=%d)",
                        name, 100 * correct / n, 100 * em / n, n)

    out = {"config": {"retriever": args.retriever, "k": args.k, "gen_model": args.gen_model,
                      "sample": args.sample, "num_qa": len(qa)}, "parsers": summary}

    # Ranking comparison vs RCPS, if a grid json was supplied.
    if args.rcps_json and args.rcps_json.exists():
        grid = json.loads(args.rcps_json.read_text())
        # --rcps_map lets the caller map grid parser-names -> our parser-names,
        # e.g. --rcps_map "WigtnOCR-2B (ours, v1)=Prod" "MinerU=MinerU-tableon".
        alias = {}
        for m in args.rcps_map:
            g, _, ours = m.partition("=")
            if g and ours:
                alias[g.strip()] = ours.strip()
        rcps = {}
        for row in (grid.get("parsers") or grid.get("rows") or []):
            nm = row.get("parser") or row.get("name")
            nm = alias.get(nm, nm)  # apply alias if given
            if nm in summary and ("rcps" in row):
                rcps[nm] = row["rcps"]
        common = [p for p in summary if p in rcps]
        if len(common) >= 2:
            acc = [summary[p]["answer_accuracy"] for p in common]
            rc = [rcps[p] for p in common]
            out["ranking_comparison"] = {
                "parsers": common, "answer_accuracy": acc, "rcps": rc,
                "spearman_rho": _spearman(acc, rc)}
            logger.info("RCPS vs answer-accuracy ranking: Spearman rho = %.3f on %s",
                        out["ranking_comparison"]["spearman_rho"], common)

    (args.out_dir / "e2e_rag.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    logger.info("wrote %s and %s", args.out_dir / "e2e_rag.json", detail_path)
    for p, s in summary.items():
        print(f"{p:16s} answer-acc {s['answer_accuracy']:.1%}  EM {s['em']:.1%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
