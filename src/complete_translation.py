"""Complete a partially translated PATSTAT corpus without losing existing translations.

The committed humanoid_patents_en.zip is the validated seed; humanoid_patents.zip
remains the immutable original source.  Only nonempty missing abstracts are sent
to Gemrouter.  A replacement English archive is emitted ONLY on 100% coverage.
"""

import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import zipfile

import translate_abstracts as translator

VALID_STATUSES = {"original_en", "translated"}
OUTPUT_MEMBER = "humanoid_patents_en.csv"


def partial_records(path):
    """Read existing completed English abstracts. Never trust IDs from ZIP alone."""
    results = {}
    with zipfile.ZipFile(path) as archive:
        members = [name for name in archive.namelist() if name.lower().endswith(".csv") and not name.endswith("/")]
        if len(members) != 1:
            raise ValueError("Partial English ZIP must contain exactly one CSV member")
        with archive.open(members[0]) as raw:
            with io.TextIOWrapper(raw, encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream)
                headers = reader.fieldnames or []
                if set(translator.OUTPUT_FIELDS) - set(headers) or len(headers) != len(set(headers)):
                    raise ValueError("Partial English dataset lacks required source/translation columns")
                for row in reader:
                    if None in row or any(v is None for v in row.values()):
                        raise ValueError("Malformed partial translated dataset")
                    family = row["docdb_family_id"].strip()
                    english = row["abstract_en"].strip()
                    status = row["translation_status"].strip()
                    if not family or family in results or not english or status not in VALID_STATUSES:
                        raise ValueError(f"Invalid or duplicate completed translation {family!r}")
                    # This dataset was normalized to English in its abstract field.
                    if row["abstract"].strip() != english:
                        raise ValueError(f"Existing English abstract/abstract_en mismatch: {family}")
                    results[family] = row
    return results


def compare_seed(source, partial):
    """Verify every seeded translation against its original source family."""
    completed = partial_records(partial)
    source_ids = set()
    eligible = missing = original_en = translated = 0
    for source_row in translator.input_rows(source):
        family = source_row["docdb_family_id"].strip()
        if not family or family in source_ids:
            raise ValueError(f"Duplicate/missing source family {family!r}")
        source_ids.add(family)
        original = source_row["abstract"]
        if not original.strip():
            missing += 1
            if family in completed:
                raise ValueError(f"Partial dataset has no source abstract: {family}")
            continue
        eligible += 1
        row = completed.get(family)
        if row is None:
            continue
        for field in ("year", "title", "title_language", "matched_cpcs"):
            if row[field] != source_row[field]:
                raise ValueError(f"Partial/source metadata differ for {family}: {field}")
        english_source = source_row["abstract_language"].strip().lower() == "en"
        expected_status = "original_en" if english_source else "translated"
        if row["translation_status"] != expected_status:
            raise ValueError(f"Invalid source-language/status assignment for {family}")
        if english_source:
            if row["abstract_en"] != original:
                raise ValueError(f"Original English abstract is not identical for {family}")
            original_en += 1
        else:
            translated += 1
    unexpected = set(completed) - source_ids
    if unexpected:
        raise ValueError(f"{len(unexpected)} completed families not in the source")
    stats = {
        "source_total": len(source_ids),
        "source_missing_abstract": missing,
        "eligible": eligible,
        "seed_completed": len(completed),
        "seed_original_en": original_en,
        "seed_translated": translated,
        "pending": eligible - len(completed),
        "source_sha256": translator.sha256(source),
        "partial_sha256": translator.sha256(partial),
    }
    if original_en + translated != len(completed):
        raise ValueError("Seed status counts do not reconcile")
    if stats["pending"] < 0:
        raise ValueError("More completed families than source-eligible families")
    return completed, stats


