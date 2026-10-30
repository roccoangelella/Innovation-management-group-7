"""Score translated patent abstracts with Perplexity's native Decider API."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

QUESTION = {
    "type": "noul",
    "instructions": (
        "Does this patent abstract describe a technology specifically for a humanoid robot "
        "or an anthropomorphic general-purpose robot? Include humanoid-specific robot "
        "control, perception, locomotion, balancing, manipulation or systems integrations. "
        "Exclude generic industrial robotic arms, appliances, standalone devices, "
        "autonomous vehicles and generic AI unless the abstract explicitly connects "
        "the invention to a humanoid robot. Judge only the abstract, not possible applications."
    ),
    "criteria": {
        "true": "The abstract explicitly concerns a humanoid robot or technology specifically developed for a humanoid robot.",
        "false": "The abstract has no explicit humanoid-robot connection or concerns only general robotics or unrelated technology.",
    },
}
MODEL_ID = "perplexity-ai/pplx-decider-flash-v1.2"


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def rows(path):
    with Path(path).open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        required = {"docdb_family_id", "abstract_en"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("Input requires docdb_family_id and abstract_en")
        seen = set()
        for row in reader:
            key = row["docdb_family_id"].strip()
            abstract = row["abstract_en"].strip()
            if not key or not abstract or key in seen:
                raise ValueError("Empty or duplicate ID, or empty English abstract")
            if "translation_status" in row and row["translation_status"].lower() not in (
                "translated", "copied", "original_en", "english", "already_english",
            ):
                # The source translation script may use another success status;
                # validate that contract explicitly rather than silently scoring failures.
                raise ValueError(f"Unrecognized translation status for {key}: {row['translation_status']}")
            seen.add(key)
            yield key, abstract


def make_request(abstract):
    """Strict model input boundary: do not forward label, reason, evidence, or other CSV fields."""
    return {"state": abstract, "questions": {"relevant": QUESTION}}


def write_csv(path, results):
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["docdb_family_id", "probability_relevant", "model_decision"])
        writer.writeheader()
        writer.writerows(results)
    tmp.replace(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--checkpoint", required=True, help="Local snapshot of native Decider checkpoint")
    parser.add_argument("--model-revision", default="unversioned")
    parser.add_argument("--output", default="/kaggle/working/predictions.csv")
    args = parser.parse_args()
    input_path = Path(args.input)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    journal = output.with_suffix(".jsonl")
    metadata = output.with_name("run_metadata.json")
    examples = list(rows(input_path))
    config = {"input_sha256": sha256(input_path), "model": MODEL_ID, "revision": args.model_revision, "dtype": "float16", "question": QUESTION}
    if metadata.exists():
        if json.loads(metadata.read_text()) != config:
            raise ValueError("Input/model/prompt changed: use a different output directory.")
    else:
        if journal.exists() or output.exists():
            raise ValueError("Existing outputs without manifest; use a clean directory.")
        metadata.write_text(json.dumps(config, indent=2), encoding="utf-8")

    done = {}
    if journal.exists():
        for line in journal.read_text(encoding="utf-8").splitlines():
            obj = json.loads(line)
            key = obj["docdb_family_id"]
            if key in done:
                raise ValueError(f"Duplicate journal ID: {key}")
            done[key] = obj

    pending = [(key, abstract) for key, abstract in examples if key not in done]
    if pending:
        import sys
        checkpoint = Path(args.checkpoint).resolve()
        if not (checkpoint / "source" / "src").exists():
            raise FileNotFoundError(f"Native Decider source missing under {checkpoint}")
        sys.path.insert(0, str(checkpoint / "source" / "src"))
        from pplx_decider import Decider
        model = Decider.from_pretrained(checkpoint, device="cuda", fast=False)
        import torch
        if next(model.backbone.parameters()).dtype != torch.float16 or model.readout.weight.dtype != torch.float16:
            raise RuntimeError("Native model is not in FP16; run via kaggle/run.py to patch the local loader.")
        with journal.open("a", encoding="utf-8") as f:
            for index, (key, abstract) in enumerate(pending, 1):
                request = make_request(abstract)
                answer = model.decide(request)["answers"]["relevant"]
                probability = float(answer["noul"])
                if not (0 <= probability <= 1):
                    raise ValueError(f"Invalid model probability for {key}")
                obj = {
                    "docdb_family_id": key,
                    "probability_relevant": probability,
                    "model_decision": int(probability >= 0.5),
                }
                f.write(json.dumps(obj) + "\n")
                f.flush()
                done[key] = obj
                if index % 10 == 0:
                    print(f"Scored {index}/{len(pending)} remaining patents", flush=True)
    write_csv(output, [done[key] for key, _ in examples])
    print(f"Saved {len(examples)} predictions to {output}")


if __name__ == "__main__":
    main()
