# Project Status

Updated 2026-10-30. Current main includes TIP/PATSTAT candidate export, resumable translation code, two distinct 100-family samplers, and an isolated Perplexity Decider Flash v1.2 FP16 Kaggle pilot.

**Observed sample:** Uniform seeded sample over 232,636 original-English nonempty abstracts (238,824 source rows in all); 100 original-English families saved under `samples/random_100/`, with source text copied verbatim into `abstract_en`. The previously proposed 90/10 multilingual/CPC-stratified sampler is separate.

**Provisional labels provided 2026-10-30:** 100 unique sample IDs match the source list in order; 98 labeled not relevant, 0 labeled relevant, 2 marked for review. The label data were AI-assisted in another chat and have not been independently adjudicated. No precision/recall/F1 can currently be validated without positive labeled examples.

**Implemented but not GPU-verified:** `python kaggle/run.py` downloads/loads the native Decider Flash checkpoint as FP16 on CUDA, scores the committed sample, and (when the labeling CSV is attached as a Kaggle Dataset) automatically evaluates predictions. Evaluation excludes unresolved labels and reports specificity, false-positive rate, and 95% Wilson interval. No actual Kaggle GPU run has been witnessed.

**Next:** run a Kaggle GPU pilot and inspect results, independently review provisional labels, and create an additional *positive-enriched* evaluation set for recall and threshold calibration. Translation, applicant/year corrections, landscaping, valuation, quadrant and recommendation remain separate work. Deadline: Sunday 20 December 2026.
