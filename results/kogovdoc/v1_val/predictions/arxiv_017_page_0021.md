## F ADDITIONAL EMPIRICAL EXPERIMENTS

### F.1 ADDITIONAL EXPERIMENTS ON GPT-2

We also repeat our experiment on DART (Nan et al., 2020) and WebNLG (Gardent et al., 2017) following the setup of Li & Liang (2021). The result is shown in Table 13. Similar to our result on E2E NLG Challenge, reported in Section 5, LoRA performs better than or at least on-par with prefix-based approaches given the same number of trainable parameters.

| Method | # Trainable Parameters | BLEU↑ | DART MET↑ | TER↓ |
|---|---|---|---|---|
| | | | | |
| GPT-2 Medium | | | | |
| Fine-Tune | 354M | 46.2 | **0.39** | **0.46** |
| Adapter$^L$ | 0.37M | 42.4 | 0.36 | 0.48 |
| Adapter$^L$ | 11M | 45.2 | 0.38 | **0.46** |
| FT$^{\text{Top}2}$ | 24M | 41.0 | 0.34 | 0.56 |
| PrefLayer | 0.35M | 46.4 | 0.38 | **0.46** |
| LoRA | 0.35M | **47.1$_{\pm 2}$** | **0.39** | **0.46** |
| | | | | |
| GPT-2 Large | | | | |
| Fine-Tune | 774M | 47.0 | **0.39** | 0.46 |
| Adapter$^L$ | 0.88M | 45.7$_{\pm 1}$ | 0.38 | 0.46 |
| Adapter$^L$ | 23M | 47.1$_{\pm 1}$ | **0.39** | **0.45** |
| PrefLayer | 0.77M | 46.7 | 0.38 | **0.45** |
| LoRA | 0.77M | **47.5$_{\pm 1}$** | **0.39** | **0.45** |

Table 13: GPT-2 with different adaptation methods on DART. The variances of MET and TER are less than 0.01 for all adaption approaches.

21