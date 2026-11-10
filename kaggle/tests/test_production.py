"""Offline production checks: no GPU, HF access or large patent corpus needed."""
import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import production
import production_run


FIELDS = ["docdb_family_id", "year", "title", "title_language", "abstract",
          "abstract_language", "matched_cpcs", "abstract_en", "translation_status"]
REVISION = "pinned-test-revision"


def make_input(path, n=6):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        for i in range(n):
            english = i % 2 == 0
            writer.writerow({"docdb_family_id": str(100 + i), "year": "2022",
                             "title": f"Patent {i}", "title_language": "en",
                             "abstract": f"Robot {i}" if english else f"Robot italien {i}",
                             "abstract_language": "en" if english else "it",
                             "matched_cpcs": "B25J", "abstract_en": f"Robot {i}",
                             "translation_status": "original_en" if english else "translated"})


def write_worker_predictions(plan, missing=None, duplicate=None):
    for i in range(2):
        folder = plan["dir"] / f"worker_{i}"
        folder.mkdir(exist_ok=True)
        with (folder / "predictions.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(production.PREDICTION_FIELDS)
            with plan["shard_paths"][i].open(newline="", encoding="utf-8") as input_stream:
                for row in csv.DictReader(input_stream):
                    key = row["docdb_family_id"]
                    if key == missing:
                        continue
                    prob = 0.8 if int(key) % 2 == 0 else 0.2
                    writer.writerow((key, prob, int(prob >= 0.5)))
                    if key == duplicate:
                        writer.writerow((key, prob, int(prob >= 0.5)))


class ProductionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root / "translated.csv"
        make_input(self.source)
        self.target = self.root / "results"

    def tearDown(self):
        self.tmp.cleanup()

    def test_shard_resume_and_export_full_original_columns(self):
        plan = production.prepare(self.source, self.target, REVISION, expected_rows=6)
        self.assertEqual(plan["count"], 6)
        self.assertEqual(sum(plan["shard_counts"]), 6)
        self.assertTrue(min(plan["shard_counts"]) > 0)
        write_worker_predictions(plan)
        result = production.merge(plan)
        self.assertEqual(result["n_predictions"], 6)
        self.assertEqual(result["n_relevant_exploratory"], 3)
        with zipfile.ZipFile(self.target / "filtered_patents.zip") as archive:
            with archive.open("filtered_patents.csv") as raw:
                import io
                with io.TextIOWrapper(raw, encoding="utf-8") as text:
                    selected = list(csv.DictReader(text))
        self.assertEqual(len(selected), 3)
        self.assertEqual([r["docdb_family_id"] for r in selected], ["100", "102", "104"])
        self.assertEqual(list(selected[0]), FIELDS + ["probability_relevant", "model_decision"])
        journal = self.target / "worker_0" / "predictions.jsonl"
        journal.write_text('{"docdb_family_id":"100"}\n')
        again = production.prepare(self.source, self.target, REVISION, expected_rows=6)
        self.assertEqual(again["shard_counts"], plan["shard_counts"])
        self.assertTrue(journal.exists())

    def test_zip_single_csv(self):
        zip_path = self.root / "translated.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.write(self.source, "humanoid_patents_en.csv")
        plan = production.prepare(zip_path, self.target, REVISION)
        self.assertEqual(plan["count"], 6)

    def test_incomplete_translation_and_raw_schema_refused(self):
        text = self.source.read_text(encoding="utf-8")
        self.source.write_text(text.replace("translated", "failed", 1), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "translation_status"):
            production.prepare(self.source, self.target, REVISION)
        with self.source.open(newline="", encoding="utf-8") as stream:
            original = list(csv.DictReader(stream))
        for row in original:
            row.pop("abstract_en")
            row.pop("translation_status")
        with self.source.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS[:-2])
            writer.writeheader()
            writer.writerows(original)
        with self.assertRaisesRegex(ValueError, "not yet translated"):
            production.prepare(self.source, self.target, REVISION)

    def test_reject_input_change_with_existing_manifest(self):
        production.prepare(self.source, self.target, REVISION)
        self.source.write_text(self.source.read_text() + "another-row\n")
        with self.assertRaises(ValueError):
            production.prepare(self.source, self.target, REVISION)

    def test_detect_missing_duplicate_and_bad_probability(self):
        plan = production.prepare(self.source, self.target, REVISION)
        write_worker_predictions(plan, missing="100")
        with self.assertRaisesRegex(ValueError, "missing IDs"):
            production.merge(plan)
        write_worker_predictions(plan, duplicate="100")
        with self.assertRaisesRegex(ValueError, "duplicate"):
            production.merge(plan)
        write_worker_predictions(plan)
        result_path = self.target / "worker_0" / "predictions.csv"
        result_path2 = self.target / "worker_1" / "predictions.csv"
        for path in (result_path, result_path2):
            content = path.read_text(encoding="utf-8")
            if "0.8,1" in content:
                path.write_text(content.replace("0.8,1", "nan,1", 1), encoding="utf-8")
                break
        with self.assertRaisesRegex(ValueError, "Invalid probability"):
            production.merge(plan)

    def test_different_physical_gpu_masks_for_workers(self):
        plan = production.prepare(self.source, self.target, REVISION)
        launches = []
        class Finished:
            def poll(self):
                return 0
            def wait(self, timeout=None):
                return 0
        def spawn(args, env):
            launches.append((args, env))
            return Finished()
        with patch.object(production.subprocess, "Popen", side_effect=spawn):
            production.run_workers(plan, "/tmp/checkpoint", REVISION, ("0", "1"))
        self.assertEqual([env["CUDA_VISIBLE_DEVICES"] for _, env in launches], ["0", "1"])
        self.assertNotEqual(launches[0][0][launches[0][0].index("--input")+1],
                            launches[1][0][launches[1][0].index("--input")+1])

    def test_translation_summary_gates_incomplete(self):
        path = self.root / "summary.json"
        path.write_text(json.dumps({"incomplete": 0, "completed": 6, "stop_reason": None}))
        self.assertEqual(production_run.translation_expected_rows(path), 6)
        path.write_text(json.dumps({"incomplete": 2, "completed": 4, "stop_reason": None}))
        with self.assertRaisesRegex(ValueError, "partial"):
            production_run.translation_expected_rows(path)

    def test_exclusive_lock_cleanup(self):
        with production_run.exclusive_run(self.target):
            with self.assertRaisesRegex(RuntimeError, "may be active"):
                with production_run.exclusive_run(self.target):
                    pass
        self.assertFalse((self.target / ".screening.lock").exists())


if __name__ == "__main__":
    unittest.main()
