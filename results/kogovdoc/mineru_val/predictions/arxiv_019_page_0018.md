- - -

An intriguing feature of diffusion models is that unconditional models can be conditioned at test-time [15, 82, 85]. In particular, [15] presented an algorithm to guide both unconditional and conditional models trained on the ImageNet dataset with a classifier log pΦ(y|xt), trained on each xt of the diffusion process. We directly build on this formulation and introduce post-hoc image-guiding:

For an epsilon-parameterized model with fixed variance, the guiding algorithm as introduced in [15] reads:

This can be interpreted as an update correcting the “score” ϵθ with a conditional distribution log pΦ(y|zt).

So far, this scenario has only been applied to single-class classification models. We re-interpret the guiding distribution pΦ(y|T (D(z0(zt)))) as a general purpose image-to-image translation task given a target image y, where T can be any differentiable transformation adopted to the image-to-image translation task at hand, such as the identity, a downsampling operation or similar.