# Final posted rebuttal authority and camera-ready mapping

> Audited: 2026-08-22 · Rechecked: 2026-08-24
> Source: user-provided copy of the final OpenReview rebuttal
> SHA-256: `654e60466b29d137af5aa527e3fd534e14d005378e5571e1775ae3728b0c5f6f`
> Canonical paper baseline: PR #12 merge `a981bca`. At that baseline,
> `paper/latex/main_camera_ready.tex` uses C2=RCPS, C3=coverage, Marker sensitivity
> `r=-0.83`, E2E in Appendix B, and C4 details in Appendices E--G.
> `paper/latex/main.tex` is the frozen submission and is excluded from current-number checks.

This digest exists to prevent pre-posting reviewer drafts from being mistaken for
the final author response. If a local reviewer-specific rebuttal file conflicts
with the source above, the final posted response controls the camera-ready audit.

## Critical P5 correction

The final bXGg response does **not** promise blind re-verification of the same
100-pair Q--A quality sample that received the LLM-assisted 94/100 score. It says
that two authors verified 100 cases stratified from the LLM-judged absent sets,
with $\kappa=0.615$, 19 jointly adjudicated disagreements, and 90.3% human--LLM
binary agreement on 93 overlapping cases. The General Response reports the same
completed study. Those are the results now reported in Appendix C.

The superseded local draft `docs/REBUTTAL_R3_bXGg.md` contains an earlier
future-tense “same 100-Q--A” plan. It is not the posted commitment.

## Explicit revision commitments

| Final-response commitment | Current status |
|---|---|
| Lead the Introduction with findings and the diagnostic | Reflected in `paper/latex/main_camera_ready.tex` |
| Add parser I/O definition and a worked example in Appendix C | Reflected in Appendix C |
| Split dense abstract prose and define parser/chunker/retriever up front | Reflected in the camera-ready text |
| Move noise-family and DPO-milestone detail to appendices; compress parser training | Reflected: main C4 is a two-paragraph secondary study; details are in Appendices E--G |
| Correct the MinerU table-recognition configuration and Limitations | Reflected in text and tables; the recovered public MinerU-off artifact now has a deterministic release audit |
| Add the end-to-end table | Reflected in Appendix B with same-configuration MinerU-on reporting |
| Add the full-grid probe-stability version | Completed with the aligned 294-page, 663-Q--A, nine-system artifact and parser/chunker bootstrap outputs |
| State retrieval rather than end-to-end generation as the primary scope | Reflected in Introduction, Discussion, and Limitations |
| Add a reproducibility checklist and exact commands | Public `v1.0.0` download and CPU-only artifact gate are documented and verified from a clean checkout |

The 2026-08-24 pass also narrowed the Abstract and Introduction from a broad
“KoGovDoc-RAG evaluation files are released” statement to the artifact that was
then present. The current tree additionally contains the portable 294-page
source map and both MinerU configurations' output sets. Remaining rerun gaps are
stated at first mention and again in Appendix H.

The 2026-08-24 hierarchy pass makes RCPS selection the visible centre of the
paper without changing the promised Appendix C. Appendices A--D now support
C1--C3 (OHR alignment/noise, end-to-end top-choice check, absent-label
robustness, and chunker coverage), while Appendices E--G contain the secondary
C4 parser-training material. Appendix C still contains the promised parser I/O
definition, worked example, and human verification.

## Completed-response claims that still require artifact checks

- MRR@10-only aggregate ranking is traceable through
  `output/results/fullgrid_aggregate_audit.json`. The separate same-294-page
  per-Q--A re-index and probe bootstrap are now stored in
  `fullgrid_perqa_294p.json` and the two `rank_stability_*_294p.json` files.
  Raw matching lowers RCPS by 0.024--0.041 without reordering either pool, so
  the response-period 0.02--0.03 description is replaced rather than repeated.
- The final response says corrected outputs, per-case verdicts, analysis scripts,
  and checkpoints are released. The Git tree contains both MinerU configurations'
  294-page outputs, a deterministic tables-off release audit, a portable 294-page
  source map, analysis scripts, and the automated-judge cache. All nine evaluated
  LoRA adapters are in the public `wigtn/RCPS-RADP-Adapters` `v1.0.0` release;
  the tracked manifest records their source/release hashes and base-model lineage.
  Human adjudication records are deliberately retained in the author-only audit
  package, so “per-case verdicts” is not interpreted as publishing those private labels.
- The response-period seven-domain OHR claims were invalidated by the later
  legacy/v2 source-page audit. The camera-ready text correctly restricts itself
  to source-aligned replacements rather than repeating the invalid claim.
- The response says retrieval-aware training does not beat a fidelity-distillation
  control. The recovered Distill per-Q--A artifact shares the R2/R3 observation
  order and strict 2,036-Q--A mask. Distill-minus-R2 and Distill-minus-R3 Hit@5
  intervals both include zero, so the camera-ready text now directly supports
  that bounded negative result without restoring the invalid 2,264-Q--A summary.
- The response's 4.9-point “upper bound” language does not isolate contamination;
  the camera-ready text treats it only as a scale comparison.

SHACL is not part of this mapping. It belongs to the separate NAACL demo project
and must not enter EMNLP commits, figures, claims, or pull history.
