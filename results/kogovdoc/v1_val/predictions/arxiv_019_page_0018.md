## C. Image Guiding Mechanisms

| Samples 256² | Guided Convolutional Samples 512² | Convolutional Samples 512² |
|-------------|-------------------------------|---------------------------|
| [Figure 14: On landscapes, convolutional sampling with unconditional models can lead to homogeneous and incoherent global structures (see column 2). $L_2$-guiding with a low resolution image can help to reestablish coherent global structures.] | | |

An intriguing feature of diffusion models is that unconditional models can be conditioned at test-time [15, 82, 85]. In particular, [15] presented an algorithm to guide both unconditional and conditional models trained on the ImageNet dataset with a classifier $\log p_\Phi(y|x_t)$, trained on each $x_t$ of the diffusion process. We directly build on this formulation and introduce post-hoc image-guiding:

For an epsilon-parameterized model with fixed variance, the guiding algorithm as introduced in [15] reads:

$$
\hat{\epsilon} \leftarrow \epsilon_\theta(z_t, t) + \sqrt{1 - \alpha_t^2} \nabla_{z_t} \log p_\Phi(y | z_t) \tag{16}
$$

This can be interpreted as an update correcting the “score” $\epsilon_\theta$ with a conditional distribution $\log p_\Phi(y | z_t)$.

So far, this scenario has only been applied to single-class classification models. We re-interpret the guiding distribution $p_\Phi(y | T(\mathcal{D}(z_0(z_t))))$ as a general purpose image-to-image translation task given a target image $y$, where $T$ can be any differentiable transformation adopted to the image-to-image translation task at hand, such as the identity, a downsampling operation or similar.

18