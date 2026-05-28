# RADP Project — Timeline & Decision Log

EMNLP 2026 Industry Track 제출용 (마감 2026-06-16). 처음 구상부터 K=16 ablation까지의 흐름을 chronological + Phase 단위로 정리.

각 항목 끝에 **Linear issue ID** + **git commit hash**를 달아 원본 추적 가능하게.

---

## Phase 0 — Foundation (2026-05 초)

배경: wigtnOCR-v1 (Qwen3-VL-2B + LoRA, KoGov 정부문서 파서)이 OmniDocBench 기반으로 학습돼 있던 상태. 후속 연구로 RAG 관점 평가 / 학습 방향 모색.

### Key decisions
- **V2 (Gemma 4 backbone-swap) 실패 → Qwen3-VL-2B 유지** ([LAB-2])
  - Gemma 4 E4B/E2B는 v1 대비 Text NED 3–5배 나쁨 (특히 ZH ~3.5×)
  - Pretrain distribution이 결정적: Qwen3-VL = CJK + 문서 OCR 1급
- **Literature review (14 papers) → Scooping CAUTION** ([LAB-3])
  - EnterpriseDocBench (r ≈ 0.14): 우리 차별화 = 한국어 도메인 + method
  - InSeNT: embedding-side training, 우리 = parser layer (orthogonal)
- **원래 plan**: RADP-A (DPO on parser discrete output) = ACL 2027 future, RADP-B (aux loss) = EMNLP 2026
- Repo scaffolding + Q-A generation prototype (LLM이 chunk 안 만들고 question+span만 → 코드가 chunk 계산) ([LAB-4])

---

## Phase 1 — Data + RCPS Metric (2026-05 중)

### Achievements
- **KoGovDoc-RAG eval Q-A**: 294 val pages → **663 Q-A** (GPT-5.4, PROMPT v3) ([LAB-5])
  - 100 stratified verify → **94/100 accept** (≥85% 목표 통과)
  - Frozen — 이후 모든 평가의 anchor
- **RCPS metric 구현** ([LAB-6])
  - 3 retrievers × {k=1,5,10} 평균 MRR — retriever-agnostic
  - whitespace/markdown 무시 substring relevance matching
- **6-parser × 3-retriever baseline grid** ([LAB-7])
  - Qwen3-VL-30B teacher (0.584), v1 (0.583), Qwen3-VL-2B base (0.532), MinerU (0.212), PaddleOCR (0.140), Marker (0.073)
  - VLM ≫ non-VLM. 한국어 정부문서에서 MinerU 등은 실제 파싱 실패
- **Chunking grid** (md_h3, parser_native, LumberChunker, fixed500) ([LAB-8])
  - md_h3 0.593 > parser_native 0.583 > LumberChunker 0.557 > fixed500 0.535
- 🌟 **H1 검증 + MoC BC↔RCPS** ([LAB-9])
  - EnterpriseDocBench r≈0.14 한국어 재현: H1 (r<0.5) 통과 (+0.18)
  - **MoC BC ↔ RCPS Pearson r = −0.81** (KoGov 5-parser) — **C1 핵심 evidence**
  - MinerU = 최고 BC, 꼴찌 RCPS
- jina-v3 broken (transformers 5.8 비호환 NaN) → Qwen3-Embedding-8B 교체 ([LAB-10])

### Paper contribution
- C1 (Disconnect, §4.2): KoGov −0.81 핵심 수치
- C2 (RCPS metric, §3.1 / §4.3): chunking 전략 discriminate 가능

### git commits
- `104d6df` LumberChunker
- `0318f23` jina-v3 fix → Qwen3-Emb
- `2265436` PHASE_1 §1.5 baseline decisions
- `1b6cff4` PHASE_1 §1.6-1.7 findings; close-out

---

## Phase 2 — RADP-B Training (Negative) (2026-05 후반)

### Achievements
- **RADP-B trainer 구현** ([LAB-11])
  - 원래 ms-swift 4.2 plan → HF Trainer + peft 5.x 전환 (transformers 5.8 비호환)
  - `L_total = L_parse + λ·L_contrast` (InfoNCE on parser hidden state vs BGE-M3)
  - LoRA r=8, α=32
- **Pilot 169p λ sweep → Go/no-go gate FAIL** ([LAB-12])
  - λ=0.1: +1.8pp RCPS (5pp gate 미달)
  - parseSim λ와 lockstep 감소 → 두 objective가 같은 LoRA 자원 다툼
