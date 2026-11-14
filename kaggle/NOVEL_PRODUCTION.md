# Novel patent families: GemRouter translation -> 2xT4 Perplexity screening

## Scope

This is a **separate incremental batch**, not a rerun or replacement of the original 238,824-family TIP extract and 237,538-family screened English corpus.

- Source: `data/new_humanoid_patents.zip`, single member `new_humanoid_patents.csv`.
- Provenance: exact input fields `docdb_family_id,year,title,title_language,abstract,abstract_language,all_cpcs,ipr_types,matching_channels`.
- Historical exclusion: the translation gate checks no DOCDB family in the new source appears in `data/raw/humanoid_patents.zip`.
- Eligibility: every nonempty source abstract is copied or translated into English; empty source abstracts are counted and excluded.
- Translation: private GemRouter API; source and model pinned in a journal manifest.
- Screening: the existing pinned `perplexity-ai/pplx-decider-flash-v1.2` FP16 model revision `6d771ad7b5ecff5e93b8fc7b90d4c5ccc341954d`; two independent T4 GPU processes. The 0.5 classification threshold is exploratory, not human-calibrated.

**Ordinary pushes do not start the pipeline.** Only manual `workflow_dispatch` or an explicitly authorized, exact-message launch-marker push of [Novel humanoid patents - GemRouter then Kaggle dual T4](../.github/workflows/novel_patents_pipeline.yml) starts API/GPU work. The marker path is `.github/novel_patents_launch_request.txt` and the exact commit message is `Authorize novel patent pipeline: GemRouter then Kaggle 2xT4`; do not create that marker until the user authorizes execution. The previous `complete_translation.yml` and `kaggle_production.yml` remain dedicated to the original corpus and must not be used for the novel batch.

## Before dispatch

1. Confirm the committed source ZIP matches the expected single-CSV schema and contains only new DOCDB IDs. GitHub Actions runs `python src/translate_novel_patents.py --check` before any API requests.
2. GitHub Actions secrets must include `GEMR_API_KEY` + `LLM_ENDPOINT` (aliases `GEMROUTER_API_KEY`, `GEMROUTER_ENDPOINT`), `KAGGLE_API_TOKEN`, and `WANDB_API_KEY`. The GemRouter endpoint must use HTTPS.
3. Your Kaggle account must be authorized to access the existing **private**, revision-pinned `pplx-decider-flash-private-v12` model dataset. This workflow *reuses* that dataset, instead of re-uploading the large model.
4. Free 2xT4 Kaggle batch GPU capacity may be required; the Actions launcher has bounded retries and refuses to overwrite a running novel session.
5. Offline tests: `python -m unittest discover -s tests -p 'test_novel_pipeline.py' -v` and `python -m unittest discover -s kaggle/tests -p 'test_wandb_live.py' -v`.

## Manual launch and recovery

For manual UI launch, open GitHub Actions -> **Novel humanoid patents - GemRouter then Kaggle dual T4** -> **Run workflow**, with both optional inputs blank for a fresh run. Alternatively, after explicit authorization, a single GitHub commit creating `.github/novel_patents_launch_request.txt` with the exact commit message `Authorize novel patent pipeline: GemRouter then Kaggle 2xT4` launches the fresh run. No authorization marker has been committed.

The workflow sequentially:

1. Revalidates source schema, counts and zero intersection against the original 64-CPC extract.
2. Runs the resumable translation script at up to 20 API requests/minute, saving only successful translations in `outputs/novel_translation/progress.jsonl`. It stops instead of screening an incomplete corpus.
3. Emits `novel_humanoid_patents_en.csv` and `novel_translation_summary.json` as the `novel-translation-complete` GitHub Actions artifact, with source and final CSV SHA256 digests.
4. Uploads the English CSV and summary to a *private*, per-run Kaggle dataset, and mounts the existing private model and temporary private W&B token.
5. Launches the *separate* `kaggle/novel_kernel/production.ipynb` on T4 x2. Each worker journals its decisions; W&B displays aggregate counts, rates and not patent text.
6. Downloads the output and journal to the `novel-screening-output` artifact, independently verifies source digests, family coverage, prediction count and preserved source columns. A time-limited partial Kaggle session is **not** reported as complete.

If **GemRouter quota stops translation**, enter the preceding Actions **run ID** in `resume_translation_run_id` when re-dispatching; it restores the source-bound journal/manifest from `novel-translation-journal`, and skips already completed IDs. Leave `resume_screen_run_id` blank.

If **Kaggle stops with an incomplete checkpoint**, enter the preceding run ID in `resume_screen_run_id` instead, leaving the translation option blank. This restores the *complete* English CSV from the earlier artifact without any GemRouter API calls, validates both worker journals against that exact input SHA256/model/prompt, and mounts the private resume dataset. Never supply a checkpoint from the original full-corpus screening.

If a run fails **before** saving a valid worker checkpoint, investigate Kaggle model/runtime diagnostics and start screening fresh from the completed translation artifact. The automatic artifact retention is 30 days; keep copies before expiry.

## Results and limitations

- `novel-translation-complete`: all eligible novel patent families, with normalized English `abstract` and `abstract_en`; original `abstract_language`, `all_cpcs`, `ipr_types` and `matching_channels` preserved.
- `novel-screening-output/predictions.csv`: probabilities and provisional binary decisions **for all eligible families**, not just positive matches.
- `novel-screening-output/filtered_patents.zip`: positive subset and the full source metadata, plus `probability_relevant,model_decision`.
- `production_summary.json`: counts and SHA256 digests; `humanoid-checkpoint.zip` is retained for a partial run.
- No new files are automatically merged into `data/filtered/filtered_patents.zip`; source and scope remain distinguishable until a separately validated union/merge is approved.
- Patent abstract relevance, translation fidelity, and the 0.5 acceptance threshold still need independent human evaluation. These are not validated positive/negative ground-truth labels.

## Implementation

`src/translate_abstracts.py` reads either explicitly supported PATSTAT schema; `src/translate_novel_patents.py` verifies new IDs and normalizes source-preserving output. `kaggle/production_run.py` and `kaggle/production.py` are reused without modifying inference semantics; `kaggle/wandb_live.py` now supports `--total` for the new count. `kaggle/validate_novel_resume.py` and `kaggle/validate_novel_output.py` enforce provenance and completeness.
