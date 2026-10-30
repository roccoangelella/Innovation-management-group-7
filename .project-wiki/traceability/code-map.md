# Evidence to implementation

| Requirement or evidence | Code | State |
| --- | --- | --- |
| Kickoff slide 9: DOCDB-family data | `src/sql_queries.py` | Implemented candidate export; year discrepancy |
| Global multilingual inclusion | `src/sql_queries.py`; `src/translate_abstracts.py` | Captured; translation implementation pending real full-corpus verification |
| Abstract-only calibrated relevance | `kaggle/run.py`; `kaggle/screen.py`; `kaggle/evaluate.py` | FP16 pilot implemented; Kaggle inference, manual labels, validation and threshold open |
| Sector trends, competition, PEST | None | Planned |
| Present/future scores, Magic Quadrant | None | Planned |
| Electrolux strategy recommendation | None | Planned |
| Translation behavior | `src/translate_abstracts.py`; `tests/test_translate_abstracts.py` | Implemented; offline-tested |
| Kaggle FP16 setup | `kaggle/run.py`; `kaggle/tests/test_run.py` | Pinned model/dtype conversion, local tests authored; GPU verification pending |
