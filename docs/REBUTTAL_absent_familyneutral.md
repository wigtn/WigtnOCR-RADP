# Rebuttal working doc — "absent is real, not a same-family artifact"

> Status: draft for the ACL rebuttal (2 of 3 reviews in; R3 due ~before 25 Jul).
> Owner: contact@wigtn.com. Ties the new **family-neutral absent diagnostic** to
> the reviewer points and lays out the exact tables to paste into the response.

## Review map (what we are answering)

| Our label | Reviewer | Overall | Posture | Key ask we act on |
|---|---|---|---|---|
| **R1** | ZQv618 | 3.0 (Workshop) | constructive, winnable | **Circularity**: pseudo-ref + QA + verbatim matching all Qwen3-family → MinerU's higher absent could be an *artifact*. Wants a **human/independent check of "absent"**. Also: parser problem-definition section; density. |
| **R2** | NAor1 | 1.5 (Resubmit) | terse, misreads | "Use external standard benchmarks (BEIR)"; "reproducibility unclear"; "novelty unclear"; readability. Gives **no actionable path** → aim to *discount* for the AC. |

Strategy: **raise R1** by giving exactly the evidence it asked for; **discount R2**
by correcting factual misreads (we already use an external benchmark; code+data
released). If R3 lands near R1, R2 is the outlier the AC can down-weight.

---

## 1. The circularity mechanism (R1's real point)

Gold `answer_span`s are verbatim substrings of the **Qwen3-VL-30B** reference.
`absent` = the span is not a substring of a parser's page output under
`normalize_for_match` (NFKC + lowercase + whitespace/markdown removal,
`types.py:17`). So:

- **Prod (Qwen3-VL-2B, same family)** tends to reproduce the reference *surface
  form* → matches → low absent.
- **MinerU / PaddleOCR (different family)** may carry the same *content* in a
  different surface form (digit separators, spacing, OCR substitutions, word
  order) → fails substring test → counted absent even when the content is there.

⇒ The parser absent gap *could* be a matching artifact. This is a fair concern.

**Partial pre-existing defense (state it first):** the matcher already strips
markdown + whitespace *specifically so formatting does not penalise non-VLM
parsers* — see the design comment at `types.py:9-14`. So the paper already
neutralises the *formatting* half of the objection. What remained untested was
the *content surface-form* half. We now test it directly.

## 2. New evidence A — matching-strictness ladder (deterministic, no LLM)

`scripts/evaluation/absent_robustness.py` recomputes each parser's absent rate
under a ladder of ever-looser presence tests (`evaluation/absent_matchers.py`):

