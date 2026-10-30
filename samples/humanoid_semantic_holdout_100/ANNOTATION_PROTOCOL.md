# Semantic Humanoid Holdout v1 — design and annotation

**Generated:** 30 October 2026. **Status:** source-verified, AI-provisional labels; not human-adjudicated; no Decider inference on these 100 cases has been performed for this dataset.

## Aim and controls

This additional set tests whether an abstract classifier can recognize *embodied humanoid-related morphology and tasks* without relying on the exact words `humanoid` or `anthropomorphic`. We deliberately also exclude `human-like`, `human-shaped`, `human-form` and `android robot` as source-abstract cues. The selection is disjoint from the first random 100 and the explicit-term 50/50 challenge (200 unique prior families).

The **40 positive** provisional labels describe: 14 full torso–arms–legs robots, 17 articulated biped walking and balance mechanisms with human-style gait relevance, and 9 multi-limb/whole-body tasks and control systems. The **60 negative** labels describe: 10 animal/special-purpose two-footed or human-worn machines, 15 quadrupeds and other nonhuman multilegged robots, 12 dual-arm robot systems without humanoid bodies, 10 general robotic hands, 8 wearable exoskeletons, and 5 specialist mobile robots.

Selection began with fixed-seed, keyword-blind discovery over the **original English patent abstracts** in `humanoid_patents.zip`. Discovery groups helped find cases, but did not automatically assign relevance labels. The chosen family identifiers are fixed in `src/assemble_semantic_holdout.py`; the assembler retrieves exact original records, validates source text and independence, and generates this dataset. There was **no use of Perplexity/Decider predictions** when choosing or labeling these cases.

## How labels should be understood

A positive means that a robot structure or task is substantially relevant to a physically embodied human-type robot, even without literal naming, e.g. a trunk with articulated paired arms and legs, human-gait biped control, or coordination of hands, feet and posture. A negative means the abstract specifically describes a different form factor or only generic equipment without a demonstrable human-body or locomotion connection.

**This task-relevance definition is broader than the existing Decider prompt's strict explicit-humanoid-link criterion.** In particular, some biped-only lower-limb inventions might be disputable. Model disagreements must therefore be analyzed separately as *annotation/construct disagreements* and *inference errors*. Independent subject-matter adjudication, ideally by two blinded reviewers, is required before asserting true recall or choosing a threshold. No positive label should be treated as human gold truth yet.

The CSV's `evidence_quote` is the first 180 verbatim characters of the source abstract, not an independently generated or verified claim-specific explanation. `reason` describes the prespecified review-group justification. Read the **entire abstract** for final adjudication.

## CSVs and Kaggle

- `semantic_holdout_100_labeled.csv`: **single portable test file**; contains `docdb_family_id,abstract_en,label,needs_review,confidence,evidence_quote,reason`.
- `semantic_holdout_100_blind_review.csv`: ID and abstract only for independent relabeling.
- `annotation_audit.csv`: source family, review group, preliminary label and reason.
- `semantic_holdout_100_full.csv`: unmodified source records for provenance; *do not feed titles/CPCs to Decider*.
- `sample_summary.json`: source checksums, class breakdown, and checksums for all outputs.

Kaggle Notebook, after cloning/pulling the repository:

```python
!python kaggle/run.py --dataset samples/humanoid_semantic_holdout_100/semantic_holdout_100_labeled.csv --output /kaggle/working/semantic_holdout_100/predictions.csv
```

The existing `kaggle/run.py --dataset` interface performs **model inference on abstract text only** and then separately reads the labels for `evaluation.json`, `evaluation_cases.csv` and `predictions.csv`. The output directory is isolated from earlier tests.

## Diagnostic lexical baselines

Calculated over the 100 committed source abstracts and provisional labels:

| Baseline | TP | TN | FP | FN | Accuracy |
|---|---:|---:|---:|---:|---:|
| Contains `humanoid` or `anthropomorphic` | 0 | 60 | 0 | 40 | 60% |
| Contains `biped`/`bipedal` or `two-legged`/`two-footed`/`two feet` | 31 | 50 | 10 | 9 | 81% |
| Above, excluding `exoskeleton`, `wearable`, `chicken`, `bird`, or `wall-climbing` | 30 | 56 | 4 | 10 | 86% |

This is harder for trivial terminology detection than the earlier 50/50 challenge, but simple keyword rules still achieve relatively high accuracy. It is a **development stress test**, not an unbiased evaluation of generalization. Deliberate 40/60 enrichment prevents using measured precision directly as production prevalence-weighted precision. Any thresholds tuned on this set must be reported separately from performance on an untouched independent test set.
