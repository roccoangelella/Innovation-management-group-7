---
id: CONSTRAINTS
type: note
status: active
title: Constraints
created: '2026-10-29'
updated: '2026-10-29'
tags: []
related: []
source_paths: []
confidence: confirmed
---

# Constraints

- Globally sourced patents: do not exclude non-English titles or abstracts (project decisions, 28 October).
- Screen **abstracts** with a decision model; no fine-tuning; no deterministic content prefilter.
- Candidate export uses DOCDB-family identifiers. Validation by approximately 100 sampled families is requested in the course (slide 9).
- Earliest priority year is the intended analytical time variable; account for recent-publication and citation lags.
- Require reproducible query, cleaning, indicators, documentation, and tests (kickoff slide 18).
- Credentials belong in local `.env` and must not be committed.
- Do not treat an incomplete translation export as a complete corpus. Do not equate offline unit tests with a verified live endpoint run.
- Avoid adding further bulk PATSTAT extracts to Git; existing tracked `humanoid_patents.zip` predates this documentation change.
