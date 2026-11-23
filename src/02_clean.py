"""PATSTAT enrichment cleaning; run from directory containing humanoid_patents_enriched.csv.

Preserves only unique DOCDB families with PATSTAT application information.
The 'earliest_filing_year' field is filing-based, NOT verified earliest priority.
"""
import re
from pathlib import Path
import pandas as pd

INPUT_CSV = Path("humanoid_patents_enriched.csv")
OUTPUT_CSV = Path("humanoid_patents_clean.csv")
TRUNCATION_START_YEAR = 2023
LEGAL_SUFFIXES = ("CO LTD", "CO", "LTD", "INC", "CORP", "CORPORATION",
                  "COMPANY", "LLC", "GMBH", "SPA", "SA", "SL", "BV", "NV")
SUBSIDIARY_MAP = {
    "ALDEBARAN ROBOTICS": "SOFTBANK ROBOTICS",
    "ALDEBARAN ROBOTIKS": "SOFTBANK ROBOTICS",
    "SOFTBANK ROBOTICS EUROPE": "SOFTBANK ROBOTICS",
    "UBTECH EDUCATION (SHENZHEN)": "UBTECH ROBOTICS",
    "SHENZHEN UBTECH TECHNOLOOGY": "UBTECH ROBOTICS",
    "SHENZHEN UBTECH": "UBTECH ROBOTICS",
    "FOURIER INTELLIGENCE": "SHANGHAI FOURIER INTELLIGENT TECHNOLOGY",
    "FOURIER POWER (BEIJING) TECHNOLOGY": "SHANGHAI FOURIER INTELLIGENT TECHNOLOGY",
    "BEIJING ZHUJI POWER TECHNOLOGY": "ZHUJI POWER (LIMX DYNAMICS)",
    "SHENZHEN ZHUJI POWER TECHNOLOGY": "ZHUJI POWER (LIMX DYNAMICS)",
    "BEIJING XIAOMI ROBOT TECHNOLOGY": "XIAOMI",
    "HANGZHOU YUSHU TECHNOLOGY": "UNITREE ROBOTICS",
    "HANGZHOU UNITREE TECHNOLOGY": "UNITREE ROBOTICS",
    "UNITREE TECHNOLOGY": "UNITREE ROBOTICS",
}

def clean_single_name(name):
    name = re.sub(r"\s+", " ", re.sub(r"[.,]", " ", name.upper().strip())).strip()
    changed = True
    while changed:
        changed = False
        for suffix in LEGAL_SUFFIXES:
            if name.endswith(" " + suffix):
                name = name[: -len(suffix) - 1].strip()
                changed = True
    return SUBSIDIARY_MAP.get(name, name)

def clean_applicant_cell(cell):
    if pd.isna(cell) or not str(cell).strip():
        return "UNKNOWN"
    names = [clean_single_name(part) for part in str(cell).split("; ") if part.strip()]
    return "; ".join(dict.fromkeys(names)) if names else "UNKNOWN"

def main():
    df = pd.read_csv(INPUT_CSV)
    df = df.drop_duplicates(subset=["docdb_family_id"])
    df = df.loc[df["n_applications"].notna()].copy()
    df = df.drop(columns=["year"])
    df["earliest_filing_year"] = df["earliest_filing_year"].astype(int)
    df["earliest_publn_year"] = df["earliest_publn_year"].astype(int)
    df["applicants_clean"] = df["applicants_psn_name"].apply(clean_applicant_cell)
    df = df.drop(columns=["applicants_raw_name", "applicants_psn_name", "applicants_han_name"])
    df["is_truncated"] = df["earliest_filing_year"] >= TRUNCATION_START_YEAR
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Saved {len(df)} families and {len(df.columns)} columns to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
