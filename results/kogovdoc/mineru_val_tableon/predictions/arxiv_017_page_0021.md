Table 12:The training hyperparameters used for different GPT-3 adaption methods.We use the same hyperparameters forall datasets after tuning learning rate.   

     Hyperparameters  Fine-Tune  PreEmbed  PreLayer  BitFit  AdapterH  LoRA    Optimizer  AdamW    Batch Size  128    #Epoch  2    Warmup Tokens  250,000    LR Schedule  Linear    Learning Rate  5.00E-06  5.00E-04  1.00E-04  1.6E-03  1.00E-04  2.00E-04     

rally,we replace them after every Transformer block with an input agnostic vector.Thus,both the embeddings and subsequent Transformer block activations are treated as trainable parameters.For more on prefix-layer tuning,see Section 5.1.

In Table15,we show the evaluationresultsofLoRA $+ \mathrm { P E }$ andLoRA $+ \mathrm { P L }$ on WikiSQL and MultiNLI. First ofall, $\mathrm { L o R A + P E }$ significantly outperforms both LoRA and prefix-embedding tuning on WikiSQL,which indicates that LoRA is somewhat orthogonal to prefix-embedding tuning.On MultiNLI, the combination ofLoRA $+ \mathrm { P E }$ doesn't perform better thanLoRA,possibly because LoRA on its own already achieves performance comparable to the human baseline.Secondly,we notice thatLoRA $^ { \mathrm { + P L } }$ performs slightly worse than LoRA even with more trainable parameters.We attribute this to the fact that prefix-layer tuning is very sensitive to the choice of learning rateand thus makes the optimizationofLoRAweightsmore difficultinLoRA $+ \mathrm { P L }$

# F ADDITIONALEMPIRICALEXPERIMENTS

# F.1 ADDITIONAL EXPERIMENTS ONGPT-2

We also repeat our experiment on DART(Nan et al.,2O2O)and WebNLG(Gardent et al.,2017) following the setup of Li&Liang (2O21).The result is shown in Table13.Similar to our result on E2E NLG Challenge,reported in Section 5,LoRA performs better than or at least on-par with prefix-based approaches given the same number of trainable parameters.

     Method  # Trainable Parameters  BLEU↑  DART MET↑  TER↓    GPT-2 Medium    Fine-Tune  354M  46.2  0.39  0.46    Adapter  0.37M  42.4  0.36  0.48    AdapterL  11M  45.2  0.38  0.46    FTTop2  24M  41.0  0.34  0.56    PrefLayer  0.35M  46.4  0.38  0.46    LoRA  0.35M  47.1±.2  0.39  0.46    GPT-2 Large    Fine-Tune  774M  47.0  0.39  0.46    AdapterL  0.88M  45.7±.1  0.38  0.46    AdapterL  23M  47.1±.1  0.39  0.45    PrefLayer  0.77M  46.7  0.38  0.45    LoRA  0.77M  47.5±.1  0.39  0.45     

Table 13:GPT-2 with different adaptation methods on DART.The variances of METand TER are less than O.O1 for all adaption approaches.