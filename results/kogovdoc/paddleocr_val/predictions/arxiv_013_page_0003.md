n heads
dimension
n layers
learning rate
batch size
n tokens
params
32
32
3.0e-4
6.7B
4096
4M
1.0T
40
13.0B
40
4M
1.0T
5120
3.0e-4
52
60
32.5B
4M
1.4T
6656
1.5e-4
64
65.2B
80
4M
1.4T
8192
1.5e-4
Table 2: Model sizes, architectures, and optimization hyper-parameters.
2.2
Overall, our entire training dataset contains
LLaMA 7B
roughly 1.4T tokens after tokenization. For most of
2.1
LLaMA 13B
our training data, each token is used only once dur-
loss
LLaMA 33B
2.0
ing training, with the exception of the Wikipedia
LLaMA 65B
raining
1.9
and Books domains, over which we perform ap-
1.8
proximately two epochs.
1.7
2.2 Architecture
1.6
Following recent work on large language models,
1.5
our network is based on the transformer architec-
400600800 1000 1200 1400
200
Billion of tokens
ture (Vaswani et al., 2017). We leverage various
improvements that were subsequently proposed,
Figure l: Training loss over train tokens for the 7B,
and used in different models such as PaLM. Here
13B, 33B, and 65 models. LLaMA-33B and LLaMA-
are the main difference with the original architec-
65B were trained on 1.4T tokens. The smaller models
ture, and where we were found the inspiration for
were trained on 1.OT tokens. All models are trained
this change (in bracket):
with a batch size of 4M tokens.
Pre-normalization [GPT3]. To improve the
training stability, we normalize the input of each
steps, and vary the learning rate and batch size with
transformer sub-layer, instead of normalizing the
the size of the model (see Table 2 for details).
output. We use the RMSNorm normalizing func-
tion, introduced by Zhang and Sennrich (2019).
2.4Efficient implementation
We make several optimizations to improve the train-
SwiGLU activation function [PaLM]. We re-
ing speed of our models. First, we use an efficient
place the ReLU non-linearity by the SwiGLU ac-
implementation of the causal multi-head attention
tivation function, introduced by Shazeer (2020) to
to reduce memory usage and runtime. This imple-
improve the performance. We use a dimension of
2 4d instead of 4d as in PaLM.
mentation, available in the xformers library,2 is
inspired by Rabe and Staats (2021) and uses the
Rotary Embeddings [GPTNeo]. We remove the
backward from Dao et al. (2022). This is achieved
absolute positional embeddings, and instead, add
by not storing the attention weights and not com-
rotary positional embeddings (RoPE), introduced
puting the key/query scores that are masked due to
by Su et al. (2021), at each layer of the network.
the causal nature of the language modeling task.
The details of the hyper-parameters for our dif-
To further improve training efficiency, we re-
ferent models are given in Table 2.
duced the amount of activations that are recom-
puted during the backward pass with checkpoint-
2.3 Optimizer
ing. More precisely, we save the activations that
Our models are trained using the AdamW opti-
are expensive to compute, such as the outputs of
mizer (Loshchilov and Hutter, 2017), with the fol-
linear layers. This is achieved by manually imple-
lowing hyper-parameters: β1 = 0.9, β2 = 0.95.
menting the backward function for the transformer
We use a cosine learning rate schedule, such that
layers, instead of relying on the PyTorch autograd.
the final learning rate is equal to 10% of the maxi-
To fully benefit from this optimization, we need to
mal learning rate. We use a weight decay of 0.1 and
2https://github.com/facebookresearch/xformers
gradient clipping of 1.0. We use 2, 000 warmup