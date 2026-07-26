(a) Learned Frey Face manifold
(b) Learned MNIST manifold
Figure 4: Visualisations of learned data manifold for generative models with two-dimensional latent
space, learned with AEVB. Since the prior of the latent space is Gaussian, linearly spaced coor-
dinates on the unit square were transformed through the inverse CDF of the Gaussian to produce
values of the latent variables z. For each of these values z, we plotted the corresponding generative
Pe(x|z) with the learned parameters 0.
(a) 2-D latent space
(b) 5-D latent space
(c) 10-D latent space
(d) 20-D latent space
Figure 5: Random samples from learned generative models of MNIST for different dimensionalities
of latent space.
BSolution of -DkL(qβ(z)Ilpe(z)), Gaussian case
The variational lower bound (the objective to be maximized) contains a KL term that can often be
integrated analytically. Here we give the solution when both the prior pe(z) = N(O, I) and the
posterior approximation Q(z|x(i)) are Gaussian. Let J be the dimensionality of z. Let μ and 
denote the variational mean and s.d. evaluated at datapoint i, and let μj and oj simply denote the
j-th element of these vectors. Then:
α²) logN(z; 0, I) dz
qe(z) log p(z) dz :
(+)
（2元）
j=1
10