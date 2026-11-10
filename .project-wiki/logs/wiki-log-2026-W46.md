# Wiki audit — 2026-W46 (9 November–15 November 2026)

## [2026-11-10] update | WLOG-20261110-001 | Implement offline-tested two-T4 production screening

Changed: [status](../STATUS.md), [architecture](../technical/architecture.md), [codebase map](../technical/codebase-map.md), [testing](../technical/testing.md), [deployment](../technical/deployment.md), [current plan](../implementation/current-plan.md), [traceability](../traceability/code-map.md), [changelog](../changes/CHANGELOG.md), [registry](../REGISTRY.yml), and [audit index](INDEX.md); source additions `kaggle/production_run.py`, `kaggle/production.py`, `kaggle/tests/test_production.py`, `kaggle/tests/test_journal.py`, and `kaggle/PRODUCTION.md`, plus journal improvements in `kaggle/screen.py`.

Summary: The user authorized production engineering before the translated source becomes available. Implemented deterministic ID-based two-way sharding, independently CUDA-masked native FP16 workers, locked and resumable output directories, fail-closed complete-ID merge, full probability output, and metadata-preserving filtered ZIP with source/provenance SHA256. CPU synthetic tests cover input validation and subprocess orchestration. The live dual-T4 memory/throughput test and final source coverage are pending; production threshold calibration is unchanged.

Questions: OQ-001 remains open (relevance boundary and threshold calibration). The fully translated corpus has not yet been attached; require translator `incomplete=0` or an independently verified count before starting. Live two-T4 acceptance is a prerequisite before bulk filtering.

## [2026-11-10] update | WLOG-20261110-002 | Materialize translated dataset humanoid_patents_en.zip in repository root

Changed: [status](../STATUS.md), root dataset `humanoid_patents_en.zip`.

Summary: The user requested placing the translated dataset in the repository root and committing/pushing to main. Exported 236,513 completed patent families (232,636 original English + 3,877 translated abstracts replacing non-English text) into `humanoid_patents_en.csv` inside `humanoid_patents_en.zip` (70.69 MiB, SHA256 `9fd66c686e5e4019165029e0aaa00b7b26a47df54d30faac0148475c5f5ae06b`). Passed `kaggle.production.inspect_input` verification. 1,025 non-English abstracts remain pending in local translation journal.
