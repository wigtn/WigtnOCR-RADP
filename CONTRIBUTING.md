# Contributing to WigtnOCR-RADP

Thanks for your interest in **Retrieval-Aware Document Parsing (RADP)**. This is a
research repository targeting the EMNLP 2026 Industry Track; contributions that
sharpen the diagnostics, the RCPS metric, or the parser-side training experiments
are very welcome.

---

## Authors & Maintainers

This project is led by two **co-first authors** (equal contribution):

| Author | Email | CRediT roles |
|--------|-------|--------------|
| **Hyeong-seob Kim** (Harrison)\* — [@Hyeongseob91](https://github.com/Hyeongseob91) | harrison@wigtn.com | Conceptualization, Methodology, Project administration — research framing, RCPS metric & method design |
| **Sang-woo Son**\* | sangwoo@wigtn.com | Software, Validation, Investigation — implementation, full-scale experiments, evaluation |

> \* **Equal contribution (co-first authors).** Hyeong-seob Kim led the research design and
> methodology; Sang-woo Son led the implementation and experiments.

This work is the follow-up to **WigtnOCR v1** (Qwen3-VL-2B document parsing fine-tuning).

---

## Development setup

We use [`uv`](https://docs.astral.sh/uv/) for Python environments.

```bash
uv sync                       # install dependencies (+ extras: dev / eval / train / data)
cp .env.example .env          # set OPENAI_API_KEY etc.
```

Optional extras: `uv sync --extra eval` (RCPS/retrieval), `uv sync --extra train`
(RADP training), `uv sync --extra data` (HuggingFace datasets).

---

## Conventions

- **Python 3.11+.** Full type hints (params + return) on every function; module
  docstring on the first line of every `.py` file. Prefer the `typing` module
  (`Optional[X]`, `Union[X, Y]`).
- **Lint & format:** [Ruff](https://docs.astral.sh/ruff/) (lint + format) and
  `mypy --strict`. Both are enforced — run them before opening a PR.
- **Dependency direction:** `scripts/ → src/wigtnocr_radp/ → configs/` (no reverse deps).
- **Tests:** `pytest`, Given/When/Then structure, named `test_<behavior>_<condition>`.
  Every behavioral change ships with a test.
- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/) —
  `feat:`, `fix:`, `refactor:`, `chore:`, `docs:`. Code & commit messages in English.
- **Branches:** `feat/<feature>`, `fix/<bug>`, `refactor/<desc>`.

---

## Pull request checklist

Before requesting review, confirm:

- [ ] `ruff check .` passes
- [ ] `ruff format .` applied
- [ ] `mypy` clean (for changed modules)
- [ ] `uv run pytest` green
- [ ] New/changed functions have type hints + docstrings
- [ ] Experiment-affecting changes note the config and the RCPS/eval fold used

---

## Reproducing experiments

The evaluation surface is documented in [`docs/RESEARCH_DIRECTION.md`](docs/RESEARCH_DIRECTION.md)
and the per-task plans in [`docs/plans/`](docs/plans/). The frozen **KoGovDoc-RAG**
Q-A set and the RCPS reference implementation (`src/wigtnocr_radp/evaluation/`) are the
shared ground truth — please do not silently re-generate or re-split them.

---

## License

By contributing, you agree that your contributions are licensed under the
[MIT License](LICENSE).
