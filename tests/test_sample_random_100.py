"""Offline synthetic tests; no external data or network."""
import csv
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
import zipfile

P = Path(__file__).resolve().parents[1] / "src/sample_random_100.py"
spec = importlib.util.spec_from_file_location("sample_random_100", P)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class TestRandomSampling(unittest.TestCase):
    def create_zip(self, path, rows):
        f = io.StringIO(newline="")
        w = csv.DictWriter(f, ["docdb_family_id", "abstract_language", "abstract", "matched_cpcs"])
        w.writeheader()
        w.writerows(rows)
        with zipfile.ZipFile(path, "w") as z:
            z.writestr("humanoid_patents.csv", f.getvalue())

    def test_order_invariance_and_output(self):
        rows = [
            {"docdb_family_id": str(n), "abstract_language": "en" if n % 3 else "de",
             "abstract": f"Original text {n}", "matched_cpcs": "A" if n % 2 else "B"}
            for n in range(250)
        ] + [{"docdb_family_id": "empty", "abstract_language": "en", "abstract": "", "matched_cpcs": ""}]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)
            a, b = path / "a.zip", path / "b.zip"
            self.create_zip(a, rows)
            self.create_zip(b, list(reversed(rows)))
            _, x, stats = mod.sample(a)
            _, y, _ = mod.sample(b)
            self.assertEqual([r["docdb_family_id"] for r in x], [r["docdb_family_id"] for r in y])
            self.assertEqual(100, len(x))
            self.assertEqual(250, stats["eligible_families"])
            self.assertEqual(1, stats["excluded"]["empty_abstract"])
            mod.write_sample(a, path / "out")
            with (path / "out/random_100_for_labeling.csv").open(newline="") as f:
                self.assertEqual(100, len(list(csv.DictReader(f))))
            with zipfile.ZipFile(path / "out/random_100_for_translation.zip") as z:
                self.assertEqual(["humanoid_patents.csv"], z.namelist())

    def test_duplicate_ids_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "a.zip"
            self.create_zip(path, [
                {"docdb_family_id": "1", "abstract_language": "en", "abstract": "abc", "matched_cpcs": ""},
                {"docdb_family_id": "1", "abstract_language": "en", "abstract": "xyz", "matched_cpcs": ""},
            ])
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                mod.sample(path, 1)


if __name__ == "__main__":
    unittest.main()
