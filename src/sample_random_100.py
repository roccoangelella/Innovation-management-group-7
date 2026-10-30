"""Reproducible random 100-family original-English-abstract sample from the source ZIP."""
import argparse
from collections import Counter
import csv
import hashlib
import heapq
import io
import json
from pathlib import Path
import sys
import zipfile

SEED = 20261030
SOURCE_NAME = "humanoid_patents.csv"
REVIEW_COLUMNS = ("docdb_family_id", "abstract_language", "abstract")


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def rank(family, seed):
    return int.from_bytes(hashlib.sha256(f"{seed}:{family}".encode()).digest(), "big")


def sample(input_zip, n=100, seed=SEED):
    """Return n lowest seeded hash ranks over originally English, nonempty DOCDB IDs."""
    if n < 1:
        raise ValueError("n must be positive")
    csv.field_size_limit(sys.maxsize)
    heap = []
    seen = set()
    excluded = Counter()
    eligible_languages = Counter()
    total = 0

    with zipfile.ZipFile(input_zip) as archive:
        if SOURCE_NAME not in archive.namelist():
            raise ValueError(f"Expected {SOURCE_NAME} inside {input_zip}")
        with archive.open(SOURCE_NAME) as raw, io.TextIOWrapper(raw, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            fields = reader.fieldnames
            if not fields or not {"docdb_family_id", "abstract_language", "abstract"}.issubset(fields):
                raise ValueError("Missing source CSV fields")
            for row in reader:
                total += 1
                key = (row["docdb_family_id"] or "").strip()
                if not key:
                    excluded["missing_id"] += 1
                    continue
                if key in seen:
                    raise ValueError(f"Duplicate DOCDB family: {key}")
                seen.add(key)
                if not (row["abstract"] or "").strip():
                    excluded["empty_abstract"] += 1
                    continue
                language = (row["abstract_language"] or "").strip().lower() or "unknown"
                if language != "en":
                    excluded["non_english_abstract"] += 1
                    continue
                eligible_languages[language] += 1
                item = (-rank(key, seed), key, row)
                if len(heap) < n:
                    heapq.heappush(heap, item)
                elif item > heap[0]:
                    heapq.heapreplace(heap, item)

    if len(heap) != n:
        raise ValueError(f"Insufficient eligible families: {len(heap)} < {n}")
    chosen = [item[2] for item in sorted(heap, key=lambda item: (-item[0], item[1]))]
    selected_languages = Counter((r["abstract_language"] or "").strip().lower() or "unknown" for r in chosen)
    stats = {
        "method": "Uniform seeded SHA-256 hash-ranking of DOCDB families with nonempty original-English abstracts; no CPC strata or relevance filtering",
        "seed": seed,
        "sample_size": n,
        "total_source_rows": total,
        "eligible_families": sum(eligible_languages.values()),
        "excluded": dict(sorted(excluded.items())),
        "eligible_languages": dict(sorted(eligible_languages.items())),
        "selected_languages": dict(sorted(selected_languages.items())),
        "input_zip_sha256": sha256(input_zip),
        "translated": False,
    }
    return fields, chosen, stats


def write_sample(input_zip, output_dir, n=100, seed=SEED):
    fields, chosen, stats = sample(input_zip, n, seed)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    full = out / "random_100_full.csv"
    review = out / "random_100_for_labeling.csv"
    subset_zip = out / "random_100_for_translation.zip"

    with full.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(chosen)
    with review.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=REVIEW_COLUMNS)
        w.writeheader()
        w.writerows({field: row[field] for field in REVIEW_COLUMNS} for row in chosen)
    with zipfile.ZipFile(subset_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.write(full, arcname=SOURCE_NAME)
    output_files = [full, review, subset_zip]
    if all((row["abstract_language"] or "").strip().lower() == "en" for row in chosen):
        kaggle_csv = out / "humanoid_100_abstracts_en.csv"
        with kaggle_csv.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=[*fields, "abstract_en", "translation_status"])
            w.writeheader()
            for row in chosen:
                w.writerow({**row, "abstract_en": row["abstract"], "translation_status": "original_en"})
        output_files.append(kaggle_csv)
    stats["files"] = {p.name: {"sha256": sha256(p), "size_bytes": p.stat().st_size}
                      for p in output_files}
    (out / "sample_summary.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="humanoid_patents.zip")
    parser.add_argument("--output-dir", default="samples/random_100")
    parser.add_argument("--size", type=int, default=100)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    write_sample(args.input, args.output_dir, args.size, args.seed)
