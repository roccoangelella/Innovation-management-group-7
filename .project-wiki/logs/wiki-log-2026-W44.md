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

## [2026-10-30] update | WLOG-20261030-004 | Fix observed Kaggle TorchAudio CUDA mismatch

Changed: [status](../STATUS.md), [testing](../technical/testing.md), [deployment](../technical/deployment.md), [codebase map](../technical/codebase-map.md), and code files `kaggle/run.py`, `kaggle/tests/test_run.py`, `kaggle/README.md`.

Summary: User-supplied Kaggle log confirms successful input/label preflight, Tesla T4 and 9.10 GB native checkpoint download. Import failed prior to model initialization because torch (CUDA 13.0) and Kaggle torchaudio (CUDA 12.8) were incompatible, indirectly blocking Transformers AutoProcessor. Fixed launcher by uninstalling unused optional torchaudio after dependency install, then validating the AutoProcessor import in a fresh Python interpreter; added mocked install-order regression coverage. No live post-fix Kaggle GPU inference has yet been observed. OQ-001 remains open. Model and source sample are unchanged.

## [2026-10-30] update | WLOG-20261030-005 | Verify 100-case single-GPU Decider predictions

Changed: [status](../STATUS.md), [testing](../technical/testing.md), [current plan](../implementation/current-plan.md), and [open questions](../requirements/open-questions.md). User-supplied Kaggle predictions CSV contains 100/100 source family IDs and 100 finite probability values, all classified as not relevant at the exploratory threshold of 0.5 (maximum 0.43625). Of 98 AI-assisted negative annotations, 0 are falsely predicted positive; two cases are unresolved. Positive-case recall and precision cannot be measured. Single GPU use is intentional in `kaggle/screen.py` (`cuda:0`). A potential production two-T4 design entails one independent FP16 model replica per card, split inputs and ID-keyed output merge; no two-GPU implementation, throughput result, or memory benchmark has been verified. OQ-001 remains open.

## [2026-10-30] update | WLOG-20261030-006 | Build 50/50 humanoid challenge set

Changed: [status](../STATUS.md), [testing](../technical/testing.md), [code map](../technical/codebase-map.md), [deployment](../technical/deployment.md), [current plan](../implementation/current-plan.md), [questions](../requirements/open-questions.md), [traceability](../traceability/code-map.md); code paths `src/mine_challenge_candidates.py`, `src/assemble_humanoid_challenge.py`, `kaggle/run.py`; files `samples/humanoid_challenge_100/` and workflows `.github/workflows/mine_challenge_candidates.yml`, `.github/workflows/generate_humanoid_challenge.yml`, `.github/workflows/kaggle_offline_tests.yml`.

Summary: Mined 435 source-faithful English candidates excluding earlier 100, screened candidate abstracts and created new 100-case set with 50 provisional humanoid positives, 30 hard robotics negatives, 10 lexical decoys and 10 clear negatives. Candidate discovery used regex only to find cases; label reasons and source excerpts are stored separately. CI verified source fidelity, unique IDs, class balance and evidence substrings; `--challenge` launches separate Kaggle input/labels/output. The labels are AI-authored provisional judgments; neither human adjudication nor challenge inference has occurred. Positive enrichment and lexical selection can bias precision and make keyword shortcuts easier; OQ-001 remains open.

## [2026-10-30] update | WLOG-20261030-007 | Consolidate Kaggle challenge input and provisional labels

Changed: [status](../STATUS.md), [code map](../technical/codebase-map.md), [testing](../technical/testing.md), [deployment](../technical/deployment.md), [current plan](../implementation/current-plan.md), [open questions](../requirements/open-questions.md), [traceability](../traceability/code-map.md); source files `src/assemble_humanoid_challenge.py`, `kaggle/run.py`, `kaggle/screen.py`, `kaggle/tests/test_run.py`; GitHub workflows and `samples/humanoid_challenge_100/challenge_100_labeled.csv`.

