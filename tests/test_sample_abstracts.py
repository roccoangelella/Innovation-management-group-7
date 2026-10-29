"""Offline tests for deterministic patent benchmark sampling."""
import csv
import io
from pathlib import Path
import tempfile
import unittest
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from sample_abstracts import sample


class SamplingTests(unittest.TestCase):
    def create_source(self, path, reverse=False):
        rows = []
        for i in range(220):
            language = "en" if i < 180 else ("de", "fr", "ja", "it")[i % 4]
            rows.append([str(i + 1), "2025", "Title", "en",
                         f"Unlabeled abstract {i}", language,
                         f"B25J{i % 9}; G06N{i % 3}"])
        if reverse:
            rows.reverse()
        text = io.StringIO()
        writer = csv.writer(text)
        writer.writerow(["docdb_family_id", "year", "title", "title_language",
                         "abstract", "abstract_language", "matched_cpcs"])
        writer.writerows(rows)
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("humanoid_patents.csv", text.getvalue())

    def test_quotas_unique_reproducible_and_zip_compatible(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            first, second = root / "a.zip", root / "b.zip"
            self.create_source(first)
            self.create_source(second, reverse=True)
            s1 = sample(first, root / "out1")
            s2 = sample(second, root / "out2")
            self.assertEqual(s1["selected"], 100)
            self.assertEqual(s1["selected_languages"]["en"], 90)
            self.assertEqual(sum(v for k, v in s1["selected_languages"].items() if k != "en"), 10)
            self.assertEqual(s1["source_cpc_codes"], s1["selected_cpc_codes"])
            a = (root / "out1/humanoid_100_abstracts.csv").read_bytes()
            b = (root / "out2/humanoid_100_abstracts.csv").read_bytes()
            self.assertEqual(a, b)
            with zipfile.ZipFile(root / "out1/humanoid_100_abstracts.zip") as z:
                self.assertEqual(z.namelist(), ["humanoid_patents.csv"])
                self.assertEqual(z.read("humanoid_patents.csv"), a)
            records = list(csv.DictReader(io.StringIO(a.decode())))
            self.assertEqual(len(records), len({r["docdb_family_id"] for r in records}))

    def test_missing_quota_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.create_source(root / "source.zip")
            with self.assertRaisesRegex(ValueError, "Insufficient eligible"):
                sample(root / "source.zip", root / "out", en_size=200)

if __name__ == "__main__":
    unittest.main()
