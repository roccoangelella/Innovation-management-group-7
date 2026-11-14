**2026-11-14 incremental batch preparation:** `data/new_humanoid_patents.zip` is committed and the distinct GemRouter → private Kaggle dual-T4 workflow has been prepared. Launch requires an explicit manual GitHub Actions dispatch; source overlap and offline checks run before API calls. Expected artifacts and source-bound recovery instructions: `kaggle/NOVEL_PRODUCTION.md`. A successful live run and human relevance validation remain outstanding. The historical 237,538-family run is unaffected.\n\n**2026-11-12 operational milestone:** English translation and full 237,538-family dual-T4 inference have been completed and independently checked. The 3,116 families retained at exploratory threshold 0.5 require independent human review. Full-corpus archives and provenance files were organized into `data/raw/`, `data/translated/`, and `data/filtered/` without altering their content. Immediate next work: relevance adjudication; applicant harmonization and sector/subfield landscape; present/future indicators and valuation. The earlier dated action items below record historical project states.

**2026-11-11 monitor recovery:** Latest Kaggle run 43002155460 failed *after* 237,538-family source and private checkpoint staging but *before* inference: Python3.13 `venv` failed `ensurepip`. The next run must use the pinned `wandb==0.31.0` pip `--target` monitor installation, retain two-GPU journal-based monitoring, pass offline notebook syntax/counter tests, and verify a nonzero W&B analyzed-document count via independent W&B API polling. If the notebook still fails at the next stage, use Kaggle execution traceback rather than assuming a working GPU/model.

**2026-11-11 queue-aware restart:** The direct-W&B code and tests are ready, but Kaggle denied the corrected batch GPU job while two sessions remained active. Retry is now automated in the Actions `submit` step, up to 150 attempts at 120-second intervals. Do not claim live labeled-document progress until W&B `documents/analyzed` > 0. The user can stop obsolete Kaggle batch sessions in Active Events to accelerate the launch; the automation does not delete kernels or guess cancellation IDs.

**2026-11-11 direct telemetry update:** 2026-11-11 — User requested direct real-time analyzed-document count in W&B. Prepared a Kaggle-private W&B credential path, 30-second journal-driven W&B client, synthetic tests, and a separate W&B API verification job that requires actual nonzero counts. Restart the current Kaggle kernel via the updated production GitHub workflow, then verify W&B chart updates at the forge.coreweave.com project, and retain each session's checkpoint. Do not infer success merely from kernel RUNNING status. Threshold calibration still pending.

---
id: CURRENT-PLAN
type: note
status: active
title: Current Plan
created: '2026-10-29'
updated: '2026-11-14'
tags: []
related: []
source_paths: []
confidence: confirmed
---

# Execution stages

