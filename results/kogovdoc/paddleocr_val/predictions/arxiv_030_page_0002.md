3.1 Transformer
import tensorflow_hub as hub
The transformer based sentence encoding model
embed = hub.Module("https://tfhub.dev/google/"
"universal-sentence-encoder/1")
constructs sentence embeddings using the en-
coding sub-graph of the transformer architecture
embedding = embed([
"The quick brown fox jumps over the lazy dog."j)
(Vaswani et al., 2017). This sub-graph uses at-
Listing l: Python example code for using the
tention to compute context aware representations
universal sentence encoder.
of words in a sentence that take into account both
the ordering and identity of all the other words
The context aware word representations are con-
2  Model Toolkit
verted to a fixed length sentence encoding vector
We make available two new models for encoding
by computing the element-wise sum of the repre-
sentences into embedding vectors. One makes use
sentations at each word position.3 The encoder
of the transformer (Vaswani et al., 2017) architec-
takes as input a lowercased PTB tokenized string
ture, while the other is formulated as a deep aver-
and outputs a 512 dimensional vector as the sen-
aging network (DAN) (Iyyer et al., 2015). Both
tence embedding.
models are implemented in TensorFlow (Abadi
The encoding model is designed to be as gen-
et al., 2016) and are available to download from
eral purpose as possible. This is accomplished
TF Hub:1
by using multi-task learning whereby a single
encoding model is used to feed multiple down-
https://tfhub.dev/google/
universal-sentence-encoder/1
stream tasks. The supported tasks include: a Skip-
Thought like task (Kiros et al., 2015) for the un-
The models take as input English strings and
supervised learning from arbitrary running text;
produce as output a fixed dimensional embedding
a conversational input-response task for the in-
representation of the string. Listing 1 provides a
clusion of parsed conversational data (Henderson
minimal code snippet to convert a sentence into
et al., 2017); and classification tasks for train-
a tensor containing its sentence embedding. The
ing on supervised data. The Skip-Thought task
embedding tensor can be used directly or in-
replaces the LSTM (Hochreiter and Schmidhu-
corporated into larger model graphs for specific
ber, 1997) used in the original formulation with
tasks.2
a model based on the Transformer architecture.
As illustrated in Figure 1, the sentence embed-
As will be shown in the experimental results
dings can be trivially used to compute sentence
below, the transformer based encoder achieves
level semantic similarity scores that achieve ex-
the best overall transfer task performance. How-
cellent performance on the semantic textual sim-
ever, this comes at the cost of compute time and
ilarity (STS) Benchmark (Cer et al., 2017). When
memory usage scaling dramatically with sentence
included within larger models, the sentence encod-
length.
ing models can be fine tuned for specific tasks us-
ing gradient based updates.
3.2 Deep Averaging Network (DAN)
3 Encoders
The second encoding model makes use of a
deep averaging network (DAN) (Iyyer et al.
We introduce the model architecture for our two
2015) whereby input embeddings for words and
encoding models in this section. Our two encoders
bi-grams are first averaged together and then
have different design goals. One based on the
passed through a feedforward deep neural network
transformer architecture targets high accuracy at
(DNN) to produce sentence embeddings. Simi-
the cost of greater model complexity and resource
lar to the Transformer encoder, the DAN encoder
consumption. The other targets efficient inference
takes as input a lowercased PTB tokenized string
with slightly reduced accuracy.
and outputs a 512 dimensional sentence embed-
ding. The DAN encoder is trained similarly to the
1The encoding model for the DAN based encoder is al-
Transformer based encoder. We make use of mul-
ready available. The transformer based encoder will be made
available at a later point.
2Visit https://colab.research.google.com/ to try the code
3wWe then divide by the square root of the length of the
sentence so that the differences between short sentences are
snippet in Listing 1. Example code and documentation is
available on the universal encoder website provided above.
not dominated by sentence length effects