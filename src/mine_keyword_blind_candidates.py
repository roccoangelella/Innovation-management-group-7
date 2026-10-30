"""Find patent abstracts for a *human-audited* keyword-blind humanoid challenge.

The patterns below are discovery tools, NEVER relevance labels. They exclude
prior evaluation families and overt humanoid terminology, then sample into
diverse review buckets using stable hash ranks.
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

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "samples" / "humanoid_semantic_holdout_100"
SEED = "semantic-holdout-review-20261030"
EXPLICIT_CUE = re.compile(
    r"\b(?:humanoids?|anthropomorphic|human[- ]like|human[- ]shaped|human[- ]form|android robots?)\b", re.I
)
BIPED = re.compile(r"\b(?:biped(?:al)?|two[- ]legged|two[- ]feet|two[- ]footed|bipedal walking)\b", re.I)
ROBOT = re.compile(r"\b(?:robot|robotic|robots)\b", re.I)
TORSO = re.compile(r"\b(?:torso|trunk|upper[- ]body|waist|shoulders?|neck|head)\b", re.I)
ARM = re.compile(r"\b(?:arms?|hands?|manipulators?|forearms?|elbows?|grippers?)\b", re.I)
LEGS = re.compile(r"\b(?:legs?|knees?|ankles?|feet|foot|gait|walking)\b", re.I)
WHOLE = re.compile(r"\b(?:whole[- ]body|full[- ]body|multi[- ]contact|zero[- ]moment[- ]point|center of mass|centre of mass|standing balance)\b",re.I)
DUALARM = re.compile(r"\b(?:dual[- ]arm|double[- ]arm|two (?:robotic )?arms|both (?:robot )?arms|bilateral manipulation)\b", re.I)
DEXTEROUS = re.compile(r"\b(?:dexterous hand|robotic hand|robot hand|five[- ]finger|five finger|multi[- ]finger|tendon[- ]driven (?:finger|hand))\b", re.I)
QUADRUPED = re.compile(r"\b(?:quadruped|four[- ]legged|four[- ]footed|robot dog|hexapod|six[- ]legged|multi[- ]legged)\b", re.I)
EXO = re.compile(r"\b(?:exoskeleton|prosthe(?:tic|sis)|wearable robot|assisting (?:human|patient))\b",re.I)
INDUSTRY = re.compile(r"\b(?:industrial robot|robotic welding|assembly line|factory robot|surgical robot|operating room|pick[- ]and[- ]place|conveyor)\b",re.I)
MOBILE = re.compile(r"\b(?:mobile manipulat|autonomous mobile robot|robot navigation|mobile robot|robotic arm)\b",re.I)

# Maximum sampled per *discovery* bucket (not the final class distribution).
CAP = {
    "biped_torso_arms": 190,
    "biped_balance": 180,
    "whole_body": 180,
    "dual_arm": 140,
    "robot_hand": 160,
    "quadruped": 95,
    "exoskeleton": 85,
    "industrial": 100,
    "mobile_manipulator": 110,
}

def digest(id_):
    return int.from_bytes(hashlib.sha256(f"{SEED}:{id_}".encode()).digest(), "big")

def bucket(abstract):
    if not ROBOT.search(abstract):
        return None
    biped = bool(BIPED.search(abstract))
    if biped and TORSO.search(abstract) and ARM.search(abstract):
        return "biped_torso_arms"
    if biped:
        return "biped_balance"
    if WHOLE.search(abstract):
        return "whole_body"
    if DUALARM.search(abstract):
        return "dual_arm"
    if DEXTEROUS.search(abstract):
        return "robot_hand"
    if QUADRUPED.search(abstract):
        return "quadruped"
    if EXO.search(abstract):
        return "exoskeleton"
    if INDUSTRY.search(abstract):
        return "industrial"
    if MOBILE.search(abstract):
        return "mobile_manipulator"
    return None

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default=str(ROOT/"humanoid_patents.zip"))
    a=p.parse_args()
    excludes=set()
    for path in [
        ROOT/"samples/random_100/random_100_full.csv",
        ROOT/"samples/humanoid_challenge_100/challenge_100_full.csv",
    ]:
        with path.open(encoding="utf-8-sig",newline="") as f:
            excludes.update(r["docdb_family_id"] for r in csv.DictReader(f))
    csv.field_size_limit(sys.maxsize)
    selected={k:[] for k in CAP}
    counts=Counter()
    inspected=0
    excluded_explicit=0
    with zipfile.ZipFile(a.input) as z:
        with z.open("humanoid_patents.csv") as b,io.TextIOWrapper(b,encoding="utf-8-sig",newline="") as f:
            reader=csv.DictReader(f)
            needed={"docdb_family_id","abstract_language","abstract"}
            if not needed.issubset(reader.fieldnames or []):
                raise ValueError(f"Input schema missing columns {needed}")
            for row in reader:
                inspected+=1
                key=row["docdb_family_id"]
                abstract=row["abstract"]
                if key in excludes or row["abstract_language"].strip().lower()!="en" or not abstract.strip():
                    continue
                if EXPLICIT_CUE.search(abstract):
                    excluded_explicit+=1
                    continue
                category=bucket(abstract)
                if category is None:
                    continue
                counts[category]+=1
                # All source fields are retained for audit; annotation is abstract-only.
                item=(-digest(key),key,{"docdb_family_id":key,"discovery_bucket":category,
                                       "abstract":abstract,"source_year":row.get("year",""),
                                       "source_title":row.get("title",""),
                                       "matched_cpcs":row.get("matched_cpcs","")})
                heap=selected[category]
                if len(heap)<CAP[category]:
                    heapq.heappush(heap,item)
                elif item>heap[0]:
                    heapq.heapreplace(heap,item)
    OUTPUT.mkdir(parents=True,exist_ok=True)
    selected_rows=[item[2] for category in CAP for item in
                   sorted(selected[category],key=lambda x:(-x[0],x[1]))]
    with (OUTPUT/"candidate_pool.jsonl").open("w",encoding="utf-8") as f:
        for row in selected_rows:
            f.write(json.dumps(row,ensure_ascii=False)+"\n")
    with (OUTPUT/"candidate_index.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=["docdb_family_id","discovery_bucket","abstract_excerpt"])
        w.writeheader()
        w.writerows({"docdb_family_id":x["docdb_family_id"],"discovery_bucket":x["discovery_bucket"],
                     "abstract_excerpt":x["abstract"][:450]} for x in selected_rows)
    summary={"method":"Hash-ranked source-abstract discovery, class labels NOT derived from regex",
             "source":"humanoid_patents.zip", "seed":SEED,"source_rows":inspected,
             "previous_family_ids_excluded":len(excludes),
             "excluded_explicit_cue_families":excluded_explicit,
             "discovery_population":dict(counts),
             "selected_candidate_counts":dict(Counter(r["discovery_bucket"] for r in selected_rows)),
             "candidate_count":len(selected_rows),
             "explicit_terms_excluded":["humanoid","anthropomorphic","human-like","human-shaped","human-form","android robot"]}
    (OUTPUT/"candidate_summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":
    main()
