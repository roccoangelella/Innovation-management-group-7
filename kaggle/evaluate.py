"""Evaluate patent screening against provisional labels, excluding unresolved cases."""
import argparse
import csv
import json
import math
from pathlib import Path


def read_unique(path, required):
    with Path(path).open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not set(required).issubset(reader.fieldnames or []):
            raise ValueError(f"{path}: required fields {required}")
        entries = {}
        for row in reader:
            key = row["docdb_family_id"].strip()
            if not key or key in entries:
                raise ValueError(f"{path}: empty/duplicate family ID {key!r}")
            entries[key] = row
    return entries


def wilson_interval(successes, trials, z=1.959963984540054):
    """Two-sided 95% Wilson binomial interval."""
    if trials == 0:
        return None
    p = successes / trials
    den = 1 + z*z/trials
    center = (p + z*z/(2*trials))/den
    half = z*math.sqrt((p*(1-p) + z*z/(4*trials))/trials)/den
    return [max(0, center-half), min(1, center+half)]


def evaluate(prediction_path, labels_path, threshold=0.5):
    if not 0 <= threshold <= 1:
        raise ValueError("Threshold must be between 0 and 1")
    predictions = read_unique(prediction_path, ("docdb_family_id", "probability_relevant"))
    annotations = read_unique(labels_path, ("docdb_family_id", "label", "needs_review"))
    if set(predictions) != set(annotations):
        missing = sorted(set(annotations) - set(predictions))
        extra = sorted(set(predictions) - set(annotations))
        raise ValueError(f"Family IDs differ: missing predictions {missing[:8]}; extra predictions {extra[:8]}")

    tp = fp = tn = fn = unresolved = 0
    cases = []
    for family, prediction in predictions.items():
        prob = float(prediction["probability_relevant"])
        if not math.isfinite(prob) or not 0 <= prob <= 1:
            raise ValueError(f"Invalid probability for {family}")
        guess = int(prob >= threshold)
        annotation = annotations[family]
        y = annotation["label"].strip()
        review = annotation["needs_review"].strip()
        if review not in ("0", "1"):
            raise ValueError(f"Invalid needs_review for {family}")
        if review == "1":
            if y:
                raise ValueError(f"Unresolved family {family} must not have a label")
            unresolved += 1
            kind = "unresolved"
        else:
            if y not in ("0", "1"):
                raise ValueError(f"Invalid label for {family}")
            if y == "1" and guess == 1:
                tp += 1
                kind = "true_positive"
            elif y == "1":
                fn += 1
                kind = "false_negative"
            elif guess == 1:
                fp += 1
                kind = "false_positive"
            else:
                tn += 1
                kind = "true_negative"
        cases.append({
            "docdb_family_id": family,
            "label": y,
            "needs_review": review,
            "probability_relevant": prob,
            "predicted_relevant": guess,
            "category": kind,
            "confidence": annotation.get("confidence", ""),
            "reason": annotation.get("reason", ""),
        })
    pos = tp + fn
    neg = tn + fp
    precision = tp/(tp+fp) if pos and (tp+fp) else None
    recall = tp/pos if pos else None
    f1 = (2*precision*recall/(precision+recall)
          if precision is not None and recall is not None and precision+recall else None)
    report = {
        "n_total": len(predictions), "n_evaluated": pos+neg,
        "n_unresolved_excluded": unresolved, "n_positive_labels": pos,
        "n_negative_labels": neg, "threshold_exploratory": threshold,
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "precision": precision, "recall": recall, "f1": f1,
        "specificity": tn/neg if neg else None,
        "false_positive_rate": fp/neg if neg else None,
        "specificity_95pct_wilson_interval": wilson_interval(tn, neg),
        "model_positive_predictions_including_unresolved": sum(x["predicted_relevant"] for x in cases),
        "warning": ("Zero verified positives: precision, recall and F1 are undefined; "
                    "only negative-class false positives and specificity can be assessed."
                    if not pos else "Provisional AI-assisted labels require independent human review."),
        "limitations": ("Originally English abstracts only; unresolved labels excluded; "
                        "AI-assisted labels not independently verified; exploratory threshold; "
                        "uniform random candidates may contain few true positives."),
    }
    return report, cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--labels", required=True)
    parser.add_argument("--output", default="/kaggle/working/evaluation.json")
    parser.add_argument("--threshold", type=float, default=0.5)
    args = parser.parse_args()
    report, cases = evaluate(args.predictions, args.labels, args.threshold)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    cases.sort(key=lambda x: (-x["probability_relevant"], x["docdb_family_id"]))
    case_path = output.with_name("evaluation_cases.csv")
    with case_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(cases[0]) if cases else ["docdb_family_id"])
        writer.writeheader()
        writer.writerows(cases)
    print(json.dumps(report, indent=2))
    print(f"Case-level output: {case_path}")


if __name__ == "__main__":
    main()