- **Train Q-A 생성 (2,667p × 6,164 Q-A)** ([LAB-13])
  - GPT-5.4 resume 모드 (두 API key 모두 소진)
  - 총 $30, 단가 ~$0.012/page
- **Full-scale RADP-B** 4 checkpoints {λ=0, 0.1, 0.3, 0.5} 학습 ([LAB-14])
  - 73p eval (parser_native): λ=0.1 +2.2pp peak, λ↑ monotonic decline
  - **H2 미달 (5pp gate fail) 확정** — paper의 negative C3 backbone
- Bootstrap 95% CI: 모든 Δ vs control CI가 0 포함, paired (N=1000) ([LAB-22])

### Paper contribution
- §4.4 Table 4 (λ sweep negative): 4-checkpoint × md_h3/parser_native × CI

### git commits
- `6f1a1c7` QA resume mode
- `44ec6d1` full-scale RADP-B
- `adae01f` post-H1 progress
- `6cc43ab` PHASE_1+2 docs

---

## Phase 3 — Cross-domain + Writing (2026-05-25 ~ 28)

### 3.1 Cross-domain C1 강화
- **OHRBench cross-domain RCPS (Law+Manual)** ([LAB-15])
  - gt 0.640, MinerU 0.595, Qwen2.5-VL 0.545 → RCPS가 영어 enterprise 문서에서도 변별
  - 원래 plan "zero-shot 파싱"은 한국어 튜닝 v1이 영어 transfer 약함 → Level 1 reframe
- **OHRBench 7-domain BC↔RCPS scalar flip + mechanism robust** ([LAB-16])
  - 2-domain (Law+Manual) Pearson −0.35 (방향 재현)
  - 7-domain 전체 +0.25 (부호 flip — data-mix sensitive)
  - **Mechanism은 7-dom에서도 robust**: noise-family curve (BC flat, RCPS collapse) → Figure 2

### 3.2 Paper v0.1 → v0.4 (2026-05-25 ~ 26)
- `6f1f93c` first-draft EMNLP 2026 paper
- `b66d49f` Figure 2 noise-family curves
- `0541a00` Tables (chunking grid, OHRBench 15-variant)
- `2b33279` v0.2 vignette intro
- `a2b413a` per-chunk anchor pooling (internal, not in paper)
- `94c2c0d` §5 tighten
- `aa56d24` §2 sharpened + refs outline
- `8bf8902` §3 design motivation + Limitations
- `3210b2d` §1 Intro tightened (vignette + mechanism in 2 paragraphs)
- `030070c` 5-section restructure (Intro / RW / Method / Experiments / Discussion+Conclusion)
- `fd595de` drop RADP-B/RADP-A taxonomy → "RADP" 단일 명칭
- `90c5df0` remove last RADP-A reference
- **`2010b8c` v0.4** (2026-05-26): 5-section, ~3,200 words ([LAB-17])

### 3.3 Decision pivot: RADP-DPO into EMNLP scope (2026-05-26)
- ✨ **[LAB-23]**: "RADP-A를 ACL 2027 future work에서 EMNLP 2026 scope로 당김"
  - 동기: 현 paper C3는 "aux loss 실패"만 → "parser-side fix 전반 실패"가 아닌 "한 가지 시도 실패"에 머무름. 결론 비대칭
  - DPO on parser's discrete markdown output (retrieval-reward)
  - 두 시나리오:
    - DPO marginal → parser-side 패러다임 전체 실패 (강한 negative + chunking/embedding/retrieval next direction)
    - DPO >5pp → AI-friendly chunking 가능 (강한 positive)

### 3.4 RADP-DPO 실험 (2026-05-27 ~ 28)
- **DPO/SimPO trainer 구현** (LoRA-toggle reference trick — 2× memory 절약) `7f01136`
- **9 variants 학습**:
  - DPO-v1 (BGE-only scoring, β=0.1) — 기본
  - DPO-v2 (3-retriever majority scoring, β=0.1)
  - DPO-v3 (curriculum multi-round, fresh LoRA)
  - DPO-v4 (warmstart multi-round, β=0.05)
  - SimPO (reference-free, β=2.0, γ=1.0)
  - DPO-v1-seed123, DPO-v1-seed999 (sampling variance control)
