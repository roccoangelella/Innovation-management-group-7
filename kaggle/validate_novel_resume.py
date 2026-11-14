"""Validate a saved *novel-only* Kaggle checkpoint before mounting it for resume.

Never import journals from the earlier 237,538-family full-corpus run.
Usage: python kaggle/validate_novel_resume.py CHECKPOINT_ZIP TRANSLATED_CSV SUMMARY_JSON STAGING_DIR DATASET_ID
"""
import csv
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import tempfile
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import production
from run import REVISION
from screen import MODEL_ID, QUESTION, sha256


def validate(checkpoint, source, summary_path, destination, dataset_id):
    checkpoint, source, summary_path, destination = map(Path, (checkpoint, source, summary_path, destination))
    if destination.exists():
        raise FileExistsError("Refusing to overwrite an existing resume staging directory")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    total = summary["completed"]
    if summary["incomplete"] != 0 or total != summary["eligible"] or total <= 1:
        raise ValueError("Not a complete novel translated input")
    if sha256(source) != summary["final_csv_sha256"]:
        raise ValueError("Translated CSV SHA256 mismatch")
    expected = {"production_manifest.json", "session_summary.json"}
    expected |= {f"worker_{i}/{name}" for i in (0, 1)
                 for name in ("predictions.jsonl", "run_metadata.json")}
    with zipfile.ZipFile(checkpoint) as z:
        if set(z.namelist()) != expected:
            raise ValueError(f"Unexpected saved journal members: {set(z.namelist()) ^ expected}")
        session = json.loads(z.read("session_summary.json"))
        if session.get("complete") is not False or session.get("resume_required") is not True or session.get("total") != total:
            raise ValueError("Checkpoint is not an incomplete novel screening session")
        with tempfile.TemporaryDirectory() as tmp:
            plan = production.prepare(source, Path(tmp) / "plan", REVISION, expected_rows=total)
            expected_manifest = production.identity(source, REVISION, total)
            if json.loads(z.read("production_manifest.json")) != expected_manifest:
                raise ValueError("Checkpoint source/model/prompt differs from novel translated dataset")
            if expected_manifest["model"] != MODEL_ID:
                raise ValueError("Unexpected screening model")
            completed = set()
            for i in (0, 1):
                with plan["shard_paths"][i].open(newline="", encoding="utf-8") as stream:
                    shard_ids = {row["docdb_family_id"] for row in csv.DictReader(stream)}
                expected_metadata = {"input_sha256": sha256(plan["shard_paths"][i]),
                                     "model": MODEL_ID, "revision": REVISION,
                                     "dtype": "float16", "question": QUESTION}
                if json.loads(z.read(f"worker_{i}/run_metadata.json")) != expected_metadata:
                    raise ValueError(f"Worker {i} checkpoint provenance mismatch")
                for line in z.read(f"worker_{i}/predictions.jsonl").splitlines():
                    record = json.loads(line)
                    if set(record) != set(production.PREDICTION_FIELDS):
                        raise ValueError("Unexpected prediction journal fields")
                    family = record["docdb_family_id"]
                    probability = record["probability_relevant"]
                    decision = record["model_decision"]
                    if (family not in shard_ids or family in completed
                            or type(probability) not in (int, float) or not math.isfinite(probability)
                            or not 0 <= probability <= 1 or type(decision) is not int
                            or decision != int(probability >= production.THRESHOLD)):
                        raise ValueError(f"Invalid or duplicate saved prediction: {family}")
                    completed.add(family)
            if len(completed) != session.get("processed") or len(completed) >= total:
                raise ValueError("Checkpoint processed counts do not reconcile")
        destination.mkdir(parents=True)
        for name in sorted(expected):
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with z.open(name) as inp, target.open("wb") as out:
                shutil.copyfileobj(inp, out)
    (destination / "dataset-metadata.json").write_text(
        json.dumps({"id": dataset_id, "title": "Private novel patent screening resume",
                    "licenses": [{"name": "other"}],
                    "description": "Source-verified append-only 2xT4 inference journal; private only"},
                   indent=2) + "\n", encoding="utf-8")
    print(f"NOVEL_CHECKPOINT_VERIFIED={len(completed)}/{total}", flush=True)


if __name__ == "__main__":
    if len(sys.argv) != 6:
        raise SystemExit(__doc__)
    validate(*sys.argv[1:])
