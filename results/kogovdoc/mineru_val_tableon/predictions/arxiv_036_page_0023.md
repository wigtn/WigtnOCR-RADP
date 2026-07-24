![](images/b12ca2ff033c42c30dc52af26d10ed2139d7048a7db3e0a02ec8d987f51e908c.jpg)  
Figure 16Left:We characterize the step on which early stopping occurs,as a function of the extent of overfitting.Thered line indicates alower bound for earlystopping that is derived in Section 5.3.Right: We display train and test loss for a series of 3ooM parameter models trained on diferent sized dataset subsamples.The testloss typically follows thatofarundone with unrestricted datauntil diverging.Note that the degree of overfiting (as compared to the infinite data limit) is significantly overestimated by $L _ { \mathrm { t e s t } } - L _ { \mathrm { t r a i n } }$ （204号 (denoted bya black bar for each run).

·We are not especially confident in the prediction of $B _ { \mathrm { c r i t } } ( L )$ for values of the loss far outside the range we have explored.Changes in $B _ { \mathrm { c r i t } }$ could have a significant impact on trade-offs between data parallelism and the number of serial training steps required,which would have a major impact on training time.   
·We did not thoroughly investigate the small data regime,and our fits for $L ( N , D )$ were poor for the smallest values of $D$ (where an epoch corresponded to only 4O steps).Furthermore,we did not experiment with regularization and data augmentation.Improvements in these could alter our results,quantitatively or qualitatively.   
·Weused the estimated training compute $C \approx 6 N B S$ ,which did not include contributions proportional to $n _ { \mathrm { c t x } }$ (see Section 2.1).So our scalings with compute may be confounded in practice in the regime of very large $n _ { \mathrm { c t x } }$ ,specifically where $n _ { \mathrm { c t x } } \gtrsim 1 2 d _ { \mathrm { m o d e l } }$ ：   
·We tuned learning rates,and we experimented with learning rate schedules.But we may have neglected to tune some hyperparameter(e.g.intialization scale or momentum) that have an important effect on scaling.   
·The optimal choice of learning rate is sensitive to the target loss.When training close to convergence, it may be necessary to use a smaller learning rate to avoid divergences.But when conducting a short training run (eg due to compute limitations),it may be possible to use a larger learning rate.We did not experiment with higher learning rates for training runs that did not proceed to convergence.

# DSupplemental Figures

# D.1Early Stopping and Test vs Train

In section 5.3 we described the result shown in Figure16,which provides a prediction foralower bound on the early stopping step.We also show the train and test lossfora given model size when training on different sized datasets.

# D.2Universal Transformers

We compare the performance of standard Transformers to recurrent Transformers $\mathrm { [ D G V ^ { + } 1 8 ] }$ in Figure 17. These models re-use parameters,and so perform slightly better as a function of $N$ ,but slightly worse as a function of compute $C$ .We include several different different possibilities for parameter re-use.

# D.3 Batch Size

We measure the critical batch size using the data displayed in figure 18.This made it possible to estimate $B _ { \mathrm { c r i t } } ( L )$ in figure 10.