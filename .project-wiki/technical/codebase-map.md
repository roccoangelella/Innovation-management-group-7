---
id: TECH-CODEBASE-MAP
type: technical
status: active
title: Codebase Map
created: '2026-10-29'
updated: '2026-10-29'
tags: []
related: []
source_paths: []
confidence: confirmed
---

# Repository map

| Path | Current responsibility |
| --- | --- |
| `src/sql_queries.py` | TIP/PATSTAT export using 64 CPC prefixes; one CSV in a ZIP |
| `src/translate_abstracts.py` | Whole-corpus translation, batch validation, journal, final CSV |
| `tests/test_translate_abstracts.py` | Offline translation tests using mocks |
| `humanoid_patents.zip` | Existing tracked, large candidate corpus |
| `README.md` | Translation operations, resumption and completeness requirements |
| `pyproject.toml` | Python >=3.12 and packaging metadata |
| `.gitignore` | Ignores secrets, translation output and Python artifacts |

Run `python src/translate_abstracts.py --stats-only` for corpus preflight; `python src/translate_abstracts.py` for production translation; `python -m unittest discover -s tests -v` for offline tests. TIP export runs where `epo.tipdata.patstat` is available. No landscaping, decision-model, scoring, or quadrant implementation is visible in the scanned repository.
