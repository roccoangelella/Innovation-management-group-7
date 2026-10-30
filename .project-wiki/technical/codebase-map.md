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
| `kaggle/screen.py` | Perplexity Decider Flash v1.2 inference on translated English abstracts, resumable unthresholded probabilities |
| `kaggle/evaluate.py` | Optional labeled-set confusion matrix and exploratory metrics |
| `kaggle/notebook_cells.py` | Kaggle setup/inference recipe; requires actual GPU/runtime verification |
| `kaggle/README.md` | Kaggle inputs, model installation, outputs, and evaluation scope |
| `humanoid_patents.zip` | Existing tracked, large candidate corpus |
| `README.md` | Main data operations |
| `pyproject.toml` | Python >=3.12 metadata |
| `.gitignore` | Ignores secrets and outputs |

Run `python -m unittest discover -s tests -v` for existing offline tests. Kaggle pilot has not yet been tested on Kaggle; its scores and calibration must not be represented as validated. No full-corpus production screening, landscaping, valuation or quadrant implementation is established.
