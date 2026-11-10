"""Offline completion tests using source-authentic CSV/ZIP schemas and mocked API."""
import argparse
import csv
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import complete_translation as finish
import translate_abstracts as translate


def make_zip(path, member, columns, entries):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        with archive.open(member, "w") as raw:
            with io.TextIOWrapper(raw, encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=columns)
                writer.writeheader()
                writer.writerows(entries)


class FinishTranslationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "source.zip"
        self.partial = self.root / "existing_en.zip"
        self.state = self.root / "state" / "progress.jsonl"
        self.final = self.root / "result.zip"
        self.csv_output = self.root / "work.csv"
        self.summary = self.root / "summary.json"
        self.rows = [
            dict(zip(translate.SOURCE_FIELDS, ["1", "2020", "R1", "en", "A robot", "en", "B25J"])),
            dict(zip(translate.SOURCE_FIELDS, ["2", "2021", "R2", "de", "Ein Roboter", "de", "B25J"])),
            dict(zip(translate.SOURCE_FIELDS, ["3", "2022", "R3", "ja", "ロボット", "ja", "B25J"])),
            dict(zip(translate.SOURCE_FIELDS, ["4", "2023", "R4", "en", "Moving arm", "en", "B25J"])),
            dict(zip(translate.SOURCE_FIELDS, ["5", "2024", "R5", "de", "", "de", "B25J"])),
        ]
        make_zip(self.source, "humanoid_patents.csv", translate.SOURCE_FIELDS, self.rows)
        current = []
        for i, english, status in [(0, "A robot", "original_en"), (1, "A robot in English", "translated"), (3, "Moving arm", "original_en")]:
            row = dict(self.rows[i])
            row["abstract"] = english
            row.update({"abstract_en": english, "translation_status": status})
            current.append(row)
        make_zip(self.partial, "humanoid_patents_en.csv", translate.OUTPUT_FIELDS, current)
        self.arguments = argparse.Namespace(
            source=str(self.source), partial=str(self.partial), state=str(self.state),
            work_csv=str(self.csv_output), final_zip=str(self.final), summary=str(self.summary),
            model="gemini-cascade", batch_size=8, max_batch_chars=12000,
            max_requests=50, rpm=2000, timeout=5, retries=0, passes=2, check=False,
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_seed_and_source_coverage(self):
        partial, stats = finish.compare_seed(self.source, self.partial)
        self.assertEqual(len(partial), 3)
        self.assertEqual(stats["source_total"], 5)
        self.assertEqual(stats["source_missing_abstract"], 1)
        self.assertEqual(stats["eligible"], 4)
        self.assertEqual(stats["pending"], 1)

    def test_complete_and_verify_normalized_zip(self):
        seen = []
        def response(endpoint, key, model, batch, timeout):
            seen.extend(r["docdb_family_id"] for r in batch)
            return {r["docdb_family_id"]: "Japanese robot English" for r in batch}
        with patch.dict(os.environ, {"LLM_ENDPOINT": "https://example.invalid/v1/chat/completions", "GEMR_API_KEY": "test"}, clear=False):
            with patch.object(translate, "request_completion", side_effect=response):
                result = finish.finish(self.arguments)
        self.assertEqual(seen, ["3"])
        self.assertEqual(result["completed"], 4)
        self.assertEqual(result["translated_new"], 1)
        self.assertEqual(result["incomplete"], 0)
        with zipfile.ZipFile(self.final) as archive:
            with archive.open("humanoid_patents_en.csv") as raw:
                with io.TextIOWrapper(raw, encoding="utf-8", newline="") as stream:
                    output = list(csv.DictReader(stream))
        self.assertEqual([r["docdb_family_id"] for r in output], ["1", "2", "3", "4"])
        self.assertTrue(all(r["abstract"] == r["abstract_en"] for r in output))
        self.assertEqual(output[1]["abstract_language"], "de")
        self.assertEqual(output[2]["translation_status"], "translated")
        self.assertEqual(self.source.exists(), True)
        self.assertEqual(self.partial.exists(), True)

    def test_incomplete_does_not_replace_archive(self):
        def fails(endpoint, key, model, batch, timeout):
            raise translate.ResponseError("deliberate synthetic failure")
        with patch.dict(os.environ, {"LLM_ENDPOINT": "https://example.invalid/v1/chat/completions", "GEMR_API_KEY": "test"}, clear=False):
            with patch.object(translate, "request_completion", side_effect=fails):
                with self.assertRaisesRegex(RuntimeError, "Translation incomplete"):
                    finish.finish(self.arguments)
        self.assertFalse(self.final.exists())
        self.assertTrue(self.partial.exists())

    def test_reject_untrusted_seed_metadata(self):
        entries = finish.partial_records(self.partial)
        rows = list(entries.values())
        rows[0]["title"] = "Unrelated invention"
        make_zip(self.partial, "humanoid_patents_en.csv", translate.OUTPUT_FIELDS, rows)
        with self.assertRaisesRegex(ValueError, "metadata differ"):
            finish.compare_seed(self.source, self.partial)

    def test_resume_from_actions_journal_without_private_manifest(self):
        # Simulate a GitHub Actions artifact containing the seed + one
        # additional successfully translated family, but no secret manifest.
        with patch.dict(os.environ, {"LLM_ENDPOINT": "https://example.invalid/v1/chat/completions", "GEMR_API_KEY": "test"}, clear=False):
            stats = finish.prepare_seed(self.source, self.partial, self.state, os.environ["LLM_ENDPOINT"], "gemini-cascade")
            self.assertEqual(stats["pending"], 1)
            with self.state.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps({
                    "docdb_family_id": "3", "abstract_en": "Japanese robot English",
                    "translation_status": "translated",
                }) + "\n")
            manifest = self.state.with_suffix(".manifest.json")
            manifest.unlink()  # The artifact excludes the secret endpoint.
            def no_api(*args, **kwargs):
                raise AssertionError("Already translated abstract was sent again")
            with patch.object(translate, "request_completion", side_effect=no_api):
                summary = finish.finish(self.arguments)
            self.assertEqual(summary["completed"], 4)
            self.assertEqual(summary["translated_new"], 1)
            self.assertEqual(summary["incomplete"], 0)
            self.assertTrue(manifest.is_file())

    def test_resume_rejects_unknown_family_from_artifact(self):
        with patch.dict(os.environ, {"LLM_ENDPOINT": "https://example.invalid/v1/chat/completions"}, clear=False):
            finish.prepare_seed(self.source, self.partial, self.state, os.environ["LLM_ENDPOINT"], "gemini-cascade")
            with self.state.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps({
                    "docdb_family_id": "9999", "abstract_en": "Unrelated",
                    "translation_status": "translated",
                }) + "\n")
            self.state.with_suffix(".manifest.json").unlink()
            with self.assertRaisesRegex(ValueError, "unknown DOCDB"):
                finish.prepare_seed(self.source, self.partial, self.state, os.environ["LLM_ENDPOINT"], "gemini-cascade")
            self.assertFalse(self.state.with_suffix(".manifest.json").exists())

    def test_missing_endpoint_refused_without_network(self):
        with patch.dict(os.environ, {"LLM_ENDPOINT": ""}):
            with self.assertRaisesRegex(ValueError, "LLM_ENDPOINT"):
                finish.finish(self.arguments)


if __name__ == "__main__":
    unittest.main()
