HellaSwag (Zellers et al., 2019), WinoGrande (Sak-
RACE-high
RACE-middle
aguchi et al., 2021), ARC easy and challenge (Clark
GPT-3
58.4
175B
45.5
et al., 2018) and OpenBookQA (Mihaylov et al.,
42.3
8B
2018). These datasets include Cloze and Winograd
57.9
PaLM
64.3
47.5
62B
style tasks, as well as multiple choice question an-
540B
68.1
49.1
swering. We evaluate in the zero-shot setting as
done in the language modeling community.
61.1
7B
46.9
In Table 3, we compare with existing models
13B
47.2
61.6
LLaMA
of various sizes and report numbers from the cor-
33B
64.1
48.3
responding papers. First, LLaMA-65B outper-
51.6
65B
67.9
forms Chinchilla-70B on all reported benchmarks
but BoolQ. Similarly, this model surpasses PaLM-
Table 6: Reading Comprehension. Zero-shot accu-
540B everywhere but on BoolQ and WinoGrande.
racy.
LLaMA-13B model also outperforms GPT-3 on
most benchmarks despite being 10x smaller.
school Chinese students. We follow the evaluation
3.2 Closed-book Question Answering
setup from Brown et al. (2020) and report results
in Table 6. On these benchmarks, LLaMA-65B is
We compare LLaMA to existing large language
competitive with PaLM-540B, and, LLaMA-13B
models on two closed-book question answering
outperforms GPT-3 by a few percents.
benchmarks: Natural Questions (Kwiatkowski
et al., 2019) and TriviaQA (Joshi et al., 2017). For
3.4Mathematical reasoning
both benchmarks, we report exact match perfor-
We evaluate our models on two mathematical rea-
mance in a closed book setting, i.e., where the mod-
soning benchmarks: MATH (Hendrycks et al..
els do not have access to documents that contain
2021) and GSM8k (Cobbe et al., 2021). MATH
evidence to answer the question. In Table 4, we
is a dataset of 12K middle school and high school
report performance on NaturalQuestions, and in Ta-
mathematics problems written in LaTeX. GSM8k
ble 5, we report on TriviaQA. On both benchmarks,
is a set of middle school mathematical problems.
LLaMA-65B achieve state-of-the-arts performance
In Table 7, we compare with PaLM and Min-
in the zero-shot and few-shot settings. More im-
erva (Lewkowycz et al., 2022). Minerva is a series
portantly, the LLaMA-13B is also competitive on
of PaLM models finetuned on 38.5B tokens ex-
these benchmarks with GPT-3 and Chinchilla, de-
tracted from ArXiv and Math Web Pages, while
spite being 5-10x smaller. This model runs on a
neither PaLM or LLaMA are finetuned on mathe-
single V100 GPU during inference.
matical data. The numbers for PaLM and Minerva
are taken from Lewkowycz et al. (2022), and we
O-shot 1-shot 5-shot
64-shot
compare with and without maj1@k. maj1@k de-
57.2
280B
43.5
57.0
Gopher
notes evaluations where we generate k samples for
Chinchilla 70B
55.4
64.1
64.6
each problem and perform a majority voting (Wang
et al., 2022). On GSM8k, we observe that LLaMA-
7B
50.0
53.4
56.3
57.6
65B outperforms Minerva-62B, although it has not
56.6
13B
60.5
63.1
64.0
LLaMA
been fine-tuned on mathematical data.
33B
67.9
65.1
69.9
70.4
71.6
68.2
72.6
73.0
65B
3.5Code generation
We evaluate the ability of our models to write
Table 5: TriviaQA. Zero-shot and few-shot exact
match performance on the filtered dev set.
code from a natural language description on two
benchmarks: HumanEval (Chen et al., 2021) and
MBPP (Austin et al., 2021). For both tasks, the
3.3Reading Comprehension
model receives a description of the program in a
We evaluate our models on the RACE reading com-
few sentences, as well as a few input-output ex-
prehension benchmark (Lai et al., 2017). This
amples. In HumanEval, it also receives a function
dataset was collected from English reading com-
signature, and the prompt is formatted as natural
prehension exams designed for middle and high
code with the textual description and tests in a