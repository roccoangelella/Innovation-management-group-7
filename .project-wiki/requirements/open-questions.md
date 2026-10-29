---
id: OPEN-QUESTIONS
type: note
status: active
title: Open Questions
created: '2026-10-29'
updated: '2026-10-29'
tags: []
related: []
source_paths: []
confidence: confirmed
---

# Open questions — 2026-10-29

- **OQ-001 (open):** Which decision-model prompt/reference and calibration threshold achieve defensible precision/recall on the agreed 100-family stratified sample? No deployed screening model appears on `main`.
- **OQ-002 (open):** The kickoff requires earliest *priority* year; `src/sql_queries.py` currently computes minimum `earliest_filing_year`. Correct before longitudinal analysis?
- **OQ-003 (open):** Has the private model endpoint demonstrated full-batch translation coverage and acceptable domain translation fidelity? Implementation and offline tests exist, but live evaluation is not established here.
- **OQ-004 (open):** What applicant name harmonization, future-value methodology, historical time split, and outcome baselines will be used?
