# Project Status

Updated 2026-10-30. Project documentation reflects the course kickoff, project decisions and current `main` repository code.

**Implemented in code:** broad CPC patent export; resumable multilingual translation; deterministic 100-family stratified sampling; isolated Kaggle Decider Flash v1.2 FP16 pilot with `python kaggle/run.py`, native decision readout, probability journal and optional evaluation. This includes a pinned checkpoint and exact-match local dtype patch to FP16.

**Not verified as complete:** live endpoint translation to full coverage, actual Kaggle GPU compatibility and inference, 100-family human annotations, calibrated relevance threshold, firm scoring, quadrant or client recommendation.

**Next:** generate/attach the translated 100-family CSV; execute the single-command Kaggle pilot on a GPU, inspect errors and outputs; evaluate independently annotated labels; resolve year semantics (priority vs filing). Open issues: [questions](requirements/open-questions.md). **Submission:** Sunday 20 December 2026.