def prepare_seed(source, partial, state, endpoint, model):
    """Reconstruct only successful journal records; never retranslate them."""
    completed, stats = compare_seed(source, partial)
    manifest = state.with_suffix(".manifest.json")
    identity = {
        "archive_sha256": stats["source_sha256"],
        "model": model,
        "endpoint": endpoint,
        "prompt_version": translator.PROMPT_VERSION,
    }
    state.parent.mkdir(parents=True, exist_ok=True)
    if state.exists() or manifest.exists():
        if not state.exists() or not manifest.exists():
            raise ValueError("Interrupted state without matching manifest")
        if json.loads(manifest.read_text(encoding="utf-8")) != identity:
            raise ValueError("Existing journal belongs to another source/model/endpoint")
        prior = translator.load_progress(state)
        for family, seed_row in completed.items():
            item = prior.get(family)
            if item is None or item["abstract_en"] != seed_row["abstract_en"] or item["translation_status"] != seed_row["translation_status"]:
                raise ValueError(f"Resumed journal does not preserve seed family {family}")
        if set(prior) - set(completed):
            source_ids = {row["docdb_family_id"].strip() for row in translator.input_rows(source)}
            if set(prior) - source_ids:
                raise ValueError("Resumed journal contains unknown family IDs")
    else:
        tmp = state.with_suffix(".jsonl.tmp")
        with tmp.open("w", encoding="utf-8") as stream:
            # Preserve stable, source-family ordering. No API calls during seeding.
            for source_row in translator.input_rows(source):
                family = source_row["docdb_family_id"].strip()
                row = completed.get(family)
                if row is not None:
                    stream.write(json.dumps({
                        "docdb_family_id": family,
                        "abstract_en": row["abstract_en"],
                        "translation_status": row["translation_status"],
                    }, ensure_ascii=False) + "\n")
        os.replace(tmp, state)
        # Manifest contains the secret endpoint; keep it in ignored outputs only.
        translator.atomic_json(manifest, identity)
    return stats


