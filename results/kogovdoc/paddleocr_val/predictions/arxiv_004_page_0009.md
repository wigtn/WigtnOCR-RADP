Total Compute Used During Training
10000
1000
Training Petaflop/s-days
100
10
13B
-11B
T5-
175B
T5-Base
T5-Small
T5-Large
GPT-3 X
GPT-3 1
GPT-3 6.7B
GPT-3 2.7B
BERT-Large
GPT-3 Small
GPT-3 Large
GPT-3 1
GPT-3 Medium
RoBERTa-Base
RoBERTa-Large
Figure 2.2: Total compute used during training. Based on the analysis in Scaling Laws For Neural Language Models
[KMH+ 2O] we train much larger models on many fewer tokens than is typical. As a consequence, although GPT-3 3B
is almost 10x larger than RoBERTa-Large (355M params), both models took roughly 50 petaflop/s-days of compute
during pre-training. Methodology for these calculations can be found in Appendix D.
Quantity
Weight in
Epochs elapsed when
(tokens)
Dataset
training for 300B tokens
training mix
60%
0.44
410 billion
Common Crawl (filtered)
19 billion
2.9
22%
WebText2
1.9
8%
Books1
12 billion
55 billion
8%
0.43
Books2
3 billion
3%
Wikipedia
3.4
Table 2.2: Datasets used to train GPT-3. "Weight in training mix' refers to the fraction of examples during training
that are drawn from a given dataset, which we intentionally do not make proportional to the size of the dataset. As a
result, when we train for 300 billion tokens, some datasets are seen up to 3.4 times during training while other datasets
are seen less than once.
A major methodological concern with language models pretrained on a broad swath of internet data, particularly large
models with the capacity to memorize vast amounts of content, is potential contamination of downstream tasks by
having their test or development sets inadvertently seen during pre-training. To reduce such contamination, we searched
for and attempted to remove any overlaps with the development and test sets of all benchmarks studied in this paper.
Unfortunately, a bug in the filtering caused us to ignore some overlaps, and due to the cost of training it was not feasible
to retrain the model. In Section 4 we characterize the impact of the remaining overlaps, and in future work we will
more aggressively remove data contamination.
2.3
Training Process
rate. We measure the gradient noise scale during training and use it to guide our choice of batch size [MKAT18]. Table
2.1 shows the parameter settings we used. To train the larger models without running out of memory, we use a mixture
of model parallelism within each matrix multiply and model parallelism across the layers of the network. All models
and hyperparameter settings are described in Appendix B.