1. **Implemented:** TIP/PATSTAT broad DOCDB-family candidate extraction including multilingual title/abstract metadata.
2. **Implemented in code; awaiting live verification:** resumable full-corpus abstract translation, independent of screening.
3. **Pilot sample generated:** uniform 100 original-English families from 232,636 eligible source abstracts committed in `samples/random_100/`; the earlier 90/10 multilingual stratified sampler (`src/sample_abstracts.py`) remains a separate path.
4. **Pilot launcher implemented and run on Kaggle:** `python kaggle/run.py` is the one-command Kaggle entrypoint after cloning, detecting the committed English sample and installing/downloading the pinned native Decider Flash v1.2 model. It patches one exact dtype assignment locally for FP16 on T4, and `screen.py` checks the resulting model dtype. Results journal probabilities, and `evaluate.py` can compare with independent manual labels. 100 native-English cases produced output on one T4 (all probabilities under 0.5). Quantitative performance on genuine positive humanoid patents and production throughput remain unverified.
5. **Provisional labels received:** 100 IDs match, 98 labeled negatives, zero positives, two unresolved. The evaluator now handles unresolved labels without failure and emits specificity/FPR, not unsupported recall/F1. **Next:** independently adjudicate labels, obtain a separate positive-enriched sample and design held-out calibration and testing. For the full corpus, benchmark two disjoint independent FP16 worker processes (one GPU/model copy each) against the existing single-GPU baseline before selecting parallelization; no two-GPU code is implemented yet.
6. **Curated challenge ready with a single labeled CSV:** `samples/humanoid_challenge_100/challenge_100_labeled.csv` contains a new disjoint 100-family English case-control benchmark, assistant-provisionally labeled 50 positive and 50 negative, with 10 lexical decoys and 30 close robotics negatives. GitHub generated/verified source-faithful inputs and labels. Run `python kaggle/run.py --challenge` next; the model gets only abstract text and the evaluator later reads labels from that same CSV. Review disagreements, independently adjudicate labels and preserve a separate held-out evaluation before tuning any threshold. No challenge inference has been recorded yet.
7. **New implicit semantic challenge ready:** `samples/semantic_challenge_100/semantic_100_labeled.csv` contains 100 newly selected English families (40 positive biped/humanlike robot technologies; 60 confusable negatives), with no `humanoid` or `anthropomorphic` whole-word cues. After independently reviewing provisional labels, run `python kaggle/run.py --semantic-challenge`, then inspect false negatives and definition mismatch. A biped + exclude-exoskeleton lexical baseline still yields 94% on this set, so avoid claims of semantic generalization. No model run yet.
8. **Later:** corrected temporal metadata, applicant normalization, sector landscape, present/future scores and no-leakage backtest, quadrant, recommendation, deck and pitch.

Deadline: 20 December 2026.

**Additional task-relevance stress test (implemented 2026-10-30):** `samples/humanoid_semantic_holdout_100/` contains 100 further original-English patent families labeled AI-provisionally 40 positive and 60 negative, with overt humanoid terms absent, 200 earlier IDs excluded, and independently saved blind-review file. Run `python kaggle/run.py --dataset samples/humanoid_semantic_holdout_100/semantic_holdout_100_labeled.csv --output /kaggle/working/semantic_holdout_100/predictions.csv` to evaluate model behavior, then analyze definition disagreements between biped-compatible tasks and the existing explicit-humanoid prompt. Do not use this purposive dataset to claim production accuracy or to pick a threshold without a separate held-out evaluation.


**2026-11-10 status:** The earlier planned independent dual-T4 native FP16 replicas are implemented as `kaggle/production_run.py` / `kaggle/production.py` with deterministic disjoint sharding, separate resumable journals and validated merged outputs. The translated full source has not been downloaded to Kaggle. Next release gates: verify translation `incomplete=0` and total family coverage, run representative concurrent two-T4 throughput/memory and interruption tests, persist outputs, and then launch the complete source. OQ-001 relevance-definition, human validation and threshold calibration remain open.


**2026-11-10 translated-data continuation:** The repository contains 236,513 completed English-abstract families and 1,025 eligible non-English families pending. `src/complete_translation.py` and GitHub Actions `complete_translation.yml` now reconstruct verified success from the partial ZIP, use the same private Gemrouter translation flow for missing abstracts, and publish the normalized English-only replacement ZIP with `humanoid_patents_en_summary.json` only if source-eligible coverage is complete. 1,286 source families lacking abstracts are excluded separately. First verify that the automated workflow succeeds and reports `incomplete=0`, then use the final dataset to benchmark dual-T4 production filtering. OQ-003 remains open on actual translation quality until audited.


**2026-11-10 quota incident:** First Gemrouter completion attempt processed 256 additional abstracts before HTTP 429, leaving 769 eligible abstracts pending. Checkpoint artifact retained. Recovered-journal validation and reconstruction are implemented with GitHub Actions download/restore and 30-day journal reupload. Next: verify the checkpoint restore CI, confirm Gemrouter quota is replenished, manually dispatch the workflow using latest saved journal ID, then validate and publish the complete English ZIP. Avoid unbounded or immediate 429 retries.
