# R3 (bXGg) — paste-ready for OpenReview

> ⚠️ 내부 메모(붙여넣지 말 것). 아래 **Title** / **Comment** 두 칸을 OpenReview 양식에 그대로 붙여넣기. Comment는 4279자(<5000 OK). 상세 원본: REBUTTAL_R3_bXGg_FULL.md

---

### Title
Answers on probe stability, end-to-end scope, and generalisation

### Comment

We thank the reviewer for an unusually careful reading and for questions that sharpen the paper's scope rather than contest its results.

**Novelty.** We agree and state it in the paper: RCPS is deliberately not a new metric — its simplicity is what makes it deployable. For an Industry-Track contribution the claim is the operational finding plus tooling: (1) intrinsic parser metrics do not merely under-predict retrieval, they *invert* the deployment choice (Boundary Clarity $r=-0.81$; an intrinsic-leaderboard pick deploys the worst-retrieving parser, 35.1 pp / 2.8× Hit@1); (2) the retriever-free coverage diagnostic localises the fault to the parser vs chunker layer — which an end-to-end score does not give. We will foreground the findings and the diagnostic (not the protocol mechanics) in the intro.

**Construct validity.** We bound the exposure rather than dismiss it. Our *comparative* claims are internally valid regardless of reference/query noise: every ranking and the 2.8× swing holds the **same Q–A fixed across systems**, so shared noise cannot create a between-parser difference, only variance. Safeguards: (a) the confirmatory OHR-Bench evidence uses **externally human-curated** Q–A; (b) we tested the specific "same-family matcher inflates non-Qwen absent" worry with a model-free matching ladder and a cross-family judge (Appendix C), and the parser absent gap does not close as the matcher loosens; (c) the frozen eval set is released. During the response period we are also running a **blind human re-verification** of the same 100-Q–A sample the LLM graded, to report a human accept rate and human–LLM agreement (κ) that directly quantifies the residual reference/answer-span noise the review flags as unclear; we will include the number in the revision.

**Parser-training section.** Agreed it is secondary. Its role is a bounded negative result — retrieval-aware training does not beat a fidelity-distillation control (overlapping CIs), itself informative — and we will compress it to the appendix.

---

**Direct answers to your three questions:**

**1. Is the RCPS ranking stable under changes to the probe set?** Stable to the choices we varied: both parser and chunker rankings are **unchanged with MRR@10 alone** (vs averaged cutoffs), and format normalisation shifts scores by 0.02–0.03 without reordering. We have not yet resampled the probe *questions* at fixed size; we will add a bootstrap-over-probe-subsets stability check (ranking agreement) to the revision — cheap and directly on point.

**2. Does RCPS predict end-to-end RAG answer quality?** We built the end-to-end pipeline during the response period and the answer is yes. For each parser we retrieve top-5 chunks (same retriever/chunker as RCPS), let a generator (GPT-5.4) answer from only those chunks, and grade the generated answer (LLM judge + exact match) over all 663 KoGov Q–A. Answer accuracy: **Prod 72.5%, MinerU 23.8%, PaddleOCR 20.5%** — the RCPS ranking (0.583 / 0.212 / 0.140) matches the end-to-end accuracy ranking exactly (**Spearman ρ = 1.0**), and selecting the parser by RCPS yields ~3.5× the downstream answer accuracy. So span-retrievability is not merely a necessary floor here; it *predicts* generated-answer quality. (The reviewer is right in principle that a low-span parser could occasionally be rescued by generation; empirically the gap is far too large for that to reorder the parsers.) We will add this end-to-end table to the revision.

**3. How well does the conclusion generalise to broader pools and deployments?** The *mechanism* generalises — formatting quality and content preservation are different properties, so appearance metrics can be blind to the content loss retrieval needs. This replicates on OHR-Bench across all seven English domains (Boundary Clarity flat under semantic corruption while retrieval collapses), a different language/documents/curated-Q–A setting. What is corpus-*specific* is the scalar magnitude/sign (the exact $r$, the 2.8× swing), which we flag as illustrative and n=5-limited. On pool breadth: the protocol is pool-agnostic by construction, but our *evidence* that it picks well is strongest when the pool spans different paradigms (VLM vs OCR), where intrinsic metrics misrank most; for near-tied same-paradigm pools the decision is genuinely close and we say so. On deployment: the coverage/absent findings are retriever-independent and transfer directly; the RCPS *ranking* is a procedure to recompute with your own retriever and probe, not a fixed leaderboard to import.

We are grateful the review identifies the paper's real boundary — retrieval, not end-to-end generation — and we will state it as an explicit scope.

