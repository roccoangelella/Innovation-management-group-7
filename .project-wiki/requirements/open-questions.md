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

- **OQ-001 (still open; partially implemented):** Which decision-model definition/prompt, acceptance threshold and evaluation procedure deliver defensible precision and recall? The FP16 Decider Flash Kaggle pilot has completed 100 English-family predictions on one T4; the negative-only evaluator is implemented. No confirmed positive cases exist, so positive-class behavior and threshold calibration are unverified. The independently provided AI-assisted labels for the 100 original-English random families contain 98 negatives, zero confirmed positives and 2 unresolved. A separately created 50/50 positive-enriched English challenge set with AI-authored provisional annotations is now available under `samples/humanoid_challenge_100/`, but it is not human-adjudicated or a representative prevalence sample. Test it without tuning first; independent annotation verification and a distinct held-out calibration/test plan remain required before choosing a production threshold. The 90/10 multilingual stratified benchmark remains separate.
- **OQ-002 (open):** The kickoff requires earliest *priority* year; `src/sql_queries.py` currently computes minimum `earliest_filing_year`. Correct before longitudinal analysis?
- **OQ-003 (open):** Has the private model endpoint demonstrated full-batch translation coverage and acceptable domain translation fidelity? Implementation and offline tests exist, but live evaluation is not established here.
- **OQ-004 (open):** What applicant name harmonization, future-value methodology, historical time split, and outcome baselines will be used?
