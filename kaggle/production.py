"""Resumable, two-T4 data-parallel screening of translated DOCDB families.

Run through kaggle/production_run.py to prepare the FP16 checkpoint first.
Only abstract_en reaches the model; original patent metadata is retained for exports.
"""

import csv
from contextlib import contextmanager
import hashlib
import io
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import zipfile

from screen import MODEL_ID, QUESTION, sha256

N_WORKERS = 2
THRESHOLD = 0.5  # Provisional only; preserve scores for subsequent calibration.
PREDICTION_FIELDS = ("docdb_family_id", "probability_relevant", "model_decision")
ALLOWED_STATUS = {"translated", "original_en", "copied", "english", "already_english"}


@contextmanager
def input_csv(path):
    """Read a plain UTF-8 CSV or an archive with exactly one CSV member."""
    path = Path(path)
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as archive:
            members = [name for name in archive.namelist() if name.lower().endswith(".csv") and not name.endswith("/")]
            if len(members) != 1:
                raise ValueError(f"Expected exactly one CSV inside {path}, found {len(members)}")
            with archive.open(members[0]) as raw:
                with io.TextIOWrapper(raw, encoding="utf-8-sig", newline="") as stream:
                    yield stream
    elif path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8-sig") as stream:
            yield stream
    else:
        raise ValueError("Production input must be a .csv or .zip containing one CSV")


def input_rows(path):
    with input_csv(path) as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames or []
        if not {"docdb_family_id", "abstract_en"}.issubset(fields):
            raise ValueError("Translated input requires docdb_family_id and abstract_en; raw source ZIP is not yet translated")
        if len(fields) != len(set(fields)) or None in fields:
            raise ValueError("Missing or duplicated CSV headers")
        if "probability_relevant" in fields or "model_decision" in fields:
            raise ValueError("Input already has screening columns; supply the untranslated-by-Decider source data")
        for row in reader:
            if None in row or any(v is None for v in row.values()):
                raise ValueError("Malformed input CSV row")
            family = row["docdb_family_id"].strip()
            english = row["abstract_en"].strip()
            if not family or not english:
                raise ValueError("Missing family ID or English abstract")
            if "translation_status" in row and row["translation_status"].strip().lower() not in ALLOWED_STATUS:
                raise ValueError(f"Incomplete/invalid translation_status for family {family}")
            if "translation_status" in row and "abstract_language" in row:
                is_original_en = row["abstract_language"].strip().lower() == "en"
                status_original_en = row["translation_status"].strip().lower() == "original_en"
                if status_original_en and not is_original_en:
                    raise ValueError(f"Incorrect original_en language for family {family}")
                if status_original_en and "abstract" in row and row["abstract"] != row["abstract_en"]:
                    raise ValueError(f"Original-English abstract differs from source for family {family}")
            yield family, english, row


def inspect_input(path, expected_rows=None):
    seen = set()
    total = 0
    for family, _, _ in input_rows(path):
        if family in seen:
            raise ValueError(f"Duplicate DOCDB family: {family}")
        seen.add(family)
        total += 1
    if total == 0:
        raise ValueError("Production input has no eligible families")
    if expected_rows is not None and total != expected_rows:
        raise ValueError(f"Expected {expected_rows} families; found {total}. Is translation complete?")
    return total


def identity(path, revision, expected_rows):
    question_hash = hashlib.sha256(json.dumps(QUESTION, sort_keys=True).encode("utf-8")).hexdigest()
    return {
        "format_version": 1,
        "input_sha256": sha256(path),
        "model": MODEL_ID,
        "model_revision": revision,
        "question_sha256": question_hash,
        "workers": N_WORKERS,
        "threshold_exploratory": THRESHOLD,
        "expected_rows": expected_rows,
    }


def atomic_json(path, value):
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, path)


