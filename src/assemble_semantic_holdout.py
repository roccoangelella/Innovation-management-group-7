"""Build an English-only keyword-blind humanoid relevance challenge.

Selection IDs and label intentions below were curated after viewing source
abstracts, WITHOUT inspecting Decider predictions on those cases.  Labels are
AI-authored provisional judgments, not human adjudication or production truth.
"""
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"samples/humanoid_semantic_holdout_100"
SEED="keyword-blind-semantic-holdout-v1-20261030"

# Each value is a set of *reviewed family IDs*, not an executable text filter.
GROUPS={
 "positive_integrated_body": (
  "18782100 54023838 94908902 73681956 92477197 78970447 69141200 "
  "86445432 92545328 81275094 86417821 92817716 70031701 90023341"
 ),
 "positive_biped_human_gait": (
  "84336725 70203103 73604435 96355840 73458982 70878106 83079564 "
  "26551932 16652812 41432044 55322736 88362185 89752150 47262273 "
  "65666073 80068260 96952194"
 ),
 "positive_whole_body_tasks": (
  "66259327 70422519 91647315 51995980 86069862 86834261 75014666 "
  "51569710 76317112"
 ),
 "negative_nonhuman_bipeds": (
  "88669050 49453596 87874416 63379503 89823293 73470508 75144521 "
  "95890969 74860101 40287080"
 ),
 "negative_multilegged_animals": (
  "91154741 86960635 86298671 57167206 83197074 63755583 52890045 "
  "97332125 82175010 59123409 86308708 65756343 88639010 89550355 82868787"
 ),
 "negative_dual_arm_manipulators": (
  "57895428 91145812 59420460 77280595 81508970 96710647 91885924 "
  "58603775 67751849 86116322 81262867 84727209"
 ),
 "negative_generic_robot_hands": (
  "73316201 23863570 85152898 56566517 40536433 60572175 36587666 "
  "96196821 55359655 43755469"
 ),
 "negative_wearable_exoskeletons": (
  "96511461 39925149 74007529 96781117 81234871 83757737 58962387 68366619"
 ),
 "negative_mobile_specialists": (
  "83639461 78509247 85385586 97421199 59197402"
 ),
}
REASONS={
 "positive_integrated_body":"Human-body robot morphology or task: coordinated torso, articulated arms/hands, and paired walking legs.",
 "positive_biped_human_gait":"Upright articulated hip/knee/ankle mechanics or human-style biped gait and balance directly address humanoid locomotion.",
 "positive_whole_body_tasks":"Coordinated left/right feet, posture, upper limbs, or body mass for human-like multi-limb control.",
 "negative_nonhuman_bipeds":"Non-humanoid two-footed mechanism: animal model, special-purpose climbing platform, or human-worn exoskeleton.",
 "negative_multilegged_animals":"Animal-type or multilegged robot platform rather than a two-legged human-body robot.",
 "negative_dual_arm_manipulators":"Two-arm industrial/service manipulator without a humanoid body or biped walking task.",
 "negative_generic_robot_hands":"General robotic hand/gripper; abstract does not establish a specifically humanoid platform.",
 "negative_wearable_exoskeletons":"Mechanical structure is worn by a human for assistance, not an independent humanoid robot.",
 "negative_mobile_specialists":"Specialized mobile, wheeled, rail, or agricultural robotic system without humanlike integrated morphology.",
}
CUE=re.compile(r"\b(?:humanoids?|anthropomorphic|human[- ]like|human[- ]shaped|human[- ]form|android robots?)\b",re.I)
LABEL_FIELDS=["docdb_family_id","abstract_en","label","needs_review","confidence","evidence_quote","reason"]
SOURCE_FIELDS=["docdb_family_id","year","title","title_language","abstract","abstract_language","matched_cpcs"]

