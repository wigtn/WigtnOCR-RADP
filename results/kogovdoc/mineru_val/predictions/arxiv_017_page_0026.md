![](images/dd52f8be9c90ff48f33dfee8220e54c96f5841c77cb4381a0f6f2b12d1f4bf85.jpg)  
Figure 7: Normalized subspace similarity between the column vectors of Ar=64 from two randomly seeded runs, for both ∆Wq and ∆Wv from the 1st, 32nd, 64th, and 96th layers in a 96-layer Transformer.

![](images/f5739ca4cedb816d773e168d7d8a476bb518c8476fca5a9cef37ea108ad25877.jpg)

Table 18: Validation loss and test set metrics on E2E NLG Challenge achieved by LoRA with different rank r using GPT-2 Medium. Unlike on GPT-3 where r = 1 suffices for many tasks, here the performance peaks at r = 16 for validation loss and r = 4 for BLEU, suggesting the GPT-2 Medium has a similar intrinsic rank for adaptation compared to GPT-3 175B. Note that some of our hyperparameters are tuned on r = 4, which matches the parameter count of another baseline, and thus might not be optimal for other choices of r.

![](images/5999c8167a66bb03c28aef9d2ad0ee835ade7f49e92c82651300b618f2e6cd29.jpg)  
Figure 8: Normalized subspace similarity between the singular directions of Wq and those of ∆Wq with varying r and a random baseline. ∆Wq amplifies directions that are important but not emphasized in W . ∆W with a larger r tends to pick up more directions that are already emphasized in W.