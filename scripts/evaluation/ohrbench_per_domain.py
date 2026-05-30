"""OHR-Bench per-domain RCPS grid (paper §4.2 appendix / cross-domain robustness).

Existing `eval_ohrbench.py` runs all listed domains as one corpus. This script
runs each of the 7 OHR-Bench domains *separately* on the three real parser
outputs (gt, MinerU, Qwen2.5-VL) so we can check whether RCPS ranks parsers
consistently across domains — a single C2 generalisation table.

Output:
    output/results/ohrbench_per_domain.json + .md

Usage:
    uv run python scripts/evaluation/ohrbench_per_domain.py --device cuda:0
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import pandas as pd

from wigtnocr_radp.evaluation import ParserNativeChunker, compute_rcps
from wigtnocr_radp.evaluation.retrievers import (
    BgeM3Retriever,
    MultilingualE5LargeRetriever,
    Qwen3EmbeddingRetriever,
)
from wigtnocr_radp.evaluation.types import QAPair, normalize_for_match

OHR = Path("data/OHR-Bench")
RETRIEVAL_TO_PARQUET = {
    "law": "law", "manual": "manual", "finance": "finance",
    "textbook": "textbook", "news": "news",
    "academic": "paper", "administration": "notes",
}
_BAD_ANSWERS = {"yes", "no", "true", "false", "n/a", "none", "not specified"}


def page_id(doc_name: str, page_idx: int) -> str:
    base = doc_name.rsplit("/", 1)[-1]
    return f"{base}__p{int(page_idx)}"


def load_qa(domains: list[str]) -> list[QAPair]:
    df = pd.read_parquet(OHR / "OHR-Bench.parquet")
    parquet_doms = {RETRIEVAL_TO_PARQUET.get(d, d) for d in domains}
    df = df[df["domain"].isin(parquet_doms)]
    gt_text = {page_id(r["doc_name"], r["page_idx"]): (r["gt_text"] or "") for _, r in df.iterrows()}
    pairs: list[QAPair] = []
    for _, row in df.iterrows():
        qas = row["qas"]
        if qas is None or "questions" not in qas:
            continue
        cols = {k: list(qas[k]) for k in qas}
        n = len(cols["questions"])
        for i in range(n):
            ans = str(cols["answers"][i]).strip()
            if len(normalize_for_match(ans)) < 2 or ans.lower() in _BAD_ANSWERS:
                continue
            pid = page_id(str(cols["doc_name"][i]), cols["evidence_page_no"][i])
            if normalize_for_match(ans) not in normalize_for_match(gt_text.get(pid, "")):
                continue
            pairs.append(QAPair(
                qa_id=str(cols["ID"][i]), page_id=pid, doc_id=str(cols["doc_name"][i]),
                language="en", domain=str(cols["doc_type"][i]),
                question=str(cols["questions"][i]), answer_span=ans,
                answer_chunk=str(cols.get("evidence_context", [""] * n)[i]),
                question_type=str(cols.get("evidence_source", ["text"] * n)[i]),
                difficulty="medium",
            ))
    return pairs


def load_parser_pages(parser: str, domains: list[str]) -> dict[str, str]:
    pages: dict[str, str] = {}
    for dom in domains:
        d = OHR / "retrieval_extracted" / parser / dom
        if not d.is_dir():
            continue
        for jf in d.glob("*.json"):
            doc_name = f"{dom}/{jf.stem}"
            for rec in json.loads(jf.read_text(encoding="utf-8")):
                pages[page_id(doc_name, rec["page_idx"])] = rec.get("text") or ""
    return pages

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ohrbench_per_domain")

DOMAINS = ("law", "manual", "finance", "news", "textbook", "academic", "administration")
PARSERS = ("gt", "MinerU", "Qwen2.5-VL")
CHUNKER = ParserNativeChunker(min_chars=30)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--out", type=Path, default=Path("output/results/ohrbench_per_domain.json"))
    args = ap.parse_args()

    retrievers = [
        BgeM3Retriever(device=args.device, batch_size=32),
        MultilingualE5LargeRetriever(device=args.device, batch_size=32),
        Qwen3EmbeddingRetriever(device=args.device, batch_size=8),
    ]

    table: dict[str, dict[str, dict]] = {}  # domain -> parser -> metrics
    for dom in DOMAINS:
        logger.info("=== domain: %s ===", dom)
        qa = load_qa([dom])
        if not qa:
            logger.warning("no Q-A for %s, skipping", dom)
            continue
        table[dom] = {"num_qa": len(qa), "parsers": {}}
        for parser in PARSERS:
            pages = load_parser_pages(parser, [dom])
            res = compute_rcps(qa, pages, retrievers, CHUNKER, k_values=(1, 5, 10))
            br = res["by_retriever"]
            rn = [r.name for r in retrievers]
            table[dom]["parsers"][parser] = {
                "rcps": res["rcps"],
                "hit@1": sum(br[n]["hit"][1] for n in rn) / len(rn),
                "mrr@10": sum(br[n]["mrr"][10] for n in rn) / len(rn),
                "num_pages": res["meta"]["num_pages"],
                "num_chunks": res["meta"]["num_chunks"],
            }
            logger.info(
                "%s/%s: RCPS=%.4f Hit@1=%.4f (n_qa=%d, n_chunks=%d)",
                dom, parser, res["rcps"], table[dom]["parsers"][parser]["hit@1"],
                len(qa), res["meta"]["num_chunks"],
            )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(
        {"domains": list(table.keys()), "parsers": PARSERS,
         "retrievers": [r.name for r in retrievers], "results": table},
        indent=2, ensure_ascii=False,
    ))

    # Markdown report (paper-ready table)
    md = ["# OHR-Bench per-domain RCPS — C2 cross-domain robustness", ""]
    md.append("Each domain runs as an isolated corpus (own chunks, own Q-A). ")
    md.append("Chunker = parser_native. RCPS = mean MRR@k across 3 retrievers × k ∈ {1, 5, 10}.")
    md.append("")
    md.append("| Domain | Q-A | RCPS gt | RCPS MinerU | RCPS Qwen2.5-VL | gt → MinerU Δ | gt → Qwen Δ |")
    md.append("|--------|:---:|:-------:|:-----------:|:---------------:|:-------------:|:-----------:|")
    for dom, info in table.items():
        ps = info["parsers"]
        rcps = {p: ps[p]["rcps"] for p in PARSERS}
        d_mineru = rcps["MinerU"] - rcps["gt"]
        d_qwen = rcps["Qwen2.5-VL"] - rcps["gt"]
        md.append(
            f"| {dom} | {info['num_qa']} | {rcps['gt']:.4f} | {rcps['MinerU']:.4f} "
            f"| {rcps['Qwen2.5-VL']:.4f} | {d_mineru:+.4f} | {d_qwen:+.4f} |"
        )
    md += ["",
        "## Ranking consistency",
        "",
        "Across all domains, gt should top RCPS (it is the clean GT text). If MinerU or Qwen2.5-VL ",
        "ever outperforms gt, RCPS would not be a robust extrinsic discriminator — flag in §4.2.",
        ""]
    rank_breaks = [
        dom for dom, info in table.items()
        if info["parsers"]["gt"]["rcps"] < max(info["parsers"]["MinerU"]["rcps"],
                                                info["parsers"]["Qwen2.5-VL"]["rcps"])
    ]
    if rank_breaks:
        md.append(f"**Domains where gt is NOT top RCPS**: {rank_breaks}")
    else:
        md.append("**gt is top RCPS in every domain.** Cross-domain ranking is consistent.")
    md_path = args.out.with_suffix(".md")
    md_path.write_text("\n".join(md))
    logger.info("wrote %s and %s", args.out, md_path)
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
