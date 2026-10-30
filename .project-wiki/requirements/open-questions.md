---
id: OPEN-QUESTIONS
type: note
status: active
title: Open Questions
created: '2026-10-29'
updated: '2026-10-30'
tags: []
related: []
source_paths: []
confidence: confirmed
---

# Open questions — 2026-10-30

- **OQ-001 (still open; partially implemented):** Which decision-model definition/prompt, acceptance threshold and evaluation procedure deliver defensible precision and recall? The FP16 Decider Flash Kaggle pilot has completed 100 English-family predictions on one T4; the negative-only evaluator is implemented. No confirmed positive cases exist, so positive-class behavior and threshold calibration are unverified. The independently provided AI-assisted labels for the 100 original-English random families contain 98 negatives, zero confirmed positives and 2 unresolved. A separately created 50/50 positive-enriched English challenge set with AI-authored provisional annotations is now available as one combined file `samples/humanoid_challenge_100/challenge_100_labeled.csv`, but it is not human-adjudicated or a representative prevalence sample. First FP16 Decider Flash inference on this challenge is now verified: 100 predictions, TP=50, TN=50, FP=FN=0 against AI-authored reference labels at threshold 0.5, with input hash matched. This is a development result, not independent human-ground-truth validity or representative deployment precision. Independent annotation verification and a distinct held-out calibration/test plan remain required before choosing a production threshold. A 2026-10-30 leakage/difficulty audit confirmed no direct label forwarding in the reviewed code, but found that a two-keyword baseline reaches 90% accuracy on the curated 50/50 benchmark; class selection and label dependence on humanoid terminology limit its discriminative validity. The earlier upload `predictions (1).csv` was from the random pilot, but a subsequent upload `predictions (2).csv` is conclusively from the challenge (input SHA matches). The 90/10 multilingual stratified benchmark remains separate.
- **OQ-002 (open):** The kickoff requires earliest *priority* year; `src/sql_queries.py` currently computes minimum `earliest_filing_year`. Correct before longitudinal analysis?
- **OQ-003 (open):** Has the private model endpoint demonstrated full-batch translation coverage and acceptable domain translation fidelity? Implementation and offline tests exist, but live evaluation is not established here.
- **OQ-004 (open):** What applicant name harmonization, future-value methodology, historical time split, and outcome baselines will be used?
