![](images/723ee9ca2b78b7957a055ac41fd78e5f6600fa78ccddd0cf973c90f48469c250.jpg)  
Figure 4:Visualisations of learned data manifold for generative models with two-dimensional latent space,learned with AEVB.Since the prior of the latent space is Gaussan,linearly spaced coordinates on the unit square were transformed through the inverse CDF of the Gaussian to produce values of the latent variables $\mathbf { z }$ For each of these values $\mathbf { z }$ ,we plotted the corresponding generative （20 $p _ { \pmb { \theta } } ( \mathbf { x } | \mathbf { z } )$ with the learned parameters $\pmb \theta$

![](images/14fa2bb8e4277239a7c31eefd2f597e84bb3869132bf620fb96f347c0d19b265.jpg)  
Figure 5:Random samples from learned generative models of MNIST for diferent dimensionalities of latent space.

# BSolution of $- D _ { K L } ( q _ { \phi } ( { \bf z } ) | | p _ { \theta } ( { \bf z } ) )$ , Gaussian case

The variational lower bound (the objective to be maximized) contains a KL term that can often be integrated analytically. Here we give the solution when both the prior $p _ { \theta } ( \mathbf { z } ) = \mathcal { N } ( 0 , \mathbf { I } )$ and the posterior approximation $q _ { \phi } ( \mathbf { z } | \mathbf { x } ^ { ( i ) } )$ are Gaussian. Let $J$ be the dimensionality of $\mathbf { z }$ .Let $\pmb { \mu }$ and $\sigma$ denote the variational mean and s.d.evaluated at datapoint $i$ ,and let $\mu _ { j }$ and $\sigma _ { j }$ simply denote the $j$ -th elementof these vectors.Then:

$$
\begin{array} { r l r } { \displaystyle \int q _ { \theta } ( { \bf z } ) \log p ( { \bf z } ) d { \bf z } = \int { \mathcal { N } } ( { \bf z } ; \pmb { \mu } , \sigma ^ { 2 } ) \log { \mathcal { N } } ( { \bf z } ; { \bf 0 } , { \bf I } ) d { \bf z } } & { } & \\ { \displaystyle = - \frac { J } { 2 } \log ( 2 \pi ) - \frac { 1 } { 2 } \sum _ { j = 1 } ^ { J } ( \mu _ { j } ^ { 2 } + \sigma _ { j } ^ { 2 } ) } & { } & \end{array}
$$