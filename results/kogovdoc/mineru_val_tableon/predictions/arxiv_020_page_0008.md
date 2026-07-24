latter would make the average lengths of the input and output sequences much longer,and therefore would require more computation.

# 4.2 Mixed Word/Character Model

A second approach we use is the mixed word/character model.As in a word model,we keep a fixed-size word vocabulary.However,unlike in a conventional word model where OOV words are collapsed into a single UNK symbol,we convert OOV words into the sequence of its constituent characters.Special prefixes are prepended to the characters,to 1) show the location of the characters ina word,and 2)to distinguish them from normal in-vocabulary characters.There are three prefixes: $\angle B > , \angle M >$ ，and $ $ ,indicating beginning of the word,middleof the wordand endof the word,respectively.For example,let'sassume the word Miki is not in the vocabulary.It will be preprocessed into a sequence of special tokens:  M  i  k  i.The process is done on both the source and the target sentences.During decoding,the output may also contain sequences ofspecial tokens.With the prefixes,it is trivial toreverse the tokenization tothe original words as part of a post-processing step.

# 5 Training Criteria

Given a dataset of parallel text containing $N$ input-output sequence pairs,denoted $\mathcal { D } \equiv \left\{ ( X ^ { ( i ) } , Y ^ { * ( i ) } ) \right\} _ { i = 1 } ^ { N }$ standard maximum-likelihood training aims at maximizing the sum of log probabilities of the ground-truth outputs given the corresponding inputs,

$$
\mathcal { O } _ { \mathrm { M L } } ( \theta ) = \sum _ { i = 1 } ^ { N } \log P _ { \theta } ( Y ^ { * ( i ) } \mid X ^ { ( i ) } ) ~ .
$$

The main problem with this objective is that it does not reflect the task reward functionas measured by the BLEU score in translation.Further,this objective does not explicitly encouragearanking among incorrect output sequences-where outputs with higher BLEU scores should stillobtain higher probabilities under the model-since incorrect outputs are never observed during training.In other words,using maximum-likelihood training only,the model willnot learn to be robust to errors made during decoding since they are never observed,which is quite a mismatch between the training and testing procedure.

Several recent papers [34,39,32] have considered different ways of incorporating the task reward into optimization of neural sequence-to-sequence models.In this work,we also attempt to refine a model pretrained on the maximum likelihood objective to directly optimize for the task reward.We show that,even on large datasets,refinement of state-of-the-art maximum-likelihood models using task reward improves the results considerably.

We consider model refinement using the expected reward objective (also used in [34]),which can be expressed as

$$
\mathcal { O } _ { \mathrm { R L } } ( \pmb { \theta } ) = \sum _ { i = 1 } ^ { N } \sum _ { Y \in \mathcal { Y } } P _ { \pmb { \theta } } ( Y \mid X ^ { ( i ) } ) ~ r ( Y , Y ^ { * ( i ) } ) .
$$

Here, $r ( Y , Y ^ { * ( i ) } )$ denotes the per-sentence score,and we are computing an expectation over all of the output sentences $Y$ ,uptoa certainlength.

The BLEU score has some undesirable properties when used for single sentences,as it was designed to be a corpus measure.We therefore use a slightly different score for our RL experiments which we cal the “GLEU score".For the GLEU score,we record all sub-sequences of $^ { 1 }$ ， $2$ ， $3$ or 4 tokens in output and target sequence (n-grams).We then compute a recall which is the ratio of the number of matching n-grams to the number of total n-grams in the target (ground truth) sequence,and a precision,which is the ratio of the number of matching n-grams to the number of total n-grams in the generated output sequence.Then GLEU score is simply the minimum of recalland precision.This GLEU score's range is always betwen $0$ (no matches)and 1(all match)and it is symmetrical when switching output and target.According to our experiments,GLEU score correlates quite well with the BLEU metric on a corpus level but does not have its drawbacks for our per sentence reward objective.