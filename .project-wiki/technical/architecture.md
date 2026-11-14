**2026-11-11 direct telemetry update:** 2026-11-11 — Operational telemetry: Kaggle runs `kaggle/wandb_live.py` as an independent W&B uploader and reads flushed `worker_0/predictions.jsonl` / `worker_1/predictions.jsonl` directly, avoiding delayed Kaggle log APIs. Private per-run Kaggle authentication is provisioned by GitHub secret and promptly deleted; Kaggle native Secrets is supported as preferred alternative. Two FP16 Decider GPU workers continue to own predictions and end-of-session checkpoints. Count metrics are not human adjudicated model performance.

---
id: TECH-ARCHITECTURE
type: technical
status: active
title: Architecture
created: '2026-10-29'
updated: '2026-11-10'
tags: []
related: []
source_paths: []
confidence: confirmed
---

# Observed and planned data flow

**Implemented:** `src/sql_queries.py` runs a broad 64-CPC-prefix EPO TIP / PATSTAT query, grouping matched applications into DOCDB families and exporting one row per family to `data/raw/humanoid_patents.zip`. Seven source fields are `docdb_family_id`, `year`, `title`, `title_language`, `abstract`, `abstract_language`, `matched_cpcs`.

**Implemented, live endpoint validation not asserted:** `src/translate_abstracts.py` reads the ZIP; validates schema, families and languages; copies original English abstracts; translates non-English/unknown-language abstracts via a private OpenAI-compatible Chat Completions endpoint; validates ID-indexed JSON; and journals successful translations and failures to resume interrupted work. Default batching uses up to 8 records and 12,000 source characters, paced at 20 requests/minute. Export: `outputs/translation/humanoid_patents_en.csv` with `abstract_en` and `translation_status`. The summary must report `incomplete: 0` before screening the full corpus.

**Implemented (synthetic validation; real-corpus run not evidenced):** `src/sample_abstracts.py` samples 90 English and 10 non-English eligible DOCDB families using seed 20261029, bounded stable-hash candidate pools, CPC deficit balancing and non-English language diversity. Exports a source-column-preserving CSV, a translation-compatible ZIP, and a JSON report. Tests: `tests/test_sample_abstracts.py`. **Planned:** reference-label review of the 100-candidate benchmark → calibrated abstract-only keep/discard decision model → sector, technology and competitor landscaping → applicant harmonization → present/future scores → Magic Quadrant → acquisition/partnership recommendation.

CPC extraction is broad **candidate generation**, not verified humanoid-robot relevance. The selected CPC codes explicitly cover adjacent robotics, exoskeleton and toy-robot concepts. No deterministic text-based relevance prefilter is authorized.


## Implemented two-T4 screening path (2026-11-10)

`kaggle/production_run.py` accepts the completed translated CSV or single-CSV ZIP (not the raw un-translated source archive), optionally gates on the translation summary (`incomplete=0`), records source/model/prompt SHA256 provenance and checks exactly two T4 GPUs. `kaggle/production.py` deterministically hashes DOCDB family IDs into disjoint shards, starts two separate CUDA-masked FP16 native Decider processes with independent journals, then verifies complete unique-ID probability outputs before writing a full prediction CSV and metadata-preserving filtered ZIP. The 0.5 decision threshold remains exploratory. Live dual-GPU memory, throughput and runtime still require verification.


## Translation completion from repository seed (2026-11-10)

`src/complete_translation.py` is a source-verified continuation wrapper for the same `src/translate_abstracts.py` translator. The previous English-only ZIP seeds successful journal entries; rows are compared with the original PATSTAT ZIP by DOCDB family ID and immutable metadata. Only missing eligible source abstracts are sent to the private Gemrouter endpoint. On complete coverage, all `abstract` and `abstract_en` fields are English in one source-preserving CSV inside `data/translated/humanoid_patents_en.zip`, while `abstract_language` retains original language provenance. A GitHub Actions workflow publishes the completed archive and summary with a fast-forward push only after strict completeness, ZIP structure and source-hash validation. Source records with no abstract are explicitly counted and excluded. Implementation and synthetic offline tests are verified; full-run outcome is not yet verified.


## Separate novel-family candidate branch (2026-11-14)

The committed `data/new_humanoid_patents.zip` is an incremental TIP/PATSTAT extract with nine source columns (`all_cpcs`, `ipr_types`, `matching_channels` beyond the original six shared metadata fields). `src/translate_abstracts.py` now accepts both explicitly declared source formats and preserves source columns, without changing the original corpus contract. `src/translate_novel_patents.py` checks that the novel DOCDB families have zero overlap with `data/raw/humanoid_patents.zip`, translates/copies eligible abstracts, and produces an English-normalized CSV with source/final SHA256 provenance. The explicitly authorized `.github/workflows/novel_patents_pipeline.yml` stages that completed CSV on Kaggle and launches `kaggle/novel_kernel/production.ipynb` with two T4 FP16 workers using the existing pinned Decider model. Journals, GPU progress, W&B document counts and final hashes remain batch-specific; the historical full-corpus checkpoint is never reused. See `kaggle/NOVEL_PRODUCTION.md` for resume and artifact requirements. No live run has yet been authorized or observed.
