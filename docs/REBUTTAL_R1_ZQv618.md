# Rebuttal to R1 (ZQv618) — constructive, goal = raise score

> ⚠️ **제출 전 이 `>` 전략 블록 전체를 삭제할 것** (내부 메모 — 리뷰어/AC에게 나가면 안 됨).
> 전략(팀 방향 반영): R1은 살릴 리뷰(3.0, Soundness 3.5). 4개 지적을 유형별로 다르게 친다.
> - 지적1(정의 부재)=판독불가 공격 → **약속 말고 지금 정의를 채운다**(입출력·버리는 것·absent 원인). (MinerU melted-table 실사례는 config 노출 위험으로 제거함.)
> - 지적2(순환성)=confound/관측적 동치 → 같은 측정기 데이터로는 안 깨짐. **다른 예측 지점(케이스를 열어봄)**에서만 깨진다: 직접 검사(실사례)+사람 검증 표본+교차가족 심판. 판정기준은 "존재"가 아니라 **retriever 회수가능성**(Degraded=회수불가→true-absent).
> - 지적3(novelty)=가치평가 → 반박 대신 **축 이동**(프로토콜 단순함 인정→findings가 주인공). 리뷰어의 "should"·Soundness 3.5·"interesting"을 아군으로. Industry Track의 존재이유=당위-현실 갭.
> - 지적4(density)=무조건 수용 + 구체 재배치("X빼고 Y넣는다"). 하나를 조건없이 수용해 나머지 3의 신뢰도를 올린다.

---

We thank the reviewer for a careful, constructive read that separates cleanly
into four asks; we address each in kind, and are especially grateful for naming
the same-family confound precisely enough to test.

## R1.1 — Parser problem definition (we show it, not promise it)

The reviewer is right that "absent" is only interpretable once the parser's I/O
is fixed. We define it concretely (and add Appendix~C):

- **Input.** A single rendered page image from Korean government documents —
  born-digital and scanned, layout-heavy: multi-column bodies, stamps/seals, and
  dense financial/spec tables with merged cells.
- **Output.** A linear Markdown transcription of readable content — body text in
  reading order, headings as ATX levels, tables as GitHub-flavoured Markdown.
  Discarded: layout coordinates, fonts, figure imagery (a figure survives only
  as emitted caption/in-image text), page furniture.
- **How ``absent'' arises.** Absence is structural and concentrates by evidence
  type — table content that does not reach the Markdown, skipped in-image text
  (captions, stamps, seals), and mis-recognised numerals/units. Because these are
  content-production failures, no chunker recovers them.
- **Provenance.** Prod is a Qwen3-VL-2B fine-tune; the reference markdown that
  defines fidelity and the gold spans is distilled from a Qwen3-VL-30B teacher
  and manually de-noised (pseudo-ground-truth, not human transcription; see
  Limitations).

This lives in Appendix~C (out of the 6-page body for space, per R1.4), and the
body's C2 paragraph points to it.

## R1.2 — Circularity is a confound; we break the observational equivalence

We agree this is the sharpest risk to C2, and that it cannot be answered with
more numbers *from the same measurer* — the confound (Qwen3 measurer + Qwen3
winner sharing a notation) and our hypothesis (parser quality) are
observationally equivalent under any Qwen3-based matching. The only way out is a
measurement where the two hypotheses predict *different* things: open the absent
cases and look. The confound predicts the answer is present but differently
formatted; our hypothesis predicts the content is genuinely gone. We test this
two ways, and by construction neither depends on Qwen3 notation:

**(a) A matching-strictness ladder** (Appendix~C), applied identically to every
parser, neutralising in turn digit/punctuation formatting, word order, and OCR
character noise. If the gap were surface-form it would shrink as the matcher
loosens. It does the opposite:

| Absent rate | L1 (paper matcher) | L4 (loosest) |
|---|---|---|
| Prod (Qwen3-VL-2B, *same family*) | 20.2% | 16.9% |
| Qwen3-VL-2B-base (*same family*) | 25.2% | 21.1% |
| Qwen3-VL-30B teacher (*= ref source*) | 18.9% | 16.3% |
| **MinerU** | **70.4%** | **68.6%** |
| **PaddleOCR** | **62.7%** | **60.5%** |
| MinerU − Prod gap | **+50.2 pp** | **+51.7 pp** |

The gap is stable and *widens* at L4; the two other same-family parsers sit
within −1.3…+5.0 pp of Prod, so shared lineage alone confers no low absent rate.
Loosening recovers more of Prod's absent (−3.3 pp of near-miss surface forms)
than MinerU's (−1.8 pp): MinerU's absent is *hard* absence. (One caveat we state
openly: the gold spans are Qwen-teacher-derived, so the ladder loosens the match
on the parser side but not the target side; the OHR-Bench check below, whose gold
is human-curated, is what closes that.)

