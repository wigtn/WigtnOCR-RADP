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
| Correct the MinerU table-recognition configuration and Limitations | Reflected in text and tables; public MinerU-off artifact still needs verification |
| Add the end-to-end table | Reflected in Appendix B with same-configuration MinerU-on reporting |
| Add the full-grid probe-stability version | Pending a same-294-page full-grid artifact |
| State retrieval rather than end-to-end generation as the primary scope | Reflected in Introduction, Discussion, and Limitations |
| Add a reproducibility checklist and exact commands | Conditional wording in R1; final clean-checkout verification remains pending |

The 2026-08-24 pass also narrowed the Abstract and Introduction from a broad
“KoGovDoc-RAG evaluation files are released” statement to the artifact that is
actually present: the frozen 663-Q--A probe and RCPS implementation. The missing
portable source-page mapping and rerun artifacts are now stated at first mention
and again in Appendix H.

The 2026-08-24 hierarchy pass makes RCPS selection the visible centre of the
paper without changing the promised Appendix C. Appendices A--D now support
C1--C3 (OHR alignment/noise, end-to-end top-choice check, absent-label
robustness, and chunker coverage), while Appendices E--G contain the secondary
C4 parser-training material. Appendix C still contains the promised parser I/O
definition, worked example, and human verification.

## Completed-response claims that still require artifact checks

- MRR@10-only aggregate ranking is now traceable through
  `output/results/fullgrid_aggregate_audit.json`: the RCPS and MRR@10-only
  orders agree for the five 294-page parsers and Prod's four chunkers. This does
  not close the separate probe-resampling promise. The reported 0.02--0.03
  normalisation shift still needs ranked chunk lists or a re-index before
  inclusion.
- The final response says corrected outputs, per-case verdicts, analysis scripts,
  and checkpoints are released. The current Git tree contains analysis scripts
  and the automated-judge cache, but the final human adjudication labels,
  MinerU-off predictions, and parser-training checkpoint/config release are not
  presently traceable here.
- The response-period seven-domain OHR claims were invalidated by the later
  legacy/v2 source-page audit. The camera-ready text correctly restricts itself
  to source-aligned replacements rather than repeating the invalid claim.
- The response's 4.9-point “upper bound” language does not isolate contamination;
  the camera-ready text treats it only as a scale comparison.

SHACL is not part of this mapping. It belongs to the separate NAACL demo project
and must not enter EMNLP commits, figures, claims, or pull history.
