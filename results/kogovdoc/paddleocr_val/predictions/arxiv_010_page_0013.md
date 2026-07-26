Figure 5: Algorithms trained with a DCGAN generator. Left: WGAN algorithm. Right:
standard GAN formulation. Both algorithms produce high quality samples.
Figure 6: Algorithms trained with a generator without batch normalization and constant
number of filters at every layer (as opposed to duplicating them every time as in [18]).
Aside from taking out batch normalization, the number of parameters is therefore reduced
by a bit more than an order of magnitude. Left: WGAN algorithm. Right: standard GAN
formulation. As we can see the standard GAN failed to learn while the WGAN still was
able to produce samples.
Figure 7: Algorithms trained with an MLP generator with 4 layers and 512 units with ReLU
nonlinearities. The number of parameters is similar to that of a DCGAN, but it lacks a
strong inductive bias for image generation. Left: WGAN algorithm. Right: standard GAN
formulation. The WGAN method still was able to produce samples, lower quality than the
DCGAN, and of higher quality than the MLP of the standard GAN. Note the significant
degree of mode collapse in the GAN MLP.
5 Related Work
There's been a number of works on the so called Integral Probability Metrics (IPMs)
[15]. Given F a set of functions from X to R, we can define
(4)
d(Pr, Pe) = sup Eα~P,[f(c)] -Eα~P。[f(c)]
feF
as an integral probability metric associated with the function class F. It is easily
verified that if for every f E F we have -f  F (such as all examples we'll consider),
then dj is nonnegative, satisfies the triangular inequality, and is symmetric. Thus,
d is a pseudometric over Prob(x).
While IPMs might seem to share a similar formula, as we will see different classes
of functions can yeald to radically different metrics.
· By the Kantorovich-Rubinstein duality [22], we know that W(Pr, Pe) = dj(Pr, Pe)
13