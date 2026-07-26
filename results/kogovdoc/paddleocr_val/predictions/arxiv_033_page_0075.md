Evaluation Dataset
We evaluate the PaLM family of models on a wide variety of tasks
Specifically, we evaluate the models on English Natural Language Process-
ing (NLP) tasks (Section 6.1), tasks from BIG-bench (BIG-bench collab-
oration, 2021), reasoning tasks (Section 6.3), code completion tasks (Sec
tion 6.4), multilingual generation and question answering tasks (Sec-
tion 6.6), translation tasks (Section 6.5), and bias and toxicity bench-
marks (Rudinger et al., 2018; Gehman et al., 2020).
We include finetuning results on SuperGLUE (?)， tasks from
Fine-tuning Dataset
GEM (Gehrmann et al., 2021), and TyDiQA (Clark et al., 2020). We
also finetune on a code dataset and share results on the finetuned model
on code synthesis tasks.
Evaluation Results
Benchmark Information
 Fewshot: English Natural Language Processing (NLP) tasks (Sec-
tion 6.1)， BIG-bench (Section 6.2), Reasoning (Section 6.3),
Code (Section 6.4), GEM (Section 6.6), Translation (Section 6.5),
Multi-lingual Question Answering (Section 6.7)
Finetuning: SuperGLUE (Section 6.1.2), GEM (Section 6.6), Ty-
DiQA (Section 6.7).
 Responsible AI: Co-occurrence, Winogender (Section 10.1.1), Real-
Toxicity (Section 10.2).
 Data contamination (Section 8)
Reported in Evaluation (Section 6)
Evaluation Results
Model Usage & Limitations
PaLM is capable of open-ended text generation. This model should not be
Sensitive Use
used for any of the unacceptable language model use cases, e.g., generation
of toxic speech.
PaLM is designed for research. The model has not been tested in settings
Known Limitations
outside of research that can affect performance, and it should not be used
for downstream applications without further analysis on factors in the
proposed downstream application.
Reported in Ethical Considerations (Section 11).
Ethical Considerations & Risks
Table 30: PaLM Model Card
75