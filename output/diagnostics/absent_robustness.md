# Family-neutral absent rate — matching-strictness ladder

Absent = the gold answer is *not* recoverable from the parser's page output under the given matcher. If the OCR-parser gap were a same-family surface artifact it would vanish as the matcher loosens (L0 -> L4).

| Parser | L0_exact | L1_normalized | L2_numeric | L3_token_recall | L4_fuzzy_lcs |
|--------|:---:|:---:|:---:|:---:|:---:|
| Prod | 24.1% | 20.2% | 19.6% | 24.1% | 16.9% |
| Qwen3-VL-30B | 22.8% | 18.9% | 16.6% | 19.2% | 16.3% |
| Qwen3-VL-2B-base | 30.0% | 25.2% | 24.7% | 27.0% | 21.1% |
| MinerU | 74.8% | 70.4% | 68.0% | 73.0% | 68.6% |
| PaddleOCR | 67.0% | 62.7% | 62.0% | 59.9% | 60.5% |
| Marker | 90.6% | 90.0% | 90.0% | 89.0% | 89.6% |

## Absent gap vs Prod (percentage points)

| Parser | L0_exact | L1_normalized | L2_numeric | L3_token_recall | L4_fuzzy_lcs |
|--------|:---:|:---:|:---:|:---:|:---:|
| Qwen3-VL-30B | -1.4 | -1.4 | -3.0 | -5.0 | -0.6 |
| Qwen3-VL-2B-base | +5.9 | +5.0 | +5.1 | +2.9 | +4.2 |
| MinerU | +50.7 | +50.2 | +48.4 | +48.9 | +51.7 |
| PaddleOCR | +42.8 | +42.5 | +42.4 | +35.7 | +43.6 |
| Marker | +66.5 | +69.8 | +70.4 | +64.9 | +72.7 |

> If the gap in the rightmost column (L4_fuzzy_lcs) is still large and positive for MinerU/PaddleOCR, their absent answers are genuinely missing content, not a surface-form mismatch with the Prod (same-family) reference.