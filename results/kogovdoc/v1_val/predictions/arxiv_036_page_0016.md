## 6.2 Predictions from $L(N, S_{\text{min}})$

The results for $L(C_{\text{min}})$ and the allocations can be predicted from the $L(N, S_{\text{min}})$ equation obtained in Section 5. Given our equation for $L(N, S_{\text{min}})$, we can substitute $S_{\text{min}} = \frac{C_{\text{min}}}{6NB}$ and then find the minimum of the loss as a function of $N$, while fixing the training compute. We carry out this procedure in detail in Appendix B, where we also provide some additional predictions.

For the loss as a function of training compute, we predict that

$$
L(C_{\text{min}}) = \left( \frac{C_{\text{min}}}{C_c} \right)^{\alpha_C^{\text{min}}} \tag{6.3}
$$

where

$$
\alpha_C^{\text{min}} \equiv \frac{1}{1/\alpha_S + 1/\alpha_B + 1/\alpha_N} \approx 0.054 \tag{6.4}
$$

in excellent agreement with the exponent of Figure 13. We also predict that

$$
N(C_{\text{min}}) \propto (C_{\text{min}})^{\alpha_C^{\text{min}} / \alpha_N} \approx (C_{\text{min}})^{0.71} \tag{6.5}
$$

which also matches the scaling of Figure 14 to within a few percent. Our scaling laws provide a predictive framework for the performance of language modeling.

16