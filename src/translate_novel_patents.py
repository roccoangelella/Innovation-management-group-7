"""Translate only novel DOCDB families and produce a provenance-preserving Kaggle CSV.

This is intentionally separate from the completed 237,538-family production corpus.
Run from repository root; no GemRouter API call is made with --check.
"""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import sys
import zipfile

import translate_abstracts as tr

SOURCE = Path("data/new_humanoid_patents.zip")
BASELINE = Path("data/raw/humanoid_patents.zip")
WORKDIR = Path("outputs/novel_translation")
CSV_NAME = "novel_humanoid_patents_en.csv"
SUMMARY_NAME = "novel_translation_summary.json"


def baseline_ids(path):
    with zipfile.ZipFile(path) as archive:
        with archive.open("humanoid_patents.csv") as raw:
            import io
            with io.TextIOWrapper(raw, encoding="utf-8-sig", newline="") as stream:
                for row in csv.DictReader(stream):
                    yield row["docdb_family_id"].strip()


def validate_source(source, baseline):
    member, fields = tr.source_layout(source)
    if member != "new_humanoid_patents.csv" or fields != tr.NOVEL_SOURCE_FIELDS:
        raise ValueError("Expected the novel PATSTAT archive with provenance columns")
    original = set(baseline_ids(baseline))
    if not original:
        raise ValueError("Baseline source is empty; cannot verify novelty")
    seen = set()
    count = 0
    for row in tr.input_rows(source):
        family = row["docdb_family_id"].strip()
        if not family.isdecimal() or int(family) <= 0 or family in seen:
            raise ValueError(f"Invalid/duplicate new DOCDB family {family!r}")
        if family in original:
            raise ValueError(f"Novel extract overlaps the baseline: {family}")
        if not row["matching_channels"].strip():
            raise ValueError(f"Missing retrieval provenance for family {family}")
        seen.add(family)
        count += 1
    if count == 0:
        raise ValueError("Novel input contains no patent families")
    stats = tr.inspect(source)
    if stats["total"] != count:
        raise AssertionError("Novel source count changed during validation")
    return stats


def create_english_csv(source, translated_csv, final_csv, expected):
    """Normalize abstract to English, retaining ALL original PATSTAT columns."""
    _, fields = tr.source_layout(source)
    full_fields = fields + ["abstract_en", "translation_status"]
    tmp = final_csv.with_suffix(".csv.tmp")
    total = originals = translated = 0
    try:
        with translated_csv.open(newline="", encoding="utf-8") as src, tmp.open(
            "w", newline="", encoding="utf-8"
        ) as dst:
            reader = csv.DictReader(src)
            if reader.fieldnames != full_fields:
                raise ValueError("Translator omitted or reordered novel PATSTAT provenance")
            writer = csv.DictWriter(dst, fieldnames=full_fields)
            writer.writeheader()
            for row in reader:
                english = row["abstract_en"]
                status = row["translation_status"]
                if not english.strip() or status not in ("original_en", "translated"):
                    raise ValueError("Incomplete translation must not reach Kaggle")
                if status == "original_en" and row["abstract"] != english:
                    raise ValueError("English source text changed")
                row["abstract"] = english
                writer.writerow(row)
                total += 1
                originals += status == "original_en"
                translated += status == "translated"
        if total != expected:
            raise ValueError(f"Output includes {total} of {expected} eligible families")
        os.replace(tmp, final_csv)
    finally:
        tmp.unlink(missing_ok=True)
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "kaggle"))
    from production import inspect_input
    if inspect_input(final_csv, expected_rows=expected) != total:
        raise AssertionError("Decider production preflight rejected normalized output")
    return {"completed": total, "original_en": originals, "translated": translated}


def sha256(path):
    return tr.sha256(path)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, default=SOURCE)
    p.add_argument("--baseline", type=Path, default=BASELINE)
    p.add_argument("--work-dir", type=Path, default=WORKDIR)
    p.add_argument("--model", default="gemini-cascade")
    p.add_argument("--max-requests", type=int, default=600, help="GemRouter API attempts per pass")
    p.add_argument("--passes", type=int, default=5)
    p.add_argument("--rpm", type=float, default=20)
    p.add_argument("--check", action="store_true", help="Offline source/overlap audit only")
    a = p.parse_args()
    if a.max_requests < 1 or a.passes < 1 or a.rpm <= 0:
        p.error("max-requests, passes and rpm must be positive")
    stats = validate_source(a.source, a.baseline)
    stats["source_sha256"] = sha256(a.source)
    print("NOVEL_SOURCE_AUDIT=" + json.dumps(stats, sort_keys=True), flush=True)
    if a.check:
        return

    work = a.work_dir
    work.mkdir(parents=True, exist_ok=True)
    final_csv = work / CSV_NAME
    summary_file = work / SUMMARY_NAME
    if final_csv.is_file() and summary_file.is_file():
        old = json.loads(summary_file.read_text(encoding="utf-8"))
        if (old.get("source_sha256") == stats["source_sha256"]
            and old.get("completed") == stats["total"] - stats["missing"]
            and old.get("incomplete") == 0
            and old.get("final_csv_sha256") == sha256(final_csv)):
            sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "kaggle"))
            from production import inspect_input
            inspect_input(final_csv, expected_rows=old["completed"])
            print("ALREADY_COMPLETE=" + str(old["completed"]), flush=True)
            return
        raise ValueError("Previously published English output does not match source; use a fresh work directory")

    if not os.getenv("LLM_ENDPOINT", "").startswith("https://"):
        raise ValueError("Missing secure LLM_ENDPOINT/GEMROUTER_ENDPOINT; set before dispatch")
    if not os.getenv("GEMR_API_KEY"):
        raise ValueError("Missing GEMR_API_KEY")
    state = work / "progress.jsonl"
    translated_csv = work / "translator_intermediate.csv"
    outcome = None
    for pass_number in range(1, a.passes + 1):
        args = argparse.Namespace(
            input=str(a.source), output=str(translated_csv), state=str(state),
            env=".env", endpoint=os.environ["LLM_ENDPOINT"], model=a.model,
            stats_only=False, batch_size=8, max_batch_chars=12000,
            max_requests=a.max_requests, rpm=a.rpm, retries=2,
            backoff=2, timeout=180,
        )
        previous = len(tr.load_progress(state))
        outcome = tr.run(args)
        print(f"NOVEL_TRANSLATION_PASS={pass_number} complete={outcome['completed']} incomplete={outcome['incomplete']}", flush=True)
        if not outcome["incomplete"]:
            break
        if outcome["stop_reason"] != "request_budget" or len(tr.load_progress(state)) <= previous:
            break
    if outcome is None or outcome["incomplete"] or outcome["stop_reason"] not in (None, "request_budget"):
        raise RuntimeError("Novel translation is incomplete; resume with the same verified journal artifact")

    eligible = stats["total"] - stats["missing"]
    counts = create_english_csv(a.source, translated_csv, final_csv, eligible)
    summary = {
        **counts, "total": stats["total"], "missing": stats["missing"],
        "eligible": eligible, "incomplete": 0, "stop_reason": None,
        "source_sha256": stats["source_sha256"],
        "final_csv_sha256": sha256(final_csv),
        "model": a.model, "prompt_version": tr.PROMPT_VERSION,
        "source_archive": str(a.source), "source_member": "new_humanoid_patents.csv",
        "normalization": "abstract and abstract_en are English; abstract_language retains source language",
    }
    tr.atomic_json(summary_file, summary)
    print("NOVEL_TRANSLATION_COMPLETE=" + json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
