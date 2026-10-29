# Innovation Management · Group 7 — Humanoid robotics (Electrolux)

PATSTAT DOCDB-family export: `src/sql_queries.py`. The translation stage below is independent of the SQL extraction and does not alter or filter its source archive.

## Full-corpus patent abstract translation

`src/translate_abstracts.py` reads the existing `humanoid_patents.zip` (`humanoid_patents.csv`) and produces an English-abstract dataset for abstract-only patent screening. It uses only Python 3.12+ standard-library modules; no extra dependencies or Google Gemini SDK are required. The model is `gemini-cascade` through the project's private OpenAI-compatible Chat Completions endpoint.

Configure **locally** in `.env` (this file is ignored by Git):

```dotenv
GEMR_API_KEY="your-private-key"
LLM_ENDPOINT="https://gemr.84-8-255-231.nip.io/v1/chat/completions"
```

From the repository root:

```bash
# Verify languages, missing abstracts and unique DOCDB family IDs; no network calls
python src/translate_abstracts.py --stats-only

# Production run: translates ALL available non-English abstracts (no total request cap)
python src/translate_abstracts.py

# Rerun exactly the same command after a crash, interruption, or endpoint quota reset
python src/translate_abstracts.py

# Optional bounded API smoke test (attempt budget for THIS invocation only)
python src/translate_abstracts.py --max-requests 3

# Offline synthetic tests (never access the private endpoint)
python -m unittest discover -s tests -v
```

### Batch policy

By default, group up to **8** non-English abstracts per request, with a soft limit of **12,000 source characters** per request. An individual long abstract remains intact even if it exceeds this limit. Each abstract is sent separately as an entry with its original `docdb_family_id`, `source_language` from `abstract_language` (or `unknown`), and original text. The prompt specifies faithful English translation, no relevance inference, and strict JSON mapping back to each ID. A malformed/truncated/missing-ID response is **not** accepted as complete: split the batch recursively until individual problematic abstracts can be logged as still pending. Successful batches are journaled immediately; no translation response is reused for the wrong ID.

The first run defaults to **20 requests/minute**, without assuming any provider daily quota or its reset time. Configure it with `--rpm 10` / `--rpm 0` (zero disables pacing). The default `--max-requests` is unlimited; use an explicit number if the proxy has a hard quota. `--retries 2`, `--timeout 180` and `--backoff 2` are configurable. HTTP 429 stops the current run without losing completed records; network/5xx errors get bounded retries. The API key is never committed or logged.

### Output and resumption

- `outputs/translation/progress.jsonl`: append-only durable record of successfully translated abstracts and copied English originals, one entry per DOCDB family. Each append is flushed and fsynced; a truncated final JSONL line is recovered on restart.
- `outputs/translation/progress.manifest.json`: source ZIP SHA-256, model, endpoint, and prompt version (`batch-v1`). A changed source/prompt/model/endpoint requires a **new** state directory/path; changing batch size/rate does not.
- `outputs/translation/progress.failures.jsonl`: compact failure events (ID + error, no source abstract or secret). Failures remain pending and are retried on a subsequent run.
- `outputs/translation/progress.summary.json`: language breakdown, counts, API attempts, successful calls, and remaining records.
- `outputs/translation/humanoid_patents_en.csv`: atomically rebuilt CSV in the original input order, with original seven columns followed by `abstract_en,translation_status`. It contains **only completed nonempty-abstract records**. English source text is copied exactly; source identifiers and original text are unchanged. Empty abstracts are excluded and counted.

**Important:** the CSV may be partial when the run ends with errors or exhausted quota. Use it as a *complete* screening corpus **only when the summary contains `incomplete: 0`**. In Perplexity Decider, pass only `abstract_en` as patent text (not the original language, title, CPC, or translation notes), along with the separately versioned screening definition. The translation step does not perform classification or scoring.

Do not run multiple processes against the same state journal. When a request succeeds but the process crashes before the fsync, that one request may be repeated after restart. Real endpoint compatibility and translation fidelity must be verified by a live test, since the offline tests intentionally use mocked responses.

## Fixed 100-family evaluation benchmark

Run from the repository root:

```bash
python src/sample_abstracts.py
python -m unittest discover -s tests -v
```

The deterministic sampler reads the **unchanged** `humanoid_patents.zip` and selects exactly 90 originally English and 10 originally non-English records, using seed `20261029`. It requires a nonempty abstract and a usable original-language code, detects duplicate DOCDB family IDs, and maintains all seven source columns without labeling or translation. SHA-256 hash-ranked bounded candidate pools make selection independent of input row order; a CPC membership-deficit heuristic encourages technology breadth without imposing equal per-CPC quotas. The ten non-English records are diversified across languages present. One family may cover several CPCs, but is sampled only once.

Outputs (not automatically committed as bulk PATSTAT data):
- `outputs/sampling/humanoid_100_abstracts.csv`: 100 unchanged source rows.
- `outputs/sampling/humanoid_100_abstracts.zip`: identical 100 records archived under `humanoid_patents.csv`, as required by the translation reader.
- `outputs/sampling/sampling_summary.json`: language counts, CPC coverage, missing codes, seed and limitations.

To translate just the sampled ZIP without colliding with the production translation journal:

```bash
python src/translate_abstracts.py --input outputs/sampling/humanoid_100_abstracts.zip --output outputs/sampling/humanoid_100_abstracts_en.csv --state outputs/sampling/translation_progress.jsonl
```

Do **not** apply the default full-corpus translation journal to this subset: the manifest binds each journal to its source ZIP hash. This stage is only evaluation sampling, not classification or annotation. The deliberately fixed 90/10 language mix and the CPC-balanced heuristic mean the benchmark must not be interpreted as a random representative estimate of production-corpus accuracy.
