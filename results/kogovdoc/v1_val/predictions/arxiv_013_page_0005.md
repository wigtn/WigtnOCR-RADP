## 3.2 Closed-book Question Answering

We compare LLaMA to existing large language models on two closed-book question answering benchmarks: Natural Questions (Kwiatkowski et al., 2019) and TriviaQA (Joshi et al., 2017). For both benchmarks, we report exact match performance in a closed book setting, i.e., where the models do not have access to documents that contain evidence to answer the question. In Table 4, we report performance on NaturalQuestions, and in Table 5, we report on TriviaQA. On both benchmarks, LLaMA-65B achieve state-of-the-arts performance in the zero-shot and few-shot settings. More importantly, the LLaMA-13B is also competitive on these benchmarks with GPT-3 and Chinchilla, despite being 5-10× smaller. This model runs on a single V100 GPU during inference.

| | 0-shot | 1-shot | 5-shot | 64-shot |
|---|---|---|---|---|
| Gopher | 280B | 43.5 | - | 57.2 |
| Chinchilla | 70B | 55.4 | - | 64.6 |
| LLaMA | 7B | 50.0 | 53.4 | 56.3 | 57.6 |
| LLaMA | 13B | 56.6 | 60.5 | 63.1 | 64.0 |
| LLaMA | 33B | 65.1 | 67.9 | 69.9 | 70.4 |
| LLaMA | 65B | 68.2 | 71.6 | 72.6 | 73.0 |

Table 5: TriviaQA. Zero-shot and few-shot exact match performance on the filtered dev set.

## 3.3 Reading Comprehension

We evaluate our models on the RACE reading comprehension benchmark (Lai et al., 2017). This dataset was collected from English reading comprehension exams designed for middle and high school Chinese students. We follow the evaluation setup from Brown et al. (2020) and report results in Table 6. On these benchmarks, LLaMA-65B is competitive with PaLM-540B, and, LLaMA-13B outperforms GPT-3 by a few percents.

## 3.4 Mathematical reasoning

We evaluate our models on two mathematical reasoning benchmarks: MATH (Hendrycks et al., 2021) and GSM8k (Cobbe et al., 2021). MATH is a dataset of 12K middle school and high school mathematics problems written in LaTeX. GSM8k is a set of middle school mathematical problems. In Table 7, we compare with PaLM and Minerva (Lewkowycz et al., 2022). Minerva is a series of PaLM models finetuned on 38.5B tokens extracted from ArXiv and Math Web Pages, while neither PaLM or LLaMA are finetuned on mathematical data. The numbers for PaLM and Minerva are taken from Lewkowycz et al. (2022), and we compare with and without maj1@k. maj1@k denotes evaluations where we generate $k$ samples for each problem and perform a majority voting (Wang et al., 2022). On GSM8k, we observe that LLaMA-65B outperforms Minerva-62B, although it has not been fine-tuned on mathematical data.

## 3.5 Code generation

We evaluate the ability of our models to write code from a natural language description on two benchmarks: HumanEval (Chen et al., 2021) and MBPP (Austin et al., 2021). For both tasks, the model receives a description of the program in a few sentences, as well as a few input-output examples. In HumanEval, it also receives a function signature, and the prompt is formatted as natural code with the textual description and tests in a

Table 6: Reading Comprehension. Zero-shot accuracy.

| | RACE-middle | RACE-high |
|---|---|---|
| GPT-3 | 175B | 58.4 | 45.5 |
| PaLM | 8B | 57.9 | 42.3 |
| PaLM | 62B | 64.3 | 47.5 |
| PaLM | 540B | **68.1** | 49.1 |
| LLaMA | 7B | 61.1 | 46.9 |
| LLaMA | 13B | 61.6 | 47.2 |
| LLaMA | 33B | 64.1 | 48.3 |
| LLaMA | 65B | 67.9 | **51.6**