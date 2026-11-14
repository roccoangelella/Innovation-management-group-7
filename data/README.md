# Patent datasets

The dataset archives are grouped by processing stage. Git moves preserve Git blob identities, bytes, internal member names, and SHA-256 digests.

| Stage | File | Purpose |
| --- | --- | --- |
| Novel candidate extract | `new_humanoid_patents.zip` | Additional DOCDB families from the separate expanded query; not yet translated or screened. See [novel pipeline](../kaggle/NOVEL_PRODUCTION.md). |\n| Raw | `raw/humanoid_patents.zip` | TIP/PATSTAT candidate extract, 238,824 DOCDB families; 1,286 have no abstract |
| Translated | `translated/humanoid_patents_en.zip` | All 237,538 families with nonempty English abstracts |
| Translated | `translated/humanoid_patents_en_summary.json` | Translation coverage and SHA256 provenance |
| Filtered | `filtered/filtered_patents.zip` | 3,116 provisionally relevant patent families (threshold 0.5), with source metadata |
| Filtered | `filtered/production_summary.json` | Full-corpus screening counts and SHA256 digests |

Archive SHA-256 checksums:
- Raw: `fbdc57c362f076cee1a7da5c98d7309e398425c48015064bcbf78eba4c329e72`
- English: `b7ce0a36f0b3e2778292bdfe10058eb81749b304b62ed6d965dfcc837103276c`
- Filtered: `0ed14dbe15b61a017a34d9d691b4d0cce75dce541fc135c920de589189b9e65a`

The complete, unthresholded `predictions.csv` is retained as part of [GitHub Actions run 43149578365](https://github.com/roccoangelella/Innovation-management-group-7/actions/runs/43149578365), artifact `13927463611` (expires 2026-12-12). The [validation run](https://github.com/roccoangelella/Innovation-management-group-7/actions/runs/43191381227) independently checked the dataset's IDs, probabilities, hash digests, and ZIP contents. W&B [run 5lapyaes](https://forge.coreweave.com/wandb/rocchissimo936-none/humanoid-patent-filtering/runs/5lapyaes) independently reported 237,538 families processed (118,464 + 119,074).

**Caveat:** 0.5 is an exploratory decision threshold. The retained 3,116 families have not been independently human-adjudicated. Before interpreting the subset as the true humanoid patent landscape, validate selected and rejected families.

The small `samples/random_100/random_100_for_translation.zip` stays under `samples/` as an independent benchmark/sampling artifact, not as a redundant production archive.
