Per-token Loss (774M Params)
103
10 
3.4 + 4.0 - T0.56
Loss
Model Parameters
2.9 + 4.5 · T
0.56
Token Index
108
102
Test Loss
0.60
Per-Token Test ]
0.62
2.3 + 5.4
107
101
106
100
101
103
105
102
100
101
103
Step
Token Index
Figure 20 This figure provides information about the performance per token as a function of model size
and training time. Left: Loss per token as a function of its position T in the 1024-token context. Loss scales
7.5
Token 1/1024
Token 2/1024
Token 4/1024
6.0
Token 8/1024
Test Loss
Token16/1024
Token 64/1024
4.5
Token 256/1024
Token 1024/1024
Token 1/8
Token 2/8
3.0
Token 4/8
Token 8/8
106
107
108
104
109
105
Parameters (excl. embedding)
Figure 21  In addition to the averaged loss, individual tokens within the 1024-token context also improve
smoothly as model size increases. Training runs with shorter context nctx = 8 (dashed lines) perform better
on early tokens, since they can allocate all of their capacity to them.
D.5Context Dependence
The trends for loss as a function of model size are displayed for different tokens in the context in Figure 21.
We see that models trained on nctx = 1024 show steady improvement with model size on all but the first
token.
Fixing model size, it appears that the loss scales as a power-law as a function of position T in the context, see
Figure 20. This may be a consequence of underlying power-law correlations in language [EP94, ACDE12,
the potential benefits (or lack thereof) from training on larger contexts. Not only do larger models converge
to better performance at T = 1024, but they also improve more quickly at early tokens, suggesting that larger
models are more efficient at detecting patterns with less contextual information. In the right-hand plot we
show how per-token performance varies for a fixed model as a function of the training step. The model begins
by learning short-range information, and only learns longer-range correlations later in training.
We have also included models trained with a tiny context nctx = 8 in order to compare with our longer
models on very early tokens. This also suggests that further improvements should be possible with much
larger models trained on large contexts.
D.6Learning Rate Schedules and Error Analysis
We experimented with a variety of learning rates and schedules. A host of schedules and resulting test
performances for a small language model are plotted in Figure 22. We conclude that the choice of learning
rate schedule is mostly irrelevant, as long as the total summed learning rate is sufficiently large, and the
schedule includes a warmup period and a final decay to near-vanishing learning rate. Variations among
25