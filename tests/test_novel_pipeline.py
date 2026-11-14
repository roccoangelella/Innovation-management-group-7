"""Offline tests for the novel PATSTAT -> GemRouter -> Kaggle compatibility path."""
import ast
import csv
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "kaggle")]
import translate_abstracts as tr
import translate_novel_patents as novel
import validate_novel_output as output_gate
from production import sha256


def write_zip(path, name, fields, rows):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(name, stream.getvalue())


class NovelPipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.baseline = self.root / "baseline.zip"
        self.novel = self.root / "novel.zip"
        write_zip(self.baseline, "humanoid_patents.csv", tr.SOURCE_FIELDS, [{
            "docdb_family_id": "100", "abstract": "Existing invention",
            "abstract_language": "en",
        }])
        self.rows = [
            {"docdb_family_id": "101", "year": "2025", "title": "A robot",
             "title_language": "en", "abstract": "A robot moves.", "abstract_language": "en",
             "all_cpcs": "B25J", "ipr_types": "PI", "matching_channels": "v3"},
            {"docdb_family_id": "102", "year": "2025", "title": "Un robot",
             "title_language": "fr", "abstract": "Un robot marche.", "abstract_language": "fr",
             "all_cpcs": "G05D", "ipr_types": "PI", "matching_channels": "v3"},
            {"docdb_family_id": "103", "year": "2025", "title": "Incomplete",
             "title_language": "en", "abstract": "", "abstract_language": "",
             "all_cpcs": "B25J", "ipr_types": "PI", "matching_channels": "v3"},
        ]
        write_zip(self.novel, "new_humanoid_patents.csv", tr.NOVEL_SOURCE_FIELDS, self.rows)

    def test_new_schema_and_overlap_gate(self):
        member, fields = tr.source_layout(self.novel)
        self.assertEqual(member, "new_humanoid_patents.csv")
        self.assertEqual(fields, tr.NOVEL_SOURCE_FIELDS)
        self.assertEqual(novel.validate_source(self.novel, self.baseline)["missing"], 1)
        self.rows[0]["docdb_family_id"] = "100"
        write_zip(self.novel, "new_humanoid_patents.csv", tr.NOVEL_SOURCE_FIELDS, self.rows)
        with self.assertRaisesRegex(ValueError, "overlaps"):
            novel.validate_source(self.novel, self.baseline)

    def test_translation_normalization_preserves_provenance_and_output_gate(self):
        stats = novel.validate_source(self.novel, self.baseline)
        self.assertEqual(stats["total"] - stats["missing"], 2)
        intermediate = self.root / "intermediate.csv"
        output = self.root / "novel_humanoid_patents_en.csv"
        with intermediate.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=tr.NOVEL_SOURCE_FIELDS + ["abstract_en", "translation_status"])
            writer.writeheader()
            writer.writerow({**self.rows[0], "abstract_en": "A robot moves.", "translation_status": "original_en"})
            writer.writerow({**self.rows[1], "abstract_en": "A robot walks.", "translation_status": "translated"})
        self.assertEqual(novel.create_english_csv(self.novel, intermediate, output, 2)["completed"], 2)
        with output.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(rows[1]["abstract"], "A robot walks.")
        self.assertEqual(rows[1]["all_cpcs"], "G05D")
        self.assertEqual(rows[1]["matching_channels"], "v3")
        summary = self.root / "novel_translation_summary.json"
        summary.write_text(json.dumps({"completed": 2, "eligible": 2, "incomplete": 0,
                                       "final_csv_sha256": sha256(output)}))
        results = self.root / "results"
        results.mkdir()
        predictions = results / "predictions.csv"
        with predictions.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(["docdb_family_id", "probability_relevant", "model_decision"])
            writer.writerow(["101", "0.8", "1"])
            writer.writerow(["102", "0.2", "0"])
        filtered = results / "filtered_patents.zip"
        with zipfile.ZipFile(filtered, "w", zipfile.ZIP_DEFLATED) as archive:
            with io.StringIO(newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(rows[0]) + ["probability_relevant", "model_decision"])
                writer.writeheader()
                writer.writerow({**rows[0], "probability_relevant": "0.8", "model_decision": "1"})
                archive.writestr("filtered_patents.csv", stream.getvalue())
        (results / "production_summary.json").write_text(json.dumps({
            "n_input": 2, "n_predictions": 2, "n_relevant_exploratory": 1,
            "input_sha256": sha256(output), "predictions_sha256": sha256(predictions),
            "filtered_zip_sha256": sha256(filtered),
        }))
        output_gate.validate(output, summary, results)
        with predictions.open("a", encoding="utf-8") as stream:
            stream.write("999,0.5,1\n")
        with self.assertRaisesRegex(ValueError, "SHA256"):
            output_gate.validate(output, summary, results)

    def test_novel_notebook_parses_and_has_no_full_corpus_assumption(self):
        nb = json.loads((ROOT / "kaggle/novel_kernel/production.ipynb").read_text(encoding="utf-8"))
        script = "".join(cell["source"][0] if False else "".join(cell["source"])
                         for cell in nb["cells"] if cell["cell_type"] == "code")
        ast.parse(script)
        self.assertIn("REPLACE_RESUME_ENABLED", script)
        self.assertIn('"--total", str(count)', script)
        self.assertNotIn("128533", script)
        self.assertNotIn("237538", script)


if __name__ == "__main__":
    unittest.main()
