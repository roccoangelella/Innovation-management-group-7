# Humanoid Challenge 100 — annotation and sampling protocol

This is a deliberately **positive-enriched**, English-only benchmark for checking the *unmodified* Perplexity Decider Flash v1.2 prompt, **not** a random population sample.

Exactly **50 positive** examples and **50 negatives** were chosen by the assistant after inspecting original source abstracts before running Decider on these cases. Candidates were discovered by abstract terminology and separately reviewed: 50 explicit humanoid/anthropomorphic embodied-robot positives, 30 difficult nonhumanoid robotics negatives, 10 lexical-decoy negatives that mention humanoid/anthropomorphic language without humanoid-robot relevance, and 10 clear nonhumanoid negatives. The earlier 100-family random test was excluded. The "discovery_bucket" tags are *not* labels.

## Label definition

- `1`: Abstract explicitly and substantively describes a humanoid / anthropomorphic embodied robot or a subsystem/control/task expressly developed for it.
- `0`: Abstract is unrelated or describes only generic robot hands, robotic arms, mobility, legged robots, human-robot interaction, medical robots, autonomous machines, or industrial automation without an explicit humanoid-specific link.

Examples deliberately mix literal 'humanoid' terminology with anthropomorphic robot descriptions and non-robot uses of the same words; this avoids making a single-keyword rule a complete solution. The strict explicit-link boundary is the *same* as the existing Kaggle model question, so this benchmark tests the current rule rather than silently substituting broad usefulness to humanoids. Some negatives have components potentially usable by a humanoid, but their abstracts do not establish that application. The 10 lexical-decoy negatives mention words such as 'humanoid' in virtual avatars, displays, or figurines without describing humanoid robotics. For borderline applications, the annotations remain AI-assisted and should be independently adjudicated before any accuracy claim.

The labels, short rationales and verbatim source excerpts are **AI-authored provisional annotations, not independent human ground truth**. They have not been model-calibrated or independently adjudicated. Please review the 100 annotations and especially the medium-confidence hard negatives before using these results to claim model performance.

## Files

- `humanoid_100_abstracts_en.csv`: direct Kaggle input (English abstract duplicated exactly to `abstract_en`, original source preserved).
- `humanoid_100_manual_labels.csv`: direct `kaggle/evaluate.py` input, same columns as prior pilot, 50/50 binary labels.
- `annotation_audit.csv`: why each provisional label was chosen, grouped by positive/hard negative/clear negative.
- `challenge_100_full.csv`: original seven source fields.
- `challenge_100_for_labeling.csv`: re-annotation input without title or CPC; use for independent blind human review.
- `selection_annotations.json`: deterministic selected IDs and assistant-written reasons.
- `candidate_pool.jsonl` and `candidate_summary.json`: source-derived candidate discovery provenance, not label predictions.

## Kaggle command

From repo root after pulling latest main, simply run `python kaggle/run.py --challenge`, or use the equivalent explicit command below:

```bash
python kaggle/run.py --input samples/humanoid_challenge_100/humanoid_100_abstracts_en.csv \
  --labels samples/humanoid_challenge_100/humanoid_100_manual_labels.csv \
  --output /kaggle/working/challenge_100/predictions.csv
```

All outputs, including the independent manifest and evaluation files, are stored under `/kaggle/working/challenge_100/` so they do **not** conflict with the original pilot journal. No translation or private endpoint is required.

## Interpretation

Because positives were purposely selected, the sample's class balance is 50% rather than the unknown production prevalence. Its reported precision is **not an estimate of full-corpus precision**. The set can reveal failures and compare fixed decision definitions or model versions, but if a threshold or prompt is chosen based on this set, its score becomes a development score: evaluate on another held-out set. Separate prevalence estimation requires representative sampling. This set contains no non-English patent and cannot assess translation quality.
