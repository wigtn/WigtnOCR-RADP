# Absent adjudication criteria — human + LLM judge protocol

> For the R1 circularity rebuttal (지적 2). Owner: 상우 (contact@wigtn.com).
> This is the protocol both the human verifiers and the GPT-5.4 judge follow when
> deciding whether a parser's L1-absent answer is a genuine parser loss or a
> matching artefact. Releasing it (with per-case verdicts) is what makes the
> circularity refutation auditable rather than "trust our judge".

## Why a 3-way label, not binary

The naive judgment is binary: *is the answer string present in the page text?*
That is the wrong question for this paper. Our object is **retrieval**, not
string existence (the title is retrieval-conditional). A value that survives only
as OCR-mangled fragments ("5.943" → "S,94ろ", or split across three broken cells)
technically "exists" but is **not recoverable by any retriever** — counting it as
"present" would credit the parser for content no downstream stage can use.

So we adjudicate three states, on a **retriever-recoverability** criterion:

| Label | Definition | Counts as |
|---|---|---|
| **present** | The answer is stated on the page in a form a retriever could match the query to (any surface form / notation). | artefact (not a parser loss) |
| **degraded** | The answer's information is physically on the page but so corrupted / fragmented / detached from its row/header that a retriever cannot recover it. | **true-absent** |
| **absent** | The answer content is not on the page at all (e.g. table melted to an image reference; row dropped). | **true-absent** |

`genuine_absent = degraded + absent`. `artefact = present`.

**Justification to put in the paper (pre-empts the re-attack).** A reviewer may
ask "why do you count *degraded* as true-absent?" The answer is definitional, not
convenient: coverage is the *ceiling on retrieval* (§ coverage diagnostic), and a
chunk is relevant iff a retriever can surface it. Content that is present-but-
unrecoverable scores zero for every retriever by construction, so on the paper's
own relevance definition it is absent. Using "string exists" instead would make
the coverage metric inconsistent with the RCPS relevance rule it is supposed to
bound. This keeps the criterion coherent with the paper rather than gerrymandered
toward our conclusion.

## Adjudication rules (for both human and LLM)

Judge **content and recoverability**, not formatting. Decide only from the page
text shown — no outside knowledge, no guessing.

1. **present** iff the specific fact the question asks for is stated on the page
   AND a reader/retriever could locate it from the query terms (row label +
   value both survive, even if numbers/units are formatted differently, commas
   dropped, whitespace/markdown differs).
2. **degraded** iff the fact's characters are physically present but (a) the value
   is separated from the row/column header that identifies it, or (b) OCR
   corruption changes ≥1 digit/character of a numeric/spec answer, or (c) it is
   fragmented across non-adjacent lines — such that a query→chunk match would
   fail even under generous fuzzy matching.
3. **absent** iff the content is not on the page (table rendered as an image
   reference, row/section missing entirely).

Tie-break: if unsure between present and degraded, choose **present** (biases
against our own claim — the honest, conservative direction).

## Human verification sampling plan

Goal: confirm the LLM judge's artefact rate on the parsers whose absent we claim
is real (MinerU, PaddleOCR), and report it *whichever way it falls*.

- **Frame**: the L1-absent set per parser (MinerU 467, PaddleOCR 416).
- **Sample**: stratified by question_type (tabular / factoid / procedural /
  figural) proportional to each parser's absent composition; n = 60 per parser
  (≈13% of MinerU absent), drawn with a fixed seed from the released eval set.
- **Blind**: verifiers see (question, gold answer, parser page text) but NOT the
  parser name or the LLM verdict; 2 independent verifiers per item, disagreements
  adjudicated by a third. Report Cohen's κ (human–human) and human–GPT agreement.
- **Report**: human artefact rate per parser with a 95% CI, next to the GPT rate.
  If human artefact rate is materially higher than GPT's, we correct the
  semantic-absent numbers and say so; the deterministic ladder (Appendix~C) is
  unaffected either way and remains the primary evidence.

## LLM judge changes needed (scripts/evaluation/absent_llm_judge.py)

Current judge is binary (`present` bool). To match this protocol:
- Change the schema to `{label: present|degraded|absent, evidence: str}`.
- `genuine_absent = degraded + absent`; `artefact = present`.
- Keep the cross-family model (GPT-5.4) and the symmetric application to all
  parsers incl. Prod. Re-run over the L1-absent sets (~1,017 calls); cache resets.
- Expected effect: degraded cases currently rated "present" (artefact) move to
  true-absent, so the MinerU−Prod genuine gap can only **grow** vs the binary
  +47.5 pp — but report the actual number.

## Honesty clause (put a version of this in the rebuttal)

This experiment can come out against us. That is why it is worth running, and why
we report the artefact rate regardless. Hiding a significant artefact rate in the
rebuttal would surface worse at camera-ready verification.
