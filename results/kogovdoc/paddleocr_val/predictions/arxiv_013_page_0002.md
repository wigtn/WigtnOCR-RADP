2 Approach
Sampling prop. Epochs Disk size
Dataset
Our training approach is similar to the methods
1.10
67.0%
3.3 TB
CommonCrawl
described in previous work (Brown et al., 2020;
C4
1.06
15.0%
783 GB
Chowdhery et al., 2022), and is inspired by the
0.64
4.5%
Github
328 GB
Chinchilla scaling laws (Hoffmann et al., 2022)
Wikipedia
83 GB
4.5%
2.45
4.5%
We train large transformers on a large quantity of
2.23
85 GB
Books
textual data using a standard optimizer.
ArXiv
2.5%
92 GB
1.06
StackExchange
2.0%
1.03
78 GB
2.1Pre-training Data
Table 1: Pre-training data. Data mixtures used for pre
Our training dataset is a mixture of several sources,
training, for each subset we list the sampling propor-
reported in Table 1, that cover a diverse set of do-
tion, number of epochs performed on the subset when
mains. For the most part, we reuse data sources
training on 1.4T tokens, and disk size. The pre-training
that have been leveraged to train other LLMs, with
runs on 1T tokens have the same sampling proportion.
the restriction of only using data that is publicly
available, and compatible with open sourcing. This
leads to the following mixture of data and the per-
languages, which use either the Latin or Cyrillic
centage they represent in the training set:
scripts: bg, ca, cs, da, de, en, es, fr, hr, hu, it,
nl, pl, pt, ro, ru, sl, sr, sv, uk. We process the
English CommonCrawl [67% ]. We preprocess
data to remove hyperlinks, comments and other
five CommonCrawl dumps, ranging from 2017
formatting boilerplate.
to 2020, with the CCNet pipeline (Wenzek et al.
2020). This process deduplicates the data at the
Gutenberg and Books3 [4.5%]. We include
line level, performs language identification with
two book corpora in our training dataset: the Guten-
a fastText linear classifier to remove non-English
berg Project, which contains books that are in the
pages and filters low quality content with an n-
public domain, and the Books3 section of TheP-
gram language model. In addition, we trained a
ile (Gao et al., 2020), a publicly available dataset
linear model to classify pages used as references
for training large language models. We perform
in Wikipedia v.s. randomly sampled pages, and
deduplication at the book level, removing books
discarded pages not classified as references.
with more than 90% content overlap.
C4 [15%]. During exploratory experiments, we
ArXiv [2.5%]. We process arXiv Latex files
observed that using diverse pre-processed Com-
to add scientific data to our dataset. Following
monCrawl datasets improves performance. We thus
Lewkowycz et al. (2022), we removed everything
included the publicly available C4 dataset (Raffel
before the first section, as well as the bibliography.
et al., 2020) in our data. The preprocessing of C4
We also removed the comments from the .tex files,
also contains deduplication and language identifi-
and inline-expanded definitions and macros written
cation steps: the main difference with CCNet is
by users to increase consistency across papers.
the quality filtering, which mostly relies on heuris-
tics such as presence of punctuation marks or the
Stack Exchange [2%]. We include a dump of
number of words and sentences in a webpage.
Stack Exchange, a website of high quality ques-
tions and answers that covers a diverse set of do-
Github [4.5%]. We use the public GitHub
mains, ranging from computer science to chemistry.
dataset available on Google BigQuery. We only
We kept the data from the 28 largest websites, re-
kept projects that are distributed under the Apache,
moved the HTML tags from text and sorted the
BSD and MIT licenses. Additionally, we filtered
answers by score (from highest to lowest).
low quality files with heuristics based on the line
length or proportion of alphanumeric characters,
Tokenizer. We tokenize the data with the byte-
and removed boilerplate, such as headers, with reg
pair encoding (BPE) algorithm (Sennrich et al.,
ular expressions. Finally, we deduplicate the result
2015), using the implementation from Sentence-
ing dataset at the file level, with exact matches.
Piece (Kudo and Richardson, 2018). Notably, we
Wikipedia [4.5%]. We add Wikipedia dumps
split all numbers into individual digits, and fallback
from the June-August 2022 period, covering 20
to bytes to decompose unknown UTF-8 characters.