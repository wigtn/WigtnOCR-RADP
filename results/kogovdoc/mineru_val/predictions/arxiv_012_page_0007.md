# 6 RESULTS

# 6.1 SEMI-SUPERVISED NODE CLASSIFICATION

Results are summarized in Table 2. Reported numbers denote classification accuracy in percent. For ICA, we report the mean accuracy of 100 runs with random node orderings. Results for all other baseline methods are taken from the Planetoid paper (Yang et al., 2016). Planetoid\* denotes the best model for the respective dataset out of the variants presented in their paper.

Table 2: Summary of results in terms of classification accuracy (in percent).   
![](images/3d97892628a40146a19cd28ebabeeccecf31b4ef1b59364459b00ca708904361.jpg)

We further report wall-clock training time in seconds until convergence (in brackets) for our method (incl. evaluation of validation error) and for Planetoid. For the latter, we used an implementation provided by the authors3 and trained on the same hardware (with GPU) as our GCN model. We trained and tested our model on the same dataset splits as in Yang et al. (2016) and report mean accuracy of 100 runs with random weight initializations. We used the following sets of hyperparameters for Citeseer, Cora and Pubmed: 0.5 (dropout rate), 5 10−4 (L2 regularization) and 16 (number of hidden units); and for NELL: 0.1 (dropout rate), 1 · 10−5 (L2 regularization) and 64 (number of hidden units).

In addition, we report performance of our model on 10 randomly drawn dataset splits of the same size as in Yang et al. (2016), denoted by GCN (rand. splits). Here, we report mean and standard error of prediction accuracy on the test set split in percent.

# 6.2 EVALUATION OF PROPAGATION MODEL

We compare different variants of our proposed per-layer propagation model on the citation network datasets. We follow the experimental set-up described in the previous section. Results are summarized in Table 3. The propagation model of our original GCN model is denoted by renormalization trick (in bold). In all other cases, the propagation model of both neural network layers is replaced with the model specified under propagation model. Reported numbers denote mean classification accuracy for 100 repeated runs with random weight matrix initializations. In case of multiple variables Θi per layer, we impose L2 regularization on all weight matrices of the first layer.

Table 3: Comparison of propagation models.   
![](images/ae084aaeb9803a0961a6f7f16214926eaa29f132448b23f04e6ca8a8a13f9413.jpg)