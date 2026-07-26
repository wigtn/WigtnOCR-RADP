(Ar= 64, A'r= 64, i,j)
AW.
17
13
19
0.8
Layer 32
25
0.7
31
37
43
0.6
49
55
0.5
61
0.4
 0.3
13
19
0.2
Layer 96
64
25
Layer
31
0.1
37
43
0.0
49
56
161616161
1616161616161
161616江616161
1616161616161
4556
22334
122334
22mm4
Figure 7: Normalized subspace similarity between the column vectors of Ar=64 from two randomly
former.
BLEU
NIST
CIDEr
Rank r
val_loss
METEOR
ROUGE_L
1.23
0.4565
0.7052
2.4329
68.72
8.7215
1.21
69.17
8.7413
0.4590
0.7052
2.4639
1.18
70.38
8.8439
0.4689
0.7186
2.5349
69.57
0.4636
0.7196
2.5196
1.17
8.7457
16
1.16
8.7483
0.7177
69.61
0.4629
2.4985
32
69.33
0.4642
0.7105
2.5255
1.16
8.7736
64
1.16
69.24
0.4651
2.5070
8.7174
0.7180
1.16
128
68.73
8.6718
0.4628
0.7127
2.5030
256
68.92
0.4629
1.16
8.6982
0.7128
2.5012
512
1.16
8.6857
68.78
0.4637
0.7128
2.5025
1024
1.17
69.37
8.7495
0.4659
0.7149
2.5090
Table 18: Validation loss and test set metrics on E2E NLG Challenge achieved by LoRA with
different rank r using GPT-2 Medium. Unlike on GPT-3 where r = 1 suffices for many tasks, here
the performance peaks at r = 16 for validation loss and r = 4 for BLEU, suggesting the GPT-2
Medium has a similar intrinsic rank for adaptation compared to GPT-3 175B. Note that some of our
hyperparameters are tuned on r = 4, which matches the parameter count of another baseline, and
thus might not be optimal for other choices of r.
Random
(Wq, Ar= 64, i,j)
Φ(Wq, Ar= 4, i,j)
Φ(Wq,Ar=8, i,j)
Φ(Wq, Arand, i,j)
451
0.200
555
658
0.175
762
0.150
865
-0.125
969
1072
0.100
1176
Figure 8: Normalized subspace similarity between the singular directions of Wg and those of △Wq
with varying r and a random baseline. △Wg amplifies directions that are important but not empha-
sized in W. △W with a larger r tends to pick up more directions that are already emphasized in
w.
26