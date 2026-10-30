# Kaggle · Perplexity Decider FP16 screening pilot

Standalone **100-family inference experiment**. Data collection, translation and sampling remain under `src/`. There is no fine-tuning and no production filtering threshold yet.

## One-command launch in Kaggle

First enable **GPU** and **Internet** in Kaggle Notebook settings, attach the translated 100-family CSV (`humanoid_100_abstracts_en.csv`) as a Kaggle Dataset, and ensure Python 3.12+. If Hugging Face access is required, add your private token as Kaggle secret `HF_TOKEN` (never commit it).

From a notebook cell:

```python
!git clone https://github.com/roccoangelella/Innovation-management-group-7.git
%cd Innovation-management-group-7
!python kaggle/run.py
```

**Only the last line is the pipeline entrypoint.** It discovers `/kaggle/input/**/humanoid_100_abstracts_en.csv` (or `outputs/sampling/humanoid_100_abstracts_en.csv` when present), checks the input, checks CUDA, installs pinned dependencies, downloads the pinned model, patches its **local** native loader for genuine FP16 execution, and runs/resumes inference. Installation and inference run in separate Python processes, so the notebook kernel does not need to be manually restarted.

For a different CSV path:

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

Only `abstract_en` is provided to the decision model. Source language, title, CPCs and metadata are not in the request. The input requires successful translation status (`original_en` or `translated`) when the field exists, and unique DOCDB family identifiers. The 100-family data must already be translated; the launch does not invoke the private translation API.

Manual evaluation after independently labeling all 100 families:

```bash
python kaggle/evaluate.py --predictions /kaggle/working/predictions.csv \
  --labels /kaggle/input/patent-labels/labels.csv \
  --output /kaggle/working/evaluation.json
```

Report precision, recall, F1 and error cases with the sampling caveat: the 90/10 language mix is not the production prevalence, and the dataset is not a representative random sample. No full-corpus deployment until a held-out calibration strategy is agreed.
