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

- `python -m unittest discover -s tests -v`: offline tests for translation and source sampling.
- `python -m unittest discover -s kaggle/tests -v`: isolated tests for Kaggle input detection, native FP16 patch and evaluation. These cannot verify actual GPU behavior.
- `python kaggle/run.py --check`: verifies the chosen English-abstract input and optional attached label identifier set without downloading model weights.
- `python kaggle/run.py`: pilot inference; with a uniquely attached `humanoid_100_manual_labels.csv`, runs evaluation automatically. `python kaggle/evaluate.py --predictions ... --labels ...` evaluates existing predictions without GPU.

**Evidence (30 October 2026):** `samples/random_100/` contains 100 source-derived unmodified English abstracts. The supplied provisional annotation CSV has 98 negatives, **zero positives**, and 2 unresolved records (`93663023`, `24533336`). Its 100 IDs were checked against the stored source IDs with exact order. Unresolved rows must be excluded. On these labels, only false-positive behavior and specificity can be assessed, with sampling intervals; recall, precision, F1 and production threshold quality are not established. AI-assisted annotations require human adjudication.

**Observed Kaggle environment (2026-10-30):** T4 `cuda:0` with 14.6 GiB, 100 sample rows and 100 matching label IDs. Model checkpoint downloaded and reconstructed (9.10 GB). Model initialization failed *before inference* because torch 2.14.0/CUDA 13.0 and preinstalled torchaudio/CUDA 12.8 disagreed. See `kaggle/README.md`. `kaggle/run.py` now uninstalls optional torchaudio and preflights `transformers.AutoProcessor` in a fresh Python subprocess, with an offline mocked regression test under `kaggle/tests/test_run.py`. This repair has not yet been retested on a Kaggle GPU.

**Post-fix pilot evidence (2026-10-30):** user-supplied `predictions.csv` confirms successful output for all 100 matched English-family IDs, with no missing probabilities and all experimental `model_decision=0`. Mean probability 0.02950; maximum 0.43625 (`93663023`, unresolved). Conditional on the 98 provisional negative annotations, FP=0, TN=98, specificity=1.000 and 95% Wilson specificity interval approximately [0.9623, 1.000]. The two unresolved families are excluded. No positive annotations exist; positive-class precision/recall/F1 remain undefined. The model uses only `cuda:0`; multi-GPU implementation has NOT been benchmarked. This is not a production recall result.

**Unverified:** peak GPU/T4 memory utilization and total wall-clock throughput, positive-case precision/recall and calibration, translation endpoint/full-corpus coverage. The larger/model-comparison plan requires a separate positive-enriched sample and non-leaking calibration/test design.

## Curated challenge evaluation (2026-10-30)

The candidate miner (`src/mine_challenge_candidates.py`) searched 232,536 eligible original-English nonempty families not used in the first random sample: 1,735 explicit-terminology and 3,495 related-robotics candidate families (the rest generic or other). The assistant inspected original abstracts and wrote 50 provisional positive and 50 provisional negative labels independently of Decider predictions. The final set includes 30 hard robotics negatives, 10 lexical decoys, 10 clear negatives; positives cover locomotion, robot hands, perception, whole-body control and human-robot interaction. The original 100 families are excluded.

`src/assemble_humanoid_challenge.py` verifies selected IDs in the original source ZIP, exact English-abstract copies, label cardinality, and deterministic mixed order. GitHub Actions verified 100 matched unique label/input IDs, 50 per class, and evidence_quote as exact source substrings. The single-command `python kaggle/run.py --challenge --check` exercises the input/annotation handoff without GPU and is covered by CI.

**Validity caveat:** The purposive class balance and explicit-terminology discovery make the challenge non-representative and susceptible to lexical shortcuts. The set is useful for smoke tests and failure analysis, not for prevalence-dependent field precision. Labels remain AI-authored provisional judgments, not verified gold labels. If the team tunes prompts/thresholds after viewing challenge outcomes, it must use a different held-out set to report unbiased performance.

## Single labeled CSV isolation checks (2026-10-30)

The combined `challenge_100_labeled.csv` holds `docdb_family_id`, `abstract_en`, `label`, `needs_review`, `confidence`, `evidence_quote` and `reason`. `kaggle/run.py --challenge` uses the **same on-disk path** twice: `screen.py` extracts only ID/abstract for the model, and `evaluate.py` later reads labels and joins predictions by ID. A unit test changes the label and reason while holding the abstract fixed and asserts the model request is identical. The label is hidden from the model **request**, not from the file or process. CI generation checks combined-vs-split row equality, source-quote fidelity, and exact 100-row 50/50 counts. No new challenge GPU scores have been observed.