def sha(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as f:
  for block in iter(lambda:f.read(1<<20),b""): h.update(block)
 return h.hexdigest()

def csv_out(path,headers,rows):
 with path.open("w",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=headers)
  w.writeheader();w.writerows(rows)

def main():
 choices={}
 for group,strings in GROUPS.items():
  label=int(group.startswith("positive_"))
  for id_ in strings.split():
   if id_ in choices: raise ValueError(f"Duplicate selected ID: {id_}")
   confidence="high" if group in ("positive_integrated_body","negative_multilegged_animals","negative_mobile_specialists") else "medium"
   choices[id_]={"label":label,"needs_review":0,"confidence":confidence,
                 "review_group":group,"reason":REASONS[group]}
 if len(choices)!=100 or Counter(v["label"] for v in choices.values())!={1:40,0:60}:
  raise ValueError("Expected 40 provisional relevant and 60 nonrelevant families")
 prior=set()
 for name in ("samples/random_100/random_100_full.csv",
              "samples/humanoid_challenge_100/challenge_100_full.csv"):
  with (ROOT/name).open(newline="",encoding="utf-8-sig") as f:
   prior.update(r["docdb_family_id"] for r in csv.DictReader(f))
 if set(choices)&prior: raise ValueError("Overlaps previous evaluation benchmark")
 found={}
 csv.field_size_limit(sys.maxsize)
 with zipfile.ZipFile(ROOT/"humanoid_patents.zip") as z:
  with z.open("humanoid_patents.csv") as inp,io.TextIOWrapper(inp,encoding="utf-8-sig",newline="") as f:
   reader=csv.DictReader(f)
   if reader.fieldnames!=SOURCE_FIELDS: raise ValueError(f"Changed source schema: {reader.fieldnames}")
   for record in reader:
    key=record["docdb_family_id"]
    if key not in choices: continue
    if key in found: raise ValueError("Repeated patent family")
    original=record["abstract"]
    if record["abstract_language"].lower().strip()!="en" or not original.strip():
     raise ValueError(f"Not English/nonempty: {key}")
    if CUE.search(original):
     raise ValueError(f"Leaking obvious humanoid terminology: {key}")
    found[key]=record
 if set(found)!=set(choices): raise ValueError(f"Missing source family IDs: {set(choices)-set(found)}")
 ids=sorted(found,key=lambda key:hashlib.sha256((SEED+":"+key).encode()).digest())
 OUT.mkdir(parents=True,exist_ok=True)
 combined=[];audit=[];blind=[];originals=[]
 for id_ in ids:
  a=found[id_]["abstract"];c=choices[id_]
  # Exact source quotation (not translated or generated). The rationale,
  # label and group stay out of the model request in kaggle/screen.py.
  excerpt=a[:min(180,len(a))]
  combined.append({"docdb_family_id":id_,"abstract_en":a,"label":c["label"],
                   "needs_review":0,"confidence":c["confidence"],
                   "evidence_quote":excerpt,"reason":c["reason"]})
  audit.append({"docdb_family_id":id_,"review_group":c["review_group"],
                "label":c["label"],"confidence":c["confidence"],"reason":c["reason"],
                "evidence_quote":excerpt})
  blind.append({"docdb_family_id":id_,"abstract_en":a})
  originals.append(found[id_])
 csv_out(OUT/"semantic_holdout_100_labeled.csv",LABEL_FIELDS,combined)
 csv_out(OUT/"semantic_holdout_100_blind_review.csv",["docdb_family_id","abstract_en"],blind)
 csv_out(OUT/"annotation_audit.csv",
         ["docdb_family_id","review_group","label","confidence","reason","evidence_quote"],audit)
 csv_out(OUT/"semantic_holdout_100_full.csv",SOURCE_FIELDS,originals)
 summary={
  "version":"v1","n":100,"positive_labels":40,"negative_labels":60,
  "needs_review":0,"language":"en","shuffle_seed":SEED,
  "method":"Purposive, manually curated candidate IDs from source abstracts without overt humanoid terms; independent of any Decider predictions for these 100 cases",
  "label_policy":"Humanoid body configuration, coordinated humanlike biped locomotion, or integrated upper/lower-body tasks vs closely related but nonhuman robots and generic devices",
  "label_status":"AI-authored provisional relevance judgments; NOT independently adjudicated human gold labels",
  "known_risks":"Broader morphology/task relevance may differ from the existing Decider prompt's strict explicit humanoid link. Class balance is enriched. Positive labeling of biped-only components needs independent review. Do not calibrate a production threshold or claim prevalence-generalized precision from this set.",
  "excluded_prior_family_count":len(prior),
  "explicit_humanoid_or_anthropomorphic_terms_found":0,
  "selection_groups":dict(Counter(v["review_group"] for v in choices.values())),
  "source_zip_sha256":sha(ROOT/"humanoid_patents.zip"),
  "files":{p.name:{"sha256":sha(p),"bytes":p.stat().st_size} for p in
           [OUT/"semantic_holdout_100_labeled.csv",OUT/"semantic_holdout_100_blind_review.csv",
            OUT/"annotation_audit.csv",OUT/"semantic_holdout_100_full.csv"]}
 }
 (OUT/"sample_summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(summary,indent=2))

if __name__=="__main__":
 main()
