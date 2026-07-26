## D Supplemental Figures

### D.1 Early Stopping and Test vs Train

In section 5.3 we described the result shown in Figure 16, which provides a prediction for a lower bound on the early stopping step. We also show the train and test loss for a given model size when training on different sized datasets.

### D.2 Universal Transformers

We compare the performance of standard Transformers to recurrent Transformers [DGV+18] in Figure 17. These models re-use parameters, and so perform slightly better as a function of $N$, but slightly worse as a function of compute $C$. We include several different different possibilities for parameter re-use.

### D.3 Batch Size

We measure the critical batch size using the data displayed in figure 18. This made it possible to estimate $B_{\text{crit}}(L)$ in figure 10.

23