# Note to the Area Chair (optional — post as an AC-directed comment)

> ⚠️ **붙여넣을 때는 아래 `---` 밑의 본문만.** 제목 줄과 이 `>` 블록은 내부 메모.
> AC/PC 앞으로 보내는 짧은 메모 (리뷰어별 응답과 별개). Industry Track borderline
> (3/3/1.5)을 accept 쪽으로 밀 때 쓰는 "리뷰 신뢰도 정리". 공격 아님 — 사실만. 선택(안 올려도 됨).

---

We thank all three reviewers. We write briefly to the meta-reviewer to summarise
where the reviews converge, as we believe the paper's soundness is now well
supported and the remaining disagreement is one of scope-fit rather than validity.

**Convergence on soundness.** The two most confident reviews — ZQv618
(confidence 3) and bXGg (confidence 4) — independently rate **Soundness 3.5** and
Overall 3, and both write substantial, specific Reasons-to-Accept praising the
operational value, the coverage diagnostic, and the careful statistical reporting
(bootstrap CIs, exploratory-vs-confirmatory labelling, the honest training null).
Their reservations coincide on two points — conceptual novelty and single-domain
breadth — which we address directly in our responses: for an Industry-Track paper
the contribution is the operational finding and the reusable fault-localisation
diagnostic, not a new metric, and the cross-domain OHR-Bench evidence plus the
released benchmark speak to breadth.

**On the third review (NAor1, Overall 1.5).** We have addressed its points
factually in our response. We note for the meta-reviewer that its central
Reasons-to-Reject rest on details already in the paper: it states no external
standard benchmark is used, whereas OHR-Bench (seven domains, 2,264 externally
curated Q–A) is our confirmatory endpoint and is labelled as such; and it lists
reproducibility as unclear, whereas we release the RCPS implementation, the frozen
eval set, and checkpoints. BEIR, which it suggests, is a text-retrieval benchmark
with no scanned/born-digital PDFs and so cannot exercise the parsing stage the
paper studies. We make these corrections respectfully and defer to the
meta-reviewer on how to weigh a review whose stated rejection grounds are
addressed in the submitted paper.

**Self-audit disclosure.** In preparing this response we found and disclose a
configuration issue in our own MinerU baseline (table recognition was off). We
re-ran MinerU with tables enabled: the parser absent gap narrows but does not
close (MinerU−Prod +50.2 → +45.9 pp; table-evidence absent 87.9% → 41.7%, still
~3× the VLM parser). The parsing–retrieval disconnect is not an artefact of the
configuration; we correct the specific table-absent figure and release both
parser outputs. We flag this proactively in the interest of a transparent record.
