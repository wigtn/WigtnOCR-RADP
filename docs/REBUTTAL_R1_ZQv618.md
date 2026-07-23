# Rebuttal to R1 (ZQv618) — constructive, goal = raise score

> 전략: R1은 살릴 리뷰(3.0). 요청한 걸 **정확히 그대로** 주면 점수 상방.
> 3대 축 — ① circularity를 새 증거로 정면 격파, ② parser 정의 섹션 신설 약속,
> ③ novelty를 "관행이어야 하나 안 지켜진다"로 리프레이밍. ⟨...⟩ 는 서버 실행 후 숫자.
> 톤: 동의→증거→반영약속. 방어적으로 굴지 말 것.

---

We thank the reviewer for the careful and constructive read, and especially for
naming the same-family confound precisely — it let us test it directly.

**R1.1 — Potential circularity (pseudo-reference, QA, and matching all Qwen3).**
We agree this is the sharpest risk to C2, and we now rule it out three ways; none
requires re-generating data.

A **matching-strictness ladder** applied identically to every parser (new
appendix; 663 KoGov Q–A). We recompute each parser's *absent* rate under
progressively looser presence tests that neutralise, in turn, digit/punctuation
formatting (1,234 = 1234), word order and insertions (≥90% answer-token recall),
and OCR character noise (longest common run ≥80% of the answer). If MinerU's
excess absent were a same-family surface artifact it would shrink toward zero as
surface form is neutralised.

It does the opposite:

| Absent rate | L1 (paper matcher) | L4 (loosest: OCR-noise-tolerant) |
|---|---|---|
| Prod (Qwen3-VL-2B, *same family* as ref) | 20.2% | 16.9% |
| Qwen3-VL-2B-base (*same family*) | 25.2% | 21.1% |
| Qwen3-VL-30B teacher (*= ref source*) | 18.9% | 16.3% |
| **MinerU** (different family) | **70.4%** | **68.6%** |
| **PaddleOCR** (different family) | **62.7%** | **60.5%** |
| MinerU − Prod gap | **+50.2 pp** | **+51.7 pp** |
| PaddleOCR − Prod gap | **+42.5 pp** | **+43.6 pp** |

Three things rule out the same-family explanation. (i) The gap does not close as
surface form is neutralised — it is stable across all five rungs and slightly
*widens* at L4. (ii) The two other *same-family* parsers (2B-base, 30B) sit within
−1.4 to +5 pp of Prod, so lineage alone does not confer a low absent rate — the
+50 pp belongs to the OCR parsers specifically. (iii) Loosening the matcher
recovers more of Prod's absent (20.2→16.9, −3.3 pp of near-miss surface forms)
than MinerU's (70.4→68.6, only −1.8 pp), i.e. MinerU's absent is *hard* absence —
content the fuzzy matcher cannot find because it is not there. The failure
concentrates where content is lost: MinerU's absent is 87.9% on table-evidence
answers (Prod 13.9%) and does not improve at L4, exactly the dropped-table-cell
mechanism the paper describes. We will fold this table into C2.

We confirm this with a **cross-family judge**: OpenAI GPT-5.4, which shares no
lineage with the Qwen3 reference, the parsers, or the gold spans, adjudicates
every L1-absent answer as genuinely-missing vs present-but-surface-mismatched
(content, not formatting), applied symmetrically to all parsers. Genuine
(judge-confirmed) absent: Prod 9.2%, MinerU 56.7%, PaddleOCR 47.5% — a
**+47.5 pp** MinerU−Prod gap. Notably the exact-span matcher over-counted *Prod's*
absent more than MinerU's (54% of Prod's absent were surface artifacts vs only
19% of MinerU's), the opposite of what the same-family-bias hypothesis predicts;
correcting it symmetrically leaves the gap essentially unchanged. MinerU's
judge-confirmed absences are overwhelmingly table-evidence answers, matching the
dropped-table-cell mechanism.

The MinerU−Prod absent gap under three independent matching regimes:

| Matching regime | MinerU−Prod absent gap |
|---|---|
| Exact-span (paper's L1 matcher) | +50.2 pp |
| OCR-noise-tolerant fuzzy (L4) | +51.7 pp |
| Cross-family semantic judge (GPT-5.4) | +47.5 pp |

Three methods that fail differently — a strict substring test, a fuzzy character
matcher, and a non-Qwen LLM judging content — agree within a 4 pp band. No
matching artifact explains a gap this large and this stable. (On OHR-Bench, whose
answers are human-curated and family-independent, the same direction holds, so
the effect is not specific to the KoGov/Qwen pipeline.) Verdicts with evidence
quotes are released for audit.

We note the paper's matcher already strips markdown and whitespace *specifically*
so that formatting cannot penalise non-VLM parsers (design comment in the
released code); the analyses above extend that to content surface form. We will
fold the ladder into the C2 table and add the judge/anchor as an appendix.

**R1.2 — Parser problem definition.** We will add a half-page setup subsection
specifying the parser's exact I/O for this corpus: input = a single page image;
output = markdown; what is discarded (layout coordinates, figures reduced to
captions); how Prod's fine-tuning data and the reference markdown were
constructed and de-noised; and a short taxonomy of what produces an *absent*
answer — dropped table cells, skipped figure/stamp text, mis-OCR'd numerals —
with 2–3 worked examples. This directly addresses the crux of C2.

**R1.3 — Conceptual novelty.** We agree end-to-end evaluation before deployment
*should* be standard; our contribution is the evidence that it is not, and the
tooling that makes it decisive. Parsing benchmarks still rank parsers by intrinsic
fidelity (OmniDocBench), and an intrinsic-metric ranking would deploy the
worst-retrieving parser here (35.1 pp / 2.8× Hit@1 cost). Beyond "evaluate
extrinsically", the protocol contributes: (a) a **fault-localisation** diagnostic
separating parser-absent from chunker-split — not something end-to-end retrieval
numbers give; (b) retriever-averaging, which we show can flip the selected parser
vs a single embedder; and (c) format-normalised span relevance that needs no
manual chunk annotation. We will sharpen this framing in the intro.

**R1.4 — Density.** We will lighten the abstract (splitting the multi-clause
sentences), move the noise-family and milestone tables fully to the appendix, and
use the reclaimed space for R1.2. 

We believe R1.1–R1.2 remove the main soundness reservation, and are grateful the
review pointed to exactly the checks that strengthen the paper.
