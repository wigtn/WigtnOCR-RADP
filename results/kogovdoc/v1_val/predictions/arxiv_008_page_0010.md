## B Solution of $-D_{KL}(q_\phi(\mathbf{z}) \| p_\theta(\mathbf{z}))$, Gaussian case

The variational lower bound (the objective to be maximized) contains a KL term that can often be integrated analytically. Here we give the solution when both the prior $p_\theta(\mathbf{z}) = \mathcal{N}(0, \mathbf{I})$ and the posterior approximation $q_\phi(\mathbf{z}|\mathbf{x}^{(i)})$ are Gaussian. Let $J$ be the dimensionality of $\mathbf{z}$. Let $\boldsymbol{\mu}$ and $\boldsymbol{\sigma}$ denote the variational mean and s.d. evaluated at datapoint $i$, and let $\mu_j$ and $\sigma_j$ simply denote the $j$-th element of these vectors. Then:

$$
\int q_\theta(\mathbf{z}) \log p(\mathbf{z}) \, d\mathbf{z} = \int \mathcal{N}(\mathbf{z}; \boldsymbol{\mu}, \boldsymbol{\sigma}^2) \log \mathcal{N}(\mathbf{z}; \mathbf{0}, \mathbf{I}) \, d\mathbf{z}
$$

$$
= -\frac{J}{2} \log(2\pi) - \frac{1}{2} \sum_{j=1}^J (\mu_j^2 + \sigma_j^2)
$$

10