elative upper bound 20 18 16 14 12 10 8 relative distance 50 100 150 200 250

# 3.4.3 Long-term decay of RoPE

We can group entries of vectors q = W qxm and k = W kxn in pairs, and the inner product of RoPE in Equation (16) can be written as a complex number multiplication.

where q[2i:2i+1] represents the 2ith to (2i + 1)th entries of q. Denote hi = q[2i:2i+1]k[∗2i:2i+1] and Sj = Pij=−01 ei(m−n)θi, and let hd/2 = 0 and S0 = 0, we can rewrite the summation using Abel transformation

Thus,

Note that the value of d1/2 Pid=/21 |Si| decay with the relative distance m − n increases by setting θi = 10000−2i/d, as shown in Figure (2).

# 4 Experiments and Evaluation

We evaluate the proposed RoFormer on various NLP tasks as follows. We validate the performance of the proposed solution on machine translation task Section (4.1). Then, we compare our RoPE implementation with BERTDevlin et al. [2019] during the pre-training stage in Section (4.2). Based on the pre-trained model, in Section (4.3), we further carry out evaluations across different downstream tasks from GLUE benchmarksSingh et al. [2018]. In Addition, we conduct experiments using the proposed RoPE with the linear attention of PerFormer Choromanski et al. [2020] in