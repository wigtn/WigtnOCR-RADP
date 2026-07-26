(non-embedding)
Smin (adjusted)
N= (1.3 · 109) ·C0.73
15000
N= (1.6 · 109) ·C0.88
Smin = (5.4 · 103) · C0.03
min
107
S (fixed-batch)
010000
Ster
105
Parameters (
5000
103
10-5
10-3
10-1
10-7
10-7
10-5
10-3
10-1
Compute (PF-days), non-embedding
Compute (PF-days), excluding embeddings
Figure 14 Left: Each value of the compute budget Cmin has an associated optimal model size N. Optimal
model size grows very rapidly with Cmin, increasing by 5x for each 10x increase in compute. The number
of data examples processed makes up the remainder of the increase, growing relatively modestly by only 2x.
Right: The batch-adjusted number of optimization steps also grows very slowly, if at all, meaning that most
of the growth in data examples processed can be used for increased batch sizes.
can be fit very well with a power-law
N(Cmin) α (Cmin)0.73.
(6.1)
In Figure 12, we show the effect of training models of sub-optimal sizes (see Appendix B.4).
By definition Cmin = 6NBcrit S, and so we can use N(Cmin) to extract further results. In particular, since
min
that the optimal number of steps will only grow very slowly with compute, as
Smin α (Cmin)0.03,
(6.2)
matching the empirical results in Figure 14. In fact the measured exponent is sufficiently small that our results
may even be consistent with an exponent of zero.
Thus we conclude that as we scale up language modeling with an optimal allocation of computation, we
should predominantly increase the model size N, while simultaneously scaling up the batch size via B α
Bcrit with negligible increase in the number of serial steps. Since compute-efficient training uses relatively
few optimization steps, additional work on speeding up early training dynamics may be waranted.
6.2 Predictions from L(N, Smin)
The results for L(Cmin) and the allocations can be predicted from the L(N, Smin) equation obtained in
Section 5. Given our equation for L(N, Smin), we can substitute Smin =
6NB
of the loss as a function of N, while fixing the training compute. We carry out this procedure in detail in
Appendix B, where we also provide some additional predictions.
For the loss as a function of training compute, we predict that
min
L(Cmin
(6.3)
Cmin
where
min
(6.4)
～ 0.054
1/αs+1/αB+1/αN
in excellent agreement with the exponent of Figure 13. We also predict that
N(Cmin) α (Cmin)am"/aN ~ (Cmin)0.71
(6.5)
which also matches the scaling of Figure 14 to within a few percent. Our scaling laws provide a predictive
framework for the performance of language modeling.
16