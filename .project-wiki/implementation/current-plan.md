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
3. **Pilot sample generated:** uniform 100 original-English families from 232,636 eligible source abstracts committed in `samples/random_100/`; the earlier 90/10 multilingual stratified sampler (`src/sample_abstracts.py`) remains a separate path.
4. **Pilot launcher implemented, not executed on Kaggle:** `python kaggle/run.py` is the one-command Kaggle entrypoint after cloning, detecting the committed English sample and installing/downloading the pinned native Decider Flash v1.2 model. It patches one exact dtype assignment locally for FP16 on T4, and `screen.py` checks the resulting model dtype. Results journal probabilities, and `evaluate.py` can compare with independent manual labels. FP16 runtime compatibility and model accuracy remain unverified.
5. **Provisional labels received:** 100 IDs match, 98 labeled negatives, zero positives, two unresolved. The evaluator now handles unresolved labels without failure and emits specificity/FPR, not unsupported recall/F1. **Next:** run the Kaggle GPU pilot, independently adjudicate labels, obtain a separate positive-enriched sample and design held-out calibration and testing.
6. **Later:** corrected temporal metadata, applicant normalization, sector landscape, present/future scores and no-leakage backtest, quadrant, recommendation, deck and pitch.

Deadline: 20 December 2026.
