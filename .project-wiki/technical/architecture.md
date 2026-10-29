---
id: TECH-ARCHITECTURE
type: technical
status: active
title: Architecture
created: '2026-10-29'
updated: '2026-10-29'
tags: []
related: []
source_paths: []
confidence: confirmed
---

# Observed and planned data flow

**Implemented:** `src/sql_queries.py` runs a broad 64-CPC-prefix EPO TIP / PATSTAT query, grouping matched applications into DOCDB families and exporting one row per family to `humanoid_patents.zip`. Seven source fields are `docdb_family_id`, `year`, `title`, `title_language`, `abstract`, `abstract_language`, `matched_cpcs`.

**Implemented, live endpoint validation not asserted:** `src/translate_abstracts.py` reads the ZIP; validates schema, families and languages; copies original English abstracts; translates non-English/unknown-language abstracts via a private OpenAI-compatible Chat Completions endpoint; validates ID-indexed JSON; and journals successful translations and failures to resume interrupted work. Default batching uses up to 8 records and 12,000 source characters, paced at 20 requests/minute. Export: `outputs/translation/humanoid_patents_en.csv` with `abstract_en` and `translation_status`. The summary must report `incomplete: 0` before screening the full corpus.

**Planned:** 100-candidate stratified relevance evaluation → calibrated abstract-only keep/discard decision model → sector, technology and competitor landscaping → applicant harmonization → present/future scores → Magic Quadrant → acquisition/partnership recommendation.

CPC extraction is broad **candidate generation**, not verified humanoid-robot relevance. The selected CPC codes explicitly cover adjacent robotics, exoskeleton and toy-robot concepts. No deterministic text-based relevance prefilter is authorized.
