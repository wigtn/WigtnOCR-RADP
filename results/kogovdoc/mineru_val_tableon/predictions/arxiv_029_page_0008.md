![](images/c98b3c18565aa99f8fca400dd1a9c3dc83c5a988d1cf3ccea1d5fda259ca4936.jpg)  
Figure 2:Long-term decay of RoPE.

# 3.4.3Long-term decay of RoPE

We can group entries of vectors $\pmb q = \pmb W _ { q } \pmb x _ { m }$ and $\pmb { k } = \pmb { W } _ { k } \pmb { x } _ { n }$ in pairs,and the inner product of RoPE in Equation (16) can be written as a complex number multiplication.

$$
( R _ { \Theta , m } ^ { d } W _ { q } { \bf x } _ { m } ) ^ { \top } ( R _ { \Theta , n } ^ { d } W _ { k } { \bf x } _ { n } ) = \mathrm { R e } \left[ \begin{array} { l } { d / 2 - 1 } \\ { \displaystyle \sum _ { i = 0 } ^ { d / 2 - 1 } { \bf q } _ { [ 2 i : 2 i + 1 ] } k _ { [ 2 i : 2 i + 1 ] } ^ { * } e ^ { i ( m - n ) \theta _ { i } } } \end{array} \right]
$$

where $\pmb { q } _ { [ 2 i : 2 i + 1 ] }$ represents the $2 i ^ { t h }$ t0 $( 2 i + 1 ) ^ { t h }$ entries of $\mathbf { \pmb { q } }$ Denote $h _ { i } ~ = ~ q _ { [ 2 i : 2 i + 1 ] } k _ { [ 2 i : 2 i + 1 ] } ^ { * }$ and $S _ { j } ~ =$ （20 $\textstyle \sum _ { i = 0 } ^ { j - 1 } e ^ { i ( m - n ) \theta _ { i } }$ , and let $h _ { d / 2 } = 0$ and $S _ { 0 } = 0$ , we can rewrite the summation using Abel transformation

$$
\sum _ { i = 0 } ^ { d / 2 - 1 } q _ { [ 2 i ; 2 i + 1 ] } k _ { [ 2 i ; 2 i + 1 ] } ^ { * } e ^ { i ( m - n ) \theta _ { i } } = \sum _ { i = 0 } ^ { d / 2 - 1 } h _ { i } ( S _ { i + 1 } - S _ { i } ) = - \sum _ { i = 0 } ^ { d / 2 - 1 } S _ { i + 1 } ( h _ { i + 1 } - h _ { i } ) .
$$

Thus,

$$
\begin{array} { r l } {  { \bigg | | \begin{array} { l } { \displaystyle \sum _ { i = 0 } ^ { d / 2 - 1 } q _ { [ 2 i ; 2 i + 1 ] } k _ { [ 2 i ; 2 i + 1 ] } ^ { * } e ^ { i ( m - n ) \theta _ { i } } | = \bigg | | \begin{array} { l } { \displaystyle \sum _ { i = 0 } ^ { d / 2 - 1 } S _ { i + 1 } ( h _ { i + 1 } - h _ { i } ) \bigg | } } \\ { \displaystyle \sum _ { i = 0 } ^ { d / 2 - 1 } S _ { i + 1 } \big | \big | ( h _ { i + 1 } - h _ { i } ) \big | } \end{array} | } \qquad } & { } \\ & { \leq \ \sum _ { i = 0 } ^ { d } | S _ { i + 1 } \big | \big | ( h _ { i + 1 } - h _ { i } ) \big | } \\ & { \leq \big ( \operatorname* { m a x } _ { i } \big | h _ { i + 1 } - h _ { i } \big | \big ) \displaystyle \sum _ { i = 0 } ^ { d / 2 - 1 } \big | S _ { i + 1 } \big | } \end{array} \end{array}
$$

Note that the value of $\begin{array} { r } { \frac { 1 } { d / 2 } \sum _ { i = 1 } ^ { d / 2 } | S _ { i } | } \end{array}$ decay with the relative distance $m - n$ increases by setting $\theta _ { i } = 1 0 0 0 0 ^ { - 2 i / d }$ ,as shown in Figure (2).

# 4Experiments and Evaluation

We evaluate the proposed RoFormer on various NLPtasks as follows.We validate the performance of the proposed solution on machine translation task Section (4.1).Then,we compare our RoPE implementation with BERTDevlin etal.[2019]during the pre-training stage in Section(4.2).Basedonthe pre-trainedmodel,in Section (4.3),wefurther carry out evaluationsacross different downstream tasks from GLUE benchmarksSingh etal.2O18].In Addition,we conduct experiments using the proposed RoPE with thelinearatentionof PerFormer Choromanski et al.[2020] in