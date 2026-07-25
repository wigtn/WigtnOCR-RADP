# Rebuttal to R3 (bXGg) — Industry Track, goal = convert Workshop(3.0) → main accept

> ⚠️ **붙여넣을 때는 아래 `---` 밑의 본문만.** 제목 줄과 이 `>` 전략 블록은 내부 메모라 리뷰어에게 나가면 안 됨.
> 전략: R3는 R1의 판박이(Soundness 3.5, Overall 3, novelty+construct-validity 지적),
> 게다가 Confidence 4로 제일 신중히 읽음. 틀린 지적/오독이 없어서 R2처럼 "교정"이 아니라
> **"인정 + 명료화 + 한계 정직"** 톤이 맞다. 4개 축:
> - novelty: R1③과 동일 프레이밍(단순함=의도, findings가 기여, Industry-Track의 ought-vs-is 갭).
>   Industry Track이라 novelty 기대 낮음 → 이 축이 R3에서 더 잘 먹힘.
> - construct validity: 비교 결과는 QA를 시스템 간 고정해서 내적 타당, OHR(사람 QA)로 외적 확인.
>   R1의 circularity 답 + config disclosure 재활용.
> - end-to-end RAG(신규): 정직하게 scope 인정 + span-retrieval이 유효 프록시인 이유 + future work.
> - retriever averaging / probe stability: 논문에 이미 있는 사실로 방어(우리가 먼저 인정한 한계).
> R3+R1이 독립적으로 3.5 soundness 수렴 → R2(1.5, excitement 1, no actionable)가 outlier임을 부각.

---

We thank the reviewer for an unusually careful and fair reading (the longest,
most specific Reasons-to-Accept of the three reviews), and for questions that
sharpen the paper's scope rather than contest its results. We answer each.

## R3.1 — Conceptual novelty ("ordinary retrieval evaluation")

We agree, and state it in the paper: RCPS is deliberately not a new similarity or
retrieval metric — its simplicity is what makes it deployable (no training, no
manual relevance labels). For an Industry-Track contribution the claim is not
methodological novelty but an operational finding with tooling:

1. Intrinsic parser metrics do not merely under-predict retrieval, they *invert*
   the deployment choice (Boundary Clarity Pearson $r=-0.81$; an
   intrinsic-leaderboard pick deploys the worst-retrieving parser here, 35.1 pp /
   2.8× Hit@1). Parsing benchmarks today still rank by intrinsic fidelity, so
   selecting by retrieval is *not* yet standard practice — quantifying the cost of
   that gap, and removing it with a training-free protocol, is exactly the
   ought-vs-is contribution an Industry Track exists for.
2. The retriever-free **coverage diagnostic** (absent vs split) is the reusable,
   non-obvious tool: it localises the fault to the parser or chunker layer — which
   an end-to-end retrieval score does *not* give — and tells a team whether to
   change the parser, raise chunk overlap, or train.

