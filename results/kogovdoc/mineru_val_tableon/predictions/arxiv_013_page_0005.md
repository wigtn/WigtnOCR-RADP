HellaSwag (Zellers etal.,2019),WinoGrande (Sakaguchi etal.,2O21),ARC easyandchallenge(Clark et al.,2018) and OpenBookQA (Mihaylov et al., 2018).These datasets include Cloze and Winograd style tasks,as well as multiple choice question answering.We evaluate in the zero-shot setting as done in the language modeling community.

In Table 3,we compare with existing models of various sizes and report numbers from the corresponding papers．First,LLaMA-65B outperforms Chinchilla-7OB onall reported benchmarks butBoolQ.Similarly, this model surpasses PaLM540B everywhere but on BoolQ and WinoGrande. LLaMA-13B model also outperforms GPT-3 on most benchmarks despite being $1 0 \times$ smaller.

# 3.2Closed-book Question Answering

We compare LLaMA to existing large language models on two closed-book question answering benchmarks:Natural Questions(Kwiatkowski et al.,2019) and TriviaQA(Joshi etal.,2017).For both benchmarks,we report exact match performance in a closed book setting,i.e.,where the models do not have access to documents that contain evidence to answer the question.In Table 4,we report performance onNaturalQuestions,and in Table 5,we report on TriviaQA.On both benchmarks, LLaMA-65B achieve state-of-the-arts performance in the zero-shot and few-shot settings.More importantly, the LLaMA-13B is also competitive on these benchmarks with GPT-3 and Chinchilla, despitebeing $5 \mathrm { - } 1 0 \times$ smaller. This model runs on a single V1OO GPU during inference.

Table 5: TriviaQA.Zero-shot and few-shot exact match performance on the filtered dev set.   

       0-shot  1-shot  5-shot  64-shot    Gopher 280B Chinchilla 70B  43.5 55.4  -  57.0  57.2    7B  50.0  53.4  64.1 56.3  64.6 57.6    13B LLaMA  56.6  60.5  63.1  64.0    33B    67.9  69.9        65.1      70.4    65B  68.2  71.6  72.6  73.0     

# 3.3Reading Comprehension

We evaluate our models on the RACE reading comprehension benchmark (Lai et al.,2O17).This dataset was collected from English reading comprehension exams designed for middle and high school Chinese students.We follow the evaluation setup fromBrown etal.(2O2O) and report results inTable6.Onthesebenchmarks,LLaMA-65Bis competitive withPaLM-540B,and,LLaMA-13B outperforms GPT-3 by a few percents.

Table 6: Reading Comprehension. Zero-shot accuracy.   

         RACE-middle  RACE-high    GPT-3  175B  58.4  45.5    PaLM  8B  57.9  42.3    62B  64.3  47.5    540B  68.1  49.1    LLaMA  7B  61.1  46.9    13B  61.6  47.2    33B  64.1  48.3    65B  67.9  51.6     

# 3.4Mathematical reasoning

We evaluate our models on two mathematical reasoning benchmarks: MATH (Hendrycks et al., 2021)and GSM8k(Cobbe etal.,2021).MATH isa dataset of12K middle school and high school mathematicsproblems written inLaTeX.GSM8k is a set of middle school mathematical problems. In Table 7,we compare with PaLM and Minerva (Lewkowycz etal.,2022).Minerva is a series of PaLM models finetuned on 38.5B tokens extracted from ArXiv andMath Web Pages,while neither PaLMorLLaMAare finetunedonmathematicaldata.ThenumbersforPaLMandMinerva are taken fromLewkowycz et al. (2022),and we compare with and without maj1@k.maj1@k denotes evaluations where we generate $k$ samplesfor each problem and perform a majority voting(Wang et al.,2022). On GSM8k,we observe thatLLaMA65B outperforms Minerva-62B,although it has not been fine-tuned on mathematical data.

# 3.5Code generation

We evaluate the ability of our models to write code from a natural language description on two benchmarks:HumanEval (Chen etal.,2021) and MBPP (Austin et al.,2O21).For both tasks, the model receives a description of the program in a few sentences,as well as a few input-output examples.InHumanEval, it also receives a function signature,and the prompt is formatted as natural code with the textual description and tests in a