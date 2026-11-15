# Patent datasets

The dataset archives are grouped by processing stage. Git moves preserve Git blob identities, bytes, internal member names, and SHA-256 digests.

| Stage | File | Purpose |
| --- | --- | --- |
| Novel candidate extract | `new_humanoid_patents.zip` | Additional DOCDB families from the separate expanded query; not yet translated or screened. See [novel pipeline](../kaggle/NOVEL_PRODUCTION.md). |\n| Raw | `raw/humanoid_patents.zip` | TIP/PATSTAT candidate extract, 238,824 DOCDB families; 1,286 have no abstract |
| Translated | `translated/humanoid_patents_en.zip` | All 237,538 families with nonempty English abstracts |
| Translated | `translated/humanoid_patents_en_summary.json` | Translation coverage and SHA256 provenance |
| Filtered | `filtered/filtered_patents.zip` | 3,116 provisionally relevant patent families (threshold 0.5), with source metadata |
| Filtered | `filtered/production_summary.json` | Full-corpus screening counts and SHA256 digests |
| **Final** | **`final/humanoid_patents_final.csv`** | **7,102 unique, source-verified positive DOCDB families: 3,116 original + 3,986 novel** |

Archive SHA-256 checksums:
- Raw: `fbdc57c362f076cee1a7da5c98d7309e398425c48015064bcbf78eba4c329e72`
- English: `b7ce0a36f0b3e2778292bdfe10058eb81749b304b62ed6d965dfcc837103276c`
- Filtered: `0ed14dbe15b61a017a34d9d691b4d0cce75dce541fc135c920de589189b9e65a`

The complete, unthresholded `predictions.csv` is retained as part of [GitHub Actions run 43149578365](https://github.com/roccoangelella/Innovation-management-group-7/actions/runs/43149578365), artifact `13927463611` (expires 2026-12-12). The [validation run](https://github.com/roccoangelella/Innovation-management-group-7/actions/runs/43191381227) independently checked the dataset's IDs, probabilities, hash digests, and ZIP contents. W&B [run 5lapyaes](https://forge.coreweave.com/wandb/rocchissimo936-none/humanoid-patent-filtering/runs/5lapyaes) independently reported 237,538 families processed (118,464 + 119,074).

**Caveat:** 0.5 is an exploratory decision threshold. The retained 3,116 families have not been independently human-adjudicated. Before interpreting the subset as the true humanoid patent landscape, validate selected and rejected families.

The small `samples/random_100/random_100_for_translation.zip` stays under `samples/` as an independent benchmark/sampling artifact, not as a redundant production archive.


## Final unified CSV (2026-11-15)

`data/final/humanoid_patents_final.csv` contains **7,102 unique DOCDB families**, one row per family (17,371,429 bytes). It was rebuilt from the separately verified original 3,116-family ZIP and the [novel 3,986-family ZIP](https://github.com/roccoangelella/Innovation-management-group-7/actions/runs/43710629726/artifacts/14162007316) using `src/build_final_humanoid_dataset.py`, which enforces the original and novel filtered ZIP SHA256 digests, column layouts, binary decisions, expected counts, source family uniqueness, and **zero overlap** between batches. The final CSV's expected SHA-256 is `de06e29a8c9053a80183ee3ed2e739d6e552892c528f8b93cb348adc70fc6132`.

**Column contract:** `docdb_family_id`, `year`, `title`, `title_language`, `abstract`, `abstract_language`, `abstract_en`, `translation_status`, `matched_cpcs`, `all_cpcs`, `ipr_types`, `matching_channels`, `probability_relevant`, `model_decision`, `source_query`. `abstract_en` is the canonical English text for analysis. The `abstract` column retains its input batch's staged value: original-query rows retain original abstract text, while novel-query rows were normalized to English during translation. Source query is `original_64_cpc` or `novel_v3`.

**CPC scope is not interchangeable:** `matched_cpcs` contains only CPC prefixes matched by the original 64-CPC extraction, whereas `all_cpcs` contains the complete available classifications as returned by the novel V3 query. Blank cells in one column indicate that source did not provide that field; do not treat them as no CPC classifications. `ipr_types` and `matching_channels` are available only for the novel query.

All rows are **provisional model positives at threshold 0.5**. They are neither independently human-adjudicated positives nor an unbiased estimate of patent-landscape recall. Empty-abstract and model-negative families are intentionally excluded from this final positive-only CSV. The original archive and the full model decision artifacts remain separately available for reproducibility and auditing.
