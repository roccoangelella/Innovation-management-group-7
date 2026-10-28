"""Export all DOCDB patent families matching 64 humanoid-robotics CPC prefixes."""

import csv
import io
import zipfile
from epo.tipdata.patstat import PatstatClient

ENV = "PROD"  # Change to "TEST" for a trial run on the small test dataset.

CPC_CODES = [
    # A. Humanoid robots and service robots
    "G06N3/008", "B62D57/032", "B62D57/028", "B25J15/0009",
    "B25J11/0005", "B25J11/001", "B25J11/0015", "B25J9/0003",
    "B25J9/0087", "B25J9/1682", "B25J11/0035", "B25J11/008", "B25J11/009",
    # B. Manipulation, mechanisms, control and sensing
    "B25J9/06", "B25J9/08", "B25J9/1025", "B25J9/1075", "B25J9/12",
    "B25J9/1612", "B25J9/162", "B25J9/163", "B25J9/1633",
    "B25J9/1656", "B25J9/1661", "B25J9/1664", "B25J9/1666",
    "B25J9/1674", "B25J9/1689", "B25J9/1694", "B25J9/1697",
    "B25J13/003", "B25J13/082", "B25J13/083", "B25J13/084",
    "B25J13/089", "B25J15/0004", "B25J15/12", "B25J17/02",
    "B25J19/0008", "B25J19/02", "B25J19/06",
    # C. Navigation, human perception, learning and speech
    "B62D57/024", "G05D1/246", "G05D1/435", "G05D1/495", "G05D1/498",
    "G05D1/622", "G05D1/639", "G05D1/642", "G05D1/648", "G05D1/686",
    "G05D1/6895", "G06V40/16", "G06V40/174", "G06V40/20",
    "G06V40/23", "G06V40/25", "G06V40/28", "G06N3/092",
    "G10L15/22", "G10L13/00",
    # D. Exoskeletons and toy robots (included at your request)
    "B25J9/0006", "A63H11/18", "A63H11/00",
]

cpc_filter = " OR ".join(
    f"STARTS_WITH(REPLACE(c.cpc_class_symbol, ' ', ''), '{code}')"
    for code in CPC_CODES
)

query = f"""
WITH matches AS (
    SELECT DISTINCT
        a.docdb_family_id,
        REPLACE(c.cpc_class_symbol, ' ', '') AS cpc
    FROM tls201_appln AS a
    JOIN tls224_appln_cpc AS c ON a.appln_id = c.appln_id
    WHERE a.ipr_type = 'PI'
      AND a.docdb_family_id > 0
      AND ({cpc_filter})
),
families AS (
    SELECT
        docdb_family_id,
        STRING_AGG(DISTINCT cpc, '; ' ORDER BY cpc) AS matched_cpcs
    FROM matches
    GROUP BY docdb_family_id
),
family_years AS (
    SELECT
        a.docdb_family_id,
        MIN(NULLIF(a.earliest_filing_year, 0)) AS year
    FROM tls201_appln AS a
    JOIN families AS f ON a.docdb_family_id = f.docdb_family_id
    WHERE a.ipr_type = 'PI'
    GROUP BY a.docdb_family_id
),
family_titles AS (
    SELECT
        a.docdb_family_id,
        t.appln_title AS title,
        t.appln_title_lg AS title_language
    FROM tls201_appln AS a
    JOIN families AS f ON a.docdb_family_id = f.docdb_family_id
    JOIN tls202_appln_title AS t ON a.appln_id = t.appln_id
    WHERE a.ipr_type = 'PI'
      AND NULLIF(TRIM(t.appln_title), '') IS NOT NULL
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY a.docdb_family_id
        ORDER BY IF(LOWER(t.appln_title_lg) = 'en', 0, 1), a.appln_id
    ) = 1
),
family_abstracts AS (
    SELECT
        a.docdb_family_id,
        ab.appln_abstract AS abstract,
        ab.appln_abstract_lg AS abstract_language
    FROM tls201_appln AS a
    JOIN families AS f ON a.docdb_family_id = f.docdb_family_id
    JOIN tls203_appln_abstr AS ab ON a.appln_id = ab.appln_id
    WHERE a.ipr_type = 'PI'
      AND NULLIF(TRIM(ab.appln_abstract), '') IS NOT NULL
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY a.docdb_family_id
        ORDER BY IF(LOWER(ab.appln_abstract_lg) = 'en', 0, 1), a.appln_id
    ) = 1
)
SELECT
    f.docdb_family_id,
    y.year,
    t.title,
    t.title_language,
    ab.abstract,
    ab.abstract_language,
    f.matched_cpcs
FROM families AS f
LEFT JOIN family_years AS y USING (docdb_family_id)
LEFT JOIN family_titles AS t USING (docdb_family_id)
LEFT JOIN family_abstracts AS ab USING (docdb_family_id)
ORDER BY f.docdb_family_id
"""

client = PatstatClient(env=ENV)
count = 0
with zipfile.ZipFile("humanoid_patents.zip", "w", compression=zipfile.ZIP_DEFLATED) as archive:
    with archive.open("humanoid_patents.csv", "w") as raw:
        with io.TextIOWrapper(raw, newline="", encoding="utf-8") as output:
            writer = csv.writer(output)
            writer.writerow(["docdb_family_id", "year", "title", "title_language", "abstract", "abstract_language", "matched_cpcs"])
            for row in client.sql_query_iterator(query, use_legacy_sql=False):
                writer.writerow([row["docdb_family_id"], row["year"], row["title"],
                                 row["title_language"], row["abstract"], row["abstract_language"],
                                 row["matched_cpcs"]])
                count += 1

print(f"Saved {count} families (64 CPC codes, {ENV}) to humanoid_patents.zip")
