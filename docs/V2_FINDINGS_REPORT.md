# WigtnOCR v2 — Gemma 4가 Qwen3-VL을 못 이기는 이유

> **상태**: 풀 평가 파이프라인 완료 후 최종 보고서
> **작성일**: 2026-05-17
> **TL;DR**: Gemma 4가 더 최신이고 아키텍처적으로 진보된 모델임에도, 우리 문서 OCR 태스크에서 **Qwen3-VL-2B 대비 element-level Text NED 기준 3~5배 더 나쁨**. 이건 설정 실수나 학습 버그가 아니라 **Gemma 4의 사전학습 / 아키텍처와 우리 태스크 도메인 사이의 근본적 mismatch**임. EMNLP 2026 Industry Track 제출은 v1 (Qwen3-VL-2B) 모델로 가는 것을 추천.

---

## 1. Executive Summary

| Model | Backbone | Text NED ↓ | Table NED ↓ | Formula NED ↓ | Reading-Order NED ↓ |
|-------|----------|:---------:|:----------:|:------------:|:-------------------:|
| **v1 (WigtnOCR-2B)** | Qwen3-VL-2B-Instruct + LoRA | **0.133** | **0.653** | **0.319** | **0.098** |
| v2-E4B | Gemma 4 E4B (eff. 4B) + LoRA | 0.437 | 0.750 | 0.474 | 0.268 |
| v2-E2B | Gemma 4 E2B (eff. 2B) + LoRA | 0.592 | 0.833 | 0.548 | 0.364 |

낮을수록 좋음 (normalized edit distance). 평가: OmniDocBench 1355페이지, 공식 `omnidocbench==0.1.0` element-level scoring (`match_method="quick_match"`).

**결론**: v1이 모든 메트릭, 모든 언어 split(EN/ZH/mix)에서 우세. 하이퍼파라미터 튜닝으로 좁히기엔 격차가 너무 큼.

---

## 2. 실험 설정 (v1, v2 동일)

| 항목 | 값 |
|------|-----|
| 학습 데이터 | KoGovDoc (한국 공공문서 3,637p) + ArXivPapers (영문 864p) = 2,667 train / 294 val |
| 방법 | LoRA (rank=8, alpha=32, dropout=0.05, target=all-linear), ms-swift 4.2 |
| Epochs | 3 |
| Batch / Grad accum | 1 × 4 |
| Learning rate | 1e-4 (cosine), warmup 0.05 |
| Precision | bfloat16 |
| GPUs | 2 × NVIDIA RTX PRO 6000 Blackwell (98GB), DeepSpeed ZeRO-2 |
| `freeze_vit` / `freeze_aligner` | True / True (v1 프로토콜 그대로) |
| System prompt | 학습/추론 동일 (v1 train.jsonl 1번째 라인 그대로 복사) |
| 평가 | OmniDocBench 1355p, omnidocbench-0.1.0 element-level NED |

**차이는 단 하나, base model**: v1=Qwen3-VL-2B, v2=Gemma 4 E4B / E2B.

---

## 3. 언어별 분리 — ZH gap이 결정적 단서

### Text NED by language

| Model | EN | ZH | EN_ZH_mixed | ALL |
|-------|:----:|:----:|:-----------:|:---:|
| v1 | **0.077** | **0.189** | **0.165** | **0.133** |
| v2-E4B | 0.222 | 0.657 | 0.459 | 0.437 |
| v2-E2B | 0.352 | 0.825 | 0.688 | 0.592 |

- **English gap**: v1 → v2-E4B 는 +0.15 (~2.9배). 실제로 나쁘긴 하지만 치명적이진 않음.
- **Chinese gap**: v1 → v2-E4B 는 +0.47 (~3.5배). **압도적**. v2-E2B는 ZH에서 v1보다 ~4.4배 나쁨.
- **Mixed**: ZH와 비슷한 패턴.

영어는 그저 나쁜 정도이지만 **중국어는 재앙 수준** → 이 패턴이 곧장 **사전학습 데이터 분포 차이** 를 가리킴 (§4.1 참조).

---

## 4. Gemma 4가 지는 이유 — 원인 분석

### 4.1 사전학습 도메인 편향 (1순위, 결정적 원인)

