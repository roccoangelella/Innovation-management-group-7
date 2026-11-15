"""Merge verified old/new Decider Flash retained patent families into one CSV.

Run from repository root with:
  python src/build_final_humanoid_dataset.py --novel novel_screening_output/filtered_patents.zip --novel-summary novel_screening_output/production_summary.json

Preserves query-specific CPC meanings: matched_cpcs (original 64-CPC query),
all_cpcs (novel V3 query). The unified abstract_en is in English.
"""
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import zipfile

ORIGINAL_FIELDS = [
    "docdb_family_id", "year", "title", "title_language", "abstract",
    "abstract_language", "matched_cpcs", "abstract_en", "translation_status",
    "probability_relevant", "model_decision",
]
NOVEL_FIELDS = [
    "docdb_family_id", "year", "title", "title_language", "abstract",
    "abstract_language", "all_cpcs", "ipr_types", "matching_channels",
    "abstract_en", "translation_status", "probability_relevant", "model_decision",
]
OUTPUT_FIELDS = [
    "docdb_family_id", "year", "title", "title_language", "abstract",
    "abstract_language", "abstract_en", "translation_status",
    "matched_cpcs", "all_cpcs", "ipr_types", "matching_channels",
    "probability_relevant", "model_decision", "source_query",
]
EXPECTED = {
    "original_64_cpc": {"n_input": 237538, "kept": 3116,
                        "zip_sha256": "0ed14dbe15b61a017a34d9d691b4d0cce75dce541fc135c920de589189b9e65a",
                        "fields": ORIGINAL_FIELDS},
    "novel_v3": {"n_input": 22437, "kept": 3986,
                 "zip_sha256": "2df33ad44389c23fdab510b86715e29ff6146a427a5093e6e3ee01b723c9b0e2",
                 "fields": NOVEL_FIELDS},
}


def sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_verified(path, summary_path, source):
    expected = EXPECTED[source]
    summary = json.loads(Path(summary_path).read_text(encoding="utf-8"))
    if (summary["n_input"] != summary["n_predictions"] or
            summary["n_input"] != expected["n_input"] or
            summary["n_relevant_exploratory"] != expected["kept"] or
            summary["threshold_exploratory"] != 0.5 or
            summary["filtered_zip_sha256"] != expected["zip_sha256"] or
            sha256(path) != expected["zip_sha256"]):
        raise ValueError("Screening summary or source ZIP SHA256 mismatch: " + source)
    result = {}
    with zipfile.ZipFile(path) as archive:
        if archive.namelist() != ["filtered_patents.csv"] or archive.testzip() is not None:
            raise ValueError("Invalid filtered patent archive: " + source)
        with archive.open("filtered_patents.csv") as binary:
            with io.TextIOWrapper(binary, encoding="utf-8", newline="") as stream:
                reader = csv.DictReader(stream)
                if reader.fieldnames != expected["fields"]:
                    raise ValueError("Unexpected column schema in " + source)
                for row in reader:
                    family = row["docdb_family_id"]
                    p = float(row["probability_relevant"])
                    if (not family.isdecimal() or int(family) <= 0 or family in result or
                            None in row or any(v is None for v in row.values()) or
                            not row["abstract_en"].strip() or not math.isfinite(p) or
                            p < 0.5 or p > 1.0 or row["model_decision"] != "1"):
                        raise ValueError("Malformed, duplicate or nonpositive retained family: " + repr(family))
                    result[family] = {**{key: "" for key in OUTPUT_FIELDS}, **row, "source_query": source}
    if len(result) != expected["kept"]:
        raise ValueError("Unexpected number of retained families in " + source)
    return result


def build(original, original_summary, novel, novel_summary, output):
    original_rows = read_verified(original, original_summary, "original_64_cpc")
    novel_rows = read_verified(novel, novel_summary, "novel_v3")
    overlap = set(original_rows) & set(novel_rows)
    if overlap:
        raise ValueError(f"Overlapping DOCDB families ({len(overlap)}); needs human conflict resolution")
    combined = {**original_rows, **novel_rows}
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_suffix(".csv.tmp")
    try:
        with tmp.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=OUTPUT_FIELDS, extrasaction="raise")
            writer.writeheader()
            for family in sorted(combined, key=lambda key: int(key)):
                writer.writerow(combined[family])
        tmp.replace(output)
    finally:
        tmp.unlink(missing_ok=True)
    ids = set()
    batches = {"original_64_cpc": 0, "novel_v3": 0}
    with output.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != OUTPUT_FIELDS:
            raise ValueError("Unexpected final CSV schema")
        for row in reader:
            family = row["docdb_family_id"]
            if family in ids or family not in combined or row != combined[family]:
                raise ValueError("Final CSV reread or family validation failed")
            ids.add(family)
            batches[row["source_query"]] += 1
    if len(ids) != 7102 or batches != {"original_64_cpc": 3116, "novel_v3": 3986}:
        raise ValueError("Final family coverage or cohort count mismatch")
    report = {"unique_families": len(ids), "cohorts": batches,
              "overlap": 0, "file": str(output), "sha256": sha256(output),
              "size_bytes": output.stat().st_size}
    print("FINAL_DATASET_VERIFIED=" + json.dumps(report, sort_keys=True), flush=True)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original", type=Path, default=Path("data/filtered/filtered_patents.zip"))
    p.add_argument("--original-summary", type=Path, default=Path("data/filtered/production_summary.json"))
    p.add_argument("--novel", type=Path, required=True)
    p.add_argument("--novel-summary", type=Path, required=True)
    p.add_argument("--output", type=Path, default=Path("data/final/humanoid_patents_final.csv"))
    args = p.parse_args()
    build(args.original, args.original_summary, args.novel, args.novel_summary, args.output)


if __name__ == "__main__":
    main()
