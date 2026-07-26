φ(A_r=64, A'_r=64, i,j)

Figure 7: Normalized subspace similarity between the column vectors of A_r=64 from two randomly seeded runs, for both ΔW_q and ΔW_v from the 1st, 32nd, 64th, and 96th layers in a 96-layer Transformer.

| Rank r | val_loss | BLEU | NIST | METEOR | ROUGE_L | CIDEr |
|--------|----------|------|------|--------|---------|-------|
| 1      | 1.23     | 68.72 | 8.7215 | 0.4565 | 0.7052  | 2.4329 |
| 2      | 1.21     | 69.17 | 8.7413 | 0.4590 | 0.7052  | 2.4639 |
| 4      | 1.18     | 70.38 | 8.8439 | 0.4689 | 0.7186  | 2.5349 |
| 8      | 1.17     | 69.57 | 8.7457 | 0.4636 | 0.7196  | 2.5196 |
| 16     | 1.16     | 69.61 | 8.7483 | 0.4629 | 0.7177  | 2.4985 |
| 32     | 1.16     | 69.33 | 8.7736 | 0.4642 | 0.7105  | 2.5255 |
| 64     | 1.16     | 69.24 | 8.7174 | 0.4651 | 0.7180  | 2.5070 |
| 128    | 1.16     | 68.73 | 8.6718 | 0.4628 | 0.7127  | 2.5030 |
| 256    | 1.16     | 68.92 | 8.6982 | 0.4629 | 0.7128  | 2.5012 |
| 512    | 1.16     | 68.78 | 8.6857 | 0.4637 | 0.7128  | 2.5025 |
| 1024   | 1.17     | 69.37 | 8.7495 | 0.4659 | 0.7149  | 2.5090 |

Table 18: Validation loss and test set metrics on E2E NLG Challenge achieved by LoRA with different rank r using GPT-2 Medium. Unlike on GPT-3 where r = 1 suffices for many tasks, here the performance peaks at r = 16 for validation loss and r = 4 for BLEU, suggesting the GPT-2 Medium has a similar intrinsic rank for adaptation compared to GPT-3 175B. Note that some of our hyperparameters are tuned on r = 4, which matches the parameter count of another baseline, and thus might not be optimal for other choices of r.

Figure 8: Normalized subspace similarity between the singular directions of W_q and those of ΔW_q with varying r and a random baseline. ΔW_q amplifies directions that are important but not emphasized in W. ΔW with a larger r tends to pick up more directions that are already emphasized in W.

| φ(W_q, A_r=4, i,j) | φ(W_q, A_r=8, i,j) | φ(W_q, A_r=64, i,j) | φ(W_q, A_rand, i,j) |
|-------------------|-------------------|-------------------|-------------------|
| 451               |                   |                   |                   |
| 555               |                   |                   |                   |
| 658               |                   |                   |                   |
| 762               |                   |                   |                   |
| 865               |                   |                   |                   |
| 969               |                   |                   |                   |
| 1072              |                   |                   |                   |
| 1176              |                   |                   |                   |

26