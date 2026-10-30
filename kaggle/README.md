# Kaggle · Perplexity Decider patent screening

Self-contained **inference experiment** for Group 7's humanoid-robot patent corpus. Translation and 100-family sampling remain under `src/`; this folder owns only model inference and evaluation. No fine-tuning.

## Model

`perplexity-ai/pplx-decider-flash-v1.2` (native Perplexity `pplx_decider.Decider` API). Do **not** use ordinary causal language-model generation or `AutoModelForSequenceClassification`: the checkpoint has a specialized decision readout and attention configuration. Official instructions: https://huggingface.co/perplexity-ai/pplx-decider-flash-v1.2

The model's repository may require Hugging Face authentication. The BF16 checkpoint needs ~9 GiB GPU memory for weights **plus runtime memory**. Kaggle GPU availability, download permissions, runtime limits and Internet settings must be checked in Kaggle itself. We have **not** run a Kaggle GPU evaluation yet.

## Run in a Kaggle notebook

1. Upload the **translated** 100-family CSV from `outputs/sampling/humanoid_100_abstracts_en.csv` as a Kaggle Dataset. Do not upload the original ZIP in place of the translated CSV.
2. Enable GPU and, when required, Internet access; configure `HF_TOKEN` as a Kaggle secret if the repository is gated. Never put tokens in notebooks, Git, or outputs.
3. Run the cells from `notebook_cells.py`, modifying only the dataset path. The setup cell downloads the pinned Perplexity model, installs its own repository requirements (which may require restarting the kernel), and then runs `screen.py`.
4. Download `predictions.csv`, `run_metadata.json` and optional `evaluation.json`. Upload only non-sensitive aggregate results to GitHub.

If Kaggle's notebook session cannot download the weights, provision a Kaggle Model/Dataset with the checkpoint in advance and pass its local path as `--checkpoint`. Run from repo root, or explicitly upload this folder to Kaggle.

## CLI

```bash
python kaggle/screen.py \
  --input /kaggle/input/translated-sample/humanoid_100_abstracts_en.csv \
  --checkpoint /kaggle/working/pplx-decider-flash-v1.2 \
  --output /kaggle/working/predictions.csv
```

Only `docdb_family_id` and `abstract_en` are read from the CSV; `translation_status` is validated when present. Original title, CPC, source language and patent metadata are never passed to the model. The prompt uses a fixed definition of humanoid robots: general-purpose articulated anthropomorphic robots, their control, perception, manipulation, locomotion, and systems explicitly designed for such robots. Ordinary appliances, standalone grippers, industrial robot arms, autonomous vehicles, and generic ML are not included without an explicit humanoid-robot link.

The script outputs **unthresholded** model probability estimates and the model's binary decision. No threshold is presented as validated. It writes each result immediately to a resumable JSONL journal and regenerates `predictions.csv` upon completion; it verifies the input and configuration hashes before resume.

## Evaluation

Once the 100 patents have been independently hand labeled, supply a CSV with `docdb_family_id,label` (`label` is 0 or 1):

```bash
python kaggle/evaluate.py --predictions /kaggle/working/predictions.csv \
  --labels /kaggle/input/patent-labels/labels.csv \
  --output /kaggle/working/evaluation.json
```

The evaluation computes confusion-matrix counts and precision, recall and F1 at the **exploratory** 0.5 cut-off. Report these with the 90/10 stratification caveat; do not interpret the dataset as a random estimate of production prevalence or automatically deploy this threshold. Any threshold selection requires distinct calibration and held-out test sets or a documented cross-validation procedure.

## Scope

This is the first Flash v1.2 experiment only. Comparisons to the larger Decider, prompt alternatives, calibration and full-corpus production scaling come **after** assessing manually reviewed results. Keep the translated CSV and labels outside the repository when licensing/privacy restrictions require it.
