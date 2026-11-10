"""Journal corruption recovery tests; no GPU required."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from screen import load_journal


def record(key="101", probability=0.9, decision=1):
    return {"docdb_family_id": key, "probability_relevant": probability, "model_decision": decision}


class JournalTests(unittest.TestCase):
    def test_torn_final_record_is_removed_and_can_resume(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "predictions.jsonl"
            good = json.dumps(record()).encode() + b"\n"
            path.write_bytes(good + b'{"docdb_family_id": "102", "probability_relevant": ')
            done = load_journal(path, {"101", "102"})
            self.assertEqual(set(done), {"101"})
            self.assertEqual(path.read_bytes(), good)

    def test_valid_last_record_without_newline_is_repaired(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "predictions.jsonl"
            path.write_text(json.dumps(record()), encoding="utf-8")
            self.assertEqual(set(load_journal(path, {"101"})), {"101"})
            self.assertTrue(path.read_bytes().endswith(b"\n"))

    def test_invalid_interior_journal_and_mismatched_id_fail(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "predictions.jsonl"
            path.write_text(json.dumps(record()) + "\n" + "broken\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Malformed journal"):
                load_journal(path, {"101"})
            path.write_text(json.dumps(record()) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unexpected"):
                load_journal(path, {"999"})

    def test_invalid_probability_is_not_reused(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "predictions.jsonl"
            path.write_text(json.dumps(record(probability=1.4)) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "probability"):
                load_journal(path, {"101"})


if __name__ == "__main__":
    unittest.main()
