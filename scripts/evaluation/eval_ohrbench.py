"""Source-aligned OHR-Bench Law--Manual compatibility RCPS evaluation.

The repository contains a legacy Q-A parquet and an expanded parser-output
bundle from a different OHR-Bench release.  Only the Law and Manual slice has
been source-aligned for this parser grid.  This script therefore refuses other
domain selections and writes to a new, explicitly named compatibility artifact.

This is not a full OHR-Bench v2 evaluation.  Full-v2 claims require
``OHR-Bench_v2.parquet`` and ``qas_v2.json`` with fresh parser outputs.

Usage:
    CUDA_VISIBLE_DEVICES=1 uv run python scripts/evaluation/eval_ohrbench.py \
        --device cuda
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import pandas as pd

from wigtnocr_radp.evaluation import (
    ParserNativeChunker,
    compute_rcps,
)
from wigtnocr_radp.evaluation.chunkers import FixedSizeChunker
from wigtnocr_radp.evaluation.retrievers import (
    BgeM3Retriever,
    MultilingualE5LargeRetriever,
    Qwen3EmbeddingRetriever,
)
from wigtnocr_radp.evaluation.types import QAPair, normalize_for_match
from wigtnocr_radp.ohrbench_paths import (
    ohr_page_id,
    require_compatibility_output_path,
    require_evidence_page_coverage,
    resolve_document_files,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("eval_ohrbench")

OHR = Path("data/OHR-Bench")
PARSERS = ("gt", "MinerU", "Qwen2.5-VL")
CHUNKERS = {"parser_native": ParserNativeChunker(min_chars=30), "fixed500": FixedSizeChunker(size=500)}
_BAD_ANSWERS = {"yes", "no", "true", "false", "n/a", "none", "not specified"}
LAW_MANUAL_COMPAT_DOMAINS = ("law", "manual")
LAW_MANUAL_COMPAT_NUM_QA = 1043
LAW_MANUAL_COMPAT_STATUS = "law_manual_legacy_compatibility_subset_not_full_v2"
DEFAULT_OUT = Path("output/results/ohrbench_law_manual_compat_rcps.json")

# CLI domain names follow the expanded v2 release, while the Q-A parquet retains
# its original labels.  This map is used only to select logical Q-A domains;
# physical parser files are resolved globally by document basename below.
RETRIEVAL_TO_PARQUET = {
    "law": "law", "manual": "manual", "finance": "finance",
    "textbook": "textbook", "news": "news",
    "academic": "paper", "administration": "notes",
}


def load_qa(domains: list[str]) -> list[QAPair]:
    """Build QAPair list from OHR-Bench.parquet for the given domains.

    Each page row carries a `qas` dict of parallel arrays. A Q-A is kept only if
    its answer is non-trivial and verbatim-present in the GT text of its
    evidence page (so the score reflects *retrievability*, not unanswerable Q-A).
    """
    df = pd.read_parquet(OHR / "OHR-Bench.parquet")
    # `domains` are retrieval-dir names; map to parquet's domain labels.
    parquet_doms = {RETRIEVAL_TO_PARQUET.get(d, d) for d in domains}
    df = df[df["domain"].isin(parquet_doms)]
    # GT text per page_id, for the answerability filter
    gt_text = {
        ohr_page_id(r["doc_name"], r["page_idx"]): (r["gt_text"] or "")
        for _, r in df.iterrows()
    }

    pairs: list[QAPair] = []
    n_raw = n_short = n_unanswerable = 0
    for _, row in df.iterrows():
        qas = row["qas"]
        if qas is None or "questions" not in qas:
            continue
        cols = {k: list(qas[k]) for k in qas}
        n = len(cols["questions"])
        for i in range(n):
            n_raw += 1
            ans = str(cols["answers"][i]).strip()
            if len(normalize_for_match(ans)) < 2 or ans.lower() in _BAD_ANSWERS:
                n_short += 1
                continue
            pid = ohr_page_id(str(cols["doc_name"][i]), cols["evidence_page_no"][i])
            if normalize_for_match(ans) not in normalize_for_match(gt_text.get(pid, "")):
                n_unanswerable += 1
                continue
            pairs.append(
                QAPair(
                    qa_id=str(cols["ID"][i]),
                    page_id=pid,
                    doc_id=str(cols["doc_name"][i]),
                    language="en",
                    domain=str(cols["doc_type"][i]),
                    question=str(cols["questions"][i]),
                    answer_span=ans,
                    answer_chunk=str(cols.get("evidence_context", [""] * n)[i]),
                    question_type=str(cols.get("evidence_source", ["text"] * n)[i]),
                    difficulty="medium",
                )
            )
    logger.info(
        "Q-A: %d kept / %d raw (dropped: short/ambiguous=%d, not-in-GT=%d)",
        len(pairs), n_raw, n_short, n_unanswerable,
    )
    return pairs


def load_parser_pages(parser: str, domains: list[str]) -> dict[str, str]:
    """Load the original-parquet corpus from any v2 physical domain folder."""

    df = pd.read_parquet(OHR / "OHR-Bench.parquet", columns=["domain", "doc_name", "page_idx"])
    parquet_doms = {RETRIEVAL_TO_PARQUET.get(d, d) for d in domains}
    df = df[df["domain"].isin(parquet_doms)]
    expected_page_ids = {
        ohr_page_id(row["doc_name"], row["page_idx"]) for _, row in df.iterrows()
    }
    resolved, missing_documents = resolve_document_files(
        OHR / "retrieval_extracted" / parser,
        df["doc_name"].astype(str),
        suffix=".json",
    )
    if missing_documents:
        logger.warning(
            "%s: %d source documents are absent from the expanded release; sample=%s",
            parser,
            len(missing_documents),
            list(missing_documents[:5]),
        )

    pages: dict[str, str] = {}
    for doc_name, json_path in resolved.items():
        for rec in json.loads(json_path.read_text(encoding="utf-8")):
            pid = ohr_page_id(doc_name, rec["page_idx"])
            if pid in expected_page_ids:
                pages[pid] = rec.get("text") or ""
    return pages


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--domains", default="law,manual")
    ap.add_argument("--parsers", default=",".join(PARSERS))
    ap.add_argument("--chunkers", default="parser_native,fixed500")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    domains = [domain.strip() for domain in args.domains.split(",") if domain.strip()]
    parsers = [parser.strip() for parser in args.parsers.split(",") if parser.strip()]
    chunkers = [chunker.strip() for chunker in args.chunkers.split(",") if chunker.strip()]

    if tuple(domains) != LAW_MANUAL_COMPAT_DOMAINS:
        raise ValueError(
            "this legacy-QA scorer is restricted to the audited Law--Manual "
            f"compatibility slice {LAW_MANUAL_COMPAT_DOMAINS}; got {domains}. "
            "Use the full-v2 inputs for any other domains."
        )
    unknown_parsers = sorted(set(parsers) - set(PARSERS))
    unknown_chunkers = sorted(set(chunkers) - set(CHUNKERS))
    if not parsers or unknown_parsers:
        raise ValueError(f"unsupported parser selection: {unknown_parsers or parsers}")
    if not chunkers or unknown_chunkers:
        raise ValueError(f"unsupported chunker selection: {unknown_chunkers or chunkers}")
    require_compatibility_output_path(args.out)

    qa = load_qa(domains)
    if len(qa) != LAW_MANUAL_COMPAT_NUM_QA:
        raise ValueError(
            "Law--Manual compatibility identity changed: "
            f"expected {LAW_MANUAL_COMPAT_NUM_QA} Q-A, got {len(qa)}"
        )
    retrievers = [
        BgeM3Retriever(device=args.device, batch_size=32),
        MultilingualE5LargeRetriever(device=args.device, batch_size=32),
        Qwen3EmbeddingRetriever(device=args.device, batch_size=8),
    ]

    results: dict[str, dict] = {}
    for ck_name in chunkers:
        results[ck_name] = {}
        for parser in parsers:
            pages = load_parser_pages(parser, domains)
            require_evidence_page_coverage(qa, pages, label=f"OHR-Bench parser={parser}")
            res = compute_rcps(qa, pages, retrievers, CHUNKERS[ck_name], k_values=(1, 5, 10))
            br = res["by_retriever"]
            rn = [r.name for r in retrievers]
            results[ck_name][parser] = {
                "rcps": res["rcps"],
                "hit@1": sum(br[n]["hit"][1] for n in rn) / len(rn),
                "hit@5": sum(br[n]["hit"][5] for n in rn) / len(rn),
                "mrr@10": sum(br[n]["mrr"][10] for n in rn) / len(rn),
                "ndcg@10": sum(br[n]["ndcg"][10] for n in rn) / len(rn),
                "num_pages": res["meta"]["num_pages"],
                "num_chunks": res["meta"]["num_chunks"],
            }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(
        {
            "domains": domains,
            "num_qa": len(qa),
            "results": results,
            "meta": {
                "status": LAW_MANUAL_COMPAT_STATUS,
                "full_v2": False,
            },
        },
        indent=2,
        ensure_ascii=False,
    ), encoding="utf-8")

    print("\n" + "=" * 78)
    print(f"OHRBench Law--Manual compatibility RCPS — domains={domains}, {len(qa)} Q-A")
    print("=" * 78)
    for ck_name in chunkers:
        print(f"\n[chunker = {ck_name}]")
        print(f"  {'parser':<14}{'RCPS':>9}{'Hit@1':>9}{'Hit@5':>9}{'MRR@10':>9}{'nDCG@10':>9}")
        for parser in parsers:
            c = results[ck_name][parser]
            print(f"  {parser:<14}{c['rcps']:>9.4f}{c['hit@1']:>9.4f}{c['hit@5']:>9.4f}"
                  f"{c['mrr@10']:>9.4f}{c['ndcg@10']:>9.4f}")
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
