---
id: TECH-SECURITY
type: technical
status: active
title: Security
created: '2026-10-29'
updated: '2026-10-29'
tags: []
related: []
source_paths: []
confidence: confirmed
---

# Secrets and data

Keep `GEMR_API_KEY` and `LLM_ENDPOINT` in local `.env`, which is ignored. Do not expose keys in commits, logs, failures, or examples. Patent abstracts are transmitted to a configured external model endpoint: verify provider handling before submitting. The translation directory `outputs/translation/` is ignored. The repository already tracks `humanoid_patents.zip`; avoid committing additional bulk extracts.
