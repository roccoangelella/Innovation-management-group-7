---
id: TECH-CODEBASE-MAP
type: technical
status: active
title: Codebase Map
created: '2026-10-29'
updated: '2026-10-30'
tags: []
related: []
source_paths: []
confidence: confirmed
---

# Repository map

| Path | Current responsibility |
| --- | --- |
| `src/sql_queries.py` | TIP/PATSTAT export using CPC prefixes; one CSV in ZIP |
| `src/translate_abstracts.py` | Whole-corpus translation, batch validation, journal, English CSV |
| `src/sample_abstracts.py` | Deterministic 100-family 90/10 evaluation sample |
| `tests/` | Offline tests for sampling and translation |
| `kaggle/run.py` | One-command Kaggle launcher: discover translated CSV, check GPU, install dependencies, download pinned model, patch local BF16 loader to FP16 and execute inference in fresh Python subprocess |
| `kaggle/screen.py` | Native Perplexity Decider Flash v1.2 abstract-only inference, FP16 assertions, probability journaling |
| `kaggle/evaluate.py` | Manual-label confusion matrix and exploratory metrics |
| `kaggle/tests/test_run.py` | Synthetic/no-GPU launch preflight and dtype patch tests |
| `kaggle/notebook_cells.py` | Minimal single-command Kaggle invocation |
| `kaggle/README.md` | Kaggle FP16 environment, input, auth, output and evaluation contract |
| `humanoid_patents.zip` | Existing tracked candidate corpus |
| `README.md` | Main data operations |
| `pyproject.toml` | Python >=3.12 metadata |
| `.gitignore` | Ignores secrets and outputs |

Run `python -m unittest discover -s tests -v` for existing offline tests and `python -m unittest discover -s kaggle/tests -v` for new launcher tests. Kaggle live model execution and FP16 accuracy remain unverified. No full-corpus screening, landscaping, valuation or quadrant implementation is established.