def prepare(path, output_dir, revision, expected_rows=None):
    """Validate all rows first, then recreate deterministic shards without touching journals."""
    path = Path(path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    output_dir = Path(output_dir).expanduser().resolve()
    total = inspect_input(path, expected_rows)
    manifest_data = identity(path, revision, expected_rows)
    manifest = output_dir / "production_manifest.json"
    if manifest.is_file():
        if json.loads(manifest.read_text(encoding="utf-8")) != manifest_data:
            raise ValueError("Production input/model/prompt changed: use a NEW --production-dir")
    else:
        if output_dir.exists() and any(p.name != ".screening.lock" for p in output_dir.iterdir()):
            raise ValueError("Production directory has files but no manifest; choose a clean directory")
        output_dir.mkdir(parents=True, exist_ok=True)
        atomic_json(manifest, manifest_data)
    shard_dir = output_dir / "shards"
    shard_dir.mkdir(exist_ok=True)
    paths = [shard_dir / f"worker_{i}.csv" for i in range(N_WORKERS)]
    temp_paths = [p.with_suffix(".csv.tmp") for p in paths]
    order_path = shard_dir / "family_order.csv"
    counts = [0] * N_WORKERS
    try:
        with open(temp_paths[0], "w", encoding="utf-8", newline="") as stream_a, \
             open(temp_paths[1], "w", encoding="utf-8", newline="") as stream_b, \
             order_path.with_suffix(".csv.tmp").open("w", encoding="utf-8", newline="") as order_stream:
            writers = [csv.writer(stream_a), csv.writer(stream_b)]
            for writer in writers:
                writer.writerow(["docdb_family_id", "abstract_en"])
            order_writer = csv.writer(order_stream)
            order_writer.writerow(["docdb_family_id"])
            for family, english, _ in input_rows(path):
                bucket = int.from_bytes(hashlib.sha256(family.encode("utf-8")).digest()[:8], "big") % N_WORKERS
                writers[bucket].writerow([family, english])
                order_writer.writerow([family])
                counts[bucket] += 1
        for temp, destination in zip(temp_paths, paths):
            os.replace(temp, destination)
        os.replace(order_path.with_suffix(".csv.tmp"), order_path)
    finally:
        for temp in [*temp_paths, order_path.with_suffix(".csv.tmp")]:
            temp.unlink(missing_ok=True)
    if sum(counts) != total or min(counts) == 0:
        raise ValueError("Invalid shard split: one worker has no records")
    print(f"Production input: {total} families; T4 shards {counts}; source SHA256 {manifest_data['input_sha256']}", flush=True)
    return {"count": total, "shard_counts": counts, "shard_paths": paths, "dir": output_dir, "input": path}


def run_workers(plan, checkpoint, revision, device_ids=("0", "1")):
    """Run two *distinct* GPU processes. CUDA device 0 in each child is a different T4."""
    checkpoint = Path(checkpoint).resolve()
    screen_py = Path(__file__).with_name("screen.py")
    if len(device_ids) != N_WORKERS or len(set(device_ids)) != N_WORKERS:
        raise ValueError("Exactly two distinct CUDA devices are required")
    workers = []
    try:
        for i, device in enumerate(device_ids):
            output = plan["dir"] / f"worker_{i}" / "predictions.csv"
            output.parent.mkdir(parents=True, exist_ok=True)
            env = os.environ.copy()
            env["CUDA_VISIBLE_DEVICES"] = str(device)
            command = [sys.executable, "-u", str(screen_py),
                       "--input", str(plan["shard_paths"][i]),
                       "--checkpoint", str(checkpoint),
                       "--output", str(output),
                       "--model-revision", revision]
            print(f"Starting worker {i}: physical GPU {device}, {plan['shard_counts'][i]} families", flush=True)
            workers.append(subprocess.Popen(command, env=env))
        while True:
            states = [proc.poll() for proc in workers]
            failures = [(i, code) for i, code in enumerate(states) if code not in (None, 0)]
            if failures:
                raise RuntimeError(f"GPU worker failure(s): {failures}. Resume using the same command and directory")
            if all(code == 0 for code in states):
                break
            time.sleep(0.5)
    finally:
        for proc in workers:
            if proc.poll() is None:
                proc.terminate()
        for proc in workers:
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()


def read_worker_results(plan):
    predictions = {}
    for i in range(N_WORKERS):
        expected = set()
        with plan["shard_paths"][i].open(encoding="utf-8", newline="") as stream:
            for row in csv.DictReader(stream):
                expected.add(row["docdb_family_id"])
        path = plan["dir"] / f"worker_{i}" / "predictions.csv"
        if not path.is_file():
            raise FileNotFoundError(f"Worker {i} did not produce {path}")
        found = set()
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            if not set(PREDICTION_FIELDS).issubset(reader.fieldnames or []):
                raise ValueError(f"Worker {i} predictions have incorrect columns")
            for row in reader:
                key = row["docdb_family_id"]
                if key in found or key not in expected or key in predictions:
                    raise ValueError(f"Worker {i} returned duplicate or unexpected family {key}")
                try:
                    probability = float(row["probability_relevant"])
                    decision = int(row["model_decision"])
                except (ValueError, TypeError) as exc:
                    raise ValueError(f"Invalid model output for {key}") from exc
                if not math.isfinite(probability) or not 0 <= probability <= 1 or decision != int(probability >= THRESHOLD):
                    raise ValueError(f"Invalid probability or worker decision for {key}")
                predictions[key] = probability
                found.add(key)
        if found != expected:
            raise ValueError(f"Worker {i}: {len(expected - found)} missing IDs; refuse incomplete merge")
    if len(predictions) != plan["count"]:
        raise ValueError("Merged predictions do not cover all input families")
    return predictions


def merge(plan):
    """Emit one scored row per family and a ZIP of retained patents with original fields."""
    manifest = json.loads((plan["dir"] / "production_manifest.json").read_text(encoding="utf-8"))
    if sha256(plan["input"]) != manifest["input_sha256"]:
        raise ValueError("Production source changed since preflight; refuse merge")
    predictions = read_worker_results(plan)
    root = plan["dir"]
    predictions_path = root / "predictions.csv"
    zip_path = root / "filtered_patents.zip"
    temp_predictions = predictions_path.with_suffix(".csv.tmp")
    temp_zip = zip_path.with_suffix(".zip.tmp")
    total = kept = 0
    try:
        with temp_predictions.open("w", newline="", encoding="utf-8") as predictions_stream, \
             zipfile.ZipFile(temp_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as output_zip:
            writer = csv.writer(predictions_stream)
            writer.writerow(PREDICTION_FIELDS)
            with output_zip.open("filtered_patents.csv", "w") as raw_output:
                with io.TextIOWrapper(raw_output, encoding="utf-8", newline="") as filtered_stream:
                    filtered_writer = None
                    for family, _, source_row in input_rows(plan["input"]):
                        if family not in predictions:
                            raise ValueError(f"Missing prediction in full dataset: {family}")
                        prob = predictions[family]
                        decision = int(prob >= THRESHOLD)
                        writer.writerow([family, format(prob, ".17g"), decision])
                        if filtered_writer is None:
                            fields = list(source_row) + ["probability_relevant", "model_decision"]
                            filtered_writer = csv.DictWriter(filtered_stream, fieldnames=fields)
                            filtered_writer.writeheader()
                        if decision:
                            filtered_writer.writerow({**source_row, "probability_relevant": format(prob, ".17g"), "model_decision": 1})
                            kept += 1
                        total += 1
        if total != plan["count"]:
            raise ValueError("Source changed during inference; refuse merge")
        os.replace(temp_predictions, predictions_path)
        os.replace(temp_zip, zip_path)
    finally:
        temp_predictions.unlink(missing_ok=True)
        temp_zip.unlink(missing_ok=True)
    summary = {
        "n_input": total, "n_predictions": len(predictions),
        "n_relevant_exploratory": kept, "n_discarded_exploratory": total - kept,
        "threshold_exploratory": THRESHOLD,
        "input_sha256": sha256(plan["input"]),
        "predictions_sha256": sha256(predictions_path),
        "filtered_zip_sha256": sha256(zip_path),
        "worker_counts": plan["shard_counts"],
        "warning": "Threshold 0.5 is provisional. AI-assisted benchmark labels do not establish production precision.",
    }
    manifest = json.loads((root / "production_manifest.json").read_text(encoding="utf-8"))
    if summary["input_sha256"] != manifest["input_sha256"]:
        raise ValueError("Production source changed after preflight")
    atomic_json(root / "production_summary.json", summary)
    print(f"Merged {total} families; {kept} provisional keep decisions; outputs: {predictions_path}, {zip_path}", flush=True)
    return summary