Summary: User requested a single portable file with source abstracts and reference labels. Generated a 100-row combined CSV and added `--dataset PATH`; `--challenge` now uses the combined CSV for both model scoring and post-inference evaluation. Only the original English abstract enters the native decision model request; metadata and AI-provisional reference labels stay out of inference. Regression checks assert that changing labels does not affect model requests; the old two-file API remains supported. These labels are not independently adjudicated and challenge-model GPU results are pending. OQ-001 remains open.

## [2026-10-30] update | WLOG-20261030-008 | Audit apparent model accuracy and leakage

Changed: [status](../STATUS.md), [testing](../technical/testing.md), [open questions](../requirements/open-questions.md). Reviewed `kaggle/run.py`, `kaggle/screen.py`, `kaggle/evaluate.py`, and the committed combined challenge abstract/label CSV against the user-supplied `predictions (1).csv`. The uploaded results belong to the **earlier random 100**, not the challenge (all 100 old IDs; zero challenge IDs). No direct passing of labels, confidence, evidence or rationale into model requests was found: `screen.rows` extracts only ID and abstract and `make_request` sends only the abstract and fixed task. Offline label-mutation regression exists; full model training provenance cannot be guaranteed. A trivial two-keyword challenge baseline achieves TP=50/FP=10/TN=40/FN=0, or 90% accuracy, due to selection/annotation design. OQ-001 remains open: independent human adjudication, harder non-keyword positives, realistic sampling, and held-out evaluation are required.

## [2026-10-30] update | WLOG-20261030-009 | Verify perfect challenge score with validity caveats

Changed: [status](../STATUS.md), [testing](../technical/testing.md), [open questions](../requirements/open-questions.md), [changelog](../changes/CHANGELOG.md).

Summary: Inspected the user's second prediction CSV and two companion metadata/evaluation files. Unlike the previous upload, the new file has precisely the curated challenge's 100 distinct patent family IDs; manifest SHA-256 equals the repository-generated combined input checksum. The reported 50 TP, 50 TN, 0 FP, 0 FN, 100% accuracy/precision/recall/F1 at threshold 0.5 are numerically correct against assistant-authored provisional labels. Minimum positive probability 0.73607, maximum negative 0.49120; 10 terminology decoys all classified negative. Source-level audit indicates no direct passing of label columns into model inference, but the positive labels systematically contain humanoid terminology and a trivial two-word baseline reaches 90% accuracy. Do **not** treat this as independent human gold-label accuracy, a random-prevalence estimate, or a production-validated threshold. OQ-001 remains open.

## [2026-10-30] update | WLOG-20261030-010 | Create non-explicit-humanoid semantic challenge

Changed: [status](../STATUS.md), [testing](../technical/testing.md), [code map](../technical/codebase-map.md), [deployment](../technical/deployment.md), [plan](../implementation/current-plan.md), [open questions](../requirements/open-questions.md), [traceability](../traceability/code-map.md); `src/mine_implicit_humanoid_candidates.py`, `src/assemble_semantic_challenge.py`, `kaggle/run.py`, `kaggle/tests/test_run.py` and related workflows, `samples/semantic_challenge_100/` and Kaggle README.

Summary: Created a third sample disjoint from both prior 100s. Scanned original ZIP for 780 English candidates without whole-word `humanoid` or `anthropomorphic`, selected and assistant-provisionally labeled 40 biped/humanlike robotics positives and 60 hard negatives (especially wearable exoskeletons), and published an original-source faithful combined CSV, blind review CSV, manual-label CSV, audit and checksums. The generation CI verified class balance, exact language/source and absence of forbidden terms, and preflighted the Kaggle CLI. Baseline diagnostics demonstrate lingering lexical shortcuts: biped only yields 91%, biped excluding exoskeleton 94%. This is not a clean held-out semantic estimate; positive definition broadened relative to original model instructions. OQ-001 remains open; model inference and human adjudication pending.
