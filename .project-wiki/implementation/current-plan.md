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
3. **Implemented in code; generation and human annotation not verified:** deterministic 100-family sample (90 English, 10 non-English), `src/sample_abstracts.py`.
4. **Pilot launcher implemented, not executed on Kaggle:** `python kaggle/run.py` is the one-command Kaggle entrypoint after cloning, detecting attached translated CSV and installing/downloading the pinned native Decider Flash v1.2 model. It patches one exact dtype assignment locally for FP16 on T4, and `screen.py` checks the resulting model dtype. Results journal probabilities, and `evaluate.py` can compare with independent manual labels. FP16 runtime compatibility and model accuracy remain unverified.
5. **Next:** generate translated 100-family CSV; run Kaggle GPU pilot; human-label cases; inspect precision, recall, prompt variants and errors; choose calibration/production threshold through explicit held-out strategy.
6. **Later:** corrected temporal metadata, applicant normalization, sector landscape, present/future scores and no-leakage backtest, quadrant, recommendation, deck and pitch.

Deadline: 20 December 2026.
