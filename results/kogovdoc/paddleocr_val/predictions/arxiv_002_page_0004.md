Input/Output Representations To make BERT
In order to train a deep bidirectional representa-
handle a variety of down-stream tasks, our input
tion, we simply mask some percentage of the input
tokens at random, and then predict those masked
representation is able to unambiguously represent
tokens. We refer to this procedure as a “masked
both a single sentence and a pair of sentences
LM"' (MLM), although it is often referred to as a
(e.g., <Question, Answer >) in one token sequence.
Throughout this work, a “sentence"' can be an arbi-
Cloze task in the literature (Taylor, 1953). In this
trary span of contiguous text, rather than an actual
case, the final hidden vectors corresponding to the
mask tokens are fed into an output softmax over
linguistic sentence. A “sequence" refers to the in-
the vocabulary, as in a standard LM. In all of our
put token sequence to BERT, which may be a sin-
gle sentence or two sentences packed together.
experiments, we mask 15% of all WordPiece to-
kens in each sequence at random. In contrast to
We use WordPiece embeddings (Wu et al.
2016) with a 30,000 token vocabulary. The first
denoising auto-encoders (Vincent et al., 2008), we
only predict the masked words rather than recon-
token of every sequence is always a special clas-
sification token ([ CLSJ). The final hidden state
structing the entire input.
corresponding to this token is used as the ag-
Although this allows us to obtain a bidirec-
tional pre-trained model, a downside is that we
gregate sequence representation for classification
tasks. Sentence pairs are packed together into a
are creating a mismatch between pre-training and
fine-tuning, since the [MASK] token does not ap-
single sequence. We differentiate the sentences in
pear during fine-tuning. To mitigate this, we do
two ways. First, we separate them with a special
not always replace ‘masked"' words with the ac-
token ([ SEP J). Second, we add a learned embed-
tual [MASK] token. The training data generator
ding to every token indicating whether it belongs
chooses 15% of the token positions at random for
to sentence A or sentence B. As shown in Figure 1,
prediction. If the i-th token is chosen, we replace
we denote input embedding as E, the final hidden
vector of the special [CLS] token as C  RH,
the i-th token with (1) the [MASK] token 80% of
and the final hidden vector for the ith input token
the time (2) a random token 10% of the time (3)
as Ti E RH.
the unchanged i-th token 10% of the time. Then,
T; will be used to predict the original token with
For a given token, its input representation is
cross entropy loss. We compare variations of this
constructed by summing the corresponding token,
procedure in Appendix C.2.
segment, and position embeddings. A visualiza-
tion of this construction can be seen in Figure 2.
Task #2: Next Sentence Prediction (NSP)
3.1Pre-training BERT
Many important downstream tasks such as Ques-
tion Answering (QA) and Natural Language Infer-
Unlike Peters et al. (2018a) and Radford et al.
ence (NLI) are based on understanding the rela-
(2018), we do not use traditional left-to-right or
tionship between two sentences, which is not di-
rectly captured by language modeling. In order
Instead, we pre-train BERT using two unsuper-
to train a model that understands sentence rela
vised tasks, described in this section. This step
tionships, we pre-train for a binarized next sen-
is presented in the left part of Figure 1.
tence prediction task that can be trivially gener-
Task #l: Masked LM Intuitively, it is reason-
ated from any monolingual corpus. Specifically
able to believe that a deep bidirectional model is
when choosing the sentences A and B for each pre-
strictly more powerful than either a left-to-right
training example, 50% of the time B is the actual
model or the shallow concatenation of a left-to-
next sentence that follows A (labeled as IsNext),
right and a right-to-left model. Unfortunately,
and 50% of the time it is a random sentence from
standard conditional language models can only be
the corpus (labeled as NotNext). As we show
in Figure 1, C is used for next sentence predic-
trained left-to-right or right-to-left, since bidirec-
tional conditioning would allow each word to in-
tion (NSP).5 Despite its simplicity, we demon-
directly “see itself"', and the model could trivially
strate in Section 5.1 that pre-training towards this
predict the target word in a multi-layered context.
task is very beneficial to both QA and NLI.
5 The final model achieves 97%-98% accuracy on NSP.
former is often referred to as a “Transformer encoder" while
6The vector C is not a meaningful sentence representation
the left-context-only version is referred to as a Transformer
decoder' since it can be used for text generation.
without fine-tuning, since it was trained with NSP.