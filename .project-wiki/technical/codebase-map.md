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
| `src/sample_abstracts.py` | Distinct 90/10 multilingual and CPC-diverse sampling implementation (generation not confirmed) |
| `src/sample_random_100.py` | Fixed-seed uniform 100-family sampling from nonempty original-English abstracts; source-preserving outputs |
| `samples/random_100/` | Generated 100-family labeling/full/translation CSV/ZIP and native-English Kaggle input, with manifest |
| `samples/LABELING_PROMPT.md` | Independent abstract-only annotation protocol |
| `tests/` | Offline tests for sampling and translation |
| `kaggle/run.py` | One-command Kaggle launcher: discover translated CSV, check GPU, install dependencies, download pinned model, patch local BF16 loader to FP16 and execute inference in fresh Python subprocess |
| `kaggle/screen.py` | Native Perplexity Decider Flash v1.2 abstract-only inference, FP16 assertions, probability journaling |
| `kaggle/evaluate.py` | Manual-label evaluator: unresolved labels excluded; confusion matrix, specificity/FPR/Wilson CI; null positive-class metrics when 0 positives; case-level CSV |
| `kaggle/tests/test_run.py` | Synthetic/no-GPU launch preflight and dtype patch tests |
| `kaggle/tests/test_evaluate.py` | Synthetic evaluation tests for negative-only labels, unresolved cases and mismatched IDs |
| `kaggle/notebook_cells.py` | Minimal single-command Kaggle invocation |
| `kaggle/README.md` | Kaggle FP16 environment, input, auth, output and evaluation contract |
| `humanoid_patents.zip` | Existing tracked candidate corpus |
| `README.md` | Main data operations |
| `pyproject.toml` | Python >=3.12 metadata |
| `.gitignore` | Ignores secrets and outputs |

Run `python -m unittest discover -s tests -v` for existing offline tests and `python -m unittest discover -s kaggle/tests -v` for Kaggle launcher/evaluator tests. Kaggle live model execution and FP16 accuracy remain unverified. No full-corpus screening, landscaping, valuation or quadrant implementation is established.