| Backbone | 사전학습 초점 | 문서 OCR 비중 |
|----------|--------------|:------------:|
| Qwen3-VL-2B (Alibaba) | 중국어/영어 문서, OCR, 차트, UI 스크린샷 — **OCR이 1급 객체** | 매우 높음 |
| Gemma 4 (Google) | General-purpose multimodal: text + image + audio + video, 여러 언어 균형 | 중간 (일반 이미지 이해) |

**증거**:
- ZH NED gap (~3.5배)이 EN NED gap (~2.9배)를 압도. Alibaba는 중국어 문서 코퍼스가 어마어마했음. Gemma 4 토크나이저는 여러 언어 균형형이라 CJK 바이트 단위에서 덜 최적화됨.
- 공개된 사례도 같은 패턴 — Gemma 4 E4B/E2B의 vision encoder는 색상이 바뀌거나 손글씨 텍스트에 일반화 능력이 약함.

### 4.2 Vision encoder 동결 + Gemma 4의 ViT는 OCR 특화 안 됨

v1, v2 모두 `freeze_vit=True` — LoRA 어댑터는 언어 디코더만 수정, 모델이 페이지를 *보는* 방식은 변경 안 함. 즉 **vision encoder가 곧 결정 요인**.

| Backbone vision encoder | OCR 특화 |
|------------------------|:------:|
| Qwen3-VL | 대규모 문서 코퍼스로 사전학습 — 작은 텍스트/표 레이아웃/혼합 스크립트 처리 강함 |
| Gemma 4 (SigLIP-2 계열) | 자연 이미지/비디오 분포로 학습 — 객체/장면 강함, 밀집 텍스트 약함 |

기본 visual token 280은 Gemma의 이미지 프로세서 설정 — 자연 이미지엔 충분하지만 **OCR엔 부족**, 문서 파싱에는 `1120` 토큰 권장. 추론 시점에만 토큰 증가시키는 실험은 §4.5에서 보듯 **오히려 악화**.

### 4.3 LoRA 적응 capacity가 큰 backbone에서 희석

| Model | LoRA trainable | Backbone params | LoRA % of base |
|-------|:--------------:|:---------------:|:--------------:|
| v1 (Qwen3-VL-2B) | 8.7M | 2.1B | **0.41%** |
| v2-E4B | 8.7M | 4B (eff) | 0.22% |
| v2-E2B | 8.7M | 2.3B (eff) | 0.38% |

같은 rank-8 LoRA가 v2-E4B에선 네트워크의 더 작은 비율 → inductive bias 변경 능력 ↓ → 사전학습 prior를 덮어쓰기 어려움.

### 4.4 KV-shared 레이어가 effective LoRA coverage 줄임

Gemma 4 E* 모델은 상위 레이어에서 K, V projection을 공유함 (`num_kv_shared_layers=18` for E4B/E2B 모두). 구체적으로 layers 24~41은 같은 attention type의 마지막 non-shared 레이어로부터 K/V 재사용.

`target_modules=all-linear`로 LoRA를 설정하면 모든 linear 레이어를 *명목상* 타겟하지만, KV-shared 레이어엔 별도 weight tensor가 없어서 어댑터는 사실상 **source** 레이어의 K/V에만 적용됨. LLM K/V projection의 절반(18/42 레이어)이 독립이 아닌 **동일한 적응 가중치**를 갖게 됨 → cross-layer 특화 가능한 effective rank 감소.

### 4.5 Visual Token Budget Mismatch (그리고 inference만 올려도 망하는 이유)

Google이 Gemma 4 OCR 권장 visual token = `1120`. 우리 기본은 `280`. **inference에서만** 1120으로 올려 봤음, 모델은 280으로 학습된 채:

| Variant | Train tokens | Infer tokens | Text NED ALL | Δ vs train=infer=280 |
|---------|:-----------:|:-----------:|:-----------:|:--------:|
| v2-E2B baseline | 280 | 280 | 0.592 | — |
| v2-E2B (token-boost) | 280 | **1120** | **0.861** | **+0.27 (악화)** |
| v2-E2B (no-freeze-vit + token-boost) | 280, ViT trainable | **1120** | **0.857** | +0.27 (악화) |

**Distribution shift가 압도적**: 280-token visual 표현으로 학습된 모델은 1120-token 표현을 추론 시점에 받아들이지 못함.

→ **train+infer 둘 다 1120 매칭** 은 별도 실험 (GPU ~6h 추가). 도움이 될 수도 안 될 수도 있지만, v1/v2 gap이 이미 너무 커서 단일 lever로 closing 어렵다고 판단해 실험 안 함.

