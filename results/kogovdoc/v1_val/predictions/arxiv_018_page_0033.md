## Datasets

- Language modelling on LAMBADA, Wikitext103 (Merity et al., 2017), C4 (Raffel et al., 2020a), PG-19 (Rae et al., 2020) and the Pile (Gao et al., 2020).
- Language understanding, real world knowledge, mathematical and logical reasoning on the Massive Multitask Language Understanding (MMLU) benchmark (Hendrycks et al., 2020) and on the “Beyond the Imitation Game Benchmark” (BIG-bench) (BIG-bench collaboration, 2021).
- Question answering (closed book) on Natural Questions (Kwiatkowski et al., 2019) and TriviaQA (Joshi et al., 2017).
- Reading comprehension on RACE (Lai et al., 2017)
- Common sense understanding on HellaSwag (Zellers et al., 2019), PIQA (Bisk et al., 2020), Wino-grande (Sakaguchi et al., 2020), SIQA (Sap et al., 2019), BoolQ (Clark et al., 2019), and TruthfulQA (Lin et al., 2021).

| Motivation | We chose evaluations from Rae et al. (2021) to allow us to most directly compare to Gopher. |
| Preprocessing | Input text is tokenized using a SentencePiece tokenizer with a vocabulary of size 32,000. Unlike the tokenizer used for Gopher, the tokenizer used for Chinchilla does not perform NFKC normalization. |

## Training Data

The same dataset is used as in Rae et al. (2021). Differences in sampling are shown in Table A1.

## Quantitative Analyses

### Unitary Results

Section 4.2 gives a detailed description of our analysis. Main take-aways include:

- Our model is capable of outputting toxic language as measured by the PerspectiveAPI. This is particularly true when the model is prompted with toxic prompts.
- Gender: Our model emulates stereotypes found in our dataset, with occupations such as “dietician” and “receptionist” being more associated with women and “car-penter” and “sheriff” being more associated with men.
- Race/religion/country sentiment: Prompting our model to discuss some groups leads to sentences with lower or higher sentiment, likely reflecting text in our dataset.

33