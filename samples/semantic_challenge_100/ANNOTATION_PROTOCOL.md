# Semantic challenge: 100 original-English patents with implicit humanlike-robot relevance

**Purpose:** A second model-independent development stress test addressing the prior benchmark's lexical shortcut. All 100 selected patent abstracts come verbatim from the original source ZIP, exclude both earlier 100-family samples, and contain neither standalone **humanoid** nor **anthropomorphic** (including humanoids). 40 assistant-labeled relevant cases are intentionally mixed with 60 related negatives.

Positive operational definition: *independent embodied bipedal robots or systems designed specifically for their joint actuation, gait, balance, whole-body locomotion, or human-like robot tasks*. This definition is broader than the prior model's strictly worded explicit humanoid requirement: disagreements may indicate **definition mismatch**, not a classification error. Negatives: exoskeletons worn by people, four/six-leg robots, standalone generic robot arms/hands, and human-image/virtual agents. Class balancing is purposive, not a population prevalence estimate.

The 100 family IDs and reasons are in `selection_annotations.json`, selected from an independent 780-case candidate pool. Each label is provisional AI-assisted, with source excerpt and explanation. Neither human independent adjudication nor model scoring on these cases has happened. Do not use this as an unbiased held-out production test if subsequent prompts are tuned to its outcomes.

**Single Kaggle input:** `semantic_100_labeled.csv` with `docdb_family_id,abstract_en,label,needs_review,confidence,evidence_quote,reason`. For independent blinded annotation use `semantic_100_for_blind_review.csv`; for source provenance use `semantic_100_full.csv`, `sample_summary.json`, and `annotation_audit.csv`.

From repo root, after `git pull --ff-only`, run:

```bash
python kaggle/run.py --semantic-challenge
```

The runner uses only abstract text for inference; labels are loaded by the evaluator afterward. Outputs are isolated in `/kaggle/working/semantic_100/`. No translation or extra Kaggle Dataset upload required. Scores must be interpreted against provisional labels and benchmark selection biases.