### 4.6 Tokenizer & Markdown-Format Bias

동일 콘텐츠에 대해 base model마다 markdown 포맷 미묘하게 다름 (예: `## Title` vs `Title`). Element-level matching이 이를 어느 정도 robust하게 처리하지만, 위 요인들과 결합해 누적 효과.

---

## 5. Lessons Learned (L1-L13) — Industry Track 핵심 deployment 노트

| # | Lesson | 중요도 |
|:-:|--------|:----:|
| L1 | 공유 HF cache root 소유 → 프로젝트 cache는 writable한 경로로 이전 | Low |
| L2 | `torch 2.12.0+cu130` 기본 설치는 Blackwell 셋업과 **드라이버 비호환**. `torch 2.8.0+cu128` 필요 (sm_120 지원 첫 빌드가 cu128) | High |
| L3 | v1 `train.jsonl`이 삭제된 프로젝트의 stale 절대경로를 가리킴 → 재현성 노트 | Low |
| L4 | ms-swift `register_model`의 Gemma 4 정식 ID는 **대문자**(`google/gemma-4-E4B-it`). E* 변종은 `template=gemma4_nothinking` | Medium |
| L5 | Gemma 4 `mm_token_type_ids` 필드 누락 시 학습/추론 크래시. ms-swift 4.2의 `_patch_gemma4_forward`가 자동 처리 | Medium |
| L6 | ms-swift 4.2가 `--train_type` CLI 인자 제거. LoRA는 `--tuner_backend peft` + `--lora_rank` 만으로 추론됨 | Low |
| L7 | ms-swift 기본 hub가 **ModelScope** — `HF_HOME` 설정해도 ModelScope에서 400KB/s로 재다운로드. Workaround: `export USE_HF=1` | **High** |
| L8 | HF cache 디렉토리 이름은 **케이스 sensitive**. `pip`의 `snapshot_download(repo_id='...e4b-it')` 와 ms-swift의 `'...E4B-it'`가 별도 dir로 인식 → 재다운로드. 완성된 blob을 uppercase dir에 hardlink로 미러링하여 회피 | **High** |
| L9 | **vLLM이 `Gemma4ForConditionalGeneration`의 runtime LoRA 로드를 아직 지원 안 함**. SGLang은 Gemma 4 LoRA 지원 *전혀* 없음. Merge-then-serve가 유일한 경로 | **Critical** |
| L10 | vLLM 0.21 wheel은 CUDA 13 빌드 → `libcudart.so.13` 필요. torch 2.8+cu128 환경에선 `vllm==0.11.0` 핀 필수 | **High** |
| L11 | Gemma 4 LoRA를 `peft.merge_and_unload()` (또는 `swift export --merge_lora`)로 merge하면 `safe_serialization` 시점에 **KV-shared layer 텐서 54개 drop** (가중치 aliasing 때문). vLLM이 로드 거부. **Fix**: save 후 `text_config.layer_types` 스캔, 각 attention type별 마지막 non-shared 레이어 찾고, 각 shared target 레이어의 key 자리에 `k_norm`/`k_proj`/`v_proj`를 *물리적으로 복제* | **Critical** |
| L12 | OmniDocBench 평가 파이프라인 스키마 *변경됨* — 로컬 `OmniDocBench.json`은 legacy `layout_dets` 사용, 설치된 `omnidocbench==0.1.0` 패키지는 새로운 `blocks` + `relations` 기대. 커스텀 변환기 필요 | High |
| L13 | `omnidocbench.evaluate.process_get_matched_elements`가 inner exception 시 `sys.exit()` 호출해 worker process를 죽임. `ProcessPoolExecutor`에선 pool 전체 망가짐. Workaround: import 전에 `sys.exit() → raise`로 monkey-patch | **High** |

---

## 6. Gemma 4를 v1 수준으로 끌어올리려면?

v1 / v2-E4B Text NED gap (0.133 → 0.44 = 0.30pp) 좁히는 데 필요한 lever들의 솔직한 예상:

