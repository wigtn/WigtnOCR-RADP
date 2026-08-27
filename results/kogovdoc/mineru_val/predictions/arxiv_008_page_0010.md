?   
2   
1   
-   
X ybjisheom   
- O   
2 2 公   
(a) Learned Frey Face manifold (b) Learned MNIST manifold

ybjishm yshm (a) 2-D latent space (b) 5-D latent space (c) 10-D latent space (d) 20-D latent space

# B Solution of −DKL(qφ(z)||pθ(z)), Gaussian case

The variational lower bound (the objective to be maximized) contains a KL term that can often be integrated analytically. Here we give the solution when both the prior pθ(z) = (0, I) and the posterior approximation qφ(z|x(i)) are Gaussian. Let J be the dimensionality of z. Let µ and σ denote the variational mean and s.d. evaluated at datapoint i, and let µj and σj simply denote the j-th element of these vectors. Then: