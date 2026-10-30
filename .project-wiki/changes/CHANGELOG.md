# CHANGELOG

2026-10-29 — Documentation baseline: project wiki created; application code unchanged.

2026-10-30 — Integrated provisional English-only random-sample label comparison into Kaggle pilot; unresolved labels excluded and zero-positive evaluation limitations documented. Live Kaggle inference not yet verified.

2026-10-30 — Kaggle FP16 pilot: repaired TorchAudio CUDA mismatch blocking Transformers AutoProcessor, added dependency preflight and regression test; Kaggle GPU rerun remains pending.

2026-10-30 — User-supplied Kaggle predictions verify a completed 100-family single-T4 pilot after the dependency fix. No positives in the provisional labels; production two-T4 data parallelism is a proposed throughput optimization, not implemented or benchmarked.

2026-10-30 — Created separate source-faithful 100-family, English-only 50/50 relevance challenge with assistant-authored provisional labels, 30 hard robotics negatives, 10 lexical decoys and 10 clear negatives. Added reproducible generator, GitHub Actions validation, and isolated Kaggle `--challenge` run; human adjudication and model inference pending.
