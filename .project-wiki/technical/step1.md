---
id: TECH-STEP1
type: technical
status: active
title: Step 1 landscape implementation
created: '2026-11-25'
updated: '2026-11-25'
tags: []
related: [STEP1-PLAN, TECH-CODEBASE-MAP, TECH-TESTING]
source_paths: [src/step1_extract.py, src/step1_landscape.py, src/step1_semantic.py, tests/test_step1.py, config/step1.json, requirements-step1.txt]
confidence: confirmed
---

# Runbook

Install CPU dependencies: python -m pip install -r requirements-step1.txt

Preview (committed dataset, no TIP, no model download):

    python src/step1_landscape.py --semantic tfidf

The preview only generates provisional family priority-proxy volume/growth, query-origin and exploratory clusters. No CPC mix or countries are fabricated from the partial source schema. Every run gets a manifest with input hash, mode and caveats. Use an empty output directory.

Run from TIP with the same frozen CSV and config; specify the actual PATSTAT edition:

    python src/step1_extract.py --edition YOUR_PATSTAT_RELEASE --env PROD

Transfer the resulting local data/step1_local folder privately, not via Git. The export uses normalized application, CPC, person-role, WIPO and global aggregate tables. Its manifest is written last and binds input/config/table hashes and counts. TEST is development only.

    python src/step1_landscape.py --metadata data/step1_local --out outputs/step1_prod --semantic none

For domain-model analysis install sentence-transformers in a separate environment and record package versions. Resolve the professor model's exact revision from its HF page (40 hex characters):

    python src/step1_landscape.py --metadata data/step1_local --out outputs/step1_patent --semantic patent --revision MODEL_COMMIT

Outputs: annual volume/growth, benchmark and raw observed truncated counts; fractional CPC, WIPO, applicant/inventor series and complete-period summaries; filing offices, PCT and office breadth; optional assignments, terms, representative IDs and annual cluster shares. Main figure candidates are PNGs, underlying CSVs are authoritative. Review top CPC titles against official scheme and append to the summary before using in deck; not automated. Model-free IP literature synthesis is in the [plan](../implementation/step1-plan.md).

Tests: python -m unittest discover -s tests -p test_step1.py -v. Synthetic checks exercise preview and metadata path, weights, missingness, zero base and truncation. GitHub workflow runs CPU preview and publishes an artifact (no remote data export/API calls, no GPU). Actual TIP execution and patent-model inference remain unverified until run evidence. No validated semantic labels are produced.

Known limitations: person IDs can duplicate real persons; family WIPO weights depend on application composition; office breadth excludes WO but EP is regional; no time-varying ownership harmonization. Full aggregate outputs are still provisional relevance-selected statistics. Input data remain unchanged. Do not interpret partial-period growth.

2026-11-25 — [GitHub Actions run 45583655627](https://github.com/roccoangelella/Innovation-management-group-7/actions/runs/45583655627) succeeded: six synthetic tests passed; the actual source-only preview processed all 7,102 family IDs with matching source SHA256, 7,026 within 2000–2026, zero missing year proxies. TF-IDF K-means k=10 used all 7,102 abstracts, cosine silhouette (1,000-sample) 0.01032546, two-seed ARI 0.59438722. Weak cluster separation and imperfect stability; do not interpret clusters as final technology segments. [Eight-file artifact 15007242429](https://github.com/roccoangelella/Innovation-management-group-7/actions/runs/45583655627/artifacts/15007242429), expires 2027-02-23; ZIP SHA256 `449e60ff463c2e419b5c202a02f0c70633c15e694459588893aac31576308373`. PROD metadata, validated relevance and patent-SBERT inference remain unverified.
