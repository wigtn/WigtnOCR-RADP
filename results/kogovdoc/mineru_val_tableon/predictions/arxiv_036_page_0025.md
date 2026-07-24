![](images/dee0e2940c932651760585a76b5bdfba4f78b74fb36d5fb543ffbe5056980dcc.jpg)  
Figure 2oThis figure provides information about the performance per token as a function of model size and training time.Left:Loss per token as a function of its position $T$ in the 1024-token context.Loss scales predictably as a power-law in $T$ Right:Test loss per token as a function of training step.

![](images/a63af3a6a033785becbcc42192d0d7fca993d1c77d4b7fe817d01bc9cf19c7bc.jpg)  
Figure 21In addition to the averaged los,individual tokens within the 1O24-token context also improve smoothly as model size increases.Training runs with shorter context $n _ { \mathrm { c t x } } = 8$ (dashed lines) perform better on early tokens,since they can allocate all of their capacity to them.

# D.5Context Dependence

Thetrends forlossasa function of model size are displayed for different tokens in the context in Figure 21. We see that models trained on $n _ { \mathrm { c t x } } = 1 0 2 4$ show steady improvement with model size on all but the first token.

Fixing model size,it appears that the loss scales as a power-law as a function of position $T$ in the context, see Figure 2O.This may be a consequence of underlying power-law correlations in language [EP94,ACDE12, LT16],or a more general feature of the model architecture and optimization.It provides some suggestion for the potential benefits (or lack thereof) from training on largercontexts.Notonly do larger models converge to better performance at $T = 1 0 2 4$ ,but they also improve more quickly at early tokens,suggesting that larger models are more efficient at detecting patterns with less contextual information.In the right-hand plot we show how per-token performance varies for a fixed modelas a function ofthe training step.The model begins by learning short-range information,and only learns longer-range correlations later in training.

We have also included models trained with a tiny context $n _ { \mathrm { c t x } } = 8$ in order to compare with our longer context models. Even modestly sized models trained on $n _ { \mathrm { c t x } } = 8$ can dominate our largest $n _ { \mathrm { c t x } } = 1 0 2 4$ models on very early tokens.This also suggests that further improvements should be possible with much larger models trained on large contexts.

# D.6Learning Rate Schedules and Error Analysis

Weexperimented with a variety of learning rates and schedules.A host of schedulesand resulting test performances for a smallanguage modelare plotted in Figure 22.We conclude that the choice of learning rate schedule is mostly irrelevant,as long as the total summed learningrate is sufficiently large,and the schedule includes a warmup period and a final decay to near-vanishing learning rate.Variations among