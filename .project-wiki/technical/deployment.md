# Deployment and execution

TIP/PATSTAT extraction runs in TIP; private endpoint translation runs locally under Python 3.12+ and is independent of screening.

Kaggle pilot: enable GPU and Internet, then clone the repository, change into its root, and run `python kaggle/run.py`. The 100-family original-English input is committed at `samples/random_100/humanoid_100_abstracts_en.csv` and discovered automatically. No translation or sample upload is required. Downloading the private Hugging Face checkpoint may require the `HF_TOKEN` Kaggle secret.

To evaluate the supplied AI-assisted labels, attach `humanoid_100_manual_labels.csv` as a Kaggle Dataset; the launcher finds it uniquely under `/kaggle/input/**/`, validates IDs, then runs `kaggle/evaluate.py` after scoring. Its outputs under `/kaggle/working` are `predictions.csv`, `evaluation.json`, `evaluation_cases.csv` and state/provenance files. For an existing predictions file, call `kaggle/evaluate.py` directly. See `kaggle/README.md`.

Current behavior uses a pinned native Decider checkpoint, local BF16→FP16 loader patch and one CUDA GPU. The first observed Kaggle run downloaded the checkpoint but failed at import because torch 2.14.0/CUDA 13.0 conflicted with Kaggle's torchaudio/CUDA 12.8. The launcher now removes *only* the optional torchaudio package and verifies `transformers.AutoProcessor` in a fresh interpreter. Rerun from the current clone with `git pull --ff-only` and `python kaggle/run.py` to reuse the existing checkpoint; avoid nested clones. This changes the notebook's ephemeral Python environment, so a separate audio workflow would need compatible TorchAudio installed. Successful GPU model inference remains unverified.

## Curated challenge in Kaggle

After pulling main from the repository root, run `python kaggle/run.py --challenge`. This selects the **single combined** `samples/humanoid_challenge_100/challenge_100_labeled.csv` as both abstract input and post-inference label source without external dataset attachment and writes all predictions/evaluations/journals to `/kaggle/working/challenge_100/`. For a separately uploaded combined CSV, run `python kaggle/run.py --dataset /kaggle/input/.../dataset.csv --output /kaggle/working/custom/predictions.csv`. The legacy `--input PATH --labels PATH` interface remains available. The model receives only abstract text, never label/annotation columns. The first random sample remains unchanged and the new outputs cannot collide with its manifest. GPU inference on this new challenge has not yet been observed.

## Implicit semantic challenge

From the cloned repository root after pulling main: `python kaggle/run.py --semantic-challenge` (`--check` for input-only preflight). The launcher automatically selects the single `samples/semantic_challenge_100/semantic_100_labeled.csv` and writes outputs into `/kaggle/working/semantic_100/`; it never reuses the previous challenge journal. Only source abstract enters `screen.py`'s model request; labels and rationale go to `evaluate.py` afterward. The 40/60 labels are AI-provisional and intentionally treat biped-specific technologies as relevant, broader than the earlier strict humanoid-only prompt. No live GPU evaluation of this set has been seen.
