"""Synthetic offline tests for evaluation with missing labels and no positive class."""
import csv
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("kaggle_eval", Path(__file__).resolve().parents[1] / "evaluate.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class EvaluateTests(unittest.TestCase):
    def test_negative_only_and_review(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            pred = path/"pred.csv"
            labels = path/"labels.csv"
            with pred.open("w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=["docdb_family_id","probability_relevant"])
                w.writeheader()
                w.writerows([
                    {"docdb_family_id":"a","probability_relevant":"0.02"},
                    {"docdb_family_id":"b","probability_relevant":"0.9"},
                    {"docdb_family_id":"c","probability_relevant":"0.7"},
                ])
            with labels.open("w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=["docdb_family_id","label","needs_review"])
                w.writeheader()
                w.writerows([
                    {"docdb_family_id":"a","label":"0","needs_review":"0"},
                    {"docdb_family_id":"b","label":"0","needs_review":"0"},
                    {"docdb_family_id":"c","label":"","needs_review":"1"},
                ])
            result, cases = module.evaluate(pred, labels)
            self.assertEqual((result["tn"], result["fp"], result["n_unresolved_excluded"]), (1,1,1))
            self.assertIsNone(result["recall"])
            self.assertIsNone(result["precision"])
            self.assertIsNone(result["f1"])
            self.assertAlmostEqual(result["specificity"], .5)
            self.assertEqual(3, len(cases))

    def test_all_labels_required(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path/"pred.csv").write_text("docdb_family_id,probability_relevant\na,0.2\n", encoding="utf-8")
            (path/"labels.csv").write_text("docdb_family_id,label,needs_review\nb,0,0\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                module.evaluate(path/"pred.csv",path/"labels.csv")


if __name__ == "__main__":
    unittest.main()
