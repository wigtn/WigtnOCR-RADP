Published as a conference paper at ICLR 2015

Table 1: ConvNet configurations (shown in columns). The depth of the configurations increases from the left (A) to the right (E), as more layers are added (the added layers are shown in bold). The convolutional layer parameters are denoted as “conv〈receptive field size〉-〈number of channels〉”. The ReLU activation function is not shown for brevity.

| ConvNet Configuration | A | A-LRN | B | C | D | E |
| --- | --- | --- | --- | --- | --- | --- |
| input (224 × 224 RGB image) | 11 weight layers | 11 weight layers | 13 weight layers | 16 weight layers | 16 weight layers | 19 weight layers |
| conv3-64 | conv3-64 | conv3-64 | conv3-64 | conv3-64 | conv3-64 | conv3-64 |
| maxpool | conv3-128 | conv3-128 | conv3-128 | conv3-128 | conv3-128 | conv3-128 |
| maxpool | conv3-256 | conv3-256 | conv3-256 | conv3-256 | conv3-256 | conv3-256 |
| maxpool | conv3-512 | conv3-512 | conv3-512 | conv3-512 | conv3-512 | conv3-512 |
| maxpool | conv3-512 | conv3-512 | conv3-512 | conv3-512 | conv3-512 | conv3-512 |
| maxpool | FC-4096 | FC-4096 | FC-4096 | FC-4096 | FC-4096 | FC-4096 |
| maxpool | FC-1000 | FC-1000 | FC-1000 | FC-1000 | FC-1000 | FC-1000 |
| maxpool | soft-max | soft-max | soft-max | soft-max | soft-max | soft-max |

Table 2: Number of parameters (in millions).

| Network | A,A-LRN | B | C | D | E |
| --- | --- | --- | --- | --- | --- |
| Number of parameters | 133 | 133 | 134 | 138 | 144 |

such layers have a 7 × 7 effective receptive field. So what have we gained by using, for instance, a stack of three 3 × 3 conv. layers instead of a single 7 × 7 layer? First, we incorporate three non-linear rectification layers instead of a single one, which makes the decision function more discriminative. Second, we decrease the number of parameters: assuming that both the input and the output of a three-layer 3 × 3 convolution stack has C channels, the stack is parametrised by 3 (3²C²) = 27C² weights; at the same time, a single 7 × 7 conv. layer would require 7²C² = 49C² parameters, i.e. 81% more. This can be seen as imposing a regularisation on the 7 × 7 conv. filters, forcing them to have a decomposition through the 3 × 3 filters (with non-linearity injected in between).

The incorporation of 1 × 1 conv. layers (configuration C, Table 1) is a way to increase the non-linearity of the decision function without affecting the receptive fields of the conv. layers. Even though in our case the 1 × 1 convolution is essentially a linear projection onto the space of the same dimensionality (the number of input and output channels is the same), an additional non-linearity is introduced by the rectification function. It should be noted that 1 × 1 conv. layers have recently been utilised in the “Network in Network” architecture of Lin et al. (2014).

Small-size convolution filters have been previously used by Ciresan et al. (2011), but their nets are significantly less deep than ours, and they did not evaluate on the large-scale ILSVRC dataset. Goodfellow et al. (2014) applied deep ConvNets (11 weight layers) to the task of street number recognition, and showed that the increased depth led to better performance. GoogLeNet (Szegedy et al., 2014), a top-performing entry of the ILSVRC-2014 classification task, was developed independently of our work, but is similar in that it is based on very deep ConvNets

3