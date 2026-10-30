---
id: TECH-TESTING
type: technical
status: active
title: Testing
created: '2026-10-29'
updated: '2026-10-30'
tags: []
related: []
source_paths: []
confidence: confirmed
---

# Testing and evidence boundaries

`python -m unittest discover -s tests -v` exercises translation with mocked responses and sampling with synthetic data. Translation completeness requires a summary with `incomplete: 0`. The tests cannot establish private endpoint compatibility or translation fidelity.

`python -m unittest discover -s kaggle/tests -v` exercises local input resolution and exact-match FP16 native-loader patching without downloading weights. `python kaggle/run.py --check` preflights the translated input without model download.

**Not yet verified with Kaggle GPU:** Python/CUDA/requirements combination, pinned private Hugging Face snapshot access, precision compatibility, peak memory, throughput or decision quality. The FP16 patch is enforced by source check and downstream assertions but must be tested on an actual T4 or other GPU. The 100-family sample is deliberately stratified (90/10 English/non-English) and cannot be treated as production prevalence. Compare scores with independent manual labels; choose production thresholds on separate calibration/evaluation evidence.

Future verification: translation fidelity, source ZIP coverage, priority-year validation, duplicate family handling, temporally valid patent-score backtests, and reproducible sector figures.
