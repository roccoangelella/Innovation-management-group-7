"""Mine a source-faithful, English-only candidate pool for HUMAN audit and selection.

Keyword patterns only route examples for inspection: they are NOT relevance labels.
"""
import argparse
from collections import Counter
import csv
import hashlib
import heapq
import io
import json
from pathlib import Path
import re
import sys
import zipfile

SEED=20261030
SOURCES="humanoid_patents.csv"
STRATA={
  "explicit": re.compile(r"\b(?:humanoid(?:s)?|anthropomorphic|human[- ](?:shaped|like|form) robot|human[- ](?:shaped|like|form) robotic|bipedal? robots?|android robots?|human[- ](?:shaped|like|form) machine)\b", re.I),
  "related": re.compile(r"\b(?:legged robots?|walking robots?|robotic hands?|robot hands?|dexterous (?:manipulation|grasping)|whole[- ]body (?:motion|control|robot)|humanoid locomotion|robot (?:balancing|balance|gait|walking)|robotic (?:grippers?|arms?)|robots? (?:locomotion|perception|navigation)|human[- ]robot interaction)\b", re.I),
  "generic": re.compile(r"\b(?:robots?|robotics?|manipulators?|autonomous|artificial intelligence|computer vision|reinforcement learning)\b", re.I),
}
CAP={"explicit":180,"related":130,"generic":85,"other":40}


def rank(s):
    return int.from_bytes(hashlib.sha256(f"{SEED}:challenge:{s}".encode()).digest(),"big")

def mine(source, prior):
    csv.field_size_limit(sys.maxsize)
    with open(prior,newline="",encoding="utf-8-sig") as f:
        excluded={r["docdb_family_id"] for r in csv.DictReader(f)}
    heaps={k:[] for k in CAP}
    counts=Counter()
    eligible=0
    seen=set()
    with zipfile.ZipFile(source) as archive:
        with archive.open(SOURCES) as raw, io.TextIOWrapper(raw,encoding="utf-8-sig",newline="") as f:
            reader=csv.DictReader(f)
            fields=reader.fieldnames
            if not {"docdb_family_id","abstract","abstract_language","matched_cpcs"}.issubset(fields or []):
                raise ValueError("Missing expected CSV fields")
            for row in reader:
                key=(row["docdb_family_id"] or "").strip()
                if not key or key in seen:
                    raise ValueError("Missing/duplicate family ID: "+repr(key))
                seen.add(key)
                if key in excluded or (row["abstract_language"] or "").strip().lower()!="en" or not (row["abstract"] or "").strip():
                    continue
                eligible+=1
                abstract=row["abstract"]
                group=next((k for k,rx in STRATA.items() if rx.search(abstract)),"other")
                counts[group]+=1
                obj={"docdb_family_id":key,"discovery_bucket":group,"abstract":abstract,"title":row.get("title",""),"matched_cpcs":row.get("matched_cpcs",""),"year":row.get("year","")}
                item=(-rank(key),key,obj)
                heap=heaps[group]
                if len(heap)<CAP[group]:
                    heapq.heappush(heap,item)
                elif item>heap[0]:
                    heapq.heapreplace(heap,item)
    chosen=[]
    for group,heap in heaps.items():
        chosen.extend(x[2] for x in sorted(heap,key=lambda v:(-v[0],v[1])))
    output=Path("samples/humanoid_challenge_100")
    output.mkdir(parents=True,exist_ok=True)
    with (output/"candidate_pool.jsonl").open("w",encoding="utf-8") as f:
        for obj in chosen:
            f.write(json.dumps(obj,ensure_ascii=False)+"\n")
    with (output/"candidate_overview.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=["docdb_family_id","discovery_bucket","matched_cpcs","year","abstract_excerpt"])
        writer.writeheader()
        for o in chosen:
            writer.writerow({k:(o["abstract"][:350] if k=="abstract_excerpt" else o[k]) for k in writer.fieldnames})
    summary={"seed":SEED,"method":"fixed-seed hash-ranked candidate discovery; regex ONLY for recall/navigation, not labels","source":"humanoid_patents.zip","eligible_english_excluding_prior_100":eligible,"discovery_bucket_population":dict(counts),"pool_buckets":dict(Counter(o["discovery_bucket"] for o in chosen)),"pool_size":len(chosen),"prior_random_100_excluded":len(excluded)}
    (output/"candidate_summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",default="humanoid_patents.zip")
    parser.add_argument("--exclude",default="samples/random_100/random_100_full.csv")
    a=parser.parse_args()
    mine(a.source,a.exclude)
