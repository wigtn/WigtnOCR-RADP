# SEMI-SUPERVISED CLASSIFICATIONWITH GRAPH CONVOLUTIONAL NETWORKS

ThomasN.Kipf University of Amsterdam T.N.Kipf@uva.nl

Max Welling   
University of Amsterdam   
Canadian Institute for Advanced Research (CIFAR)   
M.Welling@uva.nl

# ABSTRACT

We present a scalable approach for semi-supervised learning on graph-structured data that is based on an efficient variant of convolutional neural networks which operate directly on graphs.We motivate the choice of our convolutional architecture via a localized first-order approximation of spectral graph convolutions. Our model scales linearly in the number of graph edges and learns hidden layer representations that encode both local graph structure and features of nodes.In a number of experiments on citation networks and ona knowledge graph dataset we demonstrate that our approach outperforms related methods by a significant margin.

# 1 INTRODUCTION

We consider the problem of classifying nodes (such as documents) in a graph (such as a citation network),where labelsare only available fora small subset of nodes.This problem can be framed as graph-based semi-supervised learning,where label information is smoothed over the graph via some form of explicit graph-based regularization (Zhu et al.,2Oo3; Zhou et al.,2O04;Belkin et al, 2006;Weston et al.,2O12),e.g.by using a graph Laplacian regularization term in the loss function:

$$
\mathcal { L } = \mathcal { L } _ { 0 } + \lambda \mathcal { L } _ { \mathrm { r e g } } , \quad \mathrm { w i t h } \quad \mathcal { L } _ { \mathrm { r e g } } = \sum _ { i , j } A _ { i j } \| f ( X _ { i } ) - f ( X _ { j } ) \| ^ { 2 } = f ( X ) ^ { \top } \Delta f ( X ) .
$$

Here, $\mathcal { L } _ { 0 }$ denotes the supervised loss W.r.t.the labeled part of the graph, $f ( \cdot )$ can be a neural networklike differentiable function, $\lambda$ isa weighing factor and $X$ is a matrix of node feature vectors $X _ { i }$ （2 $\Delta = D - A$ denotes the unnormalized graph Laplacian of an undirected graph $\mathcal { G } = ( \nu , \mathcal { E } )$ with $N$ nodes $v _ { i } \in \mathcal V$ ,edges $\underline { { ( v _ { i } , v _ { j } ) } } \in \mathcal { E }$ ,anadjacency matrix $A \in \mathbb { R } ^ { N \times N }$ (binary or weighted) and a degree matrix $D _ { i i } = \sum _ { \dots } A _ { i j }$ .The formulation of Eq.1 relies on the assumption that connected nodes in the graph are likely to share the same label.This assumption,however,might restrict modeling capacity,as graph edges need not necessarily encode node similarity,but could contain additional information.

In this work,we encode the graph structure directly using a neural network model $f ( X , A )$ and train on a supervised target $\mathcal { L } _ { 0 }$ forall nodes with labels,thereby avoiding explicit graph-based regularization in the loss function. Conditioning $f ( \cdot )$ on the adjacency matrix of the graph will allow the model to distribute gradient information from the supervised loss $\mathcal { L } _ { 0 }$ and will enable it to learn representations of nodes both with and without labels.

Our contributions are two-fold.Firstly,we introduce a simple and well-behaved layer-wise propagation rule for neural network models which operate directly on graphs and show how it can be motivated from a first-order approximation of spectral graph convolutions (Hammond et al.,2011). Secondly,we demonstrate how this form of a graph-based neural network model can be used for fast and scalable semi-supervised classification of nodes in a graph.Experiments on a number of datasets demonstrate that our model compares favorably both in classification accuracy and eficiency (measured in wal-clock time)against state-of-the-art methods for semi-supervised learning.