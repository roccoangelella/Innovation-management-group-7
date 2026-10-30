# Wiki audit — 2026-W44 (26 October–1 November 2026)

## [2026-10-29] scan | WLOG-20261029-001 | Establish repository knowledge baseline

Changed: [project](../PROJECT.md), [status](../STATUS.md), [architecture](../technical/architecture.md), [code map](../technical/codebase-map.md), [requirements](../requirements/product-brief.md), [constraints](../requirements/constraints.md), [questions](../requirements/open-questions.md), [plan](../implementation/current-plan.md), [scan](../implementation/scans/scan-20261029.md), [traceability](../traceability/code-map.md), [registry](../REGISTRY.yml), [index](../INDEX.md), `AGENTS.md`, `.github/copilot-instructions.md`.

Summary: Established project-wiki v1.6.1 structure. Preserved course requirements and separated confirmed code from planned relevance filtering and analytics. Outstanding: OQ-001–OQ-004.

- 2026-10-29: Added reproducible 90/10 stratified sampling script, synthetic tests and README procedure; real full-corpus sample generation remains pending.

## [2026-10-30] update | WLOG-20261030-001 | Add isolated Kaggle screening pilot

Changed: [current plan](../implementation/current-plan.md) and [code map](../technical/codebase-map.md) following creation of `kaggle/README.md`, `kaggle/screen.py`, `kaggle/evaluate.py` and `kaggle/notebook_cells.py`. Pilot uses native Decider Flash v1.2 and preserves per-family probabilities. Kaggle execution, manual labels and calibration are not complete; OQ-001 remains open.

## [2026-10-30] update | WLOG-20261030-002 | FP16 single-command Kaggle launch

Changed: [status](../STATUS.md), [code map](../technical/codebase-map.md), [testing](../technical/testing.md), [deployment](../technical/deployment.md), [plan](../implementation/current-plan.md), and [traceability](../traceability/code-map.md). Added `kaggle/run.py` to auto-discover translated sample, install model dependencies, download pinned checkpoint and patch only native CUDA dtype to FP16; `screen.py` asserts dtype. Added synthetic launcher tests. No Kaggle GPU inference has been executed or verified; OQ-001 remains open.

## [2026-10-30] update | WLOG-20261030-003 | Evaluate provisional English-only labels safely

Changed: [status](../STATUS.md), [testing](../technical/testing.md), [deployment](../technical/deployment.md), [code map](../technical/codebase-map.md), [plan](../implementation/current-plan.md), [open questions](../requirements/open-questions.md) and [traceability](../traceability/code-map.md). Source changes: `kaggle/evaluate.py`, `kaggle/run.py`, `kaggle/tests/test_evaluate.py`, `kaggle/README.md`. The supplied separate-chat labeling CSV has 100 IDs matching the committed uniform original-English sample, 98 provisional negative labels, 0 positives and 2 needs-review records. Evaluation now excludes unresolved records and does not present undefined positive-class metrics as zero; false positives/specificity and Wilson intervals are available after Kaggle prediction. OQ-001 remains open: positive-enriched, independently verified cases and threshold design still needed. GPU inference is not confirmed.