We will foreground the findings and the diagnostic (not the protocol's mechanics)
as the contribution in the intro.

## R3.2 — Construct validity (Qwen teacher reference, GPT-generated Q–A, 94/100)

A fair concern, and we bound the exposure precisely rather than dismiss it. The
key point is that our *comparative* claims are internally valid regardless of
reference/query noise: every parser and chunker ranking, and the 2.8× Hit@1
swing, holds the **same Q–A set fixed across systems**, so shared noise cannot
create a between-parser difference — it can only add variance. Three further
safeguards: (a) the confirmatory cross-domain evidence (OHR-Bench) uses
**externally human-curated** Q–A, not our synthetic set; (b) we tested the most
specific form of the "reference reflects the teacher's family" worry — that a
same-family matcher inflates non-Qwen parsers' absent rate — with a model-free
matching-strictness ladder and a cross-family judge (new family-neutral analysis,
Appendix~C), and the parser absent gap does not close as the matcher is loosened;
(c) we release the frozen eval set for audit. We will add a human-verified
subsample of reference/answer spans to quantify residual noise.

## R3.3 — Retrieval vs end-to-end RAG answer quality (the scope question)

This is the most important limitation and we state it plainly: RCPS evaluates
**answer-span retrievability**, not generated-answer quality, and we do not claim
the ranking transfers unchanged to end-to-end generation. We scope to retrieval
deliberately, for two reasons the paper should make explicit: (i) retrieval is a
*necessary* condition — content absent from the parser output (20.2% here) cannot
be recovered by any generator, so the coverage/absent findings are a hard floor
on end-to-end quality regardless of the reader; (ii) an end-to-end metric
entangles the parser with the generator and prompt, which is exactly the
confound our retriever-free diagnostic is designed to remove. The reviewer is
right that a high-span-retrieval parser could still produce misleading context,
or a low-span parser could be rescued by semantic generation — measuring that
directly is the natural next step, and we will add it as explicit future work
(and, if feasible in the revision window, a small end-to-end QA-accuracy check on
the top parsers to test whether the RCPS ordering is preserved).

## R3.4 — Retriever averaging necessity (deployment uses one retriever)

We agree its empirical necessity is modest and we already report exactly that: in
our data retriever-averaging only reverses a **near-tied top pair** (0.583 vs
0.584); every lower-tier ranking is identical under a single embedder, and the
chunker ordering is unchanged (we call it "an operational edge case rather than a
broad ranking reversal"). Our recommendation is therefore conditional, and we
will make it actionable: **if you know your deployed retriever, score with it;
averaging is a hedge only when candidates are near-tied or the retriever is not
yet fixed.** This turns the component into guidance about *when* the extra
machinery is worth it, rather than an always-on requirement.

## R3.5 — Probe-set stability (a direct question)

RCPS returns a ranking under a fixed probe, and the ranking is stable to the
choices we varied: both the parser and chunker rankings are **unchanged when RCPS
is computed with MRR@10 alone** (vs the averaged cutoffs), and format
normalisation shifts scores by 0.02–0.03 without reordering. We have not yet
varied the *probe questions* themselves at fixed size; we will add a
resampling-stability check (bootstrap over probe subsets, report ranking
agreement) to the revision, since it is cheap and directly answers the question.

## R3.6 — Generalisation to broader candidate pools and deployment settings

The strongest generalisation evidence is the *mechanism*, which is
corpus-independent: formatting quality and content preservation are different
properties, so intrinsic appearance metrics can be blind to the content loss
retrieval depends on. This replicates on OHR-Bench across all seven English
domains (Boundary Clarity stays flat under semantic corruption while retrieval
collapses) — a setting with a different language, different documents, and
externally curated Q–A. What is corpus-*specific* is the magnitude and sign of
the aggregate scalar (e.g. the exact $r$ and the 2.8× swing), which we already
flag as illustrative and n=5-limited (Limitations). So we claim generality for
the mechanism and the protocol, not for the specific numbers.

On candidate-pool breadth we are honest about the limit: five parsers on the
KoGov pool (three released outputs + twelve controlled perturbations on
OHR-Bench). The protocol is pool-agnostic by construction — it scores whatever
candidates a team supplies — but our *evidence* that it picks well is strongest
when the pool spans different parsing paradigms (VLM vs OCR), which is where
intrinsic metrics misrank most and where the +45.9 pp absent gap lives. For a
pool of near-tied same-paradigm parsers the decision is genuinely close and RCPS
(and any metric) separates them only marginally — we say so.

On deployment settings: the coverage diagnostic and the absent finding are
retriever-independent (no retriever is run), so they transfer directly; the RCPS
*ranking* is what a team should recompute with its own retriever and probe (see
R3.4/R3.5). We therefore present RCPS as a procedure to run on your pool, not a
fixed leaderboard to import.

## R3.7 — Parser-training section

We agree it is secondary and take the point that it adds length for a small,
partly-inconclusive effect. Its role is a bounded negative result — retrieval-aware
parser training does *not* beat a fidelity-distillation control (overlapping CIs),
which is itself informative for practitioners tempted to invest in it. We will
compress it and move detail to the appendix so it does not compete with the
primary contribution (C1–C3), consistent with the density point the reviewers
raise.

---

## Direct answers to your three questions

- **Is the RCPS ranking stable under changes to the probe set?** Stable to the
  choices we varied — parser and chunker rankings are unchanged with MRR@10 alone
  vs averaged cutoffs, and format normalisation reorders nothing. We will add a
  bootstrap-over-probe-subsets stability check (ranking agreement) to the revision
  to answer the probe-*question* resampling case directly (R3.5).
- **Does RCPS predict end-to-end RAG answer quality?** We do not claim it does;
  RCPS measures answer-span retrievability, which is a *necessary floor* (content
  absent from the parser — 20.2% here — no generator can recover) but not
  sufficient for generation quality. Testing whether the RCPS ordering is
  preserved end-to-end is explicit future work, and we will add a small
  top-parser QA-accuracy check if feasible in the window (R3.3).
- **How well does the conclusion generalise?** The *mechanism* generalises
  (replicated on OHR-Bench, seven English domains, human Q–A); the specific scalar
  magnitudes are corpus-dependent and flagged as illustrative. The protocol is
  pool- and deployment-agnostic by construction, with the caveat that its value is
  greatest for cross-paradigm pools (R3.6).

We are grateful the review identifies the paper's real boundary — retrieval, not
end-to-end generation — and we will state it as an explicit scope.
