RoFormer
relative upper bound
20
18
16
14
12
10
relative distance
50
100
150
200
250
Figure 2: Long-term decay of RoPE.
3.4.3 Long-term decay of RoPE
We can group entries of vectors q = W q&m and k = W kan in pairs, and the inner product of RoPE in Equation (16)
can be written as a complex number multiplication.
d/2-1
(R,mWqam)T(Ro,n Wkan) = Re
(35)
i=0
d/2-1
d/2-1
d/2-1
hi(Si+1 - Si)=-  Si+1(hi+1 - hi).
q[2:2i+1]k[2i:2i+1)e(m-n)0
(36)
i=0
i=0
i=0
Thus,
d/2-1
d/2-1
-n)0元
Si+1(
i=0
i=0
d/2-1
(37)
ISi+1ll(hi+1 - hi)l
i=0
d/2-1
≤(max|hi+1- hil） ISi+1l
i=0
shown in Figure (2).
Experiments and Evaluation
We evaluate the proposed RoFormer on various NLP tasks as follows. We validate the performance of the proposed
solution on machine translation task Section (4.1). Then, we compare our RoPE implementation with BERTDevlin
et al. [2019] during the pre-training stage in Section (4.2). Based on the pre-trained model, in Section (4.3), we further
carry out evaluations across different downstream tasks from GLUE benchmarksSingh et al. [2018]. In Addition, we
conduct experiments using the proposed RoPE with the linear attention of PerFormer Choromanski et al. [202O] in