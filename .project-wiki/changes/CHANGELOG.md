# CHANGELOG

2026-10-29 — Documentation baseline: project wiki created; application code unchanged.

2026-10-30 — Integrated provisional English-only random-sample label comparison into Kaggle pilot; unresolved labels excluded and zero-positive evaluation limitations documented. Live Kaggle inference not yet verified.

2026-10-30 — Kaggle FP16 pilot: repaired TorchAudio CUDA mismatch blocking Transformers AutoProcessor, added dependency preflight and regression test; Kaggle GPU rerun remains pending.

2026-10-30 — User-supplied Kaggle predictions verify a completed 100-family single-T4 pilot after the dependency fix. No positives in the provisional labels; production two-T4 data parallelism is a proposed throughput optimization, not implemented or benchmarked.

2026-10-30 — Created separate source-faithful 100-family, English-only 50/50 relevance challenge with assistant-authored provisional labels, 30 hard robotics negatives, 10 lexical decoys and 10 clear negatives. Added reproducible generator, GitHub Actions validation, and isolated Kaggle `--challenge` run; human adjudication and model inference pending.

2026-10-30 — Consolidated curated 100-family challenge into one source-faithful labeled CSV with `--dataset` / `--challenge` CLI. The model receives abstract text only; the evaluator compares the provisional reference labels afterward. Retained backward compatibility with split files and added isolation tests.

2026-10-30 — Audited direct label leakage and benchmark difficulty. The newly uploaded predictions were for the old random sample, not the new challenge. Decider source only receives abstract text; a keyword baseline attains 90% on the intentionally selected 50/50 challenge, so strong scores would not yet prove semantic generalization.

2026-10-30 — Verified user-uploaded 100-case curated challenge predictions against SHA-matched combined dataset and provisional AI labels: TP=50/TN=50/FP=0/FN=0; no direct label-column leakage in reviewed source, but benchmark is purposively enriched and vulnerable to lexical shortcuts. Independent adjudication/held-out validation still needed.

2026-10-30 — Added non-keyword, English-only 40/60 semantic challenge from 100 previously unused patent families, isolated Kaggle `--semantic-challenge` CLI, provenance and wiki. No explicit humanoid/anthropomorphic terms, but simple biped-vs-exoskeleton baseline still 94%; annotations AI-assisted, not human gold labels.
