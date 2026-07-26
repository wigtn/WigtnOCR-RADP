AdapterH
Fine-Tune
BitFit
PreEmbed
PreLayer
LoRA
Hyperparameters
AdamW
Optimizer
128
Batch Size
# Epoch
250,000
Warmup Tokens
Linear
LR Schedule
Learning Rate
5.00E-06
5.00E-04
1.00E-04
2.00E-04
1.6E-03
1.00E-04
Table 12: The training hyperparameters used for different GPT-3 adaption methods. We use the
same hyperparameters for all datasets after tuning learning rate.
rally, we replace them after every Transformer block with an input agnostic vector. Thus, both the
embeddings and subsequent Transformer block activations are treated as trainable parameters. For
more on prefix-layer tuning, see Section 5.1.
In Table 15, we show the evaluation results of LoRA+PE and LoRA+PL on WikiSQL and MultiNLI.
First of all, LoRA+PE significantly outperforms both LoRA and prefix-embedding tuning on
WikiSQL, which indicates that LoRA is somewhat orthogonal to prefix-embedding tuning. On
MultiNLI, the combination of LoRA+PE doesn't perform better than LoRA, possibly because LoRA
on its own already achieves performance comparable to the human baseline. Secondly, we notice
that LoRA+PL performs slightly worse than LoRA even with more trainable parameters. We at-
tribute this to the fact that prefix-layer tuning is very sensitive to the choice of learning rate and thus
makes the optimization of LoRA weights more difficult in LoRA+PL.
ADDITIONAL EMPIRICAL EXPERIMENTS
F.1
ADDITIONAL EXPERIMENTS ON GPT-2
We also repeat our experiment on DART (Nan et al., 2020) and WebNLG (Gardent et al., 2017)
following the setup of Li & Liang (2021). The result is shown in Table 13. Similar to our result
on E2E NLG Challenge, reported in Section 5, LoRA performs better than or at least on-par with
prefix-based approaches given the same number of trainable parameters.
Method
DART
# Trainable
TER↓
MET个
Parameters
BLEU个
GPT-2 Medium
0.39
0.46
354M
46.2
Fine-Tune
Adapter
42.4
0.36
0.48
0.37M
45.2
0.46
Adapter
11M
0.38
0.56
FTTop2
24M
41.0
0.34
0.46
46.4
PrefLayer
0.35M
0.38
47.1±.2
0.46
0.35M
0.39
LoRA
GPT-2 Large
0.46
0.39
774M
47.0
Fine-Tune
45.7±.1
0.38
AdapterL
0.88M
0.46
47.1±.1
0.39
0.45
Adapterl
23M
46.7
PrefLayer
0.38
0.45
0.77M
47.5±.1
0.39
0.45
LoRA
0.77M
Table 13: GPT-2 with different adaptation methods on DART. The variances of MET and TER are
less than 0.01 for all adaption approaches.
21