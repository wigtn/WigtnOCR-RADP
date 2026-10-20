<div align="center">

<img src="docs/assets/rcps-cover.png" width="100%" alt="RCPS，Retrieval-Conditional Parsing Score：依据检索效果而不是外观选择文档解析器。EMNLP 2026 Industry Track">

<br>
<br>

[English](README.md) | [한국어](README.ko.md) | [中文](README.cn.md)

# WigtnOCR-RADP

**RCPS 用于基于检索的选择，coverage 用于诊断，RADP 仅用于可选的解析器训练。**

[![EMNLP 2026](https://img.shields.io/badge/EMNLP_2026-Industry_Track_·_Accepted-4F46E5?style=for-the-badge)](#许可证与引用)
[![Paper](https://img.shields.io/badge/Paper-Camera--ready_PDF-B31B1B?style=for-the-badge&logo=adobeacrobatreader&logoColor=white)](output/pdf/EMNLP2026_Industry_384_camera_ready_final.pdf)
[![WIGTN Tech](https://img.shields.io/badge/WIGTN_Tech-RCPS_report-0F172A?style=for-the-badge)](https://tech.wigtn.com/rcps/)

[![Adapters](https://img.shields.io/badge/Adapters-RCPS--RADP_v1.0.0-181717?style=flat-square&logo=github)](https://github.com/wigtn/RCPS-RADP-Adapters/releases/tag/v1.0.0)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](pyproject.toml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue?style=flat-square)](LICENSE)

</div>

---

> ✅ **EMNLP 2026 Industry Track · 投稿 #384 · 已录用**
>
> 🖼️ OpenReview 目前记录为 **Accept (Poster)**。展示形式的分配目前是暂定的，仍有可能被安排为口头报告。
>
> 📄 标题：*Retrieval-Conditional Parsing Score (RCPS): Choosing Document Parsers by Retrieval, Not by Appearance* · [最终 camera-ready PDF](output/pdf/EMNLP2026_Industry_384_camera_ready_final.pdf)
>
> 📦 基于 [WigtnOCR v1](https://huggingface.co/Wigtn/Qwen3-VL-2B-WigtnOCR) + [KoGovDoc-Bench](https://huggingface.co/datasets/Wigtn/KoGovDoc-Bench)
>
> 🧭 [`docs/PAPER_READABILITY_REVIEW_AUDIT.md`](docs/PAPER_READABILITY_REVIEW_AUDIT.md)（camera-ready 审计） · 🗓️ [`docs/CAMERA_READY_PLAN.md`](docs/CAMERA_READY_PLAN.md)

---

## 概要

文档 RAG 从解析器输出中检索，但解析器往往是依据编辑距离或 Boundary Clarity（BC）等内在指标来选择的，而不是依据检索性能。**RCPS 则在一个固定的 held-out 检索 probe 上对解析器–分块器组合进行排序，无需训练**。由此得到的工作流程如下：

1. **用 RCPS 选择**。五种完整的解析器配置覆盖 **0.137–0.584 RCPS** 的范围。经审计的 MinerU-on 的 BC 高于 Prod（**0.713 vs 0.610**），但 Hit@1 低 **42.6 个点**（**0.123 vs 0.549；Prod 为其 4.47×**）。MinerU-off 仅作为提交版输出的诊断保留。
2. **用 coverage 诊断**。在 Prod 输出中，有 **20.2%** 的参考片段在分块前没有归一化后的精确匹配，而所有测试过的分块器切分的比例都不超过 **2.3%**。
3. **仅在必要时采取措施或训练**。对于 *absent* 片段，检查或更换解析器；对于 *split* 片段，调整重叠或分块方式。73 页的解析器训练试点未达到目标；在另一个审计后的 OHR 兼容性子集上，两个 RADP-DPO 检查点的 Hit@5 分别仅比 Prod 高 **+0.95** 和 **+1.15 个点**。
4. **重新评估变更后的配置**。如果 `P` 或 `C` 发生变化，在部署前用同一 RCPS 协议评估由此得到的语料。判定为 covered 的配置直接继续，无需冗余的重新评估。

各项分析的分母不能互换：

| 分析 | 评估框架 | 作用 |
|---|---|---|
| 解析器/分块器选择 | 663 个 Q–A，检索范围为 **294 页** | 242 个证据页 + 52 个不含 Q–A 的干扰页 |
| 训练/机制 | 同样的 663 个 Q–A，检索范围为 **242 页** | 仅含证据的页面 |
| 预先设定的试点 | **202 个 Q–A / 73 页** | held-out 训练门槛 |
| OHR 扰动 | **1,043 个 Law–Manual Q–A** | 来源对齐的跨领域诊断 |
| OHR 训练审计 | **2,036 个 Q–A / 六个领域** | 审计后的兼容性子集；并非完整的 v2 重跑 |

仓库目前包含：冻结的 **663-Q–A KoGovDoc-RAG probe**（其证据分布在 242 页中）、它的 169/73 证据页划分、可移植的 294 页源页面映射、RCPS 实现、部分结果产物，以及全部九个已评估的解析器训练适配器的公开发布版本。主选择实验额外加入 52 个不含 Q–A 的干扰页，构成 294 页的索引。完整 fresh-clone 重跑所需的源文档没有打包；其余所有发布缺口均列于下文。

<p align="center">
  <img src="paper/figures/fig_overview.png" width="100%" alt="RCPS 工作流程：从固定评估框架开始，经过候选生成、基于检索的选择、coverage 诊断、可选干预，直到部署">
</p>

*图 1. RCPS 工作流程*。一个固定的 294 页 / 663-Q–A 框架评估每一个解析器–分块器候选。RCPS 先选出暂定的 `P* + C*`；随后 coverage 区分 covered、absent 和 split 片段。任何变更过的解析器或分块器都会在最终部署前再次评估。（[矢量 PDF](paper/figures/fig_overview.pdf) · [可编辑 PPTX](paper/figures/fig_overview_camera_ready.pptx)）

---

## 动机：解析质量 ≠ 检索性能

在经审计的部署对比中，MinerU-on 的 BC 高于 Prod（**0.713 vs 0.610**），但 Hit@1 低得多（**0.123 vs 0.549**）。另行保留的提交版输出 MinerU-off 诊断的 BC 为 **0.716**，Hit@1 为 **0.197**。这些配置并不构成表格识别的因果消融；但合在一起，它们表明仅凭边界外观选择解析器存在实际运行风险。

OHR-Bench、EnterpriseDocBench 以及同期的 OCR-for-RAG 研究在英文和企业场景中报告了类似的不一致。我们的贡献是把这一观察转化为部署工作流程：**用 RCPS 选择，用 coverage 诊断，仅在必要时更换或训练，并重新评估变更后的配置**。据我们所知，此前没有工作将可复用的解析器选择协议与一种区分精确片段缺失和分块边界切分的诊断结合起来。

---

## 贡献

| | 贡献 | 主要结果 |
|---|---|---|
| **C1** | 解析↔检索的**脱节**。在对齐的英文 OHR-Bench 子集上，语义噪声扰动会降低检索性能，而 BC 保持稳定或呈非单调变化。 | 经审计的 294 页 BC↔RCPS **r = −0.74**（描述性）；MinerU-on 与 Prod 的 Hit@1 相差 **42.6 个点**（0.123→0.549；4.47×） |
| **C2** | **RCPS**：一种对检索器取平均、格式归一化、基于 held-out Q–A 的**协议**，无需训练即可选择解析器/分块器。 | 完整的 294 页解析器取值范围为 **0.137–0.584**；固定 Prod 时，四种分块器取值范围为 **0.535–0.593** |
| **C3** | 一种**不依赖检索器的 coverage 诊断**：将每个参考片段分类为 *已覆盖 / 跨块切分 / 在归一化解析器输出中缺失*；这是一条在任何检索器运行*之前*即可计算的规则。 | **20.2% 精确片段缺失**，在 8 种分块器间保持不变；split 最多变化至 2.3% ⇒ 先检查解析器输出 |
| **C4** | 解析器侧训练的一张**有边界的**结果图；试点未达到目标，检索奖励训练也无法与匹配的 Distill 对照区分开。 | 审计后六领域 OHR 兼容性子集上相对 Prod 的 Hit@5：**R2 +0.95 pp**、**R3 +1.15 pp**、**Distill +1.36 pp**（n=2,036） |

---

## 方法

### RCPS：Retrieval-Conditional Parsing Score（C2）

依据*下游检索*如何利用解析器的输出来为解析器打分，而不是依据输出看起来有多干净。RCPS **不是新的相似度函数**，而是用三项选择包装普通检索 MRR 的协议：**(i) 外在评估**（在 held-out Q–A probe 上打分，而不只看解析器文本），**(ii) 检索器平均**（在指定的嵌入模型上取平均），以及 **(iii) 格式归一化的相关性**（相关块必须来自源页面，并包含归一化后的答案片段）。

```
RCPS(P, C; D, R, K) = (1 / |R||K|) · Σ_{r∈R} Σ_{k∈K} MRR@k(r, C(P), D)
```

其中，`P` 是解析器，`C` 是分块器，`D` 是固定的 held-out Q–A probe。`R = {BGE-M3, multilingual-e5-large, Qwen3-Embedding-8B}`，`K = {1, 5, 10}`。当且仅当一个块的源页面与答案所在页面一致，并且在经过统一的空白字符与 Markdown 归一化后包含参考片段时，该块才是**相关的**。对每个查询，若第一个相关块出现在排名 `j ≤ k` 处，MRR@`k` 为 `1/j`；若前 `k` 个结果中没有相关块，则为零；随后对所有查询取平均。评估**无需训练**。参考实现：[`src/wigtnocr_radp/evaluation/`](src/wigtnocr_radp/evaluation/)。

<p align="center">
  <img src="paper/figures/fig_rcps_protocol.png" width="62%" alt="RCPS 协议：为每个解析器-分块器组合建立索引，检索固定的 probe，应用参考页面与归一化片段相关性规则，对 MRR 取平均，并对候选排序">
</p>

*图 2. RCPS 评估协议*。每个候选都使用相同的 probe、相同的检索器/检索深度设定，以及相同的参考页面加归一化片段相关性规则。RCPS 对标准 MRR 取平均，无需训练。（[矢量 PDF](paper/figures/fig_rcps_protocol.pdf)）

### Coverage 诊断：解析器 vs 分块器（C3）

RCPS 对解析器 + 分块器 + 检索器进行联合打分，因此低分本身并不能说明是*哪一*层出了问题。固定解析器输出、只改变分块器，将每个归一化后的参考片段分类为 **covered**、**split**（存在于解析后的页面输出中，但被切分到多个块中，因此有可能通过重叠恢复）或 **absent**（在归一化解析器输出中没有精确匹配，因此重新分块无法恢复该精确片段）。该诊断指出应当优先检查的层；absent 匹配既可能反映真实的内容遗漏，也可能只是表面形式不一致，需要逐例审查才能区分。代码：[`scripts/evaluation/coverage_diagnostic.py`](scripts/evaluation/coverage_diagnostic.py)。

<p align="center">
  <img src="paper/figures/fig_coverage.png" width="78%" alt="Coverage 诊断：分块前无匹配率为 20.2%，八种分块器的分块边界切分率为 0 到 2.3%">
</p>

*图 3. 固定 Prod 时的 coverage 诊断*。分块前的精确片段无匹配率保持在 **20.2%**；更换分块器只影响切分，在八种分块器中最高为 **2.3%**。（[矢量 PDF](paper/figures/fig_coverage.pdf)）

### 解析器侧训练：一项次要研究（C4）

当 coverage 诊断指向解析器输出时，我们测试了以下方法和对照。

- **RADP-aux** *（隐藏状态辅助损失，未达阈值）*。`L_total = L_parse + λ·L_contrast` 在解析器池化后的答案片段隐藏状态与冻结的 BGE-M3 嵌入之间使用 InfoNCE。它在 73 页试点上的最佳估计仍低于预先设定的成功标准。实际执行的参数扫描从 `Qwen/Qwen3-VL-2B-Instruct` 训练适配器，并将其应用于 Prod 进行评估；因此它与基于偏好的变体并不是同一基座模型下的比较。
- **RADP-DPO** *（离散输出的检索奖励 DPO）*。从生产解析器中采样 K 个解析结果，按页面内 BGE-M3 MRR（在 `k = {1, 5, 10}` 上取平均）为每个结果打分，组成偏好对，并以 **LoRA-toggle 参考模型**（`π_θ` = LoRA 开启，`π_ref` = LoRA 关闭）进行训练。候选池和负样本在 **R1 → R2 → R3** 中逐步扩展。原始 R2 执行日志确认了 `beta = 0.1`；其可移植的执行配置和源日志哈希记录在 [`docs/provenance/RADP_DPO_R2_EXECUTED_CONFIG.md`](docs/provenance/RADP_DPO_R2_EXECUTED_CONFIG.md) 中。完整的九个适配器发布清单以及原始/发布哈希记录在 [`checkpoint_release_manifest.json`](docs/provenance/checkpoint_release_manifest.json) 中。
- **RADP-Distill** *（基于保真度的对照）*。候选依据与参考 Markdown 的编辑距离排序，而不是依据页面内 BGE-M3 MRR 检索奖励。在对齐的 2,036-Q–A 框架上，其 Hit@5 相对 Prod 的差值为 **+1.36 pp**。Distill-minus-R2 与 Distill-minus-R3 的直接比较区间都包含零。
- **SimPO** *（无参考模型的对照）*。它在 242 页上的 Hit@5 点估计为负，但两个置信区间都跨过零；这些实验无法分离出是哪一种优化差异导致了该结果。

---

## 实验

### 实验设置

- **KoGovDoc-RAG 选择框架**：全部 **663 个 Q–A** 在 **294 页**（**229 KoGov + 65 arXiv**）中检索。答案出现在其中 242 页上；其余 52 页是不含 Q–A 的干扰页。Q–A 由 `gpt-5.4-2026-03-05` 生成；另一项 LLM 辅助检查接受了 94/100 个抽样对。这并不是对完整 probe 的人工验证。
- **KoGovDoc-RAG 训练框架**：DPO/SimPO 和机制分析使用同样的 663 个 Q–A，但只在 **242 个含证据的页面**中检索。预先设定的试点使用一个 held-out 的 **73 页 / 202-Q–A** 数据折。偏好数据来自另一个页面不重叠的 2,667 页 Prod 语料，其中有 6,164 个生成的 Q–A。
- **OHR-Bench 框架**：C1 使用 **1,043 个来源对齐的 Law–Manual Q–A**、三个基准输出，以及十二个相互依赖的扰动（三个格式类、九个语义类）；它们并不是 15 个独立的解析器。C4 使用另一个 **2,036-Q–A / 六领域兼容性子集**，其中排除了 223 条错位的旧版 `notes` 行，以及五个证据页不在当前解析器输出包中的 Q–A。两个框架都不能替代完整的 v2 重跑。
- **模型与评分**：**Prod** 是针对韩语文档解析微调的 Qwen3-VL-2B；训练变体使用 LoRA（r=8, α=32）。RCPS 对 3 个检索器 × 3 种检索深度取平均。除非另有说明，报告的不确定性均采用 Q–A 级配对百分位 bootstrap。

### C1：脱节现象（KoGovDoc-RAG 评估集）

下方的部署对比由拥有完整输出的五个候选组成。MinerU-on 是该对比中使用的、经过审计且启用表格处理的配置。

| 完整 294 页部署对比 | BC | CS | RCPS | Hit@1 |
|---|:---:|:---:|:---:|:---:|
| Qwen3-VL-30B（教师模型） | 0.623 | 3.38 | **0.584** | 0.545 |
| **Prod（本文，2B）** | 0.610 | 3.07 | 0.583 | **0.549** |
| Qwen3-VL-2B（基座） | 0.520 | 3.74 | 0.532 | 0.500 |
| PaddleOCR | — | 3.46 | 0.140 | 0.125 |
| MinerU-on | **0.713** | — | 0.137 | 0.123 |

Boundary Clarity 在四个完整的 294 页部署配置（Qwen3-VL-30B、Prod、Qwen3-VL-2B 和 MinerU-on）上有定义。它们的 BC–RCPS 相关系数为 **Pearson r = −0.74**。加入 Marker 的 38 页结果后为 **r = −0.83 (n = 5)**。两个估计都是描述性的；PaddleOCR 没有测得的 BC，而 Marker 不是完整输出的结果。

| 提交版/子集诊断 | 范围 | BC | CS | RCPS | Hit@1 |
|---|:---:|:---:|:---:|:---:|:---:|
| MinerU-off（提交版） | 294 页 | 0.716 | 2.81 | 0.212 | 0.197 |
| Marker | 38 页 | **0.717** | 3.41 | 0.073 | 0.068 |

MinerU-on 与 MinerU-off 的差异不只在表格处理上，因此它们的分数并不能估计表格识别的因果效应。BC 即 Boundary Clarity（越高越好）；CS 即 Chunk Stickiness（越低越好）。

<p align="center">
  <img src="paper/figures/fig_disconnect.png" width="100%" alt="Boundary Clarity 与 RCPS 的关系（采用经审计部署对比中的 MinerU-on），以及 MinerU-on 与 Prod 的 Hit at 1 差距">
</p>

*图 4. 解析质量可能导致检索候选排序错误*。子图 (a) 使用经审计的 294 页部署对比中的 MinerU-on；子图 (b) 在 Hit@1 上比较 MinerU-on 与 Prod。MinerU-off 仍是单独标注的提交版输出诊断，而不是表格识别的因果消融。（[矢量 PDF](paper/figures/fig_disconnect.pdf)）

### C1：对齐扰动诊断（跨领域，OHR-Bench）

在对齐的 Law–Manual 子集上，语义噪声会降低检索性能，而 BC 没有一致的响应。从无噪声到重度噪声，MinerU 的 RCPS 下降（**0.595 → 0.265**），而 BC 呈非单调变化（**0.657 → 0.631**）；Qwen2.5-VL 的 RCPS 下降（**0.545 → 0.497**），而 BC 保持在 **0.563** 附近。GOT 没有无噪声输出，但从轻度到重度噪声，其 RCPS 下降（**0.461 → 0.298**），而 BC 上升（**0.586 → 0.624**）。15 行汇总的相关系数为 **r = −0.35**；由于同一家族内的变体相互依赖，该值仅作描述性报告。这一受限子集并不能证明更广泛的领域通用性。

### C2：RCPS 对解析器和分块器排序

| 分块器 | RCPS | Hit@1 | MRR@10 |
|---|:---:|:---:|:---:|
| md-h3 | **0.593** | 0.556 | 0.613 |
| parser_native | 0.583 | 0.549 | 0.602 |
| LumberChunker | 0.557 | 0.514 | 0.580 |
| fixed500 | 0.535 | 0.491 | 0.560 |

*KoGov 分块网格（663 个 Q–A，Prod 输出，3 检索器 RCPS 平均）*。在提交版输出的汇总网格上（其中包含 MinerU-off，而不是单独的 MinerU-on 部署行），仓库中跟踪的审计发现：使用三检索器的**单一 MRR@10** 而不是 MRR@{1,5,10} 的平均值，仍能完整保持五个 294 页解析器和全部四个分块器的排序。相反，去掉检索器平均、只用 BGE-M3 会**颠倒排名第一的解析器**（Prod 第一；完整 RCPS 把 30B 教师模型排在第一）；除此之外，五个解析器的排名一致（**Kendall τ = 0.80**）。我们没有报告格式敏感性消融，因为重建它所需的已排序块列表没有被保存。部署检索器已确定时，使用该检索器；检索器尚未确定或候选几乎打平时，用多检索器平均作为对冲。RCPS 是一套可操作的协议，而不是换了名字的 MRR。

在另一项三解析器端到端检查中，Prod 同样获得最高的判定答案准确率（**72.5%**，MinerU-on 为 **23.8%**，PaddleOCR 为 **20.5%**）。排名较低的两者相对 RCPS 顺序颠倒，而且答案的生成和判定由同一个 GPT-5.4 检查点完成。因此，我们只把这一结果视为对首选的检查，而不是对完整排名的验证。

### C3：coverage 诊断区分输出缺失与分块边界

在 Prod 的输出上（294 页：**229 KoGov + 65 arXiv**；663 个 Q–A，**不使用检索器**），有 **134/663 (20.2%)** 的归一化参考片段在解析器输出中没有精确匹配，而最多只有 **15/663 (2.3%)** 被切分到多个块中。精确片段缺失率在全部八种分块器上保持不变，因此重新分块无法让这些情况变为精确片段覆盖。这一结果表明应在调整分块器之前先检查解析器输出；但它本身并不能说明答案语义完全缺失，而不是以不同的表面形式呈现。

我们还测试了标签的稳健性。GPT-5.4 将 Prod 中 **56%** 的精确匹配缺失案例重新归类为可恢复的表面形式差异，但这个评判模型与 GPT 系列的 Q–A 生成器并不独立。在另一个隐去解析器身份、分层抽取的 100 个 absent 案例样本中，两位作者在裁定前独立地在 81/100 个案例上达成一致（**κ = 0.615**）。裁定后，检索不可用率分别为：MinerU-on **42/50 (84.0%)**，Prod **12/30 (40.0%)**，PaddleOCR **19/20 (95.0%)**。由于抽样比例和 MinerU 配置不同，无法据此提出总体层面的复现结论。抽样清单、两份评分文件以及 19 个案例的裁定记录都已用仓库评分器独立复核。它们保存在仅限作者的审计包中；公开发布仅报告上述汇总结果。

### C4：解析器侧训练仍低于试点目标

在 held-out 的 73 页 / 202-Q–A 试点上，RADP-aux 和 RADP-DPO 都没有达到预先设定的目标：至少 5 个 RCPS 点，且 95% 置信区间的下界大于零。后来的一次 OHR 审计发现，原始结果混用了不同的基准版本。移除 223 条错位的旧版 `notes` 行，以及与一个缺失证据页相关的五个 Q–A 后，仓库中跟踪的数组得出如下严格的六领域兼容性结果：

| 相对 Prod 的 Δ（pp） | Hit@1 | Hit@5 | Hit@10 | MRR@10 | nDCG@5 |
|---|:---:|:---:|:---:|:---:|:---:|
| RADP-DPO R2（检索奖励） | +0.59 | +0.95 | +0.90 | +0.78 | +0.82 |
| RADP-DPO R3（难负样本） | +1.46 | +1.15 | +0.90 | +1.30 | +1.28 |
| RADP-Distill（编辑距离对照） | +0.98 | +1.36 | +1.47 | +1.12 | +1.16 |

*审计后的旧版兼容性子集，n=2,036，三检索器宏平均，1,000 次 Q–A 级配对 bootstrap 重采样（seed 42）。Hit@5 的 95% CI：R2 **[+0.33,+1.54]**，R3 **[+0.31,+2.05]**，Distill **[+0.43,+2.29]**。Distill−R2 为 **+0.41 pp [−0.43,+1.26]**，Distill−R3 为 **+0.21 pp [−0.61,+1.05]**。该子集是在版本审计之后定义的；它既不是原始的确证性分析，也不是完整的 OHR-Bench v2 评估。*

在探索性的 KoGov 数据折上（242 页，n = 663），RADP-DPO 各里程碑检查点的 Hit@5 达到 +1.96 到 +2.11 pp（P[Δ>0] ≈ 0.90；所有双侧区间都跨过零）。SimPO 的 Hit@5 点估计在 md-h3 下为 **−0.85 pp**，在 parser-native 分块下为 **−0.70 pp**；两个置信区间都跨过零。这一合并分析把 169 个开发证据页和 73 个 held-out 证据页合在一起，因此并不是新的独立 holdout。匹配的 OHR 比较并未表明基于检索奖励的偏好对选择优于基于编辑距离的偏好对选择。

### C4：现有测量无法确定训练机制

| 变体 | BC ↑ | TextNED ↓（相对参考） |
|---|:---:|:---:|
| Prod（参考） | 0.630 | 0.240 |
| RADP-DPO R2 | 0.647 | **0.163** |
| RADP-DPO R3 | — | 0.185 |
| RADP-aux λ=0.1 | 0.652 | 0.423 |

*部分 242 页机制测量结果。现有的 R1–R3 测量结果相对 Prod 都有更低的 TextNED 和为正的 Hit@5 点估计；精简表格展示了 R2 和 R3，但 TextNED 并未复现它们的检索排序。R3 的 BC 以及这些结构性指标的不确定性估计目前都不可用。这种同时出现是事后观察，并不能证明保真度或边界的变化导致了检索差异。*

---

## 部署指南

1. **用 RCPS 评估解析器，而不是只看内在指标**。Boundary Clarity 给出的候选排序可能不被下游检索器保持。在经审计的 MinerU-on–Prod 对比中，选择 Prod 对应于固定 KoGovDoc-RAG probe 上的 Hit@1 **0.123 → 0.549**；这是该候选池内的结果，并不是普适的效应量。*这是最具杠杆作用的结论。*
2. **先运行 coverage 诊断**。如果精确片段*缺失*占主导，检查对应的解析器输出，并在内容确实缺失时更换解析器；如果*切分*占主导，调整分块器或重叠。
3. **如果训练解析器，请在未动用过的子集上测量，并加入基于保真度的基线**。经审计的 DPO 检查点的 Hit@5 点估计比 Prod 高约一个点，但无法从当前的逐 QA 产物中恢复 Distill 比较。
4. **让结论紧扣现有证据**。目前的机制结果显示 DPO 与低于 Prod 的 TextNED 相关联；它们并不能确定因果机制，也不能证明存在按证据类型区分的优势。

---

## 仓库结构

```
.
├── configs/                  # 实验配置 (YAML)
├── src/wigtnocr_radp/
│   ├── qa_generation/        # Q-A 生成
│   ├── evaluation/           # RCPS, 分块器, 检索器, coverage, Boundary Clarity, bootstrap CI
│   └── training/             # RADP-aux (对比学习) · RADP-DPO · SimPO (LoRA-toggle ref)
├── scripts/
│   ├── training/             # 候选生成, 偏好对 / 编辑距离对, DPO/Distill/SimPO 流水线
│   ├── evaluation/           # baseline_grid, chunking_grid, coverage_diagnostic, rcps_protocol_ablation, OHR 链
│   └── figures/              # 论文图表生成脚本 (disconnect, coverage, RCPS protocol, noise family)
├── experiments/              # RADP-Distill 训练/评估工具
├── paper/                    # 冻结的投稿版 + camera-ready 工作版 LaTeX + 图表
├── data/KoGovDoc-RAG/        # 冻结的 663-Q–A probe + 169/73 证据页划分
├── docs/                     # RESEARCH_DIRECTION · TIMELINE · ROADMAP · plans/ · literature_review/
├── output/                   # 部分结果 JSON; 产物状态见下文
└── tests/
```

> **图源说明**：camera-ready 的规范资源为 `paper/figures/fig_overview.pdf`、`fig_rcps_protocol.pdf`、`fig_coverage.pdf` 和 `fig_disconnect.pdf`；本 README 中显示的 PNG 文件是它们的网页预览。图 1 的规范可编辑源文件是 `paper/figures/fig_overview_camera_ready.pptx`；其中 RCPS 标签为 C2，coverage 标签为 C3。

## 本地代码检查（Linux/WSL CUDA 环境）

```bash
uv sync --extra dev
uv run pytest
uv run python scripts/analysis/source_page_map.py --check data/KoGovDoc-RAG/source_page_map_v1.json
uv run python scripts/analysis/audit_mineru_output_release.py --check output/results/mineru_output_release_audit.json
uv run python scripts/analysis/audit_kogov_training_table.py --check output/results/kogov_training_table_10k_audit.json
uv run python scripts/evaluation/coverage_diagnostic.py --out_dir /tmp/rcps-coverage-check
```

这些命令假定使用 `pyproject.toml` 和 `uv.lock` 中写定的 Linux/WSL CUDA 12.8 依赖源；完整依赖集在干净 macOS/CPU 环境下的安装路径尚未打包或验证。`pytest` 运行仓库中跟踪的单元测试和对齐门控测试。coverage 计算本身只需 CPU。它默认使用的 `results/kogovdoc/v1_val/predictions/` 下的 Prod 输出和 663-Q–A probe 都已在仓库中跟踪。可移植的源页面映射支持清单检查，但 coverage 命令使用的私有训练格式文件 `data/KoGovDoc-Bench/val.jsonl` 含有参考转录文本，没有打包。因此该命令**并非 fresh-clone 即可完整运行**；它可以通过 `--parser_dir` 和 `--val_jsonl` 使用等价的本地输入。

这些命令并不能复现论文中的每一个实验。完整重跑仍依赖外部源文档、部分解析器输出、嵌入缓存和解析器运行环境。缺失的部分在下文中明确列出。

### 仅需 CPU 的产物与检查点验证

已发布的评估产物和九个 LoRA 适配器可以在没有 GPU 的干净 checkout 中进行审计：

```bash
RCPS_RELEASE_DIR="$(mktemp -d)"
curl -fL -o /tmp/RCPS-RADP-Adapters-v1.tar.gz \
  https://github.com/wigtn/RCPS-RADP-Adapters/releases/download/v1.0.0/RCPS-RADP-Adapters-v1.tar.gz
tar -xzf /tmp/RCPS-RADP-Adapters-v1.tar.gz -C "$RCPS_RELEASE_DIR"
python3 scripts/release/verify_camera_ready_artifacts.py \
  --checkpoint-dir "$RCPS_RELEASE_DIR"
```

发布压缩包的 SHA-256 为 `22b4a0d4f5560f4d7c31633a1c885bbe3568a2bef841bfd94bf2407c339f08c6`。确定性构建器、公开下载清单和纳入策略记录在 [`CHECKPOINT_RELEASE.md`](docs/provenance/CHECKPOINT_RELEASE.md) 中。

---

## 作者（按 OpenReview 与 camera-ready 顺序）

**WigtnOCR v1**（Qwen3-VL-2B 文档解析微调）的后续工作。

1. Sang-Woo Son
2. Hyeong-seob Kim
3. Hyeonsang Kim
4. Hyun-woo Cho
5. Jinmo Kim

作者名单及顺序与投稿时完全一致。Industry Track 主席已书面确认，可以在不改变该顺序的前提下将 Hyeong-seob Kim 指定为通讯作者。因此，camera-ready PDF 将共同单位列为 **WIGTN, Seoul, Republic of Korea**，并使用 ACL 模板中的 `Correspondence: harrison@wigtn.com` 一行。其他邮箱只会根据已确认的元数据添加。

---

## 产物与可复现性状态

### 当前仓库

- **KoGovDoc-RAG probe 文件**：663 个 Q–A，其证据分布在 **242 页**中，另附冻结的 169 开发 / 73 held-out 证据页划分。论文的选择框架将这 242 页与 52 个不含 Q–A 的干扰页一起建立索引（**294 页 = 229 KoGov + 65 arXiv**）；完整的源页面语料没有在此打包。可移植的 [`source-page map`](data/KoGovDoc-RAG/source_page_map_v1.json) 将每个 `val_####` ID 关联到其领域和仓库中跟踪的解析器输出文件名，且不暴露本机路径或参考转录文本。另有一个 LLM 辅助的 100 对 Q–A 质量检查样本及其 94/100 的汇总结果已在仓库中跟踪；样本中空白的 `verification` 字段并不是人工标注。
- **RCPS 参考实现**：[`src/wigtnocr_radp/evaluation/`](src/wigtnocr_radp/evaluation/)。
- **部分评估产物**：汇总的解析器/分块器网格、对齐的全网格与经审计训练的逐 Q–A 数组、coverage 与端到端诊断，以及 Prod、PaddleOCR、MinerU-on 和提交版输出 MinerU-off 运行的完整 294 页输出。恢复出的 off 输出通过确定性的 [`release audit`](output/results/mineru_output_release_audit.json) 与其汇总结果绑定；on/off 两次运行不被视为受控的表格识别消融。基于 10,000 次重采样的 [`KoGov training-table audit`](output/results/kogov_training_table_10k_audit.json) 从仓库中跟踪的 MRR 数组重建 Hit@5，并复现了 camera-ready 表 8 中的每一个数值。294 页全网格审计包括 [`fullgrid_perqa_294p.json`](output/results/fullgrid_perqa_294p.json) 以及固定种子的解析器/分块器 [`ranking-stability`](output/results/rank_stability_parser_rcps_294p.json) 结果。在 1,000 次 500-of-663 抽样中，Prod 在 100% 的抽样里都高于 Base 和所有 OCR 解析器；完整的分块器排序在 96.1% 的抽样中保持不变。原始匹配使 RCPS 降低 0.024–0.041，但不会改变任一候选池的排序。
- **对齐的 OHR 审计产物**：1,043-Q–A 的 Law–Manual C1 结果、对齐的 RADP-Distill 逐 Q–A 数组，以及严格的 2,036-Q–A 旧版兼容性子集的确定性推导。较早的七领域输出出于溯源目的仍保留在目录树中，并列于 [`MANIFEST.legacy-invalid.sha256`](output/results/MANIFEST.legacy-invalid.sha256)；它们不是有效的 camera-ready 证据。
- **人工检查汇总结果**：论文记录了隐去解析器身份的 100 个案例 absent 标签研究（κ = 0.615，原始一致 81/100，以及裁定后按解析器划分的比率）。底层的抽样、评分和裁定记录已经复核，并保存在仅限作者的审计包中。
- **解析器训练检查点**：全部九个已评估的 LoRA 适配器均已在 [`wigtn/RCPS-RADP-Adapters` 的 `v1.0.0` 发布版](https://github.com/wigtn/RCPS-RADP-Adapters/releases/tag/v1.0.0) 中公开。仓库中跟踪的 [`release manifest`](docs/provenance/checkpoint_release_manifest.json) 记录了源哈希与可移植哈希、训练/评估所用的基座模型以及实际执行的配置。该发布包含四种 RADP-aux 设置、RADP-DPO R1–R3、RADP-Distill 和 RADP-SimPO。
- **Camera-ready 图表资源**：图 1–4 以矢量 PDF 保存，并附有用于 README 的 PNG 预览；图 1 还包括其规范的可编辑 PPTX。编译后的论文已检查确认字体均已嵌入，且没有 Type 3 字体。
- **旧版指标隔离**：`output/baselines/correlation_v1.json` 仅作为 Phase-1 的历史产物保留，并标注为使用非 MoC 的边界定义；它不是 camera-ready 证据。

### Camera-ready 待补充：目前尚不可用

- Qwen3-VL-30B 和 Qwen3-VL-2B-base 的解析器输出，以及已发布解析器的精确重跑命令。
- 论文没有提出关于完整 OHR-Bench v2 的结论；未来的完整 v2 实验需要官方 v2 Q–A，以及重新运行解析器和检索。旧版的七领域 / combined-CI / OHR-TextNED 产物仍在隔离清单中单独存放。
- 完整的 BC/CS 机制数据以及对齐的不确定性估计。
- 原始偏好对文本和完整的原始训练日志。公开的检查点发布改为提供可移植的执行配置、已验证的适配器以及现有的结构化 trainer 状态。
- 一条可移植的 **fresh-clone 端到端复现路径**，包括外部数据、解析器输出、嵌入缓存、基座模型获取，以及去除依赖特定机器的运行时假设。

## 许可证与引用

仓库代码以 **Apache License 2.0** 发布。第三方数据集和模型资源保留其原有的许可证和条款。

```bibtex
@inproceedings{son2026rcps,
  title     = {Retrieval-Conditional Parsing Score (RCPS): Choosing Document Parsers by Retrieval, Not by Appearance},
  author    = {Son, Sang-Woo and Kim, Hyeong-seob and Kim, Hyeonsang and Cho, Hyun-woo and Kim, Jinmo},
  booktitle = {Proceedings of EMNLP 2026 (Industry Track)},
  year      = {2026},
  note      = {Accepted}
}
```
