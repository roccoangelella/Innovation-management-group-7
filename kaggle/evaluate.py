"""Evaluate a manually labeled set. Cut-off 0.5 is exploratory, not calibrated."""
import argparse
import csv
import json
from pathlib import Path


def read(path, required):
    with Path(path).open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not set(required).issubset(reader.fieldnames or []):
            raise ValueError(f"Required fields: {required}")
        rows = {}
        for row in reader:
            key = row["docdb_family_id"].strip()
            if not key or key in rows:
                raise ValueError("Blank/duplicate family ID")
            rows[key] = row
        return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--labels", required=True)
    parser.add_argument("--output", default="evaluation.json")
    args = parser.parse_args()
    preds = read(args.predictions, ["docdb_family_id", "probability_relevant"])
    labels = read(args.labels, ["docdb_family_id", "label"])
    if set(preds) != set(labels):
        raise ValueError("Prediction and label IDs must match exactly")
    tp = fp = tn = fn = 0
    for key, row in preds.items():
        y = int(labels[key]["label"])
        if y not in (0, 1):
            raise ValueError("Only binary labels 0/1 accepted")
        prob = float(row["probability_relevant"])
        if not 0 <= prob <= 1:
            raise ValueError("Invalid probability")
        guess = int(prob >= 0.5)
        tp += y == 1 and guess == 1
        fp += y == 0 and guess == 1
        tn += y == 0 and guess == 0
        fn += y == 1 and guess == 0
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = 2 * precision * recall / (precision + recall) if precision is not None and recall is not None and precision + recall else None
    report = {
        "n": len(preds), "threshold_exploratory": 0.5,
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "precision": precision, "recall": recall, "f1": f1,
        "caveat": "Stratified 100-family sample (90/10 English/non-English). Not a representative production prevalence estimate; threshold uncalibrated.",
    }
    Path(args.output).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