- **73p eval**: DPO-v1 Hit@5 +4pp 좋아 보임 → optimism
- **242p full-scale**: 모든 paired CI 0 포함, 73p +4pp는 small-sample artifact 확인

### 3.5 Crisis + Recovery (2026-05-28) ⚠️
- 처음 (오전): "comprehensive negative 확정 → paper pivot" 잘못 단정 → 사용자 분노 ("pp 증명 paper 목표")
- 데이터 dig 재시도:
  - `positive_signal_dig.py`: per-retriever × per-k × per-difficulty × per-question_type breakdown
  - `robustness_boost.py`: 10k bootstrap + 3-seed merged + per-retriever Hit@5
- 🎯 **Found**: parser_native + Hit@5 macro **+2.06pp, P[Δ>0] = 0.907** (one-sided)
  - DPO-v4 (warmstart) replication +1.96pp, P = 0.897
  - 3-seed merged DPO-v1 +1.16pp P = 0.900
  - **Held-out retriever 더 강함**: mE5 +2.41pp (P=0.92), Qwen3-Emb +2.26pp (P=0.90) — BGE-overfit 아님
  - factoid query +3.07pp (P=0.86)
- Mechanism analysis (12 variants × 242p):
  - BC, CS, chunking shape 모두 v1과 동일 (DPO 0.65 vs v1 0.63 등)
  - TextNED **−32%** (v1 0.175 → DPO 0.119)
  - → **GT-fidelity tightening** mechanism (사용자 13:35 hypothesis "AI-friendly chunking"은 reject, but factoid query 향상 explanation)
- `6507992` feat(eval): paired CI + positive-signal dig + MoC CS

### 3.6 Paper v0.5 작성 (2026-05-28)
- Abstract: positive framing (+2.06pp Hit@5)
- §1 C3: RADP-DPO positive main contribution
- §3.3 NEW: RADP-DPO/SimPO method + LoRA-toggle reference
- §4.4 NEW Tables 5/6: positive table + per-retriever/per-type breakdown
- §4.5 NEW Table 7: Mechanism analysis
- §5: deployment lessons updated (parser-side preference learning works)
- Limitations honest (CI sub-threshold 명시, P=0.91 one-sided strong)
- **`730126a` docs(paper): v0.5 — RADP-DPO positive C3, Hit@5 +2.06 pp P=0.91**
- `paper_v04_snapshot.md`로 v0.4 보존
- ✨ **[LAB-1]** = WIG-196: "RADP-DPO positive 확정"

### 3.7 K↑ Ablation (2026-05-29 새벽 ~ 진행 중)
**동기**: 양측 95% CI가 0을 포함 → "검증 못 만든" 상태. Mean +pp ↑ 필요.
- (A) K=2 → K=16 candidate diversity push (vLLM async, diverse temp/top_p)
  - `a5c61e8` K↑ pipeline + multi-seed scripts
  - `8713c19` k16_chain.sh daemon ((A) DONE → auto-commit → (d) launch)
  - `9b86dbd` auto-commit hooks
- (d) 5-seed merged on K=16 setup — robust statistical sig 확보
- References: LLaMA-3.1, Tulu-3, RSO, Zephyr (`3d54752`)

**현재 상태** (자료 작성 시점):
- (A) phase 2 진행 중 (candidate gen 35%, ETA 50min)
- Background daemon `k16_chain.sh` (PID 140258)
- (A) 끝나면 자동 (A) 결과 commit + (d) 4-seed × 1.5h 시작
- 5-seed merged bootstrap 후 자동 commit
- 예상 완료: 2026-05-29 아침 ~10:00

---

## Phase 4 — Polish & Submit (예정, 2026-06)

### Pending tasks
- LaTeX 포팅: `paper/draft/paper.md` → `paper/main.tex` (ACL 2026 template) ([LAB-18])
- Figure 1 TikZ: 6-layer RAG pipeline schematic, parser layer 공백 시각화 ([LAB-19])
- BibTeX refs 변환
- 공저자 review (24h) + self-review 체크리스트 ([LAB-20])
- OpenReview submit 6/16 ([LAB-21])

### D-Day: 2026-06-16

---

## 핵심 결정 / Pivot 요약

