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

## Leakage and benchmark-difficulty audit — 2026-10-30

Code inspection confirms `kaggle/run.py --challenge` reads the combined labeled CSV in two separate steps: `kaggle/screen.py:rows()` yields only `(docdb_family_id, abstract_en)`, and `make_request(abstract)` gives Perplexity only `state=abstract` plus the fixed humanoid question. Only after the inference subprocess completes does `kaggle/evaluate.py` read `label` and compare IDs. A prior offline regression test counterfactually changes `label` and `reason` while holding `abstract_en` fixed and confirms the model request is unchanged. This rules out a direct annotation-column pathway in reviewed source code, **not** possible pretraining contamination or unobserved runtime behavior.

**Important uploaded-file attribution:** user-provided `predictions (1).csv` contained 100 IDs **exactly matching the first uniform-random sample** and **zero matching the separate 50/50 challenge**; all 100 model decisions were 0, with maximum probability 0.4362465. It does **not** demonstrate performance on the newer challenge. For that test, use `/kaggle/working/challenge_100/predictions.csv` and its `evaluation.json`, with `run_metadata.json` input hash for attribution.

**Benchmark shortcut baseline calculated from 100 committed challenge abstract/label pairs:** classify positive if the case-insensitive abstract contains whole-word `humanoid` or `anthropomorphic`. This yields TP=50, FN=0, TN=40, FP=10; **90% accuracy**, **100% recall**, **83.3% precision**, and **80% specificity** without any language model. This is partly structural: the challenge generator requires positive cases to contain an explicit term, and selection deliberately enriched to 50 positives/50 negatives. Thus even excellent scores on this test cannot independently demonstrate semantic reasoning or field precision; a terminology-blind positive set, independent annotation, and held-out realistic-prevalence test remain needed. Keep the source-derived counts and interpretations separate from GPU model results (not yet observed on challenge).

## Verified 100-case challenge predictions (2026-10-30)

User-uploaded artifacts: `predictions (2).csv`, `evaluation (1).json`, `run_metadata.json` (not committed to source repo). `run_metadata.input_sha256` matches the previously committed `samples/humanoid_challenge_100/sample_summary.json.files.challenge_100_labeled.csv.sha256`: `dfb1a9593e479cd5b1f82c79973f3d54d75c6de831f9e23e5b3f8f8bf8e93005`. All 100 prediction DOCDB IDs match the 100 labels (no duplicates/omissions); both files use 50 positive and 50 negative provisional reference judgments. At the exploratory threshold 0.5, TP=50, TN=50, FP=0, FN=0. Precision, recall, specificity, F1 and observed accuracy = 1.0. The minimum positive probability is 0.7360694628 (`91185849`); maximum negative probability 0.4912025484 (`63001358`), giving a probability-score gap 0.2448669144. Each of 10 lexical-decoy negatives was rejected.

Interpretation is confined to the assistant-curated 50/50 challenge, whose labels were authored using source abstracts and were not independently human-adjudicated. Wilson 95% interval for a 50/50 class-specific 50/50 success rate (sensitivity or specificity) is roughly [0.9287, 1.000] **conditional on those 50 selected cases** and does not overcome the nonprobability selection bias. All positive labels contain humanoid/anthropomorphic wording; the two-word baseline reaches 90% accuracy (TP=50, TN=40, FP=10, FN=0). Reviewed source code provides no path from `label`, `reason`, `confidence` or `evidence_quote` into Decider's request, but cannot rule out dataset-construction shortcuts or model pretraining exposure. The sample is not a valid independent prevalence-weighted estimate of real-world precision or calibrated production performance. OQ-001 is still open.

## Implicit/bipedal semantic stress set (2026-10-30)

Built by `src/mine_implicit_humanoid_candidates.py` (780 source-derived English candidates excluding the previous 200 families, with whole-word explicit-humanoid terminology removed) and `src/assemble_semantic_challenge.py` (100 independently selected source families, 40 biped/humanlike robotics positives, 60 exoskeleton/quadruped/general robotics negatives). Included annotated CSV `samples/semantic_challenge_100/semantic_100_labeled.csv`, blind-review input, evidence audit, original source rows and SHA-256 manifest. The code excludes exact previous family IDs and verifies source content, language, label counts, and no forbidden exact terms. GitHub Actions completed source generation and `python kaggle/run.py --semantic-challenge --check` preflight. No Perplexity predictions on the new sample are available yet.

**Shortcut benchmark:** Case-insensitive `humanoid|anthropomorphic` returns only negatives (60% accuracy); simple `biped|bipedal|two-legged|two-footed` yields TP35/TN56/FP4/FN5 (91%); excluding `exoskeleton` gives TP34/TN60/FP0/FN6 (94%). The new benchmark thus changes the cue from explicit humanoid to biped vs exoskeleton, rather than eliminating lexical separability. The positive relevance policy is **broader than** the model's original instruction: it includes biped-specific inventions. Evaluation must distinguish incorrect model decisions from differing relevance definitions. All annotations are AI-assisted and await independent blind human adjudication. It is a development stress test, not an unbiased held-out production estimate.

## Additional keyword-blind task benchmark

`src/assemble_semantic_holdout.py` enumerates 100 reviewed family IDs, validates **exact** source-ZIP original English abstracts, absence of specified overt human-shape terms, class balance 40/60 and disjointness from both previous 100-family samples. `.github/workflows/generate_semantic_holdout.yml` ran the source generation and checked 100 unique IDs, exact source evidence substring, same-order blind-review file, and class counts. `kaggle/run.py --dataset` is the unchanged input path; the ground-truth label is only read by evaluation after `screen.rows` yields ID and abstract. Output directory: `/kaggle/working/semantic_holdout_100/`. On the AI-provisional annotations, fixed lexical rules reach 60% for `humanoid|anthropomorphic`, 81% for biped terms, and 86% after simple exclusions, so apparent improvements should be compared with these baselines and independently adjudicated. The positive construct includes biped-specific humanlike locomotion, broader than Decider's initial explicit-humanoid-link criterion. The stress test is purposive, not representative, and no inference on these 100 has yet been observed.
