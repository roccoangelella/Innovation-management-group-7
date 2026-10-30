# Evidence to implementation

| Requirement or evidence | Code | State |
| --- | --- | --- |
| Kickoff slide 9: DOCDB-family data | `src/sql_queries.py` | Implemented candidate export; year discrepancy |
| Global multilingual inclusion | `src/sql_queries.py`; `src/translate_abstracts.py` | Captured; translation implementation pending real full-corpus verification |
| Kickoff slide 9: hand-validate ~100 random families | `src/sample_random_100.py`; `samples/random_100/`; `samples/LABELING_PROMPT.md` | Actual source draw generated; AI-assisted labels received, pending independent adjudication; no positives in current 100 |
| Positive-enriched relevance challenge | `src/mine_challenge_candidates.py`; `src/assemble_humanoid_challenge.py`; `samples/humanoid_challenge_100/`; `kaggle/run.py --challenge` | Separate 100 source-grounded English families and 50/50 AI provisional labels generated; GPU challenge inference and human adjudication pending |
| Abstract-only calibrated relevance | `kaggle/run.py`; `kaggle/screen.py`; `kaggle/evaluate.py` | FP16 pilot and unresolved-aware evaluator implemented; provisional negative-only labels received; GPU validation, positive examples and threshold selection open |
| Sector trends, competition, PEST | None | Planned |
| Present/future scores, Magic Quadrant | None | Planned |
| Electrolux strategy recommendation | None | Planned |
| Translation behavior | `src/translate_abstracts.py`; `tests/test_translate_abstracts.py` | Implemented; offline-tested |
| Kaggle FP16 setup | `kaggle/run.py`; `kaggle/tests/test_run.py` | Pinned model/dtype conversion, local tests authored; GPU verification pending |
