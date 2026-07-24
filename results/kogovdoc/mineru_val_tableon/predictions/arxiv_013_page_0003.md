Table 2:Model sizes,architectures,and optimization hyper-parameters.   

     params  dimension  n heads  n layers  learning rate  batch size  n tokens    6.7B  4096  32  32  3.0e-4  4M  1.0T    13.0B  5120  40  40  3.0e-4  4M  1.0T    32.5B  6656  52  60  1.5e-4  4M  1.4T    65.2B  8192  64  80  1.5e-4  4M  1.4T     

Overall,our entire training dataset contains roughly 1.4T tokens after tokenization.For most of our training data,each token is used only once during training,with the exception of the Wikipedia and Books domains,over which we perform approximately two epochs.

# 2.2 Architecture

Following recent work on large language models, ournetworkis based on the transformer architecture(Vaswani et al., 2O17).We leverage various improvements that were subsequently proposed, and used in different models such as PaLM.Here are the main difference with the original architecture,and where we were found the inspiration for this change (in bracket):

Pre-normalization [GPT3].To improve the training stability,we normalize the input of each transformer sub-layer,instead of normalizing the output.We use the RMSNorm normalizing function, introduced by Zhang and Sennrich (2019).

SwiGLU activation function [PaLM]. We replace theReLUnon-linearitybythe SwiGLUactivation function,introduced by Shazeer (2O2O) to improve the performance.We use a dimension of $\textstyle { \frac { 2 } { 3 } } 4 d$ instead of $4 d$ as in PaLM.

Rotary Embeddings[GPTNeo].We remove the absolute positional embeddings,and instead,add rotarypositional embeddings (RoPE),introduced bySu etal.(2021),at each layer of the network.

The details of the hyper-parameters for our different models are given in Table 2.

# 2.3Optimizer

Our models are trained using the AdamW optimizer(Loshchilov and Hutter,2O17),with the following hyper-parameters: $\beta _ { 1 } = 0 . 9 , \beta _ { 2 } = 0 . 9 5$ We use a cosine learning rate schedule,such that the final learning rate is equal to $10 \%$ of the maximal learning rate.We use a weight decay of O.1 and gradient clipping of 1.0.We use 2,O0O warmup steps,and varythe learningrate and batch size with the size of the model (see Table 2 for details).

![](images/6804580938cd3ea9fc97667a1ae5ab29e6ffd7594786051c833e06665e3d5345.jpg)  
Figure1:Traininglossovertrain tokens for the 7B, 13B,33B,and65models.LLaMA-33BandLLaMA65B were trained on 1.4T tokens.The smaller models were trained on $1 . 0 \mathrm { T }$ tokens．All models are trained with a batch size of 4M tokens.

# 2.4Efficient implementation

We make several optimizations to improve the training speed of our models.First,we use an efficient implementation of the causal multi-head attention to reduce memory usage and runtime.This implementation,available in the xformers library,² is inspired byRabe and Staats(2O21)and uses the backward from Dao etal. (2022). Thisis achieved by not storing the attention weights and not computing the key/query scores that are masked due to the causal nature of the language modeling task.

To further improve training efficiency,we reduced the amount of activations that are recomputed during the backward pass with checkpointing.More precisely,we save the activations that are expensive to compute,such as the outputs of linearlayers.Thisisachievedbymanuallyimplementing the backward function for the transformer layers,instead of relying on the PyTorch autograd. To fully benefit from this optimization,we need to