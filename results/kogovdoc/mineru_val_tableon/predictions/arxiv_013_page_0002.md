# 2Approach

Our training approach is similar to the methods described in previous work(Brown et al.,2020; Chowdhery et al.,2022),and is inspired by the Chinchilla scaling laws (Hoffmann etal.,2022). We train large transformers on a large quantity of textual data using a standard optimizer.

# 2.1Pre-training Data

Our training dataset is a mixture of several sources, reported in Table1,that cover a diverse set of domains.For the most part,we reuse data sources thathave been leveraged to train otherLLMs,with therestriction of onlyusingdata that is publicly available,and compatible with open sourcing.This leads to the following mixture of data and the percentage they represent in the training set:

English CommonCrawl $[67 \%$ J.We preprocess five CommonCrawl dumps,ranging from 2017 to 2020,with the CCNet pipeline (Wenzek et al., 2020).This process deduplicates the data at the line level,performs language identification with afastText linear classifier to remove non-English pages and filters low quality content with an ngram language model. In addition,we trained a linearmodel to classify pages used as references in Wikipedia v.s. randomly sampled pages,and discarded pagesnotclassified as references.

$C 4 [ 1 5 \% ]$ ．During exploratory experiments,we observed that using diverse pre-processed CommonCrawl datasets improves performance.We thus included the publiclyavailable C4 dataset (Raffel et al.,2O2O) in our data.The preprocessing of C4 also contains deduplication and language identification steps: the main difference with CCNet is the quality filtering,which mostly relies on heuristics such as presence of punctuation marks or the number of words and sentences in a webpage.

Github $[ 4 . 5 \% ]$ ．We use the public GitHub dataset available on Google BigQuery. We only kept projects that are distributed under the Apache, BSD and MIT licenses.Additionally,we filtered low quality files with heuristics based on the line length or proportion of alphanumeric characters, and removed boilerplate,such as headers,with regular expressions.Finally,we deduplicate the resulting dataset at the file level,with exact matches.

Wikipedia $[ 4 . 5 \% \$ .WeaddWikipedia dumps from the June-August 2O22 period,covering 20

     Dataset  Sampling prop.Epochs Disk size      CommonCrawl  67.0%  3.3TB    C4  15.0%  1.10 1.06 783GB    Github  4.5%  328 GB    Wikipedia  4.5%  2.45 83GB    Books  4.5%  2.23 85GB    ArXiv  2.5%  92GB    StackExchange  2.0%  1.06 1.03 78 GB     

Table 1: Pre-training data.Data mixtures used for pretraining,for each subset we list the sampling proportion,number of epochs performed on the subset when training on $1 . 4 \mathrm { T }$ tokens,and disk size. The pre-training runs on 1T tokens have the same sampling proportion.

languages,which use either the Latin or Cyrillic scripts:bg,ca,cs,da,de,en,es,fr,hr,hu,it, nl,pl,pt,ro,ru,sl,sr,sv,uk.We process the data to remove hyperlinks,comments and other formatting boilerplate.

Gutenberg and Books3 $[ 4 . 5 \% ]$ ．We include two book corpora in our training dataset: the GutenbergProject,which contains books that are in the public domain,and the Books3 section of ThePile (Gao etal.,2O2O),a publiclyavailable dataset for training large language models. We perform deduplication at the book level,removing books with more than $90 \%$ content overlap.

ArXiv $[ 2 . 5 \% ]$ .We process arXiv Latex files to add scientific data to our dataset. Following Lewkowycz et al. (2022), we removed everything before the first section,as well as the bibliography. We also removed the comments from the .tex files, and inline-expanded definitions and macros written by users to increase consistency across papers.

Stack Exchange $[ 2 \% ]$ .We includea dump of Stack Exchange,a website of high quality questions and answers that covers a diverse set of domains,ranging from computer science to chemistry. We kept the data from the 28 largest websites,removed the HTML tags from text and sorted the answers by score (from highest to lowest).

Tokenizer.We tokenize the data with the bytepair encoding(BPE)algorithm(Sennrich et al., 2015),using the implementation from SentencePiece (Kudo and Richardson,2O18).Notably, we split all numbers into individual digits,and fallback to bytes to decompose unknown UTF-8 characters.