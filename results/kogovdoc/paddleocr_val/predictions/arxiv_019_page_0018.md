C. Image Guiding Mechanisms
Samples 2562
Guided Convolutional Samples 5122
Convolutional Samples 5122
Figure 14. On landscapes, convolutional sampling with unconditional models can lead to homogeneous and incoherent global structures
(see column 2). L2-guiding with a low resolution image can help to reestablish coherent global structures.
An intriguing feature of diffusion models is that unconditional models can be conditioned at test-time [15, 82, 85]. In
particular, [15] presented an algorithm to guide both unconditional and conditional models trained on the ImageNet dataset
with a classifier log p (ylct), trained on each t of the diffusion process. We directly build on this formulation and introduce
post-hoc image-guiding:
For an epsilon-parameterized model with fixed variance, the guiding algorithm as introduced in [15] reads:
 ← Ee(zt,t) + V1 - α Vzt log ps(ylzt) .
(16)
This can be interpreted as an update correcting the “score" ee with a conditional distribution log pα (yl zt).
differentiable transformation adopted to the image-to-image translation task at hand, such as the identity, a downsampling
operation or similar.
18 