"""Generate 100 English patent examples and provisional independent labels from source ZIP.

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
OUT=ROOT/"samples/humanoid_challenge_100"
ZIP=ROOT/"humanoid_patents.zip"
FIELDS=["docdb_family_id","year","title","title_language","abstract","abstract_language","matched_cpcs"]
LABEL_COLUMNS=["docdb_family_id","label","needs_review","confidence","evidence_quote","reason"]
COMBINED_COLUMNS=["docdb_family_id","abstract_en","label","needs_review","confidence","evidence_quote","reason"]
SEED="humanoid-challenge-v1-20261030"

def sha256(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def quote(abstract,label):
    if label:
        hit=re.search(r"humanoid|anthropomorphic",abstract,re.I)
        if hit is None:
            raise ValueError("Positive label does not explicitly mention humanoid/anthropomorphic robot: "+abstract[:160])
        return abstract[max(0,hit.start()-26):min(len(abstract),hit.end()+86)]
    return abstract[:120]

def main():
    data=json.loads((OUT/"selection_annotations.json").read_text(encoding="utf-8"))
    if len(data)!=100 or Counter(x["label"] for x in data)!={0:50,1:50}:
        raise ValueError("Challenge requires exactly 50 positives and 50 negatives")
    keyed={str(x["docdb_family_id"]):x for x in data}
    if len(keyed)!=100:
        raise ValueError("Duplicate label IDs")
    if any(x["needs_review"]!=0 or x["confidence"] not in ("high","medium") for x in data):
        raise ValueError("Curated examples must have decisions and confidence")
    earlier=ROOT/"samples/random_100/random_100_full.csv"
    with earlier.open(newline="",encoding="utf-8-sig") as f:
        excluded={row["docdb_family_id"] for row in csv.DictReader(f)}
    if set(keyed)&excluded:
        raise ValueError("Challenge overlaps previous 100-family benchmark")
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
                    selected[fid]=row
    if set(selected)!=set(keyed):
        raise ValueError("Selected IDs missing from source: "+str(set(keyed)-set(selected)))
    # Shuffle positives and negatives together deterministically, preserving ID-based joins.
    ids=sorted(selected,key=lambda s:hashlib.sha256((SEED+":"+s).encode()).hexdigest())
    OUT.mkdir(parents=True,exist_ok=True)
    outputs={}
    for filename,headers,rows in [
        ("challenge_100_full.csv",FIELDS,[selected[i] for i in ids]),
        ("humanoid_100_abstracts_en.csv",FIELDS+["abstract_en","translation_status"],
          [{**selected[i],"abstract_en":selected[i]["abstract"],"translation_status":"original_en"} for i in ids]),
        ("challenge_100_for_labeling.csv",["docdb_family_id","abstract_language","abstract"],
          [{c:selected[i][c] for c in ("docdb_family_id","abstract_language","abstract")} for i in ids]),
        ("humanoid_100_manual_labels.csv",LABEL_COLUMNS,
          [{**{c:keyed[i][c] for c in ("docdb_family_id","label","needs_review","confidence","reason")},
            "evidence_quote":quote(selected[i]["abstract"],keyed[i]["label"])} for i in ids]),
        ("challenge_100_labeled.csv",COMBINED_COLUMNS,
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
        "n":len(ids),"label_counts":{"relevant":50,"not_relevant":50,"needs_review":0},
        "selection_groups":dict(Counter(x["bucket"] for x in data)),
        "language":"en","seed_for_output_order":SEED,
        "source_zip_sha256":sha256(ZIP),
        "annotation_source":"AI-authored prospective labeling based only on patent abstract, before Kaggle model scores",
        "labeling_definition":"1 only for explicit humanoid/anthropomorphic robot or a component/control system expressly designed for one; 0 for related robotics without such a link",
        "limitations":"Purposive 50:50 case-control challenge; not representative of production prevalence. AI labels provisional pending independent human adjudication. Precision and F1 from this challenge are NOT field prevalence estimates. Re-using it to choose a threshold makes reported performance in-sample.",
        "excluded_previous_sample":True,
        "files":outputs
    }
    (OUT/"sample_summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2,ensure_ascii=False))

if __name__=="__main__":
    main()
