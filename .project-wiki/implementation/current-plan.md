---
id: CURRENT-PLAN
type: note
status: active
title: Current Plan
created: '2026-10-29'
updated: '2026-10-30'
tags: []
related: []
source_paths: []
confidence: confirmed
---

# Execution stages

1. **Implemented:** TIP/PATSTAT broad DOCDB-family candidate extraction including multilingual title/abstract metadata.
2. **Implemented in code; awaiting live verification:** resumable full-corpus abstract translation, independent of screening.
3. **Implemented in code; generation and human annotation not verified:** deterministic 100-family sample (90 English, 10 non-English) from `src/sample_abstracts.py`; source translations and manual labels still required for evaluation.
4. **Pilot implemented; not executed on Kaggle:** `kaggle/screen.py` using Perplexity Decider Flash v1.2 native inference with untranslated metadata excluded, probabilities persisted, and `kaggle/evaluate.py` for 100-family manual-label assessment. Kaggle GPU/model download and performance are unverified; no production threshold has been calibrated.
5. **Next:** generate translated 100-family CSV, run Kaggle pilot, manually label cases, compare prompt variants and decide calibration/selection rule. Full-corpus production screening remains future work.
6. **Later:** corrected temporal metadata, applicant normalization, sector and competitor landscape, present/future scores and no-leakage backtest, quadrant, recommendation, deck and pitch.

The project deadline is 20 December 2026.
