# Plan to push R3 (bXGg) 3.0 → 3.5+ : E2E RAG + dataset validity + Industry framing

> Team direction (2026-07-25): (1) we did NOT run end-to-end RAG — build the
> pipeline and show the impact on metrics; (2) address the distillation-dataset
> doubt (Qwen-teacher reference); (3) argue that a Research-track 3.0 is an
> Industry-track 4.0+. If (1)+(2) land, R3 is plausibly 3.5.

## Status check

- **E2E RAG: confirmed absent.** The repo measures retrieval only (RCPS/MRR/Hit@k,
  coverage diagnostic, absent judge). No generator-consumes-context answer metric
  exists (verified across scripts/, src/, output/). R3's Reason-to-Reject #3 and
  Question #2 are therefore correct, not a misread — we must *build*, not rebut.
- **Dataset:** KoGov reference markdown is a Qwen3-VL-30B teacher distillation;
  Q–A are GPT-5.4-generated, LLM-judge-checked (94/100). R1 and R3 both flag this.

## (1) End-to-end RAG — the experiment R3 asks for

**Deliverable in this branch:** `scripts/evaluation/eval_e2e_rag.py`. It reuses the
repo's chunker + retriever (retrieval half identical to RCPS), then adds the
missing stage: retrieve top-k → a generator answers from ONLY those chunks → score
the generated answer by (a) a cross-family LLM judge (correct 1/0, accepts
paraphrase) and (b) exact/substring EM. It computes each parser's **answer
accuracy** and the **Spearman ρ between the parser ranking by answer accuracy and
by RCPS** — the exact "does RCPS predict end-to-end quality?" number.

**Run (on the machine with data + a GPU embedder + OpenAI key):**
```bash
export OPENAI_API_KEY=...
uv run python scripts/evaluation/eval_e2e_rag.py \
    --qa data/KoGovDoc-RAG/qa_pairs_v1.jsonl \
    --root <RESULTS>/kogovdoc --val_jsonl data/KoGovDoc-Bench/val.jsonl \
    --parsers Prod MinerU-tableon Qwen3-VL-30B PaddleOCR \
    --retriever bge-m3 --k 5 --gen_model gpt-5.4-2026-03-05 \
    --sample 200 --rcps_json output/baselines/grid_v1_parser_native.json
```
Start with `--sample 200` (cost/time), then full 663. Use **MinerU-tableon** (the
fair config) so the E2E comparison isn't re-contaminated by the table-off bug.

**What to report (either outcome is publishable):**
- If parser ranking by answer accuracy tracks RCPS (high ρ) → "RCPS predicts
  end-to-end quality; span-retrievability is a sufficient proxy for selection."
  This *upgrades* the contribution from "retrieval floor" to "validated selector."
- If it diverges → an honest, interesting finding: RCPS is a necessary floor but
  generation can reorder near-ties; we report where and why. Still answers R3.
- Cost estimate: 4 parsers × 200 QA × 1 generate + ≤1 judge ≈ ≤1,600 API calls
  (~$ single digits, ~15 min). Full 663 ≈ 5× that.

## (2) Distillation-dataset doubt — three concrete moves

The worry: the reference (hence gold spans) is a Qwen-teacher distillation, so
noise/teacher-style could bias the benchmark. We already argue comparative claims
hold the Q–A fixed across systems (internal validity). To *reduce* the doubt:

1. **Human-verify a stratified subsample of the reference/answer spans** (n≈60,
   blind, 2 annotators + tiebreak; report Cohen's κ and the % of gold spans judged
   faithful). This directly quantifies residual reference noise — the number R3
   says is "unclear." Cheap, and we already committed to it in the rebuttal.
2. **Cross-reference-source check:** re-derive gold spans for that subsample from
   the *raw page* (human transcription), independent of the Qwen teacher, and
   re-run the absent ladder against those human targets. If the parser gap holds
   vs human gold, the teacher-style-bias worry is closed at the source (this also
   strengthens R1.2). Ties into `scripts/evaluation/absent_robustness.py`.
3. **OHR-Bench is the external control:** its Q–A are human-curated and not
   teacher-derived, and the mechanism replicates there — state this explicitly as
   the answer to "does the benchmark reflect the teacher's strengths?"

Moves (1)+(2) are a small annotation effort on the data machine; (3) is text.

## (3) Industry-Track framing — "Research 3.0 ≈ Industry 4.0+"

All three reviewers scored on the ACL rubric where "3.0 = solid but narrower than
main-*conference* expectation." That expectation is calibrated to the **Research
track**, whose bar is methodological novelty. This is an **Industry-Track**
submission, judged on operational value, deployability, and real-world evidence —
where the reviewers' own praise lives:
- R1/R3 both give **Soundness 3.5** and write long Reasons-to-Accept on
  "operationally meaningful," "deployable," "actionable decomposition," "careful
  reporting."
- The single recurring reservation — *limited conceptual novelty* — is the axis an
  Industry Track explicitly de-prioritises. On the Industry-Track rubric
  (practical impact, evidence, deployability) the same submission clears the main
  bar.

**Where to say it:** not as "please regrade," but folded into the AC-facing note
and each novelty reply — "for an Industry-Track contribution the deliverable is
the operational finding + reusable diagnostic, and the reviews' Soundness 3.5 and
Reasons-to-Accept reflect exactly that." The E2E result (1), if positive, is the
concrete evidence that converts "sensible recipe" into "validated selection method
with measured downstream impact" — the strongest single lever to move 3.0 → 3.5+.

## Sequencing

1. Run E2E on `--sample 200` (fast) → get the ρ and per-parser answer accuracy.
2. If positive, run full 663 + add a short E2E paragraph/table to the paper and to
   the R3 reply (replace "future work" with the actual number).
3. Human-verify subsample for dataset validity (parallel, on data machine).
4. Fold the Industry-Track framing into the novelty replies (text only, now).
