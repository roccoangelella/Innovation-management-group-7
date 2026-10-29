"""Deterministic unlabeled DOCDB-family benchmark sampling; standard library only."""
import argparse
from collections import Counter
import csv
import hashlib
import heapq
import json
from pathlib import Path
import zipfile
from translate_abstracts import SOURCE_FIELDS, input_rows

SEED = 20261029

def cpcs(row):
    return {c.strip().replace(" ", "") for c in row["matched_cpcs"].split(";") if c.strip()}

def rank(family):
    return int.from_bytes(hashlib.sha256(f"{SEED}:{family}".encode()).digest()[:8], "big")

def choose(candidates, target, desired, initial=()):
    chosen = list(initial)
    used = {r["docdb_family_id"] for r in chosen}
    covered = Counter(c for r in chosen for c in cpcs(r))
    while len(chosen) < target:
        best, best_key = None, None
        for row in candidates:
            family = row["docdb_family_id"]
            if family in used:
                continue
            benefit = sum(
                (max(0.0, desired.get(c, 0) - covered[c]) ** 2
                 - max(0.0, desired.get(c, 0) - covered[c] - 1) ** 2)
                / max(1.0, desired.get(c, 0))
                for c in cpcs(row)
            )
            key = (benefit, -rank(family), family)
            if best_key is None or key > best_key:
                best, best_key = row, key
        if best is None:
            raise ValueError("Insufficient candidates")
        chosen.append(best)
        used.add(best["docdb_family_id"])
        covered.update(cpcs(best))
    return chosen

def sample(input_path, output_dir, en_size=90, other_size=10, pool_size=12000):
    """Use fixed-seed hash-ranked pools and greedy proportional CPC coverage."""
    if min(en_size, other_size) < 0 or pool_size < en_size + other_size:
        raise ValueError("Invalid quotas or pool size")
    pools, seen = {}, set()
    languages, source_cpcs, excluded = Counter(), Counter(), Counter()
    for row in input_rows(input_path):
        family = row["docdb_family_id"].strip()
        if not family or family in seen:
            raise ValueError(f"Missing or duplicate DOCDB family: {family!r}")
        seen.add(family)
        language = row["abstract_language"].strip().lower()
        if not row["abstract"].strip():
            excluded["empty_abstract"] += 1
            continue
        if language in ("", "unknown", "und", "null", "none"):
            excluded["invalid_language"] += 1
            continue
        languages[language] += 1
        source_cpcs.update(cpcs(row))
        heap = pools.setdefault(language, [])
        item = (-rank(family), family, row)
        limit = pool_size if language == "en" else max(200, pool_size // 10)
        if len(heap) < limit:
            heapq.heappush(heap, item)
        elif item > heap[0]:
            heapq.heapreplace(heap, item)
    if languages["en"] < en_size or sum(v for k, v in languages.items() if k != "en") < other_size:
        raise ValueError("Insufficient eligible records for 90/10 quotas")
    english = [item[2] for item in pools.get("en", [])]
    foreign = [item[2] for lang, heap in pools.items() if lang != "en" for item in heap]
    en_freq = Counter(c for row in english for c in cpcs(row))
    non_freq = Counter(c for row in foreign for c in cpcs(row))
    en_targets = {c: en_size * v / len(english) for c, v in en_freq.items()}
    non_targets = {c: other_size * v / len(foreign) for c, v in non_freq.items()}
    selected_en = choose(english, en_size, en_targets)
    diverse = []
    for language in sorted((k for k in languages if k != "en"), key=lambda k: (-languages[k], k))[:other_size]:
        diverse.append(min((item[2] for item in pools[language]),
                           key=lambda row: (rank(row["docdb_family_id"]), row["docdb_family_id"])))
    selected_non = choose(foreign, other_size, non_targets, diverse)
    selected = sorted(selected_en + selected_non, key=lambda r: (rank(r["docdb_family_id"]), r["docdb_family_id"]))
    assert len(selected) == en_size + other_size
    assert len({r["docdb_family_id"] for r in selected}) == len(selected)
    assert sum(r["abstract_language"].strip().lower() == "en" for r in selected) == en_size
    dest = Path(output_dir)
    dest.mkdir(parents=True, exist_ok=True)
    csv_path = dest / "humanoid_100_abstracts.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=SOURCE_FIELDS)
        writer.writeheader()
        writer.writerows(selected)
    with zipfile.ZipFile(dest / "humanoid_100_abstracts.zip", "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.write(csv_path, arcname="humanoid_patents.csv")
    selected_cpcs = Counter(c for r in selected for c in cpcs(r))
    summary = {
        "seed": SEED, "total_source_families": len(seen),
        "eligible": sum(languages.values()), "excluded": dict(excluded),
        "language_pool": dict(sorted(languages.items())),
        "selected": len(selected),
        "selected_languages": dict(sorted(Counter(r["abstract_language"].strip().lower() for r in selected).items())),
        "source_cpc_codes": len(source_cpcs),
        "selected_cpc_codes": len(selected_cpcs),
        "uncovered_cpc_codes": sorted(set(source_cpcs) - set(selected_cpcs)),
        "selected_cpc_memberships": dict(sorted(selected_cpcs.items())),
        "candidate_pool_en": len(english), "candidate_pool_non_en": len(foreign),
        "method": "Fixed-seed SHA-256 candidate pools, greedy CPC deficit coverage, non-English language diversity",
        "limitations": "CPC balancing is approximate using bounded candidate pools; multi-CPC families count once per family; 90/10 deliberately differs from corpus language shares."
    }
    (dest / "sampling_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return summary

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="humanoid_patents.zip")
    parser.add_argument("--output-dir", default="outputs/sampling")
    args = parser.parse_args()
    print(json.dumps(sample(args.input, args.output_dir), indent=2))

if __name__ == "__main__":
    main()
