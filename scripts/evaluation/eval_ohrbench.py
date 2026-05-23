"""OHRBench cross-domain RCPS evaluation (EMNLP C1/C2 generalization).

Validates the parsing-retrieval diagnosis (C1) and RCPS metric (C2) on the
OHR-Bench benchmark (English, enterprise domains) — independent of the Korean
KoGovDoc data, to show the findings are not single-domain artifacts.

OHR-Bench ships, per page, the ground-truth structured text plus real parser
outputs (MinerU, Qwen2.5-VL). We run our RCPS pipeline over each parser's
output for the Law and Manual domains and report the parser × RCPS grid.

Usage:
    CUDA_VISIBLE_DEVICES=1 uv run python scripts/evaluation/eval_ohrbench.py \
        --device cuda --out output/results/ohrbench_crossdomain.json
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

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("eval_ohrbench")

OHR = Path("data/OHR-Bench")
PARSERS = ("gt", "MinerU", "Qwen2.5-VL")
CHUNKERS = {"parser_native": ParserNativeChunker(min_chars=30), "fixed500": FixedSizeChunker(size=500)}
_BAD_ANSWERS = {"yes", "no", "true", "false", "n/a", "none", "not specified"}


def page_id(doc_name: str, page_idx: int) -> str:
    return f"{doc_name}__p{int(page_idx)}"


def load_qa(domains: list[str]) -> list[QAPair]:
    """Build QAPair list from OHR-Bench.parquet for the given domains.

    Each page row carries a `qas` dict of parallel arrays. A Q-A is kept only if
    its answer is non-trivial and verbatim-present in the GT text of its
    evidence page (so the score reflects *retrievability*, not unanswerable Q-A).
    """
    df = pd.read_parquet(OHR / "OHR-Bench.parquet")
    df = df[df["domain"].isin(domains)]
    # GT text per page_id, for the answerability filter
    gt_text = {page_id(r["doc_name"], r["page_idx"]): (r["gt_text"] or "") for _, r in df.iterrows()}

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
            pid = page_id(str(cols["doc_name"][i]), cols["evidence_page_no"][i])
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
    """{page_id: text} for one parser over the given domains."""
    pages: dict[str, str] = {}
    for dom in domains:
        d = OHR / "retrieval_extracted" / parser / dom
        if not d.is_dir():
            logger.warning("missing %s", d)
            continue
        for jf in d.glob("*.json"):
            doc_name = f"{dom}/{jf.stem}"
            for rec in json.loads(jf.read_text(encoding="utf-8")):
                pages[page_id(doc_name, rec["page_idx"])] = rec.get("text") or ""
    return pages


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--domains", default="law,manual")
    ap.add_argument("--parsers", default=",".join(PARSERS))
    ap.add_argument("--chunkers", default="parser_native,fixed500")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--out", type=Path, default=Path("output/results/ohrbench_crossdomain.json"))
    args = ap.parse_args()

    domains = args.domains.split(",")
    parsers = args.parsers.split(",")
    chunkers = args.chunkers.split(",")

    qa = load_qa(domains)
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
        {"domains": domains, "num_qa": len(qa), "results": results}, indent=2, ensure_ascii=False))

    print("\n" + "=" * 78)
    print(f"OHRBench cross-domain RCPS — domains={domains}, {len(qa)} Q-A")
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
