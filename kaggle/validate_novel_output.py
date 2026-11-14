"""Offline final-audit gate for Kaggle novel-only 2xT4 outputs.

Verify one prediction per source DOCDB family, source/outputs hashes and the
preserved-metadata subset before accepting a Kaggle session as completed.
"""
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

from production import THRESHOLD, sha256


def validate(source, translation_summary, outputs):
    source, translation_summary, outputs = map(Path, (source, translation_summary, outputs))
    summ = json.loads(translation_summary.read_text(encoding="utf-8"))
    if summ.get("incomplete") != 0 or summ.get("completed") != summ.get("eligible"):
        raise ValueError("Source translation is not complete")
    if sha256(source) != summ["final_csv_sha256"]:
        raise ValueError("Translated CSV source digest mismatch")
    ps = json.loads((outputs / "production_summary.json").read_text(encoding="utf-8"))
    predictions = outputs / "predictions.csv"
    filtered = outputs / "filtered_patents.zip"
    if ps.get("input_sha256") != sha256(source) or ps.get("predictions_sha256") != sha256(predictions) or ps.get("filtered_zip_sha256") != sha256(filtered):
        raise ValueError("Screening source/output SHA256 mismatch")
    expected = {}
    with source.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        required = {"docdb_family_id", "abstract_en", "all_cpcs", "ipr_types", "matching_channels"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("Novel source provenance fields missing")
        columns = reader.fieldnames
        for row in reader:
            family = row["docdb_family_id"]
            if not family or family in expected:
                raise ValueError("Duplicate/empty source family")
            expected[family] = row
    if len(expected) != summ["completed"] or ps.get("n_input") != len(expected):
        raise ValueError("Translated input count differs from screening summary")
    seen = {}
    with predictions.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ["docdb_family_id", "probability_relevant", "model_decision"]:
            raise ValueError("Unexpected prediction columns")
        for row in reader:
            family = row["docdb_family_id"]
            if family not in expected or family in seen:
                raise ValueError("Unexpected or duplicate predicted DOCDB family")
            prob = float(row["probability_relevant"])
            import math
            if not math.isfinite(prob) or not 0 <= prob <= 1:
                raise ValueError("Invalid model probability")
            if row["model_decision"] != str(int(prob >= THRESHOLD)):
                raise ValueError("Inconsistent exploratory decision")
            seen[family] = row
    if len(seen) != len(expected) or ps.get("n_predictions") != len(expected):
        raise ValueError("Not all novel families have predictions")
    positive_ids = {family for family, row in seen.items() if row["model_decision"] == "1"}
    if ps.get("n_relevant_exploratory") != len(positive_ids):
        raise ValueError("Positive count mismatch")
    with zipfile.ZipFile(filtered) as archive:
        if archive.namelist() != ["filtered_patents.csv"]:
            raise ValueError("Unexpected filtered ZIP member")
        if archive.testzip() is not None:
            raise ValueError("Corrupted filtered ZIP")
        observed = set()
        with archive.open("filtered_patents.csv") as raw:
            with io.TextIOWrapper(raw, newline="", encoding="utf-8") as stream:
                reader = csv.DictReader(stream)
                if positive_ids and reader.fieldnames != columns + ["probability_relevant", "model_decision"]:
                    raise ValueError("Filtered archive lost extraction provenance columns")
                for row in reader:
                    family = row["docdb_family_id"]
                    if family not in positive_ids or family in observed:
                        raise ValueError("Unexpected/duplicate filtered family")
                    for field in columns:
                        if row[field] != expected[family][field]:
                            raise ValueError("Source metadata changed during filtering")
                    observed.add(family)
        if observed != positive_ids:
            raise ValueError("Filtered ZIP omits provisionally relevant families")
    print(f"NOVEL_SCREENING_VERIFIED={len(seen)} families, {len(positive_ids)} provisional positives", flush=True)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    validate(*sys.argv[1:])