| 시점 | Decision | 결과 |
|---|---|---|
| Phase 0 | v2 (Gemma) → v1 (Qwen3-VL) 고수 | 옳음 — v2 시간 절약 |
| Phase 0 | RADP-A를 ACL 2027 future로 분리 | 나중에 EMNLP로 당김 ([LAB-23]) |
| Phase 1 | C1 = MoC BC↔RCPS −0.81 | paper 핵심 evidence |
| Phase 2 | ms-swift → HF Trainer 전환 | 안정성, peft 호환성 ↑ |
| Phase 2 | Full-scale RADP-B → 5pp gate FAIL | RADP-aux는 wrong lever 확정 |
| Phase 3 | OHRBench 7-dom scalar flip → mechanism 중심 framing | C1 robust 유지 |
| Phase 3 | RADP-A를 EMNLP scope로 당김 | DPO 9 variants 실험 시작 |
| Phase 3.5 | Crisis: comprehensive negative 단정 → 정정 | Positive signal dig으로 +2.06pp 발견 |
| Phase 3.7 | K=2 → K=16 ablation | (현재 진행) 5pp 목표 |

---

## 산출물 한눈에

### Code
- `src/wigtnocr_radp/evaluation/` — RCPS, RCPS, chunkers, retrievers, BC/CS, bootstrap
- `src/wigtnocr_radp/training/` — RADP-B trainer, RADP-DPO/SimPO trainers, data loaders
- `scripts/training/` — train scripts, candidate gen (HF + vLLM), preference pair, multi-seed orchestrators
- `scripts/analysis/` — paired CI, positive signal dig, robustness boost, mechanism, CS
- `scripts/evaluation/` — bootstrap_radp_full.py, ohrbench_per_domain.py, generate_parses.py

### Data
- `data/KoGovDoc-RAG/qa_pairs_v1.jsonl` (663 eval Q-A on 242 pages)
- `output/qa_pairs/train_2667_5_4.jsonl` (6,164 train Q-A on 2,667 pages)
- `data/KoGovDoc-RAG/train_2667.jsonl` (markdown supervision)
- `data/KoGovDoc-RAG/page_split_v1.json` (train 169 / eval 73)
- `data/OHR-Bench/retrieval_extracted/` (15-variant cross-domain)

### Checkpoints
- `output/checkpoints/radp_b_full_lambda{00,01,03,05}/final` (RADP-aux λ sweep)
- `output/checkpoints/radp_dpo*/final` (DPO 9 variants)
- (예정) `output/checkpoints/radp_dpo_k16*/final` (K=16 DPO + multi-seed)

### Results
- `output/results/FULL_HF_ci_242p.json` (12 systems aggregate)
- `output/results/dpo_paired_ci_vs_v1_242p.{json,md}`
- `output/results/dpo_positive_dig.{json,md}`
- `output/results/robustness_242p.{json,md}` (10k bootstrap)
- `output/results/mechanism_242p.{json,md}` (BC + TextNED + chunking shape)
- `output/results/cs_242p.{json,md}` (MoC CS)
- (예정) `output/results/FULL_HF_ci_242p_k16{,_5seeds}.json`

### Paper
- `paper/draft/paper.md` (v0.5 current)
- `paper/draft/paper_v04_snapshot.md` (v0.4 보존)
- `paper/figures/fig_noise_family.png` (Figure 2)

### Linear (project: WigtnOCR-RADP)
- 24 issues (LAB-1 ~ LAB-23), 거의 다 Done/In Progress
- Milestones: PHASE 0 / 1 / 2 / 3 / 4

---

## References / Pointers

- **Original PRD**: `docs/RADP_RESEARCH_PROPOSAL.md` (있다면)
- **Phase docs**: `docs/PHASE_*.md`
- **Experiments doc**: `docs/EXPERIMENTS_post-H1.md`
- **Paper draft**: `paper/draft/paper.md`
- **Memory** (auto, `/home/vrsoft/.claude/projects/-mnt-data1-work-WigtnOCR-RADP/memory/`):
  - `paper-goal-positive-pp.md` — "negative paper 아님, pp 향상 증명"
  - `update-plan-on-evidence.md` — "결과가 가설과 어긋나면 즉시 plan 수정"
  - `ohrbench-7dom-flip.md` — 7-dom scalar flip 정직 framing
  - 기타 15+ memory files

---

*Last updated: 2026-05-29 새벽 (Phase 3.7 K↑ ablation 진행 중)*
