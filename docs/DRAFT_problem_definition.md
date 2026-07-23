# Draft: parser problem-definition subsection (answers R1.2)

> Paste-ready LaTeX for a new subsection under §Setup (`sec:setup`) in main.tex.
> Gives the parser's exact I/O for this corpus, how Prod + the reference were
> built, and a taxonomy of what produces an *absent* answer — the crux R1 flagged
> as undefined. Numbers are from the family-neutral diagnostic
> (`output/diagnostics/absent_robustness.json`, per-question-type breakdown).
> Keep it to ~½ column; move any overflow to an appendix.

---

```latex
\subsection{What a Parser Produces --- and Drops}
\label{sec:parser-def}

\paragraph{Parser I/O for this corpus.} A \emph{document parser} here is a
function from a single rendered page image to a linear Markdown transcription of
its readable content: body text in reading order, headings as ATX (\texttt{\#})
levels, and tables as GitHub-flavoured Markdown. Non-textual structure is
deliberately \emph{discarded}: pixel/layout coordinates, font and colour, figure
imagery (a figure survives only as whatever caption or in-image text the parser
emits), and page furniture (running heads, stamps, handwritten margin notes)
unless transcribed as text. Downstream, only this Markdown is chunked, embedded,
and retrieved --- so any answer content the parser fails to emit is invisible to
every later stage, which is exactly what the coverage diagnostic (\S\ref{sec:coverage})
measures.

\paragraph{Prod and the reference markdown.} \textbf{Prod} is a Qwen3-VL-2B
\citep{qwen3vl} model fine-tuned (LoRA, \S\ref{sec:setup}) for Korean
government-document parsing under the I/O contract above. The \emph{reference}
markdown --- against which fidelity (TextNED) and the gold answer spans are
defined --- is distilled from a larger Qwen3-VL-30B teacher and manually
de-noised to remove contaminated samples; it is pseudo-ground-truth, not human
transcription (see Limitations). Gold answer spans are verbatim substrings of
this reference, so ``absent'' means the parser's own Markdown does not contain the
span under the format-normalised matching of \S\ref{sec:rcps}.

\paragraph{What makes an answer \emph{absent}.} Absence is not random OCR jitter
but a small set of structural failures, and it concentrates by evidence type. On
Prod's output, table-evidence answers are absent $13.9\%$ of the time and
factoid/procedural answers $\sim\!21\%$, but figure-evidence answers $71.4\%$ ---
figures rendered as images carry no retrievable text. The three recurring causes:
(i)~\textbf{dropped table cells} --- a value present in a source table never
reaches the Markdown, the dominant failure for OCR-style parsers (MinerU is
absent on $87.9\%$ of table-evidence answers, vs Prod's $13.9\%$; \S\ref{sec:c1c2});
(ii)~\textbf{skipped in-image text} --- captions, stamps, seals, and figure
labels left untranscribed; and (iii)~\textbf{mis-recognised numerals/units} ---
a digit or unit corrupted past the fuzzy-match tolerance (\S\ref{sec:c1c2}), which
turns a would-be hit into an absence. Because these are content-production
failures, no chunker recovers them --- the motivation for the parser-side
analysis in \S\ref{sec:c4}.
```

---

## Placement / cross-refs to wire up
- Label `sec:parser-def`; reference it from the C2 paragraph in `sec:c1c2` and
  from the coverage-diagnostic intro (`sec:coverage`) so the "absent" term points
  back here.
- The `87.9%` / `13.9%` tabular numbers come from the new family-neutral run and
  also anchor the R1.1 circularity table — reuse the same appendix figure.
- If space is tight: keep paragraphs (1) and (3), compress (2) into one sentence.
