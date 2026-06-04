# Arm B — TextNED-DPO distillation baseline

**Purpose.** The decisive REVISE→ACCEPT experiment from the review consensus.
It isolates whether RADP-DPO's gain is just **edit-distance distillation** or a
genuine **retrieval-reward** effect, by running an arm that mirrors RADP-DPO in
every respect *except the selection signal*.

| | Arm A — RADP-DPO (R2/R3) | Arm B — TextNED-DPO (this experiment) |
|---|---|---|
| Candidate pool | `output/candidates/v1_k14_front.jsonl` (K=14, 37,338 cand / 2,667 pg) | **SAME** |
| K | 14 (R3) | **SAME** |
| Pair selection | chosen = argmax page-local RCPS, rejected = argmin RCPS | **chosen = argmin TextNED-vs-GT, rejected = argmax TextNED** |
| DPO loss | `RadpDPOTrainer`, LoRA-toggle reference | **SAME** |
| LoRA | r=8, α=32, all-linear, π_init=π_ref | **SAME** |
| β / lr / epochs / seed | 0.1 / 1e-5 / 2 / 42 | **SAME** |
| Eval | KoGov 242p/663-QA + OHR 2,264-QA, parser_native, 3-retriever macro, paired bootstrap | **SAME folds/cells** |

**TextNED** = character-level Levenshtein distance ÷ longer string
(`rapidfuzz.distance.Levenshtein.normalized_distance`), the same metric as paper
§4.5 (`scripts/analysis/ohr_text_ned.py`). Ground-truth markdown = the v1 train
assistant target (`messages[role=="assistant"].content` in
`data/KoGovDoc-RAG/train_2667.jsonl`).

> β note: the in-repo RADP-DPO recipe (K16 pipeline, add_dpo_seeds, v4) uses
> **β=0.1**, so the default here is 0.1 to keep Arm B a *controlled* swap. The
> review brief referenced β=0.05 — pass `--beta 0.05` to `train_arm_b.py` if you
> need that exact value, but then re-run Arm A at β=0.05 too for a fair head-to-head.

---

## Files

- `scripts/training/build_preference_pairs_textned.py` — CPU pair builder
  (mirror of `build_preference_pairs.py`, TextNED ranking). **No GPU, no recompute.**
- `experiments/arm_b_textned_distill/train_arm_b.py` — builds pairs (phase 1, CPU)
  then DPO-trains (phase 2, GPU) via the existing `scripts/training/train_radp_dpo.py`.
- `experiments/arm_b_textned_distill/eval_arm_b.sh` — KoGov + OHR eval via the
  existing harness (`generate_parses.py` + `bootstrap_radp_full.py`;
  vLLM-LoRA + `ohrbench_parse_only.py` + `ohrbench_v1dpo_full.py`).

## Run commands

```bash
cd /mnt/data1/work/WigtnOCR-RADP

# 1. Build TextNED preference pairs — CPU only, ~1-2 min for all 2,667 pages.
uv run python experiments/arm_b_textned_distill/train_arm_b.py --pairs_only
#   → output/preference/arm_b_textned_pairs.jsonl

# 2. DPO-train Arm B (mirrors RADP-DPO recipe). Needs 1 A100. ~1h.
CUDA_VISIBLE_DEVICES=1 uv run python experiments/arm_b_textned_distill/train_arm_b.py
#   → output/checkpoints/arm_b_textned/final
#   (or run steps 1+2 together by omitting --pairs_only)

# 3. Evaluate on BOTH folds (KoGov 242p + OHR 2,264-QA). Needs GPU + Docker/vLLM.
bash experiments/arm_b_textned_distill/eval_arm_b.sh
#   → output/results/arm_b_kogov_ci.json
#   → output/results/arm_b_ohr_ci.json
```

## Estimated compute

| Phase | Resource | Time |
|---|---|---|
| 1. Build pairs | CPU | ~1-2 min (verified on slice) |
| 2. DPO train (2 ep, ~1.5-2.5k pairs) | 1× A100 | ~1 h |
| 3a. KoGov regen (242 pg) | 1× A100 | ~30 min |
| 3b. KoGov bootstrap (3 retrievers) | 1× A100 | ~10 min |
| 3c. OHR parse (~4,040 pg, vLLM) | 1× A100 | ~40 min |
| 3d. OHR scoring (3 retrievers, n_boot=1000) | 1× A100 | ~1 h |
| **Total** | **1× A100** | **~2-3 GPU-day incl. seed reruns / retries** |

(Single end-to-end pass is ~3-4 h; the 2-3 GPU-day budget covers multi-seed
robustness reruns matching Arm A's 5-seed protocol if reviewers ask for it.)

## DECISION RULE (apply to **OHR-Bench Hit@5**, vs v1 baseline)

Let R2's reported RADP-DPO CI on OHR Hit@5 be **[+0.35, +1.43] pp**.

1. **If Arm B's Hit@5 gain over v1 lands within [+0.35, +1.43]** → the
   retrieval reward adds nothing over edit-distance distillation. **C3 must
   reframe RADP-DPO as a distillation method**, not a retrieval-reward method.
2. **If RADP-DPO exceeds Arm B with a paired Δ-CI (RADP-DPO − Arm B) that
   excludes 0** → the retrieval framing is saved: the retrieval reward delivers a
   gain that edit-distance distillation does not.
3. Otherwise (Arm B below the band, or inconclusive paired CI) → report as-is;
   the experiment is still informative about the source of the gain.

The eval harness already emits the head-to-head: `eval_arm_b.sh` scores
`v1, dpo_v4 (=RADP-DPO), arm_b` in the same bootstrap so the paired Δ-CI is
directly available in `arm_b_kogov_ci.json` / `arm_b_ohr_ci.json`.

## Verified status (architect + dry-run)

**RUNNABLE NOW (no GPU):**
- TextNED-target extraction — **VERIFIED**. GT markdown is the assistant message
  in `train_2667.jsonl`; all 2,667 train pages have GT, all 37,338 K=14
  candidates have GT coverage. No recompute needed (candidate markdowns are
  persisted in `v1_k14_front.jsonl`).
- Pair construction — **VERIFIED** end-to-end on a 700-candidate slice (49 pairs,
  correct chosen/rejected by min/max NED, gap filter working). Output loads
  cleanly as `DPOExample` objects in the real `DPOPreferenceDataset.from_jsonl`.
- All training/eval prerequisites present: training images, v1-merged base,
  RADP-DPO(v4) KoGov parses (242) and OHR parses (4,040) for the head-to-head.

**NEEDS GPU (not executed here, by instruction):**
- Phase 2 DPO training (1× A100).
- Phase 3 KoGov regen + bootstrap, OHR parse + scoring.

**Verified caveat / blocker:**
- OHR-Bench parsing for a LoRA adapter requires serving v1-merged **with the
  Arm-B LoRA** through vLLM (`--enable-lora --lora-modules arm_b=...`). This is
  the established pattern from `scripts/evaluation/ohr_v5_eval_chain.sh` and is
  wired into `eval_arm_b.sh`; it needs Docker + the `vllm/vllm-openai:nightly`
  image and a free GPU/port 8002. (See the note at
  `ohrbench_v1_dpo_eval.py:255` — base vLLM serves v1 only, LoRA variants need
  the LoRA-enabled server.)
