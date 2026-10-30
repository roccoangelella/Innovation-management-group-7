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

## Kaggle runtime error: TorchAudio CUDA mismatch (2026-10-30)

An observed Kaggle T4 run successfully validated the 100 original-English abstracts and 100 attached provisional labels and downloaded the 9.10 GB model checkpoint. It then failed **before inference** because the requirements installed PyTorch 2.14.0 with CUDA 13.0 while Kaggle's preinstalled TorchAudio extension was compiled against CUDA 12.8. Importing `transformers.AutoProcessor` indirectly imported TorchAudio and raised a CUDA-version mismatch.

The single-command launcher now uninstalls **only the unnecessary optional `torchaudio` package** after installing the checkpoint requirements (including with `--skip-install`), then checks `from transformers import AutoProcessor` in a fresh subprocess before model loading. No audio inputs are used for this study. This modifies the ephemeral Kaggle Python environment; other audio tasks in the same notebook may need a compatible TorchAudio reinstallation.

In the **existing clone**, run:

```python
!git pull --ff-only
!python kaggle/run.py
```

Run from the repository root (do not clone into itself again). Keep the existing `/kaggle/working/pplx-decider-flash-v1.2-fp16` checkpoint to reuse cached weights. The change addresses the observed import error; model initialization, GPU memory use, 100-case inference and evaluation still require a real rerun to verify.

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

## Curated 50/50 humanoid challenge (2026-10-30)

After reviewing the original English patent abstracts without looking at Decider predictions, 50 provisional positives, 30 hard nonhumanoid robotics negatives, 10 lexical-decoy negatives, and 10 clear negatives were selected in `samples/humanoid_challenge_100/`. These 100 source families are **disjoint** from the earlier pure-random 100. Their labels are AI-authored provisional judgments, **not human gold labels**.

From the repo root, run a single command:

```bash
python kaggle/run.py --challenge
```

This selects the single committed `samples/humanoid_challenge_100/challenge_100_labeled.csv`, containing both abstracts and provisional labels, and writes `predictions.csv`, `evaluation.json`, `evaluation_cases.csv`, and a separate resume journal under **`/kaggle/working/challenge_100/`**, without colliding with the earlier pilot. **Only the abstract_en text is passed into Decider**; label and annotation fields are loaded only by the evaluation stage. No extra Kaggle dataset or translation call is needed. For details and selection caveats see [the challenge annotation protocol](../samples/humanoid_challenge_100/ANNOTATION_PROTOCOL.md).

You can also run a single uploaded CSV anywhere on Kaggle: `python kaggle/run.py --dataset /kaggle/input/<your-dataset>/challenge_100_labeled.csv --output /kaggle/working/custom_test/predictions.csv`. The combined CSV needs at least `docdb_family_id,abstract_en,label,needs_review`. The two-file `--input` + `--labels` interface is preserved for compatibility. The labels are **hidden from the model request, not hidden from the CSV or Python runtime**.

Because this is **purposively enriched to 50% positives**, its precision and F1 are NOT estimates of production performance; and if the prompt/threshold is tuned on this set, subsequent scores on this same set are not held-out estimates.

## Evaluate the original 100 manually labeled abstracts

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

## Original-English semantic challenge, 40/60 (2026-10-30)

One combined input file: [`samples/semantic_challenge_100/semantic_100_labeled.csv`](../samples/semantic_challenge_100/semantic_100_labeled.csv), containing 100 previously unused source abstracts, AI-assisted provisional `label`, `needs_review`, `confidence`, evidence excerpt and reason. No selected abstract contains the whole words *humanoid* or *anthropomorphic*. The relevant class includes **independent biped-specific robot motion and structure**, extending the previous prompt's strict explicit humanoid connection. Label-definition disagreements are possible.

Run from the repo root, after pulling current main:

```bash
python kaggle/run.py --semantic-challenge
```

The launcher selects both abstract and labels from the combined file but `screen.py` forwards **only** `abstract_en` to the model. Results go into `/kaggle/working/semantic_100/` (not the old challenge directory). `--semantic-challenge --check` validates input without downloading weights. Blind annotation input is `semantic_100_for_blind_review.csv`.

**Shortcut audit:** A classifier matching case-insensitive biped/two-legged terminology gives TP 35, TN 56, FP 4, FN 5 (91% accuracy). Excluding abstracts mentioning *exoskeleton* gives TP 34, TN 60, FP 0, FN 6 (94% accuracy). The old exact-word `humanoid OR anthropomorphic` baseline now returns no positives (60% accuracy). So this is useful for analyzing **false negatives and decision-boundary ambiguity**, but it is **not a clean semantic-generalization benchmark**: selected examples remain lexically correlated and were AI-labeled, not independently adjudicated. A later human-validated, realistic-prevalence set with more difficult concept-matched examples is still required.

## Additional keyword-blind semantic holdout

Another independently selected 100-family dataset is in `samples/humanoid_semantic_holdout_100/semantic_holdout_100_labeled.csv` (40 provisional task-relevant positives, 60 near negatives). This is distinct from `--semantic-challenge` and from the earlier `--challenge` test. To run the **new** holdout, use:

```bash
python kaggle/run.py --dataset samples/humanoid_semantic_holdout_100/semantic_holdout_100_labeled.csv --output /kaggle/working/semantic_holdout_100/predictions.csv
```

This uses the existing `--dataset` single-file interface and isolated output directory. Only `abstract_en` enters the model request. See `samples/humanoid_semantic_holdout_100/ANNOTATION_PROTOCOL.md`; labels are AI-provisional, class balance enriched, and the broader morphology/task-relevance definition may differ from the model's strict explicit-link prompt. No GPU predictions have been recorded for this set.
