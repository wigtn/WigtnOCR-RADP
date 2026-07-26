## 6 RESULTS

### 6.1 SEMI-SUPERVISED NODE CLASSIFICATION

Results are summarized in Table 2. Reported numbers denote classification accuracy in percent. For ICA, we report the mean accuracy of 100 runs with random node orderings. Results for all other baseline methods are taken from the Planetoid paper (Yang et al., 2016). Planetoid* denotes the best model for the respective dataset out of the variants presented in their paper.

Table 2: Summary of results in terms of classification accuracy (in percent).

| Method | Citeseer | Cora | Pubmed | NELL |
|--------|----------|------|--------|------|
| ManiReg [3] | 60.1 | 59.5 | 70.7 | 21.8 |
| SemiEmb [28] | 59.6 | 59.0 | 71.1 | 26.7 |
| LP [32] | 45.3 | 68.0 | 63.0 | 26.5 |
| DeepWalk [22] | 43.2 | 67.2 | 65.3 | 58.1 |
| ICA [18] | 69.1 | 75.1 | 73.9 | 23.1 |
| Planetoid* [29] | 64.7 (26s) | 75.7 (13s) | 77.2 (25s) | 61.9 (185s) |
| GCN (this paper) | **70.3 (7s)** | **81.5 (4s)** | **79.0 (38s)** | **66.0 (48s)** |
| GCN (rand. splits) | 67.9 ± 0.5 | 80.1 ± 0.5 | 78.9 ± 0.7 | 58.4 ± 1.7 |

We further report wall-clock training time in seconds until convergence (in brackets) for our method (incl. evaluation of validation error) and for Planetoid. For the latter, we used an implementation provided by the authors³ and trained on the same hardware (with GPU) as our GCN model. We trained and tested our model on the same dataset splits as in Yang et al. (2016) and report mean accuracy of 100 runs with random weight initializations. We used the following sets of hyperparameters for Citeseer, Cora and Pubmed: 0.5 (dropout rate), 5 · 10⁻⁴ (L2 regularization) and 16 (number of hidden units); and for NELL: 0.1 (dropout rate), 1 · 10⁻⁵ (L2 regularization) and 64 (number of hidden units).

In addition, we report performance of our model on 10 randomly drawn dataset splits of the same size as in Yang et al. (2016), denoted by GCN (rand. splits). Here, we report mean and standard error of prediction accuracy on the test set split in percent.

### 6.2 EVALUATION OF PROPAGATION MODEL

We compare different variants of our proposed per-layer propagation model on the citation network datasets. We follow the experimental set-up described in the previous section. Results are summarized in Table 3. The propagation model of our original GCN model is denoted by renormalization trick (in bold). In all other cases, the propagation model of both neural network layers is replaced with the model specified under propagation model. Reported numbers denote mean classification accuracy for 100 repeated runs with random weight matrix initializations. In case of multiple variables Θᵢ per layer, we impose L2 regularization on all weight matrices of the first layer.

Table 3: Comparison of propagation models.

| Description | Propagation model | Citeseer | Cora | Pubmed |
|-------------|-------------------|----------|------|--------|
| Chebyshev filter (Eq. 5) | $K=3$<br>$K=2$<br>$\sum_{k=0}^K T_k(\tilde{L}) X \Theta_k$ | 69.8 | 79.5 | 74.4 |
| 1st-order model (Eq. 6) | $X \Theta_0 + D^{-\frac{1}{2}} AD^{-\frac{1}{2}} X \Theta_1$ | 68.3 | 80.0 | 77.5 |
| Single parameter (Eq. 7) | $(I_N + D^{-\frac{1}{2}} AD^{-\frac{1}{2}}) X \Theta$ | 69.3 | 79.2 | 77.4 |
| Renormalization trick (Eq. 8) | $\tilde{D}^{-\frac{1}{2}} \tilde{A} \tilde{D}^{-\frac{1}{2}} X \Theta$ | **70.3** | **81.5** | **79.0** |
| 1st-order term only | $D^{-\frac{1}{2}} AD^{-\frac{1}{2}} X \Theta$ | 68.7 | 80.5 | 77.8 |
| Multi-layer perceptron | $X \Theta$ | 46.5 | 55.1 | 71.4 |

³https://github.com/kimiyoung/planetoid

7