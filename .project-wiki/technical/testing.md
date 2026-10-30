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

**Unverified:** successful model initialization, peak GPU/T4 memory and precision compatibility, model predictions and calibration, translation endpoint/full-corpus coverage. The larger/model-comparison plan requires a separate positive-enriched sample and non-leaking calibration/test design.
