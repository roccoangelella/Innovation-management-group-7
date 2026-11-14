# Innovation Management · Group 7 — Humanoid robots (Electrolux)

Patent-based sector scouting for the 2026/27 Innovation Management project at Politecnico di Torino. Unit of analysis: **DOCDB patent family**.

## Datasets

| Stage | File | Families |
| --- | --- | ---: |
| TIP/PATSTAT extract | [Raw patents](data/raw/humanoid_patents.zip) | 238,824 |
| Nonempty English abstracts (original + translated) | [English corpus](data/translated/humanoid_patents_en.zip) | 237,538 |
| Provisional Perplexity Decider Flash screening (threshold 0.5) | [Retained patents](data/filtered/filtered_patents.zip) | 3,116 |

The raw extract contains 1,286 families without abstracts. The full set of 237,538 screening decisions was independently checked for ID and archive integrity. **Relevance decisions are provisional, not human-validated.** See [dataset provenance, checksums, and prediction artifacts](data/README.md).

## Pipeline

1. **Collect:** [TIP/PATSTAT SQL queries](src/sql_queries.py).
2. **Translate:** [English-abstract translation](src/translate_abstracts.py) using a locally configured private endpoint (credentials must not be committed).
3. **Screen:** [Perplexity Decider Flash on two Kaggle T4 GPUs](kaggle/PRODUCTION.md), implemented in [production_run.py](kaggle/production_run.py).
4. **Validate:** [100-family evaluation runner](kaggle/run.py) and [validation methodology](.project-wiki/technical/testing.md).

To check the completed English corpus before a GPU run:

```bash
python kaggle/production_run.py --input data/translated/humanoid_patents_en.zip --expected-rows 237538 --check
```

Offline tests: `python -m unittest discover -s tests -v` and `python -m unittest discover -s kaggle/tests -v`.

## Perplexity validation — 31 October 2026

**Keyword-blind, purposively selected holdout:** 100 original-English patent families (40 provisionally relevant, 60 provisionally irrelevant), threshold **0.5**. Metrics are against **AI-provisional labels**, not independent human ground truth.

| Class | Precision | Recall | F1 | Support |
| --- | ---: | ---: | ---: | ---: |
| Irrelevant (0) | 0.966 | 0.933 | 0.949 | 60 |
| Relevant (1) | 0.905 | 0.950 | **0.927** | 40 |
| Macro average | 0.935 | 0.942 | 0.938 | 100 |
| Weighted average | 0.941 | 0.940 | 0.940 | 100 |

**Accuracy:** 0.940 · **Confusion matrix:** TP 38, FP 4, TN 56, FN 2 · **Specificity:** 0.933.

This is a stress test, **not** an unbiased estimate of production precision, recall, or threshold calibration. Independent blinded annotation and representative evaluation remain necessary. Details: [testing evidence](.project-wiki/technical/testing.md) · [sample/annotation protocol](samples/humanoid_semantic_holdout_100/ANNOTATION_PROTOCOL.md).

## Documentation

[Project wiki](.project-wiki/INDEX.md) · [Kaggle production guide](kaggle/PRODUCTION.md) · [Dataset provenance](data/README.md)
