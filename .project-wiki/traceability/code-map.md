# Evidence to implementation

| Requirement or evidence | Code | State |
| --- | --- | --- |
| Kickoff slide 9: DOCDB-family data | `src/sql_queries.py` | Implemented candidate export; year discrepancy |
| Global multilingual inclusion | `src/sql_queries.py`; `src/translate_abstracts.py` | Captured; translation implementation pending real full-corpus verification |
| Kickoff slide 9: hand-validate ~100 random families | `src/sample_random_100.py`; `samples/random_100/`; `samples/LABELING_PROMPT.md` | Actual source draw generated; AI-assisted labels received, pending independent adjudication; no positives in current 100 |
| Positive-enriched relevance challenge | `src/mine_challenge_candidates.py`; `src/assemble_humanoid_challenge.py`; `samples/humanoid_challenge_100/`; `kaggle/run.py --challenge` | Single combined source-grounded abstract + provisional 50/50 label CSV and legacy split files generated; model inputs isolated to abstract only; challenge GPU inference and human adjudication pending |
| Implicit biped/humanlike semantic stress test | `src/mine_implicit_humanoid_candidates.py`; `src/assemble_semantic_challenge.py`; `samples/semantic_challenge_100/`; `kaggle/run.py --semantic-challenge` | New source-faithful 100-family 40/60 provisional set materialized; lacks explicit humanoid terms; baseline lexical accuracy still high, no GPU evaluation yet |
| Abstract-only calibrated relevance | `kaggle/run.py`; `kaggle/screen.py`; `kaggle/evaluate.py` | FP16 pilot and unresolved-aware evaluator implemented; provisional negative-only labels received; GPU validation, positive examples and threshold selection open |
| Sector trends, competition, PEST | None | Planned |
| Present/future scores, Magic Quadrant | None | Planned |
| Electrolux strategy recommendation | None | Planned |
| Translation behavior | `src/translate_abstracts.py`; `tests/test_translate_abstracts.py` | Implemented; offline-tested |
| Kaggle FP16 setup | `kaggle/run.py`; `kaggle/tests/test_run.py` | Pinned model/dtype conversion, local tests authored; GPU verification pending |

| Keyword-blind additional semantic challenge | `src/mine_keyword_blind_candidates.py`; `src/assemble_semantic_holdout.py`; `samples/humanoid_semantic_holdout_100/`; `kaggle/run.py --dataset` | 100 source-verified families, 40/60 AI provisional labels, no overt humanoid cues and no overlap with first 200; held-out GPU predictions and human adjudication pending |
