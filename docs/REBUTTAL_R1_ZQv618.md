# Rebuttal to R1 (ZQv618) — constructive, goal = raise score

> 전략(팀 방향 반영): R1은 살릴 리뷰(3.0, Soundness 3.5). 4개 지적을 유형별로 다르게 친다.
> - 지적1(정의 부재)=판독불가 공격 → **약속 말고 지금 보여준다**(표 붕괴 실사례 1개).
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
- **How ``absent'' arises (the crux).** A concrete case from our eval
  (page `val_0000`, a unit-price schedule 단가산출서). The question asks for the
  overhead cost (경비) of a pipe-laying line item; the gold answer is `5,943`.
  **Prod** parses the full nine-column table (품명/규격/단위/합계/노무비/재료비/
  경비/…), so the value is present and retrievable. **MinerU** emits, for the
  entire page, a single line — `![](images/…​.jpg)` (80 characters total): the
  table collapsed to an unparsed image reference, so every cell value is gone.
  This is the dominant absent mechanism (dropped/melted tables): MinerU is absent
  on 87.9% of table-evidence answers vs Prod's 13.9%. The other two are skipped
  in-image text (captions, stamps, seals) and mis-recognised numerals.
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
formatted; our hypothesis predicts the content is genuinely gone. We test this at
three scales, and by construction none depends on Qwen3 notation:

**(a) Direct inspection — the worked example above.** In the `val_0000` case
MinerU's entire page is an image placeholder: there is *no text at all* to
mismatch. A notation-sharing artifact cannot explain an absence where the parser
emitted zero table text. This is exactly the "open the case and look" arbiter,
and it lands on our side.

**(b) A matching-strictness ladder** (Appendix~C), applied identically to every
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
within −1.4…+5 pp of Prod, so shared lineage alone confers no low absent rate.
Loosening recovers more of Prod's absent (−3.3 pp of near-miss surface forms)
than MinerU's (−1.8 pp): MinerU's absent is *hard* absence.

**(c) A cross-family arbiter + human check.** A GPT-5.4 judge (no lineage with
the Qwen3 reference, parsers, or gold spans) adjudicates every L1-absent answer;
crucially, the criterion is not "does the string exist" but "is the answer
**recoverable by a retriever**" — a value present only as OCR-mangled fragments
below retrieval usefulness is counted *Degraded → true-absent*, because this
paper's object is retrieval, not string existence (justification detailed in the
adjudication protocol we release). Under this, genuine (non-recoverable) absent
is Prod 9.2% vs MinerU 56.7% — a +47.5 pp gap. Notably the exact matcher
over-counts *Prod's* absent (54% of it surface artifacts) more than MinerU's
(19%) — the opposite of the same-family-bias prediction. We are also
human-verifying a stratified subsample of MinerU/PaddleOCR absent cases against
this same recoverability criterion, and **will report the artifact rate
whichever way it falls** — the analysis is only worth running because it could
have gone against us.

Across three unrelated matching regimes the MinerU−Prod gap holds within a 4 pp
band (exact +50.2, OCR-fuzzy +51.7, cross-family-recoverability +47.5). No
matching artifact explains a gap this large across measurers this different.

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
