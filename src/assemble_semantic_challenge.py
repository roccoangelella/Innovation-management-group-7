"""Generate 100 source-authentic, non-explicit-term semantic challenge rows.

Human-authored annotations are in selection_annotations.json. DO NOT generate
relevance labels from regex or a decision model. Output samples are source-faithful.
"""
import csv
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile
import io

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"samples/semantic_challenge_100"
ZIP=ROOT/"humanoid_patents.zip"
FIELDS=["docdb_family_id","year","title","title_language","abstract","abstract_language","matched_cpcs"]
LABEL_COLUMNS=["docdb_family_id","label","needs_review","confidence","evidence_quote","reason"]
COMBINED_COLUMNS=["docdb_family_id","abstract_en","label","needs_review","confidence","evidence_quote","reason"]
SEED="semantic-challenge-v1-20261030"

def sha256(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def quote(abstract,label):
    # Source-grounded evidence; no keyword-based labeling or term requirement.
    return abstract[:160]

def main():
    data=json.loads((OUT/"selection_annotations.json").read_text(encoding="utf-8"))
    if len(data)!=100 or Counter(x["label"] for x in data)!={0:60,1:40}:
        raise ValueError("Semantic challenge requires exactly 40 positives and 60 negatives")
    keyed={str(x["docdb_family_id"]):x for x in data}
    if len(keyed)!=100:
        raise ValueError("Duplicate label IDs")
    if any(x["needs_review"]!=0 or x["confidence"] not in ("high","medium") for x in data):
        raise ValueError("Curated examples must have decisions and confidence")
    earlier=ROOT/"samples/random_100/random_100_full.csv"
    with earlier.open(newline="",encoding="utf-8-sig") as f:
        excluded={row["docdb_family_id"] for row in csv.DictReader(f)}
    prior=ROOT/"samples/humanoid_challenge_100/challenge_100_full.csv"
    with prior.open(newline="",encoding="utf-8-sig") as f:
        excluded.update(row["docdb_family_id"] for row in csv.DictReader(f))
    if set(keyed)&excluded:
        raise ValueError("Semantic challenge overlaps either previous benchmark")
    selected={}
    csv.field_size_limit(sys.maxsize)
    with zipfile.ZipFile(ZIP) as z:
        with z.open("humanoid_patents.csv") as b, io.TextIOWrapper(b,encoding="utf-8-sig",newline="") as f:
            reader=csv.DictReader(f)
            if reader.fieldnames!=FIELDS:
                raise ValueError(f"Source schema unexpectedly changed: {reader.fieldnames}")
            for row in reader:
                fid=row["docdb_family_id"]
                if fid in keyed:
                    if fid in selected: raise ValueError("Duplicate selected DOCDB family")
                    if row["abstract_language"].strip().lower()!="en" or not row["abstract"].strip():
                        raise ValueError("Non-English or empty selected abstract")
                    if re.search(r"\b(?:humanoids?|anthropomorphic)\b",row["abstract"],re.I):
                        raise ValueError("Explicit humanoid/anthropomorphic term found in "+fid)
                    selected[fid]=row
    if set(selected)!=set(keyed):
        raise ValueError("Selected IDs missing from source: "+str(set(keyed)-set(selected)))
    # Shuffle positives and negatives together deterministically, preserving ID-based joins.
    ids=sorted(selected,key=lambda s:hashlib.sha256((SEED+":"+s).encode()).hexdigest())
    OUT.mkdir(parents=True,exist_ok=True)
    outputs={}
    for filename,headers,rows in [
        ("semantic_100_full.csv",FIELDS,[selected[i] for i in ids]),
        ("semantic_100_abstracts_en.csv",FIELDS+["abstract_en","translation_status"],
          [{**selected[i],"abstract_en":selected[i]["abstract"],"translation_status":"original_en"} for i in ids]),
        ("semantic_100_for_blind_review.csv",["docdb_family_id","abstract_language","abstract"],
          [{c:selected[i][c] for c in ("docdb_family_id","abstract_language","abstract")} for i in ids]),
        ("semantic_100_manual_labels.csv",LABEL_COLUMNS,
          [{**{c:keyed[i][c] for c in ("docdb_family_id","label","needs_review","confidence","reason")},
            "evidence_quote":quote(selected[i]["abstract"],keyed[i]["label"])} for i in ids]),
        ("semantic_100_labeled.csv",COMBINED_COLUMNS,
          [{"docdb_family_id":i,"abstract_en":selected[i]["abstract"],
            "label":keyed[i]["label"],"needs_review":keyed[i]["needs_review"],
            "confidence":keyed[i]["confidence"],
            "evidence_quote":quote(selected[i]["abstract"],keyed[i]["label"]),
            "reason":keyed[i]["reason"]} for i in ids]),
    ]:
        path=OUT/filename
        with path.open("w",encoding="utf-8",newline="") as f:
            w=csv.DictWriter(f,fieldnames=headers,extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        outputs[filename]={"sha256":sha256(path),"size_bytes":path.stat().st_size}
    with (OUT/"annotation_audit.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=["docdb_family_id","label","discovery_group","confidence","evidence_quote","reason"])
        w.writeheader()
        w.writerows({"docdb_family_id":i,"label":keyed[i]["label"],"discovery_group":keyed[i]["bucket"],
                     "confidence":keyed[i]["confidence"],"evidence_quote":quote(selected[i]["abstract"],keyed[i]["label"]),
                     "reason":keyed[i]["reason"]} for i in ids)
    summary={
        "n":len(ids),"label_counts":{"relevant":40,"not_relevant":60,"needs_review":0},
        "selection_groups":dict(Counter(x["bucket"] for x in data)),
        "language":"en","seed_for_output_order":SEED,
        "source_zip_sha256":sha256(ZIP),
        "forbidden_whole_words":["humanoid","humanoids","anthropomorphic"],
        "annotation_source":"AI-authored prospective labeling based only on patent abstract, before Kaggle model scores",
        "labeling_definition":"1 for independent biped robots, humanlike embodied robot systems or their explicitly biped-specific locomotion/structure/control; 0 for human-worn exoskeletons, nonhuman multi-leg robots and general robotics without embodied humanlike design",
        "limitations":"Purposive 40:60 non-keyword development challenge, not representative of field prevalence, generated after previous benchmark feedback. AI labels provisional pending independent human adjudication. The positive definition intentionally includes biped-specific technology without an explicit humanoid cue and may differ from the current strict Decider prompt. Never interpret its precision/F1 as deployment metrics.",
        "excluded_previous_sample":True,
        "files":outputs
    }
    (OUT/"sample_summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2,ensure_ascii=False))

if __name__=="__main__":
    main()
