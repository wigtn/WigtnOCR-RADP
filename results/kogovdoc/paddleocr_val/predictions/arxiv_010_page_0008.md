Algorithm 1 WGAN, our proposed algorithm. All experiments in the paper used
the default values α = 0.00005, c = 0.01, m = 64, ncritic = 5.
Require: : α, the learning rate. c, the clipping parameter. m, the batch size.
Ncritic, the number of iterations of the critic per generator iteration.
Require: : wo, initial critic parameters. So, initial generator's parameters.
l: while  has not converged do
for t = O, .., ncritic do
2:
Sample (r(i)ym)
3:
4:
gw ←V [=1 fw(z(i)) -=1 fw(ge(z(i)]
5:
w ← w + α: RMSProp(w, gw)
6:
w ← clip(w, -c,c)
7:
end for
8:
Sample (z(i) )1 ~ p(z) a batch of prior samples.
9:
ge - fu(ge(z(i)
10:
← -α:RMSProp(, ge)
11:
12: end while
The fact that the EM distance is continuous and differentiable a.e. means that
we can (and should) train the critic till optimality. The argument is simple, the
more we train the critic, the more reliable gradient of the Wasserstein we get, which
is actually useful by the fact that Wasserstein is differentiable almost everywhere.
For the JS, as the discriminator gets better the gradients get more reliable but the
true gradient is O since the JS is locally saturated and we get vanishing gradients,
as can be seen in Figure 1 of this paper and Theorem 2.4 of [1]. In Figure 2
we show a proof of concept of this, where we train a GAN discriminator and a
WGAN critic till optimality. The discriminator learns very quickly to distinguish
between fake and real, and as expected provides no reliable gradient information.
The critic, however, can't saturate, and converges to a linear function that gives
limits the possible growth of the function to be at most linear in different parts of
the space, forcing the optimal critic to have this behaviour.
makes it impossible to collapse modes when we do. This is due to the fact that mode
collapse comes from the fact that the optimal generator for a ficed discriminator
is a sum of deltas on the points the discriminator assigns the highest values, as
observed by [4] and highlighted in [11].
In the following section we display the practical benefits of our new algorithm,
and we provide an in-depth comparison of its behaviour and that of traditional
GANs.