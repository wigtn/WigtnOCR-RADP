Published as a conference paper at ICLR 2017
SEMI-SUPERVISED CLASSIFICATION WITH
GRAPH CONVOLUTIONAL NETWORKS
Max Welling
Thomas N. Kipf
University of Amsterdam
University of Amsterdam
Canadian Institute for Advanced Research (CIFAR)
T.N.Kipf@uva.nl
M.Welling@uva.nl
ABSTRACT
 22 Feb 2017
We present a scalable approach for semi-supervised learning on graph-structured
data that is based on an efficient variant of convolutional neural networks which
operate directly on graphs. We motivate the choice of our convolutional archi-
tecture via a localized first-order approximation of spectral graph convolutions.
Our model scales linearly in the number of graph edges and learns hidden layer
representations that encode both local graph structure and features of nodes. In
a number of experiments on citation networks and on a knowledge graph dataset
[cs.LG]
we demonstrate that our approach outperforms related methods by a significant
margin.
INTRODUCTION
arXiv:1609.02907v4 [
We consider the problem of classifying nodes (such as documents) in a graph (such as a citation
network), where labels are only available for a small subset of nodes. This problem can be framed
as graph-based semi-supervised learning, where label information is smoothed over the graph via
some form of explicit graph-based regularization (Zhu et al., 2003; Zhou et al., 2004; Belkin et al.,
2006; Weston et al., 2012), e.g. by using a graph Laplacian regularization term in the loss function:
L = Lo + 入Lreg ，
with Lreg = Aijllf(Xi) - f(X,)I2 = f(X)T△f(X).
(1)
i,j
Here, Lo denotes the supervised loss w.r.t. the labeled part of the graph, f (-) can be a neural network-
like differentiable function, ^ is a weighing factor and X is a matrix of node feature vectors Xi.
△ = D - A denotes the unnormalized graph Laplacian of an undirected graph  = (V, ) with
N nodes Ui E V, edges (vi, Ui) E E, an adjacency matrix A E RNxN (binary or weighted) and
a degree matrix Dii = Z; Aij. The formulation of Eq. 1 relies on the assumption that connected
nodes in the graph are likely to share the same label. This assumption, however, might restrict
modeling capacity, as graph edges need not necessarily encode node similarity, but could contain
additional information.
In this work, we encode the graph structure directly using a neural network model f(X, A) and
train on a supervised target Lo for all nodes with labels, thereby avoiding explicit graph-based
regularization in the loss function. Conditioning f() on the adjacency matrix of the graph will
allow the model to distribute gradient information from the supervised loss Lo and will enable it to
learn representations of nodes both with and without labels.
Our contributions are two-fold. Firstly, we introduce a simple and well-behaved layer-wise prop-
agation rule for neural network models which operate directly on graphs and show how it can be
motivated from a first-order approximation of spectral graph convolutions (Hammond et al., 2011).
Secondly, we demonstrate how this form of a graph-based neural network model can be used for
fast and scalable semi-supervised classification of nodes in a graph. Experiments on a number of
datasets demonstrate that our model compares favorably both in classification accuracy and effi-
ciency (measured in wall-clock time) against state-of-the-art methods for semi-supervised learning.