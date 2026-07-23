# Rebuttal to R2 (NAor1) — goal = correct misreads, let the AC down-weight

> 전략: R2(1.5)는 actionable 결론이 없고 핵심 근거가 **사실 오독**. 공격하지 말고,
> 정중하게 팩트만 교정해서 "이 리뷰의 감점 사유가 오해에 기반한다"는 걸 AC가
> 스스로 보게 한다. 특히 (1) 외부 벤치마크 미사용 주장 → OHR-Bench가 바로 그것,
> (2) reproducibility unclear → 코드/데이터/체크포인트 공개. 짧고 단정하게.

---

We thank the reviewer. Several of the concerns rest on points the paper already
addresses; we clarify them here and hope they resolve the reservations.

**"Use external standard benchmarks; results are specific to one corpus."**
The paper already does. Alongside the released Korean corpus (KoGov, our
contributed artifact), all confirmatory claims run on **OHR-Bench** — an external,
independently-curated document-RAG benchmark of seven domains and 2,264
verbatim-answerable Q–A (Law, Manual, Finance, Textbook, News, Academic,
Administration). KoGov is explicitly labelled *exploratory* and OHR-Bench
*confirmatory* (§C4, Limitations); the parser-training endpoint, the cross-domain
insensitivity finding, and the noise-perturbation grid are all on OHR-Bench, not
KoGov. Regarding BEIR specifically: BEIR is a *text* retrieval benchmark and
contains no scanned or born-digital PDFs, so it cannot exercise the document-
**parsing** stage that is this paper's subject — a parser cannot be varied on
inputs that arrive as clean text. OHR-Bench is the appropriate external standard
for the parsing→retrieval question, and we use it as such.

**"Reproducibility is unclear."** We release the RCPS reference implementation,
the evaluation code, the frozen KoGov eval set, and the parser-training
checkpoints; OHR-Bench is public. Every comparative result holds the Q–A set
fixed across systems (paired bootstrap CIs, 1,000+ resamples), and the protocol
requires no manual relevance annotation. We are happy to add a reproducibility
checklist and exact run commands to the appendix if that would help.

**"Novelty is unclear."** The contribution is not a new similarity function — its
simplicity is deliberate — but the empirical finding that intrinsic parser metrics
*invert* the correct deployment choice (a 2.8× Hit@1 swing), that the failure
localises to the parser layer (a fault-localisation diagnostic, not an end-to-end
score), and that retriever-averaged, format-normalised selection recovers the
right parser. Extrinsic selection *should* be standard practice, yet parser
leaderboards are still ranked by intrinsic fidelity; quantifying that misranking
and removing its cost is exactly the ought-vs-is gap an Industry-Track paper
exists to close. We will state this delta explicitly in the intro.

**"Difficult to read."** We take this seriously and will revise for clarity:
splitting the long multi-clause sentences (starting with the abstract),
standardising terminology (parser / chunker / retriever roles defined up front),
and adding a parser problem-definition (Appendix~C) so the setup is
self-contained. No result depends on the dense phrasing; the revision is purely
expository.

We believe the external-benchmark and reproducibility concerns stem from details
already in the paper, and the remaining points are expository fixes we can make
within the revision; we would welcome the reviewer revisiting the score in that
light.
