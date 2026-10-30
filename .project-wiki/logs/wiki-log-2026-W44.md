# Wiki audit — 2026-W44 (26 October–1 November 2026)

## [2026-10-29] scan | WLOG-20261029-001 | Establish repository knowledge baseline

Changed: [project](../PROJECT.md), [status](../STATUS.md), [architecture](../technical/architecture.md), [code map](../technical/codebase-map.md), [requirements](../requirements/product-brief.md), [constraints](../requirements/constraints.md), [questions](../requirements/open-questions.md), [plan](../implementation/current-plan.md), [scan](../implementation/scans/scan-20261029.md), [traceability](../traceability/code-map.md), [registry](../REGISTRY.yml), [index](../INDEX.md), `AGENTS.md`, `.github/copilot-instructions.md`.

Summary: Established project-wiki v1.6.1 structure. Preserved course requirements and separated confirmed code from planned relevance filtering and analytics. Outstanding: OQ-001–OQ-004.

- 2026-10-29: Added reproducible 90/10 stratified sampling script, synthetic tests and README procedure; real full-corpus sample generation remains pending.

## [2026-10-30] update | WLOG-20261030-001 | Add isolated Kaggle screening pilot

Changed: [current plan](../implementation/current-plan.md) and [code map](../technical/codebase-map.md) following creation of `kaggle/README.md`, `kaggle/screen.py`, `kaggle/evaluate.py` and `kaggle/notebook_cells.py`. Pilot uses native Decider Flash v1.2 and preserves per-family probabilities. Kaggle execution, manual labels and calibration are not complete; OQ-001 remains open.
