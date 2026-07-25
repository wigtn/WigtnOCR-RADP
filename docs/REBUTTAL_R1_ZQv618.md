# R1 (ZQv618) — paste-ready for OpenReview

> ⚠️ 내부 메모(붙여넣지 말 것). 아래 **Title** / **Comment** 두 칸을 OpenReview 양식에 그대로 붙여넣기. Comment는 4601자(<5000 OK). 상세 원본: REBUTTAL_R1_ZQv618_FULL.md

---

### Title
Definition added, circularity ruled out (model-free + cross-family), novelty reframed

### Comment

We thank the reviewer for a careful, constructive read, and especially for naming the same-family confound precisely enough to test.

**R1.1 — Parser problem definition.** We agree "absent" is only interpretable once the parser's I/O is fixed, and add a definition (Appendix C). *Input*: one page image from Korean government documents (born-digital + scanned; multi-column, stamps, merged-cell tables). *Output*: a linear Markdown transcription (body text in reading order, ATX headings, GitHub tables); discarded are layout coordinates, fonts, figure imagery, page furniture. *How "absent" arises*: content that never reaches the Markdown — dropped table cells, skipped in-image text, mis-recognised numerals — none recoverable by any chunker. *Provenance*: Prod is a Qwen3-VL-2B fine-tune; the reference and gold spans are distilled from a Qwen3-VL-30B teacher and manually de-noised (pseudo-ground-truth; see Limitations).

**R1.2 — Circularity.** This is the sharpest risk to C2, and it cannot be answered with more numbers *from the same measurer*: the confound (Qwen measurer + Qwen winner) and our hypothesis (parser quality) are observationally equivalent under any Qwen-based matching. The way out is a measurement where they predict *different* things — loosen the match and see whether the gap closes.

(a) A **model-free matching-strictness ladder** (Appendix C), applied identically to every parser, neutralising in turn digit/punctuation formatting, word order, and OCR character noise. If the gap were surface-form it would shrink; it does the opposite. MinerU−Prod absent gap: **+50.2 pp (L1, paper matcher) → +51.7 pp (L4, loosest)**. The two other *same-family* parsers (Qwen3-VL-2B-base, 30B teacher) sit within −1.3…+5.0 pp of Prod, so shared lineage alone confers no low absent rate.

(b) A **cross-family arbiter** (GPT-5.4, a different family than the Qwen parsers under test) labels every L1-absent answer by retriever-recoverability (present / degraded / absent), coherent with the paper's relevance rule. Genuine absent: **Prod 8.9% vs MinerU 59.3% (+50.4 pp)**. Decisively, the exact matcher over-counts *Prod's* absent (56% surface artefacts) ~3.5× more than the OCR parsers' (~16%) — the *opposite* of what same-family bias predicts.

The gap is stable across all three regimes (exact +50.2, fuzzy +51.7, judge +50.4). These are refinements on the same absent set, not independent measurements; the one orthogonal check is OHR-Bench (human-curated, family-independent gold), where the direction holds. All per-case verdicts are released for audit. For camera-ready we will add a blind human-verified subsample.

**Config self-audit (proactive disclosure).** We found our MinerU baseline was run with table recognition off. Re-running with tables on: table-evidence absent falls 87.9% → 41.7% (still ~3× Prod's 13.9%), and the overall gap narrows +50.2 → **+45.9 pp — it does not close**. The disconnect is not a configuration artefact; the specific table-absent magnitude was, and we correct it (Limitations) and release both outputs.

**R1.3 — Novelty.** We agree extrinsic pre-deployment evaluation *should* be standard, and we do not claim RCPS is methodologically novel — its simplicity is deliberate (training-free, no manual labels). The contribution is the empirical findings, which the reviewer's own marks already value (Soundness 3.5; "interesting" null result): (1) intrinsic metrics are not merely uncorrelated with retrieval but *anti-correlated* (Boundary Clarity $r=-0.81$), so an intrinsic-leaderboard pick deploys the worst-retrieving parser (35.1 pp / 2.8× Hit@1); (2) a retriever-free coverage diagnostic that localises the fault to the parser vs chunker layer; (3) the training null result. Parser leaderboards are still ranked by intrinsic fidelity because the cost is *assumed* prohibitive — quantifying that misranking and removing the cost is exactly the ought-vs-is gap an Industry Track exists to close. We will reframe the intro so the findings, not the protocol, are the headline.

**R1.4 — Density.** Agreed (also raised independently by another reviewer), so we treat it as fact. Concrete reallocation: the noise-family and DPO-milestone tables move fully to the appendix, the multi-clause abstract sentences are split, and the new parser definition + family-neutral diagnostic sit in appendices so the 6-page body does not grow. Terminology (parser / chunker / retriever) is defined up front.

We believe R1.1–R1.2 remove the main soundness reservation and R1.3 realigns the paper with the reviewer's own high marks for its empirical core.

