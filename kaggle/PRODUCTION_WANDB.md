# Kaggle production: dual T4 + W&B telemetry

Entry points: `.github/workflows/kaggle_production.yml`, `kaggle/production_kernel/production.ipynb`, and `kaggle/monitor_kaggle.py`.

## Secure input and model access

The completed `humanoid_patents_en.zip` and `humanoid_patents_en_summary.json` are cloned from a pinned GitHub commit in Kaggle. Expected count: **237,538** eligible families.

The pinned native Perplexity Decider Flash v1.2 checkpoint requires authenticated Hugging Face access. GitHub Actions alone uses `HF_TOKEN` to download the pinned revision and provision an account-private Kaggle dataset. Neither the HF secret nor the W&B secret is placed into the notebook. GitHub Actions uses `KAGGLE_API_TOKEN` to submit the private dual-T4 notebook and `WANDB_API_KEY` to relay Kaggle log counters into W&B. Patent IDs and abstracts are not logged to W&B.

## Minimal W&B charts

Project: `humanoid-patent-filtering`. Live metrics are processed families, completion %, per-worker counts, throughput in families/hour, estimated remaining hours, optional GPU utilization and memory per T4, and provisional model-positive fraction at threshold 0.5.

These are operational and model prediction metrics, **not externally validated precision, recall or accuracy**. W&B updates depend on Kaggle execution logs becoming available.

## Session persistence

Because 237,538 families may exceed a session, inference is limited to 300 minutes per notebook run. At end, its per-worker journals and provenance are archived in `/kaggle/working/humanoid-checkpoint.zip`. If complete, all-family `predictions.csv`, metadata-preserving `filtered_patents.zip`, and `production_summary.json` are exported. Incomplete sessions write `session_summary.json` instead of claiming full completion. The GitHub monitor downloads these outputs and saves them for 30 days as a workflow artifact.

To continue later, attach the prior `humanoid-checkpoint.zip` as a private Kaggle input, keeping original dataset and model revision fixed. The loader checks IDs, source hash and worker metadata before reusing predictions. Nothing in `/tmp` persists between Kaggle sessions.

## Methodological release gates

Private Hugging Face access and the mirror's upload/storage limits may block initial setup. A requested dual-T4 accelerator does not prove successful model execution; inspect live GPU metrics. Only a full merge with exactly 237,538 unique family probabilities establishes screening completion. The 0.5 model cutoff remains exploratory pending independently adjudicated calibration samples.
