---
id: CURRENT-PLAN
type: note
status: active
title: Current Plan
created: '2026-10-29'
updated: '2026-10-30'
tags: []
related: []
source_paths: []
confidence: confirmed
---

# Execution stages

1. **Implemented:** TIP/PATSTAT broad DOCDB-family candidate extraction including multilingual title/abstract metadata.
2. **Implemented in code; awaiting live verification:** resumable full-corpus abstract translation, independent of screening.
3. **Pilot sample generated:** uniform 100 original-English families from 232,636 eligible source abstracts committed in `samples/random_100/`; the earlier 90/10 multilingual stratified sampler (`src/sample_abstracts.py`) remains a separate path.
4. **Pilot launcher implemented and run on Kaggle:** `python kaggle/run.py` is the one-command Kaggle entrypoint after cloning, detecting the committed English sample and installing/downloading the pinned native Decider Flash v1.2 model. It patches one exact dtype assignment locally for FP16 on T4, and `screen.py` checks the resulting model dtype. Results journal probabilities, and `evaluate.py` can compare with independent manual labels. 100 native-English cases produced output on one T4 (all probabilities under 0.5). Quantitative performance on genuine positive humanoid patents and production throughput remain unverified.
5. **Provisional labels received:** 100 IDs match, 98 labeled negatives, zero positives, two unresolved. The evaluator now handles unresolved labels without failure and emits specificity/FPR, not unsupported recall/F1. **Next:** independently adjudicate labels, obtain a separate positive-enriched sample and design held-out calibration and testing. For the full corpus, benchmark two disjoint independent FP16 worker processes (one GPU/model copy each) against the existing single-GPU baseline before selecting parallelization; no two-GPU code is implemented yet.
6. **Curated challenge ready with a single labeled CSV:** `samples/humanoid_challenge_100/challenge_100_labeled.csv` contains a new disjoint 100-family English case-control benchmark, assistant-provisionally labeled 50 positive and 50 negative, with 10 lexical decoys and 30 close robotics negatives. GitHub generated/verified source-faithful inputs and labels. Run `python kaggle/run.py --challenge` next; the model gets only abstract text and the evaluator later reads labels from that same CSV. Review disagreements, independently adjudicate labels and preserve a separate held-out evaluation before tuning any threshold. No challenge inference has been recorded yet.
7. **Later:** corrected temporal metadata, applicant normalization, sector landscape, present/future scores and no-leakage backtest, quadrant, recommendation, deck and pitch.

Deadline: 20 December 2026.
