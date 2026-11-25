"""Run in EPO TIP PROD. Export normalized metadata for the retained family IDs."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, default=Path("data/final/humanoid_patents_final.csv"))
    p.add_argument("--out", type=Path, default=Path("data/step1_local"))
    p.add_argument("--env", choices=["TEST", "PROD"], default="PROD")
    p.add_argument("--config", type=Path, default=Path("config/step1.json"))
    p.add_argument("--edition", required=True, help="PATSTAT release shown in TIP")
    args = p.parse_args()
    cfg = json.loads(args.config.read_text())
    with args.input.open(encoding="utf-8-sig", newline="") as f:
        ids = [int(row["docdb_family_id"]) for row in csv.DictReader(f)]
    if not ids or min(ids) <= 0 or len(ids) != len(set(ids)):
        raise ValueError("Expected unique positive DOCDB family IDs")
    if cfg["ipr_type"] != "PI":
        raise ValueError("Only invention patents are supported")
    from epo.tipdata.patstat import PatstatClient
    client = PatstatClient(env=args.env)
    args.out.mkdir(parents=True, exist_ok=True)
    manifest = args.out / "manifest.json"
    manifest.unlink(missing_ok=True)
    scope = "SELECT * FROM tls201_appln WHERE ipr_type='PI' AND docdb_family_id IN (" + ",".join(map(str, sorted(ids))) + ")"
    prefix = "WITH a AS (" + scope + ") "
    queries = {
        "applications": (["docdb_family_id","appln_id","appln_auth","appln_kind","appln_filing_year","earliest_filing_year"], prefix + "SELECT docdb_family_id, appln_id, appln_auth, appln_kind, appln_filing_year, earliest_filing_year FROM a"),
        "cpc": (["appln_id","cpc_class_symbol"], prefix + "SELECT DISTINCT a.appln_id, c.cpc_class_symbol FROM a JOIN tls224_appln_cpc c USING(appln_id)"),
        "persons": (["appln_id","person_id","country","applt_seq_nr","invt_seq_nr"], prefix + "SELECT DISTINCT a.appln_id, p.person_id, TRIM(p.person_ctry_code) AS country, r.applt_seq_nr, r.invt_seq_nr FROM a JOIN tls207_pers_appln r USING(appln_id) JOIN tls206_person p ON p.person_id=r.person_id WHERE r.applt_seq_nr>0 OR r.invt_seq_nr>0"),
        "wipo": (["appln_id","techn_field_nr","weight"], prefix + "SELECT a.appln_id, w.techn_field_nr, w.weight FROM a JOIN tls230_appln_techn_field w USING(appln_id)"),
        "wipo_names": (["techn_field_nr","techn_field","techn_sector"], "SELECT DISTINCT techn_field_nr, techn_field, techn_sector FROM tls901_techn_field_ipc"),
        "global_families": (["year","n"], "WITH f AS (SELECT docdb_family_id, MIN(CASE WHEN earliest_filing_year BETWEEN 1800 AND 2100 THEN earliest_filing_year END) AS year FROM tls201_appln WHERE ipr_type='PI' AND docdb_family_id>0 GROUP BY docdb_family_id) SELECT year, COUNT(*) AS n FROM f WHERE year BETWEEN %d AND %d GROUP BY year" % (cfg["year_min"], cfg["year_max"])),
        "global_applications": (["year","n"], "SELECT appln_filing_year AS year, COUNT(DISTINCT appln_id) AS n FROM tls201_appln WHERE ipr_type='PI' AND docdb_family_id>0 AND appln_filing_year BETWEEN %d AND %d GROUP BY year" % (cfg["year_min"], cfg["year_max"])),
    }
    counts, hashes = {}, {}
    for name, (columns, sql) in queries.items():
        path = args.out / (name + ".csv")
        n = 0
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            for row in client.sql_query_iterator(sql, use_legacy_sql=False):
                writer.writerow({k: row[k] for k in columns})
                n += 1
        counts[name] = n
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        print(name, n, flush=True)
    manifest.write_text(json.dumps({"environment":args.env,"edition":args.edition,
        "input_sha256":hashlib.sha256(args.input.read_bytes()).hexdigest(),
        "config":cfg,"counts":counts,"sha256":hashes}, indent=2))
if __name__ == "__main__":
    main()
