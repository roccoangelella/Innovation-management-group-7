## [2026-11-12] update | WLOG-20261112-001 | Reorganize canonical patent dataset directories

Changed: [status](../STATUS.md), [architecture](../technical/architecture.md), [deployment](../technical/deployment.md), [codebase map](../technical/codebase-map.md), [security](../technical/security.md), [constraints](../requirements/constraints.md), [current plan](../implementation/current-plan.md), [changelog](../changes/CHANGELOG.md), [data layout](../../data/README.md), [README](../../README.md), and the active repository scripts and workflows.

Summary: Retained the three nonredundant original/translated/filtered patent ZIP files and two provenance JSON files, moving them into `data/` stage folders without changing bytes or Git blob identities. Updated all active extract, translation, sampling, Kaggle notebook, and GitHub Actions references to new paths. Disabled automatic dual-T4 production launches on workflow code changes. Original corpus 237,538-family production and 3,116 provisional positives were verified by [Actions run 43191381227](https://github.com/roccoangelella/Innovation-management-group-7/actions/runs/43191381227) before relocation. The small sampling ZIP remains in `samples/random_100/`.

Questions: OQ-001 remains open for independent human review and threshold calibration.

## [2026-11-11] update | WLOG-20261111-006 | Fail-closed private checkpoint access retry

2026-11-11 23:40 CET — Resume retry diagnosis: original Actions run 43012383316 completed with durable checkpoint artifact 13872887675. Resume run 43071759641 recovered and strictly validated 128,533/237,538 unique predictions (worker counts 61,695 and 66,838; 109,005 remaining), including source/model/shard identity. Kaggle acknowledged PRIVATE dataset creation at roccoangelella/humanoid-production-resume-43012383316, then immediately returned HTTP 403 on dataset file listing; therefore no resumed Kaggle notebook was submitted. Replaced unsafe duplicate-create behavior with bounded read-only verification of the existing private dataset and fail-closed handling of persistent access errors. Original artifact remains retained; no rescore/retranslation authorized. Evidence: https://github.com/roccoangelella/Innovation-management-group-7/actions/runs/43071759641.

Changed: production workflow and project status/changelog/wiki audit. No source corpus, prediction journals, model revision or secret values changed.


## [2026-11-11] update | WLOG-20261111-005 | Queue-aware Kaggle dual-T4 restart

Changed: project status, deployment, plan, changelog, and production workflow.

Summary: Corrected direct Kaggle-to-W&B monitor passed offline tests, but corrected notebook submission failed because Kaggle had two active GPU batch slots occupied. Public cancellation endpoint returned HTTP 404/400 for IDs inferred from version numbers; no destructive deletion attempted. Added bounded retry (150 × 120 seconds, 355-minute job timeout) to GitHub Actions so the job can start when a GPU batch slot opens. Live metric confirmation must come from the separate W&B API verification job (nonzero cumulative analyzed-document count), not a mere notebook submission.


## [2026-11-11] update | WLOG-20261111-004 | Direct W&B progress counts from Kaggle

Changed: project status, technical architecture/deployment/testing, current plan, changelog, `kaggle/wandb_live.py`, `kaggle/verify_wandb_live.py`, `kaggle/tests/test_wandb_live.py`, `kaggle/production_kernel/production.ipynb`, `.github/workflows/kaggle_production.yml`, `.github/workflows/kaggle_wandb_tests.yml`, and `kaggle/PRODUCTION_WANDB.md`.

Summary: User explicitly required W&B to show the real analyzed-document count. The former GitHub Actions monitor could not access live Kaggle logs. Implemented direct W&B logging every 30 seconds by a Kaggle-side process reading each GPU's flushed JSONL prediction journal, exposing total/processed/remaining, per-GPU progress, speed, and provisional positives. The GitHub action provisions a temporary private Kaggle auth dataset from the W&B secret, attaches it without putting credentials in public files, verifies nonzero counts via W&B API, and deletes the private credential dataset at completion. Live inference and telemetry must still be validated.


## [2026-11-11] update | WLOG-20261111-003 | Repair Kaggle production startup and W&B monitor

Changed: status, technical deployment, changelog, production Kaggle notebook, W&B monitor, and production Actions workflow.

Summary: Initial production notebook verified 237,538 translated families but failed before inference due to an assumed private model mount path. W&B monitoring was pointed to the wrong Kaggle slug. Corrective changes use unique model manifest discovery, canonical URL extraction, and structured CLI log parsing. Evidence: GitHub Actions diagnostic run 42997636292. New production inference outcome not yet verified.

# Wiki audit — 2026-W46 (9 November–15 November 2026)

## [2026-11-10] update | WLOG-20261110-001 | Implement offline-tested two-T4 production screening

Changed: [status](../STATUS.md), [architecture](../technical/architecture.md), [codebase map](../technical/codebase-map.md), [testing](../technical/testing.md), [deployment](../technical/deployment.md), [current plan](../implementation/current-plan.md), [traceability](../traceability/code-map.md), [changelog](../changes/CHANGELOG.md), [registry](../REGISTRY.yml), and [audit index](INDEX.md); source additions `kaggle/production_run.py`, `kaggle/production.py`, `kaggle/tests/test_production.py`, `kaggle/tests/test_journal.py`, and `kaggle/PRODUCTION.md`, plus journal improvements in `kaggle/screen.py`.

Summary: The user authorized production engineering before the translated source becomes available. Implemented deterministic ID-based two-way sharding, independently CUDA-masked native FP16 workers, locked and resumable output directories, fail-closed complete-ID merge, full probability output, and metadata-preserving filtered ZIP with source/provenance SHA256. CPU synthetic tests cover input validation and subprocess orchestration. The live dual-T4 memory/throughput test and final source coverage are pending; production threshold calibration is unchanged.

Questions: OQ-001 remains open (relevance boundary and threshold calibration). The fully translated corpus has not yet been attached; require translator `incomplete=0` or an independently verified count before starting. Live two-T4 acceptance is a prerequisite before bulk filtering.

## [2026-11-10] update | WLOG-20261110-002 | Materialize translated dataset humanoid_patents_en.zip in repository root

Changed: [status](../STATUS.md), root dataset `humanoid_patents_en.zip`.

Summary: The user requested placing the translated dataset in the repository root and committing/pushing to main. Exported 236,513 completed patent families (232,636 original English + 3,877 translated abstracts replacing non-English text) into `humanoid_patents_en.csv` inside `humanoid_patents_en.zip` (70.69 MiB, SHA256 `9fd66c686e5e4019165029e0aaa00b7b26a47df54d30faac0148475c5f5ae06b`). Passed `kaggle.production.inspect_input` verification. 1,025 non-English abstracts remain pending in local translation journal.

## [2026-11-10] update | WLOG-20261110-003 | Complete partial English patent dataset through GitHub Actions

Changed: [status](../STATUS.md), [architecture](../technical/architecture.md), [deployment](../technical/deployment.md), [codebase map](../technical/codebase-map.md), [testing](../technical/testing.md), [current plan](../implementation/current-plan.md), [traceability](../traceability/code-map.md), [changelog](../changes/CHANGELOG.md), `src/complete_translation.py`, `tests/test_complete_translation.py`, `.github/workflows/translation_tests.yml`, `.github/workflows/complete_translation.yml`, and root `README.md`.

Summary: The user provided Actions secrets for Gemrouter and committed a partial English corpus. Implemented strict source-ID/metadata reconciliation before seeding the translator's journal, translating only missing nonempty abstracts and publishing a replacement single-CSV ZIP only after 100% eligible coverage with English `abstract` and `abstract_en`. Preserves original PATSTAT language metadata, source ZIP and successful partial seed on errors. GitHub Actions performs translation and publishes final ZIP plus public completion summary; secrets are not committed. Synthetic tests (5) passed. Live workflow outcome is separately auditable.

Questions: OQ-003 remains open for actual endpoint coverage, non-English translation fidelity and completed archive verification. OQ-001 remains open regarding relevance-screening calibration.

## [2026-11-10] update | WLOG-20261110-004 | Diagnose HTTP 429 and restore resumable translations

Changed: [status](../STATUS.md), [deployment](../technical/deployment.md), [testing](../technical/testing.md), [current plan](../implementation/current-plan.md), [changelog](../changes/CHANGELOG.md), `src/complete_translation.py`, `tests/test_complete_translation.py`, and `.github/workflows/complete_translation.yml`.

Summary: Inspected GitHub Actions run [42849164410](https://github.com/roccoangelella/Innovation-management-group-7/actions/runs/42849164410): `HTTP 429: rate or quota exhausted` interrupted Gemrouter after 256 newly translated abstracts, reaching 236,769 of 237,538 eligible, with 769 pending. The workflow failed before publication, preserved the original ZIP, and uploaded restart journal artifact 13781484888. Implemented fail-closed restoration of a journal-only artifact with source validation, reconstitution of the private manifest, dedicated offline tests, and a workflow separation between push-triggered restoration verification and user-dispatched API calls. The endpoint's quota reset is unknown; no claim of completed English corpus.

Questions: OQ-003 remains open for endpoint quota and translation fidelity. Publication remains contingent on successful completion and final data conservation checks.

## [2026-11-11] update | WLOG-20261111-001 | Start source-verified translation continuation

Changed: [status](../STATUS.md), [deployment](../technical/deployment.md), [changelog](../changes/CHANGELOG.md), `.github/workflows/complete_translation.yml`.

Summary: The user explicitly requested an API continuation after the prior HTTP 429. The already-validated GitHub Actions run 42857129812 supplies the source-verified recovery journal with 236,769 of 237,538 eligible DOCDB families completed. Implemented an exact commit-message-gated one-time push launch in the workflow and updated the default checkpoint ID. All ordinary push events retain no-API preflight semantics. Publication remains conditional on completed English coverage, provenance and source-hash checks. Quota availability and actual run outcome are to be verified through the resulting Actions log.

Questions: OQ-003 remains open for endpoint budget, translation completeness and independent domain fidelity.

## [2026-11-11] update | WLOG-20261111-002 | Production dual-T4 Kaggle + minimal W&B monitoring

Changed: [status](../STATUS.md), [deployment](../technical/deployment.md), [testing](../technical/testing.md), [traceability](../traceability/code-map.md), [changelog](../changes/CHANGELOG.md), new `kaggle/PRODUCTION_WANDB.md`, `kaggle/monitor_kaggle.py`, `kaggle/production_kernel/production.ipynb`, `.github/workflows/kaggle_production.yml`, and updated `kaggle/production.py` / `kaggle/production_run.py`.

Summary: After final translation completion, user authorized model predictions on all 237,538 eligible DOCDB family abstracts using Kaggle T4 ×2 with simple real-time W&B operational graphs. Implementation pins source and model versions, separates physical CUDA worker processes, records progress/throughput/GPU utilization and memory without patent text, and saves a restartable checkpoint at session expiry. Secure provisioning uses GitHub's private HF secret to mirror the restricted model to a private Kaggle dataset; W&B key remains only in GitHub Actions. Validation of live Kaggle model load and final merge is pending, and provisional 0.5 predictions are not externally adjudicated classification accuracy.

Questions: OQ-001 remains open on relevance boundary and human-reviewed calibration; OQ-003 remains open on independent translation fidelity. GPU quota, model access and throughput can only be verified from live run evidence.

## [2026-11-11] update | WLOG-20261111-006 | Fix Kaggle W&B ensurepip failure and resubmit

Changed: `kaggle/production_kernel/production.ipynb`, `.github/workflows/kaggle_production.yml`, `kaggle/tests/test_wandb_live.py`, `STATUS.md`, `technical/deployment.md`, `technical/testing.md`, `implementation/current-plan.md`, and `changes/CHANGELOG.md`.

Summary: Investigated failed production GitHub run 43002155460. Kaggle notebook staged source (237,538 eligible families) and private model, but Python3.13 `venv` failed internal `ensurepip` before any predictions. Independent W&B verification timed out with no nonzero analyzed count. Changed notebook to use monitor-only `pip --target` site packages and `PYTHONPATH`, avoiding venv; added regression coverage. Production restart and actual count confirmation must be independently checked from the new Actions and W&B runs.

Questions: Existing relevance-model calibration and translation fidelity questions remain open; telemetry startup is an implementation issue.

## [2026-11-11] update | WLOG-20261111-007 | Verify live W&B inference and current run progress

Changed: project status, technical deployment, changelog, and new .github/workflows/kaggle_progress_check.yml.

Evidence: Production run 43012383316 submit job passed and independent verify_wandb job completed successfully after reporting WANDB_DIRECT_COUNT=204/237538 at 11:37 UTC, URL https://forge.coreweave.com/wandb/rocchissimo936-none/humanoid-patent-filtering/runs/kd2vlyzi. Production monitor still active at that time; not proof of full screening. Added read-only W&B metric and Kaggle session status check to fetch a contemporaneous count without affecting the Kaggle execution.

## [2026-11-11] update | WLOG-20261111-002 | Recover dual-T4 checkpoint

**2026-11-11 — Production Kaggle checkpoint and continuation:** Original Actions run [43012383316](https://github.com/roccoangelella/Innovation-management-group-7/actions/runs/43012383316) ended successfully as an Actions workflow, but Kaggle `session_summary.json` explicitly reports **incomplete inference**: 128,533/237,538 families scored, 109,005 remaining, `resume_required=true`. The durable original [artifact 13872887675](https://github.com/roccoangelella/Innovation-management-group-7/actions/runs/43012383316/artifacts/13872887675) contains both journals (61,695 and 66,838 predictions), manifest and logs. Local inspection found 128,533 unique family IDs with no duplicates. The checkpoint manifest source SHA256 is `b7ce0a36f0b3e2778292bdfe10058eb81749b304b62ed6d965dfcc837103276c`, pinned model `perplexity-ai/pplx-decider-flash-v1.2`, revision `6d771ad7b5ecff5e93b8fc7b90d4c5ccc341954d`. Workflow continuation now downloads the original artifact, checks source SHA, regenerates deterministic shards, checks both worker metadata/shard hashes, IDs and predictions, and uploads only the checkpoint to a **private** Kaggle dataset without overwriting the original. A new dual-T4 notebook is launched only after verifying the original notebook is finished and private model is available. Full completion must still be confirmed from the next session's validated merge and W&B metrics; Actions success alone is insufficient.

