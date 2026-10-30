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
| `src/mine_challenge_candidates.py` | Keyword-assisted recall into a candidate pool for *human-style review*, not automatic labels |
| `src/assemble_humanoid_challenge.py` | Source-faithful curated dataset generator producing a combined abstract-and-label CSV and legacy split CSVs, with annotation/ID checks |
| `samples/humanoid_challenge_100/` | Curated 50/50 English case-control challenge, one combined `challenge_100_labeled.csv` for scoring and evaluation, legacy split CSVs, evidence audit and provenance |
| `kaggle/run.py` | One-command Kaggle launcher (`--challenge` for committed single-CSV 50/50 challenge; `--dataset PATH` for external combined input): discover English CSV and labels, check GPU, download pinned model, install dependencies; remove mismatched unnecessary torchaudio; verify AutoProcessor import in fresh interpreter; patch native FP16 loader and execute inference |
| `kaggle/screen.py` | Native Perplexity Decider Flash v1.2 abstract-only inference: `rows` yields only ID/abstract and `make_request` sends only abstract text and fixed question; FP16 and journal checks |
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
