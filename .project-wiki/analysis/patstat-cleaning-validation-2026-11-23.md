# PATSTAT family cleaning and query-validation status (2026-11-23)

## Evidence and scope

Teammate-supplied `Cleaning.docx`, `02_clean.py`, and `humanoid_patents_clean.csv` were inspected against the project kickoff (page 9) and the existing pipeline. This note documents **a separately supplied enriched/cleaned output**; it does not assert that the bulk enriched or cleaned CSV has been committed.

- Prior versioned model-filtered source: `data/final/humanoid_patents_final.csv`, **7,102** unique model-positive DOCDB families (3,116 original CPC query + 3,986 novel V3 query).
- Teammate-cleaned result: **7,096** rows, **7,096** unique nonblank DOCDB IDs, **33** columns; 6 source families excluded where PATSTAT application enrichment was absent.
- All 7,096 rows have `model_decision=1`, `probability_relevant>=0.5`, nonempty `abstract_en`; 7,010 original-English / 86 translated.
- Query origins: 3,110 `original_64_cpc` and 3,986 `novel_v3`. The six removed source records therefore belong to the original-query subset.
- Years 1974–2026; `is_truncated=True` for 3,016 families (2023 onward); zero disagreement with the implemented rule.
- Applicant field `applicants_clean` is populated for all records; **22** are explicit `UNKNOWN` entries.
- Not all other PATSTAT fields are populated: `applicant_countries` blank in 5,863 rows, `patstat_cpc_codes` blank in 2,701, `n_backward_citations` blank in 3,208 and `n_forward_citations` blank in 2,852. Preserve the distinction between missing and zero when computing indicators.

## What the cleaning script does

`src/02_clean.py` is the teammate-supplied processing logic: deduplicate by DOCDB family ID; exclude no-PATSTAT-application families; drop duplicate `year`, cast year columns to integer; normalize PSN applicant names including a limited manually reviewed subsidiary map; retain dates; flag filing years >= 2023.

**Interpretation caveats**:
1. Despite the kickoff's *earliest priority year* instruction, the field implemented is `earliest_filing_year`; verify priority derivation upstream before time-trend claims.
2. The truncation cutoff >=2023 is a documented conservative convention, not an empirically derived completeness correction.
3. `model_decision=1` shows inclusion after a model filter, **not independent sector relevance validation**. Previously reported F1=0.927 uses provisional AI-assisted labels and a purposive holdout, so it is not a representative final-set precision estimate.
4. Corporate naming aliases are not an exhaustive ownership history or full applicant-entity disambiguation.
5. The six excluded families must be explicitly recorded in analysis denominators; inspect PATSTAT join keys if their loss is material.

## Tutor Masali's query-validation protocol (reported by teammate)

1. Use the previously labelled 100 patents for **CPC/IPC query precision**; review false positives to refine included codes.
2. For each keyword/group, count families **incremental to the CPC query**, then blind-random sample 20–30 of its additions irrespective of model score. Retain terms only if incremental precision is acceptable. Report per-group numerators, denominators, overlaps, and retention decisions.
3. Independently label a **random ~100-family sample of the final retained dataset** to estimate its precision, with an uncertainty interval.
4. For recall, manually inspect a random sample from **near-sector excluded families**, e.g. discarded-keyword or neighbouring nonincluded CPC hits. This estimates recall over the defined near-sector sampling frame, not global patent-universe recall.

A past 100-family **model-score benchmark** is not interchangeable with either the **CPC-query precision sample** or the final **representative human-annotated precision sample** unless selection frames and independent labels are verified.

## Step 0 completion gate

- [x] Source extraction and model screening produced a positive-only dataset.
- [x] PATSTAT enrichment and four cleaning rules applied to the teammate-supplied CSV; output inspected for structural invariants.
- [ ] Commit or regenerate `humanoid_patents_clean.csv` from the enriched source with verified hashes and archival provenance.
- [ ] Reconcile earliest priority year versus filing year.
- [ ] Complete documented CPC/IPC, incremental-keyword, final-set precision and near-sector recall validation with independent, blinded relevance labels.
- [ ] Report the impact of missing PATSTAT citation/CPC/applicant-country fields on later indicators.

**Decision: extraction/filtering and cleaning are operational, but formally validated Step 0 is not complete.**
