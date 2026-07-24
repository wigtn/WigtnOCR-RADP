![](images/02863a2862dc7c31e0d1bd1dac040848360cf321acfd6ccaa7bbfc569eb64d00.jpg)  
Figure 5:Algorithms trained with a DCGAN generator.Left:WGAN algorithm.Right: standardGANformulation.Both algorithms produce high quality samples.

![](images/9572b03e1c903c6f26f5f0b5bd390e0b46787c2920671dd2fec0f60d5f4bde45.jpg)  
Figure 6:Algorithms trained with a generator without batch normalization and constant number of filters at every layer(as opposed to duplicating them every time as in [18]). Aside from taking out batch normalization,the number of parameters is therefore reduced byabit more than an order of magnitude.Left:WGAN algorithm.Right:standard GAN formulation.As we can see the standard GAN failed to learn while the WGAN still was ableto producesamples.

![](images/bbc8549bc2d807f04936d35e203268f674bc4adfa150400bcbd34276c91adefa.jpg)  
Figure 7:Algorithms trained with an MLP generator with 4 layers and 512 units with ReLU nonlinearities.The number of parameters is similar to that ofa DCGAN,but it lacks a strong inductive bias for image generation.Left:WGAN algorithm.Right:standardGAN formulation.The WGAN method still was able to produce samples,lower quality than the DCGAN,and of higher quality than the MLP of the standard GAN.Note the significant degree of mode collapse in the GANMLP.

# 5 Related Work

There's been a number of works on the so called Integral Probability Metrics (IPMs) [15].Given $\mathcal { F }$ a set of functions from $\mathcal { X }$ to $\mathbb { R }$ ，we can define

$$
d _ { \mathcal { F } } ( \mathbb { P } _ { r } , \mathbb { P } _ { \theta } ) = \operatorname* { s u p } _ { f \in \mathcal { F } } \mathbb { E } _ { x \sim \mathbb { P } _ { r } } [ f ( x ) ] - \mathbb { E } _ { x \sim \mathbb { P } _ { \theta } } [ f ( x ) ]
$$

as an integral probability metric associated with the function class $\mathcal { F }$ .It iseasily verified that if for every $f \in { \mathcal { F } }$ we have $- f \in \mathcal { F }$ (such as all examples we'll consider), then $d _ { \mathcal { F } }$ is nonnegative,satisfies the triangular inequality,and is symmetric. Thus, （2 $d _ { \mathcal { F } }$ isa pseudometric over $\operatorname { P r o b } ( \mathcal { X } )$

While IPMs might seem to share a similar formula,as we will see different classes of functions can yeald to radically different metrics.

·By the Kantorovich-Rubinstein duality [22],we know that $W ( \mathbb { P } _ { r } , \mathbb { P } _ { \theta } ) = d _ { \mathcal { F } } ( \mathbb { P } _ { r } , \mathbb { P } _ { \theta } )$