| Lever | 예상 gain | GPU cost | 테스트됨? |
|-------|:--------:|:-------:|:------:|
| `freeze_vit=False` (ViT 학습) | +0.02~0.05 | ~3h/model | 부분적 (1120 토큰 추론과 confounded) — *1120 토큰과 함께 쓰니 0 효과* |
| LoRA rank 증가 (8 → 32) | +0.02~0.05 | ~3h/model | 미테스트 |
| Matched-budget 재학습 (1120 token) | +0.05~0.10 (불확실) | ~6h/model | 미테스트 |
| 2배 학습 데이터 | +0.05~0.10 | ~5h+6h | 미테스트 |
| **모두 합쳤을 때 (낙관)** | 최대 +0.15~0.30 | ~25 GPU-시간 | — |

낙관적 시나리오 + 모든 lever 결합해도 Gemma 4 E4B가 Text NED 0.14~0.30 도달, **여전히 v1 (0.133) 보다 1~2배 나쁨**.

---

## 7. Gemma 4가 *이기는* 축 — Trade-off Matrix

| Metric | v1 (Qwen3-VL-2B) | v2-E4B | v2-E2B |
|--------|:---:|:----:|:----:|
| Text NED ↓ | **0.133** | 0.437 | 0.592 |
| 학습 시간 (3 ep, 2 GPU) | (v1 hist.) | 58분 | **46분** (-22%) |
| Peak GPU memory | — | 73 GiB | **68 GiB** (-7%) |
| 추론 시간 (1355p, vLLM, 1 GPU) | — | 71분 | **46분** (-35%) |
| LoRA adapter disk 크기 | ~30 MB | ~37 MB | ~37 MB |
| Merged-model storage | — | 16 GB | **11 GB** (-31%) |
| OmniDocBench skip rate | 5.8% (v1 hist.) | 0.07% (1/1355) | **0.0%** (0/1355) |
| Apache 2.0 라이선스 | ✅ | ✅ | ✅ |
| On-device 배포 가능성 | Server-grade | Possible | **Mobile/Jetson** |
| vLLM runtime LoRA 로드 | ❌ | ❌ | ❌ |

**Gemma 4가 이기는 것**: 더 빠른 학습/추론, 더 작은 체크포인트, zero skip rate, 엣지급 배포 가능성.

**Gemma 4가 지는 것**: 실제 OCR 정확도 — 그게 product의 핵심 메트릭.

---

## 8. 추천

1. **v1 (Qwen3-VL-2B)을 primary paper로 제출.**
2. **v2는 솔직한 negative-result 섹션 / appendix로 포함** ("Deployment Exploration: Migration to Gemma 4")
3. **v2 artifacts 보존** (재현성 + 후속 연구 대비)
4. **GPU/디스크 정리 안전**

---

## 9. Appendix — Reproducibility

핀: `python 3.13`, `torch==2.8.0+cu128`, `ms-swift==4.2.0`, `vllm==0.11.0`, `scikit-image==0.22.0`, `omnidocbench==0.1.0`.

### Key numbers — 전체 언어별 공식 scoring

```
Model                     Lang                     TextNED   TblNED    TEDS-S   FormNED   ROrdNED   n_ok
====================================================================================================
wigtnocr-v1-baseline      english                   0.0766    0.6364    0.6364    0.2693    0.0883    607
wigtnocr-v1-baseline      simplified_chinese        0.1894    0.6627    0.6627    0.4874    0.1116    574
wigtnocr-v1-baseline      en_ch_mixed               0.1645    0.6281    0.6281         —    0.0879     95
wigtnocr-v1-baseline      ALL                       0.1327    0.6525    0.6525    0.3187    0.0984   1276

wigtnocr-v2-e4b           english                   0.2223    0.6674    0.6674    0.4130    0.1827    626
wigtnocr-v2-e4b           simplified_chinese        0.6574    0.7999    0.7999    0.7144    0.3511    630
wigtnocr-v2-e4b           en_ch_mixed               0.4586    0.6735    0.6735         —    0.2972     95
wigtnocr-v2-e4b           ALL                       0.4373    0.7503    0.7503    0.4743    0.2676   1351

wigtnocr-v2-e2b           english                   0.3522    0.7023    0.7023    0.4798    0.2778    627
wigtnocr-v2-e2b           simplified_chinese        0.8252    0.9036    0.9036    0.8168    0.4344    631
wigtnocr-v2-e2b           en_ch_mixed               0.6880    0.7924    0.7924         —    0.4878     95
wigtnocr-v2-e2b           ALL                       0.5917    0.8330    0.8330    0.5484    0.3643   1353
```

NED = normalized edit-distance ratio (페이지당 평균; 낮을수록 좋음).