| Rung | Neutralises | 
|---|---|
| L0 exact | nothing (raw substring) |
| **L1 normalized** | markdown + whitespace + case (← the paper's matcher) |
| L2 numeric | digit separators, in-content punctuation (1,234 == 1234) |
| L3 token-recall | word order / insertions (≥90% of answer tokens present) |
| L4 fuzzy-LCS | OCR character noise (longest common run ≥80% of answer) |

**Logic:** if MinerU/PaddleOCR's excess absent were a surface-form artifact, the
gap over Prod would shrink toward 0 as we climb L1→L4. If it *survives to L4*,
the content is genuinely absent.

**RESULT (ran on server ml35, 2026-07-23, 663 KoGov Q–A, no API):**

```
Absent rate (%)          L0     L1     L2     L3     L4
Prod (Qwen3-VL-2B)       24.1   20.2   19.6   24.1   16.9
Qwen3-VL-30B (ref src)   22.8   18.9   16.6   19.2   16.3
Qwen3-VL-2B-base         30.0   25.2   24.7   27.0   21.1
MinerU                   74.8   70.4   68.0   73.0   68.6
PaddleOCR                67.0   62.7   62.0   59.9   60.5
--- gap vs Prod (pp) ---
MinerU − Prod           +50.7  +50.2  +48.4  +48.9  +51.7   ← does NOT close; widens at L4
PaddleOCR − Prod        +42.8  +42.5  +42.4  +35.7  +43.6
```

**Verdict: circularity rejected.** The gap is stable across all five rungs and
*widens* at the loosest (L4). Same-family 2B-base/30B sit within −1.4..+5 pp of
Prod, so lineage ≠ low absent. Loosening recovers more of Prod's absent (−3.3 pp)
than MinerU's (−1.8 pp) → MinerU's absent is hard (content gone), not near-miss
surface form. By question type, MinerU absent is 87.9% on tabular (Prod 13.9%),
flat at L4 — the dropped-table-cell mechanism. Files:
`output/diagnostics/absent_robustness.{json,md}`.

Symmetric by construction (same matcher applied to every parser, Prod included),
so this cannot favour Qwen. Caveat we will state honestly: Korean josa
agglutination makes L1–L4 conservative (they *under*-count presence), which only
strengthens "present" claims and motivates the LLM ceiling below.

## 3. New evidence B — cross-family LLM-judge ceiling (L5)

`scripts/evaluation/absent_llm_judge.py` takes each parser's L1-absent set and
asks a **non-Qwen judge (OpenAI GPT-5.4)** whether the page text contains the
information to answer the question (content, not formatting). This removes *any*
same-family surface bias — the judge shares no lineage with the reference, the
parsers, or the gold spans.

Each L1-absent answer → `genuine_absent` (judge: not present) or `artifact`
(judge: present, L1 missed it). **RESULT (ran ml35, GPT-5.4, full L1-absent sets,
1,017 verdicts):**

```
                 L1-absent   artifact(% of absent)   semantic-absent
Prod             20.2%       54% (73/134)            9.2%
MinerU           70.4%       19% (91/467)            56.7%
PaddleOCR        62.7%       24% (101/416)           47.5%
```

MinerU−Prod semantic-absent gap = **+47.5 pp**. Prod's artifact fraction (54%) >
MinerU's (19%) — exact-span over-counted *Prod's* absent more, opposite of the
same-family-bias prediction. Three regimes converge: exact +50.2 / fuzzy +51.7 /
semantic +47.5 pp. Files: `output/diagnostics/absent_llm_judge.{json,_cache.jsonl}`.
MinerU genuine-absent samples are overwhelmingly tabular (table-cell drop).

**Claim we expect to make:** MinerU/PaddleOCR retain a large semantic-absent gap
over Prod ⇒ their answers are genuinely missing content. Running the judge on
Prod's own absent set makes the artifact-fraction comparison symmetric; if L1
were pro-Qwen-biased, OCR parsers would show a *higher* artifact fraction — we
subtract exactly that out, so the residual gap is bias-free.

Also gives R1 the **human-style verification it requested**, at scale and
audit-able (verdicts cached with evidence quotes in
`output/diagnostics/absent_llm_judge_cache.jsonl`). Optionally hand-verify ~30
judge verdicts per parser to report judge accuracy.

## 4. New evidence C — external-GT anchor (OHR-Bench)

OHR-Bench answers are **human-curated** (independent of Qwen). Absent rate of
MinerU vs Qwen2.5-VL there is family-neutral *by construction*: the answer
surface form comes from humans, so no parser family has a matching edge. If
MinerU still shows higher absent on OHR-Bench → decisive that the effect is not a
KoGov/Qwen pipeline artifact. (Compute with the same ladder over
`data/OHR-Bench/retrieval_extracted/{MinerU,Qwen2.5-VL}`; answers from
`OHR-Bench.parquet`.) This also doubles as the reply to **R2's "use an external
benchmark"** — we already do, as the confirmatory endpoint (§C4).

---

## 5. Response snippets (paste-ready once numbers land)

**To R1 (circularity):** "We agree the shared Qwen3 lineage is a potential
confound and tested it three ways. (a) A matching-strictness ladder that
neutralises digit-formatting, word order, and OCR character noise leaves the
MinerU−Prod absent gap at __ pp (vs __ pp under the paper's matcher) — the gap
does not close as surface form is neutralised. (b) A cross-family GPT-5.4 judge,
which shares no lineage with the reference or any parser, confirms __% of
MinerU's absent answers are genuinely missing content. (c) On OHR-Bench, whose
answers are human-curated, MinerU's absent rate remains higher. The parser gap is
real content loss, not a same-family matching artifact. We add these as a new
appendix and will fold the ladder into the C2 table."

**To R1 (parser problem-definition):** add a ½-page §Setup subsection: parser
input = one page image; output = markdown; what is discarded (layout coords,
figures→captions); how Prod's SFT data and the 30B reference markdown were built;
and a taxonomy of what makes an answer "absent" (dropped table cells, skipped
figure text, mis-OCR'd numerals) with 2–3 examples.

**To R2 (external benchmark / reproducibility):** "OHR-Bench (7 domains, 2,264
externally-curated Q–A) *is* our external standard benchmark and the confirmatory
endpoint (§C4, Limitations); KoGov is labelled exploratory. BEIR contains no
scanned/born-digital PDFs, so it cannot exercise the parser stage this paper
studies. Code, the RCPS reference implementation, the frozen eval set, and
training checkpoints are released for reproduction." Keep tone neutral; the goal
is to let the AC see the misreads.

---

## 6. Run order (on the GPU machine where parser outputs live)

```bash
# 1. deterministic ladder (no API) — fills tables in §2 and the OHR anchor
uv run python scripts/evaluation/absent_robustness.py --ref Prod

# 2. cross-family LLM ceiling — fills §3 (pilot first, then full)
export OPENAI_API_KEY=...
uv run python scripts/evaluation/absent_llm_judge.py --parsers Prod MinerU PaddleOCR --max_per_parser 40   # pilot
uv run python scripts/evaluation/absent_llm_judge.py --parsers Prod MinerU PaddleOCR                        # full
```

Outputs land in `output/diagnostics/absent_robustness.{json,md}` and
`absent_llm_judge.{json,jsonl}`. Paste the numbers into §2/§3 tables and the §5
snippets.
