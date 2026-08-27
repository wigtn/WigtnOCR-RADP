Parameters (non-embedding) N = (1.3 109) C0m.i7n3 🌳• • Smin (adjusted) •   
N = (1.6 109) C0.88 m🎶 15000 Smin = (5.4 103) C0m.i0n3 -   
107 - S (fixed-batch) d - 10000   
105 • 🌳   
- 5000   
103 - 0   
10 7 10 5 10 3 10 1 10 7 10 5 10 3 10 1   
Compute (PF-days), non-embedding Compute (PF-days), excluding embeddings

can be fit very well with a power-law

In Figure 12, we show the effect of training models of sub-optimal sizes (see Appendix B.4).

By definition Cmin ≡ 6N BcritS, and so we can use N (Cmin) to extract further results. In particular, since prior fits show B ∝ L−4.8 and L ∝ Cm−i0n.05, we can conclude that Bcrit ∝ C0m.i2n4. This leads us to conclude matching the empirical results in Figure 14. In fact the measured exponent is sufficiently small that our results may even be consistent with an exponent of zero.

Thus we conclude that as we scale up language modeling with an optimal allocation of computation, we should predominantly increase the model size N, while simultaneously scaling up the batch size via B ∝ Bcrit with negligible increase in the number of serial steps. Since compute-efficient training uses relatively few optimization steps, additional work on speeding up early training dynamics may be warranted.

# 6.2 Predictions from L(N, Smin)

The results for L(Cmin) and the allocations can be predicted from the L(N, Smin) equation obtained in Section 5. Given our equation for L(N, Smin), we can substitute Smin = 6CNmiBn and then find the minimum of the loss as a function of N , while fixing the training compute. We carry out this procedure in detail in Appendix B, where we also provide some additional predictions.

For the loss as a function of training compute, we predict that

where

in excellent agreement with the exponent of Figure 13. We also predict that which also matches the scaling of Figure 14 to within a few percent. Our scaling laws provide a predictive framework for the performance of language modeling.