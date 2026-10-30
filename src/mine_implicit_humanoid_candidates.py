"""Mine ambiguous, non-explicit-name English patent abstracts for blind review.

Candidate routing is NOT labeling. No Decider predictions or label fields are used.
"""
import csv
from collections import Counter
import hashlib
import heapq
import io
import json
from pathlib import Path
import re
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"samples/semantic_challenge_100"
SEED="semantic-heldout-v1-20261030"
FORBIDDEN=re.compile(r"\b(?:humanoids?|anthropomorphic)\b",re.I)
PATTERNS={
 "biped":re.compile(r"\b(?:bipedal?|two[- ]legged|two[- ]feet|two[- ]footed|two[- ]leg|upright walking|two mechanical legs|double[- ]leg|biped walking|two legs)\b",re.I),
 "body_parts":re.compile(r"\b(?:robot(?:ic)? (?:upper|lower) (?:body|limbs?)|robot (?:trunk|torso|pelvis|hips?)|robot (?:ankle|knee) joints?|waist (?:and|with) (?:legs|arms)|head (?:and|with) (?:arms|legs)|arm(?:s)? (?:and|with) leg(?:s)?|walking (?:posture|gait|stability)|whole[- ]body control)\b",re.I),
 "robot_tasks":re.compile(r"\b(?:legged robots?|walking robots?|robotic hands?|robot hands?|dexterous manipulation|whole[- ]body|mobile manipulators?|robot(?:ic)? arms?|robots? (?:locomotion|perception|navigation|balancing)|human[- ]robot interaction|exoskeleton robots?|prosthetic legs?|quadruped robots?)\b",re.I),
 "lexical_decoys":re.compile(r"\b(?:prosthe(?:ses|tic)|exoskeleton|bionic(?:s)?|robot dog|quadruped|four[- ]legged|walking aid|human posture|human-like motion|virtual human|human motion|human gait)\b",re.I),
 "random_background":re.compile(r"\brobot(?:s|ic|ics)?\b",re.I)
}
CAP={"biped":280,"body_parts":200,"robot_tasks":130,"lexical_decoys":110,"random_background":60}
def rank(key):
 return int.from_bytes(hashlib.sha256(f"{SEED}:{key}".encode()).digest(),"big")
def main():
 excluded=set()
 for path in (ROOT/"samples/random_100/random_100_full.csv",ROOT/"samples/humanoid_challenge_100/challenge_100_full.csv"):
  with path.open(newline="",encoding="utf-8-sig") as f:
   excluded.update(r["docdb_family_id"] for r in csv.DictReader(f))
 heaps={k:[] for k in CAP}
 counts=Counter()
 rejected=Counter()
 csv.field_size_limit(sys.maxsize)
 with zipfile.ZipFile(ROOT/"humanoid_patents.zip") as archive:
  with archive.open("humanoid_patents.csv") as b,io.TextIOWrapper(b,encoding="utf-8-sig",newline="") as f:
   rd=csv.DictReader(f)
   if not {"docdb_family_id","abstract","abstract_language"}.issubset(rd.fieldnames or []):
    raise ValueError("Missing required source columns")
   for row in rd:
    key=row["docdb_family_id"]
    abstract=row["abstract"]
    if key in excluded or row["abstract_language"].strip().lower()!="en" or not abstract.strip():
     rejected["excluded/language/empty"]+=1;continue
    if FORBIDDEN.search(abstract):
     rejected["explicit_name"]+=1;continue
    bucket=next((k for k,rx in PATTERNS.items() if rx.search(abstract)),None)
    if bucket is None:
     rejected["not_routed"]+=1;continue
    counts[bucket]+=1
    item=(-rank(key),key,{"docdb_family_id":key,"discovery_bucket":bucket,
      "abstract":abstract,"title":row.get("title",""),"year":row.get("year",""),
      "matched_cpcs":row.get("matched_cpcs","")})
    h=heaps[bucket]
    if len(h)<CAP[bucket]:heapq.heappush(h,item)
    elif item>h[0]:heapq.heapreplace(h,item)
 selected=[o[2] for bucket,h in heaps.items() for o in sorted(h,key=lambda v:(-v[0],v[1]))]
 OUT.mkdir(parents=True,exist_ok=True)
 with (OUT/"candidate_pool.jsonl").open("w",encoding="utf-8") as f:
  for row in selected:f.write(json.dumps(row,ensure_ascii=False)+"\n")
 with (OUT/"candidate_overview.csv").open("w",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=["docdb_family_id","discovery_bucket","abstract_excerpt"])
  w.writeheader()
  for row in selected:w.writerow({"docdb_family_id":row["docdb_family_id"],"discovery_bucket":row["discovery_bucket"],
   "abstract_excerpt":row["abstract"][:430]})
 summary={"seed":SEED,"selection":"seeded hash sample within independently routed abstract-only candidate strata; NOT labels",
 "forbidden_terms":["humanoid","humanoids","anthropomorphic"],"prior_sets_excluded":len(excluded),
 "pool_size":len(selected),"pool_buckets":dict(Counter(x["discovery_bucket"] for x in selected)),
 "source_counts":dict(counts),"rejected":dict(rejected)}
 (OUT/"candidate_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
 print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
