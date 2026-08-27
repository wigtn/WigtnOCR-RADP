3.2 1T 10T 1.4T 3.0 1T 2.68 - 100B 63B 613e189 10B 100B ● • ● : 6e19 13e20 : Q ❤ 。 ● 6e20 - 1B 2.2 ● 1e21 100M ● 3e21 2.0 100M 300M 1B 3B 6B 30B 1017 1019 1021 1023 1025 100M1017 1019 1021 1023 1025 Parameters FLOPs FLOPs

For each FLOP budget, we plot the final loss (after smoothing) against the parameter count in Figure 3 (left). In all cases, we ensure that we have trained a diverse enough set of model sizes to see a clear minimum in the loss. We fit a parabola to each IsoFLOPs curve to directly estimate at what model size the minimum loss is achieved (Figure 3 (left)). As with the previous approach, we then fit a power law between FLOPs and loss-optimal model size and number of training tokens, shown in Figure 3 (center, right). Again, we fit exponents of the form 𝑁𝑜𝑝𝑡 ∝ 𝐶𝑎 and 𝐷𝑜𝑝𝑡 ∝ 𝐶𝑏 and we find that 𝑎 = 0.49 and 𝑏 = 0.51—as summarized in Table 2.

# 3.3. Approach 3: Fitting a parametric loss function

Lastly, we model all final losses from experiments in Approach 1 & 2 as a parametric function of model parameter count and the number of seen tokens. Following a classical risk decomposition (see Section D.2), we propose the following functional form

The first term captures the loss for an ideal generative process on the data distribution, and should correspond to the entropy of natural text. The second term captures the fact that a perfectly trained transformer with 𝑁 parameters underperforms the ideal generative process. The final term captures the fact that the transformer is not trained to convergence, as we only make a finite number of optimisation steps, on a sample of the dataset distribution.

Model fitting. To estimate 𝐴, 𝐵, 𝐸, 𝛼, 𝛽 , we minimize the Huber loss (Huber, 1964) between the predicted and observed log loss using the L-BFGS algorithm (Nocedal, 1980):

We account for possible local minima by selecting the best fit from a grid of initialisations. The Huber loss (𝛿 = 10−3) is robust to outliers, which we find important for good predictive performance over held-out data points. Section D.2 details the fitting procedure and the loss decomposition.