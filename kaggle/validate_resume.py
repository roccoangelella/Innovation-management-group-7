"""Strict, offline provenance and duplicate validation of an interrupted Kaggle run."""
import csv, hashlib, json, math, os, shutil, sys, tempfile, zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import production
from run import REVISION
from screen import MODEL_ID, QUESTION, sha256

EXPECTED=237538
SOURCE_SHA="b7ce0a36f0b3e2778292bdfe10058eb81749b304b62ed6d965dfcc837103276c"
REV="6d771ad7b5ecff5e93b8fc7b90d4c5ccc341954d"

def validate(archive_path, source_path, dest_path):
    archive_path,source_path,dest_path=map(Path,(archive_path,source_path,dest_path))
    if sha256(source_path)!=SOURCE_SHA or REVISION!=REV:
        raise ValueError("Source SHA256 or pinned revision differs")
    with zipfile.ZipFile(archive_path) as z:
        session=json.loads(z.read("session_summary.json"))
        if session["complete"] or session["total"]!=EXPECTED or not session["resume_required"]:
            raise ValueError("Expected an incomplete saved session")
        with zipfile.ZipFile(z.open("humanoid-checkpoint.zip")) as ck:
            names={"production_manifest.json","session_summary.json"}
            names|={f"worker_{i}/{name}" for i in (0,1) for name in ("run_metadata.json","predictions.jsonl")}
            if set(ck.namelist())!=names:
                raise ValueError("Unexpected checkpoint contents")
            if json.loads(ck.read("session_summary.json"))!=session:
                raise ValueError("Inconsistent checkpoint session summary")
            with tempfile.TemporaryDirectory() as td:
                plan=production.prepare(source_path,Path(td)/"shards",REV,expected_rows=EXPECTED)
                expected_manifest=production.identity(source_path,REV,EXPECTED)
                if json.loads(ck.read("production_manifest.json"))!=expected_manifest:
                    raise ValueError("Source, model, question or threshold manifest mismatch")
                if expected_manifest["model"]!=MODEL_ID or expected_manifest["model_revision"]!=REV:
                    raise ValueError("Pinned model mismatch")
                seen=set()
                counts=[]
                for i in (0,1):
                    shard=plan["shard_paths"][i]
                    with shard.open(newline="",encoding="utf-8") as f:
                        ids={r["docdb_family_id"] for r in csv.DictReader(f)}
                    expected_meta={"input_sha256":sha256(shard),"model":MODEL_ID,"revision":REV,"dtype":"float16","question":QUESTION}
                    if json.loads(ck.read(f"worker_{i}/run_metadata.json"))!=expected_meta:
                        raise ValueError(f"Worker {i} shard hash/model mismatch")
                    count=0
                    for line in ck.read(f"worker_{i}/predictions.jsonl").splitlines():
                        row=json.loads(line)
                        if set(row)!=set(production.PREDICTION_FIELDS):
                            raise ValueError("Unexpected prediction fields")
                        key=row["docdb_family_id"]; p=row["probability_relevant"]; d=row["model_decision"]
                        if not isinstance(key,str) or key not in ids or key in seen:
                            raise ValueError("Duplicate or unexpected family ID")
                        if type(p) not in (int,float) or not math.isfinite(p) or not 0<=p<=1 or type(d) is not int or d!=int(p>=0.5):
                            raise ValueError("Invalid probability or decision")
                        seen.add(key); count+=1
                    counts.append(count)
                if not all(counts) or len(seen)!=session["processed"] or len(seen)>=EXPECTED:
                    raise ValueError("Invalid journal totals or checkpoint already complete")
                if dest_path.exists():
                    raise FileExistsError("Refusing to overwrite existing staged checkpoint")
                dest_path.mkdir(parents=True)
                with ck.open("production_manifest.json") as f:
                    pass
                with z.open("humanoid-checkpoint.zip") as inp,(dest_path/"humanoid-checkpoint.zip").open("wb") as out:
                    shutil.copyfileobj(inp,out)
                (dest_path/"dataset-metadata.json").write_text(json.dumps({
                    "id":os.environ["KAGGLE_OWNER"]+"/humanoid-production-resume-43012383316",
                    "title":"Private validated humanoid production checkpoint",
                    "licenses":[{"name":"other"}],
                    "description":"Private resumable screening checkpoint; original artifact retained"
                }))
                print("CHECKPOINT_VALIDATED="+str(len(seen))+"/"+str(EXPECTED),flush=True)
                print("WORKER_COUNTS="+json.dumps(counts),flush=True)
                print("REMAINING="+str(EXPECTED-len(seen)),flush=True)

if __name__=="__main__":
    validate(*sys.argv[1:])
