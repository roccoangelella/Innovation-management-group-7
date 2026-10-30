# Kaggle · Perplexity Decider FP16 screening pilot

Standalone **100-family inference experiment**. Data collection, translation and sampling remain under `src/`. There is no fine-tuning and no production filtering threshold yet.

## One-command launch in Kaggle

First enable **GPU** and **Internet** in Kaggle Notebook settings and ensure Python 3.12+. The repository already includes the 100 originally English, unmodified sample at `samples/random_100/humanoid_100_abstracts_en.csv`; **no translated Kaggle Dataset is required for this pilot**. If Hugging Face access is required, add a private token as Kaggle secret `HF_TOKEN` (never commit it).

From a notebook cell:

```python
!git clone https://github.com/roccoangelella/Innovation-management-group-7.git
%cd Innovation-management-group-7
!python kaggle/run.py
```

**Only the last line is the pipeline entrypoint.** It discovers the English-only sample already committed under `samples/random_100/` (or accepts a custom CSV via `--input`), checks the input, checks CUDA, installs pinned dependencies, downloads the pinned model, patches its **local** native loader for genuine FP16 execution, and runs/resumes inference. Installation and inference run in separate Python processes, so the notebook kernel does not need to be manually restarted.

For a custom translated CSV, supply its path explicitly:

```bash
python kaggle/run.py --input /kaggle/input/my-sample/humanoid_100_abstracts_en.csv
```

Preflight the input without downloading weights: `python kaggle/run.py --check`.

## Why an explicit FP16 patch?

The official checkpoint at `perplexity-ai/pplx-decider-flash-v1.2` stores BF16 tensors; in the pinned release the native `pplx_decider/model.py` hardcodes BF16 for CUDA. NVIDIA T4 GPUs do not execute BF16 natively. The launcher replaces **one exact dtype assignment** with `torch.float16` in the locally downloaded source, then loads the model natively. If the source changes, it fails instead of silently falling back to BF16. The model's noncausal attention, per-question readout, decision request format and saved temperature calibration are unchanged. FP16 results must still be tested against manually labeled patents; no equivalence to the official BF16 benchmark is claimed.

Model revision: `6d771ad7b5ecff5e93b8fc7b90d4c5ccc341954d`.
Official reference: https://huggingface.co/perplexity-ai/pplx-decider-flash-v1.2
The checkpoint is ~9.1 GB, plus working GPU memory. On dual T4 setups, **one** 16 GiB GPU is used; memory is not pooled. Adequate GPU memory, Hugging Face permissions, internet access and compatible Kaggle Python/PyTorch versions are required. **The GPU run has not yet been verified on Kaggle.**

## Output

- `/kaggle/working/predictions.csv`: `docdb_family_id,probability_relevant,model_decision`. Decision uses exploratory 0.5, **not** a validated filtering threshold.
- `/kaggle/working/predictions.jsonl`: append-only resumable results.
- `/kaggle/working/run_metadata.json`: input hash, question/prompt, pinned model and revision.

Only `abstract_en` is provided to the decision model. Source language, title, CPCs and metadata are not in the request. The input requires successful translation status (`original_en` or `translated`) when the field exists, and unique DOCDB family identifiers. For this pilot, all 100 input abstracts were originally English, so `abstract_en` is a verbatim copy and no translation was performed. Custom non-English samples must be translated before inference; the launcher does not call the private translation API.

Manual evaluation after independently labeling all 100 families:

```bash
python kaggle/evaluate.py --predictions /kaggle/working/predictions.csv \
  --labels /kaggle/input/patent-labels/labels.csv \
  --output /kaggle/working/evaluation.json
```

Report precision, recall, F1 and error cases with the sampling caveat: this is an English-only random sample of broad CPC candidates, and it may have too few truly relevant humanoid patents for reliable precision/recall estimates. It does not assess translated non-English abstracts. No full-corpus deployment until a held-out calibration strategy is agreed.

## Evaluate the 100 manually labeled abstracts

The independent labeling file `humanoid_100_manual_labels.csv` contains **98 negative labels, no positive labels, and 2 unresolved rows** (family IDs `93663023`, `24533336`). These labels were produced by an AI-assisted annotator and require adjudication. **Do not publish them as human gold labels.**

In Kaggle, add this CSV as a Kaggle Dataset using **Add Input**. After cloning the repository, `python kaggle/run.py` automatically finds the unique attached `/kaggle/input/**/humanoid_100_manual_labels.csv` and runs evaluation immediately after model inference. Or supply `--labels /kaggle/input/<dataset-slug>/humanoid_100_manual_labels.csv` to disambiguate.

Outputs:
- `/kaggle/working/evaluation.json`: confusion counts, false-positive rate, specificity, and 95% Wilson confidence interval. With **zero confirmed positives**, precision, recall and F1 are correctly `null` (not zero).
- `/kaggle/working/evaluation_cases.csv`: joined labels/predictions ranked by descending model probability, including unresolved cases for review.
- `/kaggle/working/predictions.csv`: full inference results, independent of the labels.

To evaluate existing predictions without repeating expensive inference, run:

```bash
python kaggle/evaluate.py --predictions /kaggle/working/predictions.csv --labels /kaggle/input/<dataset-slug>/humanoid_100_manual_labels.csv --output /kaggle/working/evaluation.json
```

The pilot is an initial **negative-case test**, not a valid recall/precision test. Add an independently adjudicated positive-enriched evaluation set before selecting any production acceptance threshold. The model never sees labels during inference. Kaggle GPU execution remains unverified.
