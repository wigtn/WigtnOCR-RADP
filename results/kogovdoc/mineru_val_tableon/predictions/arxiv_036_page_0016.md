![](images/8eb78aa4b8935f5fe059fc6bde84482d8fd2623c3404fb052cd087189c8fd3ff.jpg)  
Figure 14 Left: Each value of the compute budget $C _ { \mathrm { m i n } }$ has an associated optimal model size $N$ . Optimal model size grows very rapidly with $C _ { \mathrm { m i n } }$ ,increasingby 5x foreach $1 0 \mathrm { x }$ increase in compute. The number of data examples processed makes up the remainder of the increase,growing relatively modestly by only $2 \mathrm { x }$ Right:The batch-adjusted number of optimizationsteps also growsvery slowly,if at all,meaning that most of the growth in data examples processed can be used for increased batch sizes.

canbe fitverywellwitha power-law

$$
N ( C _ { \mathrm { m i n } } ) \propto ( C _ { \mathrm { m i n } } ) ^ { 0 . 7 3 } .
$$

In Figure 12,we show the effect of training models of sub-optimal sizes (see Appendix B.4).

By definition $C _ { \mathrm { m i n } } \equiv 6 N B _ { \mathrm { c r i t } } S$ ,and so we can use $N ( C _ { \mathrm { m i n } } )$ to extract further results. In particular, since priorfits show $B \propto L ^ { - 4 . 8 }$ and $L \propto C _ { \mathrm { m i n } } ^ { - 0 . 0 5 }$ , we can conclude that $B _ { \mathrm { c r i t } } \propto C _ { \mathrm { m i n } } ^ { 0 . 2 4 }$ .This leads us to conclude that the optimal number of steps will only grow very slowly with compute,as"

$$
S _ { \mathrm { m i n } } \propto ( C _ { \mathrm { m i n } } ) ^ { 0 . 0 3 } ,
$$

matching the empirical results in Figure14.In factthe measured exponent is suficiently smallthat ourresults may even be consistent with an exponent of zero.

Thus we conclude that as we scale up language modeling with an optimal allocation of computation, we should predominantly increase the model size $N$ ,while simultaneously scaling up the batch size via $B \propto$ $B _ { \mathrm { c r i t } }$ with negligible increase in the number of serial steps.Since compute-effcient training uses relatively few optimization steps,additional work on speeding up early training dynamics may be warranted.

# 6.2Predictions from $L ( N , S _ { \mathrm { m i n } } )$ （204号

The results for $L ( C _ { \mathrm { m i n } } )$ and the allocations can be predicted from the $L ( N , S _ { \mathrm { m i n } } )$ equation obtained in   
section5Giveiucucnot m $L ( N , S _ { \mathrm { m i n } } )$ wacangsuestrate $\begin{array} { r } { S _ { \mathrm { m i n } } = \frac { C _ { \mathrm { m i n } } } { 6 N B } } \end{array}$ andisherfind hemigtaim $N$   
AppendixB,where we also provide some additional predictions.

For the loss as a function of training compute,we predict that

$$
L ( C _ { \mathrm { m i n } } ) = \left( \frac { C _ { c } ^ { \mathrm { m i n } } } { C _ { \mathrm { m i n } } } \right) ^ { \alpha _ { C } ^ { \mathrm { m i n } } }
$$

where

$$
\alpha _ { C } ^ { \mathrm { m i n } } \equiv \frac { 1 } { 1 / \alpha _ { S } + 1 / \alpha _ { B } + 1 / \alpha _ { N } } \approx 0 . 0 5 4
$$

in excellent agreement with the exponent ofFigure 13.We also predict that

$$
N ( C _ { \mathrm { m i n } } ) \propto ( C _ { \mathrm { m i n } } ) ^ { \alpha _ { C } ^ { \mathrm { m i n } } / \alpha _ { N } } \approx ( C _ { \mathrm { m i n } } ) ^ { 0 . 7 1 }
$$

which also matches the scaling of Figure14 to within afew percent.Our scaling laws provide a predictive framework for the performance of language modeling.