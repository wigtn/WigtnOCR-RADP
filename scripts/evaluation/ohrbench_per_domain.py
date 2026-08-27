"""Per-domain RCPS grid for the corrected legacy OHR compatibility subset.

The legacy Q-A parquet and expanded parser-output release are not a single
benchmark version.  This script excludes the invalid legacy ``notes`` domain
and the five audited missing-page Q-A, verifies the exact 2,036-Q-A/six-domain
identity, and labels every output as a compatibility result.  It is not a full
OHR-Bench v2 or seven-domain evaluation.

Output:
    output/results/ohrbench_per_domain_compat2036.json + .md

Usage:
    uv run python scripts/evaluation/ohrbench_per_domain.py --device cuda:0
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from wigtnocr_radp.evaluation import ParserNativeChunker, compute_rcps
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
    require_supported_ohr_alignment_audit,
    resolve_document_files,
)

OHR = Path("data/OHR-Bench")
RETRIEVAL_TO_PARQUET = {
    "law": "law", "manual": "manual", "finance": "finance",
    "textbook": "textbook", "news": "news",
    "academic": "paper", "administration": "notes",
}
_BAD_ANSWERS = {"yes", "no", "true", "false", "n/a", "none", "not specified"}
RESULT_STATUS = "strict_legacy_compatibility_subset_not_full_v2"
DEFAULT_ALIGNMENT_AUDIT = Path("output/results/ohrbench_alignment_audit.json")
DEFAULT_OUT = Path("output/results/ohrbench_per_domain_compat2036.json")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_alignment_audit(path: Path) -> dict[str, Any]:
    audit = json.loads(path.read_text(encoding="utf-8"))
    strict = audit.get("c4_strict_compatibility_subset")
    require_supported_ohr_alignment_audit(audit, path=path)
    if not isinstance(strict, dict):
        raise ValueError(f"unsupported OHR alignment audit: {path}")
    if int(strict.get("num_qa", -1)) != 2036:
        raise ValueError(f"alignment audit does not define the 2,036-Q-A subset: {path}")
    return audit


def load_qa(domains: list[str], alignment_audit: dict[str, Any]) -> list[QAPair]:
    df = pd.read_parquet(OHR / "OHR-Bench.parquet")
    parquet_doms = {RETRIEVAL_TO_PARQUET.get(d, d) for d in domains}
    df = df[df["domain"].isin(parquet_doms)]
    gt_text = {
        ohr_page_id(r["doc_name"], r["page_idx"]): (r["gt_text"] or "")
        for _, r in df.iterrows()
    }
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
            pid = ohr_page_id(str(cols["doc_name"][i]), cols["evidence_page_no"][i])
            if normalize_for_match(ans) not in normalize_for_match(gt_text.get(pid, "")):
                continue
            pairs.append(QAPair(
                qa_id=str(cols["ID"][i]), page_id=pid, doc_id=str(cols["doc_name"][i]),
                language="en", domain=str(row["domain"]),
                question=str(cols["questions"][i]), answer_span=ans,
                answer_chunk=str(cols.get("evidence_context", [""] * n)[i]),
                question_type=str(cols.get("evidence_source", ["text"] * n)[i]),
                difficulty="medium",
            ))

    qa_ids = [qa.qa_id for qa in pairs]
    if len(set(qa_ids)) != len(qa_ids):
        raise ValueError("legacy OHR Q-A contain duplicate qa_ids")

    strict = alignment_audit["c4_strict_compatibility_subset"]
    missing_ids = set(strict["excluded"]["missing_v2_page_qa_ids"])
    expected_missing = len(missing_ids) if "textbook" in parquet_doms else 0
    found_missing = missing_ids.intersection(qa_ids)
    if len(found_missing) != expected_missing:
        raise ValueError(
            f"missing-page Q-A identity mismatch: got {len(found_missing)}, "
            f"expected {expected_missing}"
        )
    pairs = [qa for qa in pairs if qa.qa_id not in missing_ids]

    actual_counts = dict(sorted(Counter(qa.domain for qa in pairs).items()))
    expected_counts = {
        domain: int(count)
        for domain, count in strict["domain_counts"].items()
        if domain in parquet_doms
    }
    expected_counts = dict(sorted(expected_counts.items()))
    if actual_counts != expected_counts:
        raise ValueError(
            f"strict compatibility domain identity mismatch: "
            f"got {actual_counts}, expected {expected_counts}"
        )
    return pairs


def load_parser_pages(parser: str, domains: list[str]) -> dict[str, str]:
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
            "%s/%s: %d source documents absent; sample=%s",
            parser,
            ",".join(domains),
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ohrbench_per_domain")

DOMAINS = ("law", "manual", "finance", "news", "textbook", "academic")
PARSERS = ("gt", "MinerU", "Qwen2.5-VL")
CHUNKER = ParserNativeChunker(min_chars=30)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--domains", default=",".join(DOMAINS))
    ap.add_argument("--alignment-audit", type=Path, default=DEFAULT_ALIGNMENT_AUDIT)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    domains = [domain.strip() for domain in args.domains.split(",") if domain.strip()]
    if not domains or len(domains) != len(set(domains)):
        raise ValueError(f"domain selection must be non-empty and unique: {domains}")
    unsupported_domains = sorted(set(domains) - set(DOMAINS))
    if unsupported_domains:
        raise ValueError(
            f"domains {unsupported_domains} are not in the audited six-domain compatibility subset; "
            "use full-v2 inputs instead"
        )
    require_compatibility_output_path(args.out)
    md_path = args.out.with_suffix(".md")
    require_compatibility_output_path(md_path)
    if args.out.resolve() == args.alignment_audit.resolve():
        raise ValueError("output path must differ from the alignment-audit input")
    alignment_audit = load_alignment_audit(args.alignment_audit)

    retrievers = [
        BgeM3Retriever(device=args.device, batch_size=32),
        MultilingualE5LargeRetriever(device=args.device, batch_size=32),
        Qwen3EmbeddingRetriever(device=args.device, batch_size=8),
    ]

    table: dict[str, dict[str, dict]] = {}  # domain -> parser -> metrics
    for dom in domains:
        logger.info("=== domain: %s ===", dom)
        qa = load_qa([dom], alignment_audit)
        if not qa:
            raise ValueError(f"audited compatibility domain has no Q-A: {dom}")
        table[dom] = {"num_qa": len(qa), "parsers": {}}
        for parser in PARSERS:
            pages = load_parser_pages(parser, [dom])
            require_evidence_page_coverage(
                qa,
                pages,
                label=f"OHR-Bench domain={dom} parser={parser}",
            )
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
        {
            "domains": list(table.keys()),
            "parsers": PARSERS,
            "retrievers": [r.name for r in retrievers],
            "results": table,
            "meta": {
                "status": RESULT_STATUS,
                "full_v2": False,
                "num_qa": sum(int(info["num_qa"]) for info in table.values()),
                "alignment_audit": str(args.alignment_audit),
                "alignment_audit_sha256": _sha256(args.alignment_audit),
            },
        },
        indent=2, ensure_ascii=False,
    ), encoding="utf-8")

    # Markdown report for inspecting the corrected compatibility subset.
    md = ["# OHR-Bench per-domain RCPS — corrected legacy compatibility subset", ""]
    md.append("This is a six-domain, 2,036-Q-A compatibility analysis, not a full-v2 result.")
    md.append("")
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
        "## Descriptive ranking check",
        "",
        "Across all domains, gt should top RCPS (it is the clean GT text). If MinerU or Qwen2.5-VL ",
        "ever outperforms gt, inspect that compatibility-domain result before using it.",
        ""]
    rank_breaks = [
        dom for dom, info in table.items()
        if info["parsers"]["gt"]["rcps"] < max(info["parsers"]["MinerU"]["rcps"],
                                                info["parsers"]["Qwen2.5-VL"]["rcps"])
    ]
    if rank_breaks:
        md.append(f"**Domains where gt is NOT top RCPS**: {rank_breaks}")
    else:
        md.append("**gt is top RCPS in every audited compatibility domain.**")
    md_path.write_text("\n".join(md), encoding="utf-8")
    logger.info("wrote %s and %s", args.out, md_path)
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
