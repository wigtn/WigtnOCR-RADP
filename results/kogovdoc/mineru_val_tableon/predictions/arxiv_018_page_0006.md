![](images/56ef7c98c200b9ef5a5889eeffdf2b4d9178484193cec869af1cd6cc1b18d67d.jpg)  
Figure 3|IsoFLOP curves.For various model sizes,we choose the number of training tokens such that the final FLOPs is a constant.The cosine cycle length is set to match the target FLOP count.We find a clear valley in loss,meaning that for a given FLOP budget there is an optimal model to train (left). Using the location of these valleys,we project optimal model size and number of tokens for larger models (center and right).In green,we show the estimated number of parameters and tokens for an optimal model trained with the compute budget of Gopher.

For each FLOP budget,we plot the final loss (after smoothing) against the parameter count in Figure 3(left).In allcases,we ensure that we have trained a diverse enough set of model sizes to see a clear minimum in the loss.We fit a parabola to each IsoFLOPs curve to directly estimate at what model size the minimum loss is achieved (Figure 3 (left)).As with the previous approach,we then fit a power law between FLOPs and loss-optimal model size and number of training tokens,shown in Figure 3 (center, right). Again, we fit exponents of the form $N _ { o p t } \propto C ^ { a }$ and $D _ { o p t } \propto C ^ { b }$ and we find that $a = 0 . 4 9$ and $b = 0 . 5 1$ —assummarizedin Table 2.

# 3.3.Approach 3:Fittinga parametric loss function

Lastly,we model all final losses from experiments in Approach $1 \& 2$ asa parametric function of model parameter count and the number of seen tokens.Following a classcal risk decomposition (see SectionD.2),we propose the following functional form

$$
\hat { L } ( N , D ) \triangleq E + \frac { A } { N ^ { \alpha } } + \frac { B } { D ^ { \beta } } .
$$

The first term captures the loss for an ideal generative process on the data distribution,and should correspond to the entropy of natural text.The second term captures the fact that a perfectly trained transformer with $N$ parameters underperforms the ideal generative process.The final term captures the fact that the transformer is not trained to convergence,as we only make a finite number of optimisation steps,on a sample of the dataset distribution.

Model fitting. To estimate $( A , B , E , \alpha , \beta )$ ,we minimize the Huber loss (Huber,l964) between the predicted and observed log loss using the L-BFGS algorithm (Nocedal,1980):

$$
\operatorname* { m i n } _ { A , B , E , \alpha , \beta } \quad \sum _ { \mathrm { R u n s } i } { \mathrm { H u b e r } } _ { \delta } { \Big ( } \log { \hat { L } } ( N _ { i } , D _ { i } ) - \log L _ { i } { \Big ) }
$$

We account for possible local minima by selecting the best fit from a grid of initialisations.The Huber loss $( \delta = 1 0 ^ { - 3 }$ ) is robust to outliers,which we find important for good predictive performance over held-out data points.Section D.2 details the fiting procedure and the loss decomposition.