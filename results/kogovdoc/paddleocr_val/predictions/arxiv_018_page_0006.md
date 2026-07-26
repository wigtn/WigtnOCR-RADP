10T
3.2
3.0
100B
638
6e18
Parameters
100B
Tokens
le19
10B
3e19
2.6
6e19
10B
1e20
1B
2.4
3e20
6e20
1B
2.2
le21
100M
3e21
2.0
1021
1019
1021
1023
1025
30B
1017
1023
1019
100M300M
1B
3B 6B
Parameters
FLOPs
FLOPs
Figure 3 I IsoFLOP curves. For various model sizes, we choose the number of training tokens such
that the final FLOPs is a constant. The cosine cycle length is set to match the target FLOP count. We
find a clear valley in loss, meaning that for a given FLOP budget there is an optimal model to train
(left). Using the location of these valleys, we project optimal model size and number of tokens for
larger models (center and right). In green, we show the estimated number of parameters and tokens
for an optimal model trained with the compute budget of Gopher.
For each FLOP budget, we plot the final loss (after smoothing) against the parameter count in
Figure 3 (left). In all cases, we ensure that we have trained a diverse enough set of model sizes to see
a clear minimum in the loss. We fit a parabola to each IsoFLOPs curve to directly estimate at what
model size the minimum loss is achieved (Figure 3 (left)). As with the previous approach, we then fit
a power law between FLOPs and loss-optimal model size and number of training tokens, shown in
Figure 3 (center, right). Again, we fit exponents of the form Nopt α Ca and Dopt cα Cb and we find that
a = 0.49 and b = 0.51as summarized in Table 2.
3.3. Approach 3: Fitting a parametric loss function
Lastly, we model all final losses from experiments in Approach 1 & 2 as a parametric function of
model parameter count and the number of seen tokens. Following a classical risk decomposition (see
Section D.2), we propose the following functional form
L(N, D) = E +
(2)
Nα
DB
The first term captures the loss for an ideal generative process on the data distribution, and should
correspond to the entropy of natural text. The second term captures the fact that a perfectly trained
transformer with N parameters underperforms the ideal generative process. The final term captures
the fact that the transformer is not trained to convergence, as we only make a finite number of
optimisation steps, on a sample of the dataset distribution.
Model fitting. To estimate (A, B, E, α, β), we minimize the Huber loss (Huber, 1964) between the
predicted and observed log loss using the L-BFGS algorithm (Nocedal, 198O):
Hubers( log L(Ni, Di) - log Li
(3)
min
A,B,E,α,β
Runs i
We account for possible local minima by selecting the best fit from a grid of initialisations. The Huber
loss (8 = 1o-3) is robust to outliers, which we find important for good predictive performance over
held-out data points. Section D.2 details the fitting procedure and the loss decomposition.