def normalize_zip(translated_csv, destination, expected_eligible):
    """Make abstract itself English, preserve source-language metadata separately."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = destination.with_suffix(".zip.tmp")
    processed = english_original = translated = 0
    try:
        with translated_csv.open(newline="", encoding="utf-8-sig") as source_stream, zipfile.ZipFile(
            temp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6
        ) as archive:
            reader = csv.DictReader(source_stream)
            if reader.fieldnames != translator.OUTPUT_FIELDS:
                raise ValueError("Translator CSV does not match the expected schema")
            with archive.open(OUTPUT_MEMBER, "w") as raw:
                with io.TextIOWrapper(raw, encoding="utf-8", newline="") as stream:
                    writer = csv.DictWriter(stream, fieldnames=translator.OUTPUT_FIELDS)
                    writer.writeheader()
                    for row in reader:
                        english = row["abstract_en"]
                        status = row["translation_status"]
                        if not english.strip() or status not in VALID_STATUSES:
                            raise ValueError("Translator produced an empty/incomplete English abstract")
                        row["abstract"] = english
                        writer.writerow(row)
                        processed += 1
                        english_original += status == "original_en"
                        translated += status == "translated"
        if processed != expected_eligible:
            raise ValueError(f"Replacement ZIP has {processed} rows, expected {expected_eligible}")
        os.replace(temp, destination)
    finally:
        temp.unlink(missing_ok=True)
    # Validate with the actual two-T4 production ingestion contract (no CUDA required).
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "kaggle"))
    from production import inspect_input
    if inspect_input(destination, expected_rows=expected_eligible) != processed:
        raise ValueError("Production input preflight did not validate the English archive")
    # Validate the normalization independently of the screening input checks.
    with zipfile.ZipFile(destination) as archive:
        if archive.testzip() is not None:
            raise ValueError("Corrupt compressed output")
        with archive.open(OUTPUT_MEMBER) as raw:
            with io.TextIOWrapper(raw, encoding="utf-8", newline="") as stream:
                for row in csv.DictReader(stream):
                    if row["abstract"] != row["abstract_en"]:
                        raise ValueError("Final ZIP contains a non-normalized abstract")
    return {"completed": processed, "original_en": english_original, "translated": translated}


def finish(args):
    source = Path(args.source).resolve()
    partial = Path(args.partial).resolve()
    state = Path(args.state).resolve()
    csv_output = Path(args.work_csv).resolve()
    final_zip = Path(args.final_zip).resolve()
    endpoint = os.environ.get("LLM_ENDPOINT", "")
    if not endpoint.startswith("https://"):
        raise ValueError("Set LLM_ENDPOINT to the private HTTPS Chat Completions endpoint")
    stats = prepare_seed(source, partial, state, endpoint, args.model)
    print("Validated committed translation seed:", json.dumps(stats, indent=2), flush=True)
    if args.check:
        return stats
    if stats["pending"] and not os.environ.get("GEMR_API_KEY"):
        raise ValueError("Set GEMR_API_KEY in the GitHub Actions secret")
    last_completed = stats["seed_completed"]
    outcome = None
    for pass_no in range(1, args.passes + 1):
        config = argparse.Namespace(
            input=str(source), output=str(csv_output), state=str(state),
            model=args.model, env=".env", endpoint=endpoint,
            stats_only=False, batch_size=args.batch_size,
            max_batch_chars=args.max_batch_chars, max_requests=args.max_requests,
            rpm=args.rpm, retries=args.retries, backoff=2, timeout=args.timeout,
        )
        outcome = translator.run(config)
        print(f"Translation pass {pass_no}: {outcome['completed']}/{stats['eligible']} eligible, {outcome['incomplete']} remaining", flush=True)
        if outcome["completed"] == stats["eligible"] and outcome["incomplete"] == 0:
            break
        if outcome["completed"] == last_completed or outcome["stop_reason"]:
            break
        last_completed = outcome["completed"]
    if outcome is None or outcome["incomplete"] or outcome["completed"] != stats["eligible"]:
        raise RuntimeError("Translation incomplete; original and partial archives are untouched. Rerun with checkpoint to continue")
    counters = normalize_zip(csv_output, final_zip, stats["eligible"])
    summary = {
        "total": stats["source_total"],
        "missing": stats["source_missing_abstract"],
        "completed": counters["completed"],
        "original_en": counters["original_en"],
        "translated": counters["translated"],
        "incomplete": 0,
        "stop_reason": None,
        "seed_completed": stats["seed_completed"],
        "translated_new": counters["translated"] - stats["seed_translated"],
        "eligible": stats["eligible"],
        "source_sha256": stats["source_sha256"],
        "seed_archive_sha256": stats["partial_sha256"],
        "final_archive_sha256": translator.sha256(final_zip),
        "model": args.model,
        "prompt_version": translator.PROMPT_VERSION,
        "note": "All nonempty abstracts normalized to English in abstract and abstract_en; abstract_language retains original PATSTAT source language. Source families without abstracts excluded.",
    }
    if summary["translated_new"] != stats["pending"]:
        raise ValueError("Translation counts did not reconcile after full export")
    translator.atomic_json(Path(args.summary).resolve(), summary)
    print("Completed translation and validated final archive:", json.dumps(summary, indent=2), flush=True)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default="humanoid_patents.zip")
    parser.add_argument("--partial", default="humanoid_patents_en.zip")
    parser.add_argument("--state", default="outputs/translation/progress.jsonl")
    parser.add_argument("--work-csv", default="outputs/translation/humanoid_patents_en.csv")
    parser.add_argument("--final-zip", default="outputs/translation/final_humanoid_patents_en.zip")
    parser.add_argument("--summary", default="outputs/translation/humanoid_patents_en_summary.json")
    parser.add_argument("--model", default="gemini-cascade")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--max-batch-chars", type=int, default=12000)
    parser.add_argument("--max-requests", type=int, default=600)
    parser.add_argument("--rpm", type=float, default=20)
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--passes", type=int, default=3)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if min(args.batch_size, args.max_batch_chars, args.max_requests, args.passes) < 1 or args.rpm <= 0:
        parser.error("Batch, character, request, pass and rate settings must be positive")
    finish(args)


if __name__ == "__main__":
    main()
