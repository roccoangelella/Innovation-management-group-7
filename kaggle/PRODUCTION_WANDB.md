# Direct real-time Kaggle → W&B document counter (2026-11-11)

**Published repository data:** `data/filtered/filtered_patents.zip` and `data/filtered/production_summary.json`. Translated input: `data/translated/humanoid_patents_en.zip`.

**Canonical dashboard:** https://forge.coreweave.com/wandb/rocchissimo936-none/humanoid-patent-filtering

## What actually appears

The Kaggle notebook launches two independent GPU-T4 screening workers. The dedicated Kaggle-side monitor reads each worker's **append-only, on-disk** `predictions.jsonl` journal every 30 seconds. Only complete newline-terminated records are counted. W&B receives:

- `documents/analyzed`: cumulative number of model decisions actually journaled; target **237,538**.
- `documents/total` and `documents/remaining`: absolute progress.
- `documents/percent`: completion percentage.
- `workers/t4_0_analyzed` and `workers/t4_1_analyzed`: documents processed by each GPU.
- `throughput/documents_per_second`: recent processing speed.
- `decisions/provisional_positive`: model-positive count at exploratory 0.5 threshold, **not human-validated classification accuracy**.

No patent text, DOCDB IDs or API keys enter W&B metrics. The old GitHub Actions Kaggle-log relay is no longer responsible for live counter updates, since Kaggle does not reliably make stdout available during execution.

## Secure W&B authentication

The GitHub Action uses the existing `WANDB_API_KEY` repository secret without embedding its value in any public GitHub commit. Kaggle's official CLI does not manage Kaggle Secrets, so the workflow creates a **single-run Kaggle dataset that is private by default** (never `--public`). It includes an owner-only token file mounted inside the private notebook. Its name contains the GitHub run ID and it is deleted when the associated monitor job exits. The notebook alternatively accepts a Kaggle-native `WANDB_API_KEY` user secret, if already configured. Credentials are not included in notebook source, output CSV, W&B charts, or exported checkpoints. **Security caveat:** while the temporary private dataset exists, the credential is available to the authenticated Kaggle account and platform; do not publish/share that dataset. Prefer Kaggle's native Secrets manager for durable setup. Key rotation is prudent if the temporary dataset was ever accidentally shared.

## Session execution and validation

Source: pinned `humanoid_patents_en.zip` with 237,538 eligible translated DOCDB-family abstracts. Model: pinned native `pplx-decider-flash-v1.2` FP16 on **T4 ×2**. Model weights are provisioned through an account-private Kaggle dataset using the GitHub `HF_TOKEN`.

A dedicated GitHub job polls W&B's API (not Kaggle logs) for a positive `documents/analyzed` count and prints the actual W&B run URL. **Submission and notebook status alone do not prove inference**: wait for this job to pass. A 300-minute session writes resumable per-GPU journals and a final or partial summary into Kaggle output. Later sessions may attach the prior checkpoint; full labeling is confirmed only when the merge produces exactly 237,538 unique scored families and valid SHA-256 digests.

Offline counter checks: `python -m unittest discover -s kaggle/tests -p test_wandb_live.py -v`.
