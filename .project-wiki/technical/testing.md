---
id: TECH-TESTING
type: technical
status: active
title: Testing
created: '2026-10-29'
updated: '2026-10-29'
tags: []
related: []
source_paths: []
confidence: confirmed
---

# Testing and evidence boundaries

`python -m unittest discover -s tests -v` exercises translation with mocked responses; it cannot establish private endpoint compatibility, model accuracy, global throughput, or downstream relevance precision. Translation completeness is verified by the summary's `incomplete: 0`.

Future verification: fixed stratified 100-family evaluation, calibrated screening precision/recall, translation fidelity on non-English patent samples, source ZIP coverage, priority-year validation, duplicate-family handling, temporally valid patent-score backtests and reproducible sector figures.