We also disclose, proactively, a configuration issue we found in our own audit:
the MinerU baseline was run with table recognition off (tables emitted as image
refs). We re-ran MinerU with tables enabled: table-evidence absent falls from
87.9% to 41.7% (still ~3× Prod's 13.9%), and the overall MinerU−Prod absent gap
narrows from +50.2 to **+45.9 pp — it does not close**. So the disconnect is not
an artefact of the configuration; the specific table-absent magnitude was, and we
correct it (Setup/Limitations) and release the tables-on outputs.

**(b) A cross-family arbiter.** A GPT-5.4 judge — a *different family than the
parsers under test* (GPT vs Qwen3-VL); note the gold Q–A are GPT-generated, so the
judge is independent of the parsers being ranked but not of the query
distribution, which is exactly why the model-free ladder (a) carries the
argument and this only corroborates — labels every L1-absent answer by the paper's
own relevance criterion, **retriever-recoverability**: *present* (recoverable → a
surface artifact), *degraded* (physically on the page but not retriever-recoverable
→ true-absent), *absent* (not on the page → true-absent). Judging recoverability
rather than string existence keeps the label coherent with the RCPS relevance rule
(a chunk is relevant iff a retriever can surface it). Genuine (non-recoverable)
absent is **Prod 8.9% vs MinerU 59.3% — a +50.4 pp gap**. Decisively, the exact
matcher over-counts *Prod's* absent (56% surface artifacts) ~3.5× more than the
OCR parsers' (~16%) — the exact opposite of what same-family bias predicts;
PaddleOCR alone has 22% *degraded* (OCR-mangled beyond retrieval), a category a
binary present/absent test would have mislabelled. The `degraded` label is not
load-bearing: even at the adversarial extreme of counting *every* degraded case
as present (artifact), the genuine gap is still Prod 8.4% vs MinerU 52.8% =
**+44 pp**.

Crucially, this refutation does not rest on any LLM: the deterministic matching
ladder (a) is model-free and already places the gap at +50–52 pp; the
cross-family judge (b) only confirms it. For camera-ready we will additionally
human-verify a blind, stratified subsample against the same criterion and report
its artifact rate whichever way it falls.

As the criterion is loosened — exact substring → OCR-fuzzy → LLM
recoverability — the MinerU−Prod gap does not shrink:

| Matching regime | MinerU−Prod absent gap |
|---|---|
| Exact-span (paper's L1 matcher) | +50.2 pp |
| OCR-noise-tolerant fuzzy (L4) | +51.7 pp |
| Cross-family recoverability judge | +50.4 pp |

These are progressive refinements on the same L1-absent set and gold spans, not
three independent measurements, so their agreement shows the gap is neither a
surface-form nor a recoverability artifact — it is not from-scratch triangulation.
The one genuinely orthogonal check is OHR-Bench, whose gold Q–A are human-curated
and family-independent, and the gap direction holds there too. Two further points:
the paper's matcher already
strips markdown/whitespace *specifically* so formatting cannot penalise non-VLM
parsers (design comment in the released code), and on **OHR-Bench** — whose
answers are human-curated and family-independent — the same direction holds, so
the effect is not specific to the KoGov/Qwen pipeline. All per-case verdicts
(with evidence quotes) are released for audit.

## R1.3 — Novelty: we concede the protocol, and move the axis

The reviewer is correct that end-to-end pre-deployment evaluation *should* be
standard practice, and we do not claim RCPS is conceptually novel — its
simplicity is deliberate (training-free, no manual chunk annotation), because a
selection protocol is only adopted if it is cheap. The contribution is not the
protocol but the empirical findings, and the reviewer's own assessment already
values them (Soundness 3.5; "interesting" null result in Reasons to Accept):

1. Intrinsic parser metrics are not merely uncorrelated with retrieval but
   *anti-correlated* (Boundary Clarity Pearson $r=-0.81$) — an intrinsic-leaderboard
   choice deploys the worst-retrieving parser here, a 35.1 pp / 2.8× Hit@1 cost.
2. A retriever-free coverage diagnostic that localises the failure to the parser
   vs chunker layer — not something an end-to-end score provides.
3. The null result on retrieval-reward parser training (fidelity distillation
   matches it), which the reviewer flagged as interesting.

The reviewer's premise is our argument: everyone *should* evaluate extrinsically,
yet parser leaderboards are still ranked by intrinsic fidelity because the cost
is assumed prohibitive. Quantifying how badly that assumption misranks parsers,
and removing the cost, is precisely the "ought-vs-is" gap an Industry Track
exists to close — the stronger the reviewer's "should," the stronger this gap.
We will reframe the intro so the findings, not the protocol, are the headline;
this lets the score rise without contradicting the reviewer's own ratings.

## R1.4 — Density (conceded, with a concrete reallocation)

Agreed, and independently raised by the second reviewer, so we treat it as fact,
not preference. The revision is a concrete page reallocation, not a vague
promise: **out** to the appendix go the noise-family and DPO-milestone tables and
the multi-clause abstract sentences (split for readability); **in** to the freed
space goes nothing in the body — the new parser definition (R1.1) and
family-neutral diagnostic (R1.2) sit in appendices so the 6-page body does not
grow. Standardised parser/chunker/retriever terminology is defined up front.

---

We believe R1.1–R1.2 remove the main soundness reservation and R1.3 realigns the
paper with the reviewer's own high marks for its empirical core; we are grateful
the review pointed to exactly the checks that strengthen it.
