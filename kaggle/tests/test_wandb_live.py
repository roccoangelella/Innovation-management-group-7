"""Counter correctness without requiring GPUs, API tokens, or W&B network."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wandb_live import JournalCounter


class JournalCounterTests(unittest.TestCase):
    def test_counts_only_complete_appended_records_and_never_double_counts(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "worker_0").mkdir()
            (root / "worker_1").mkdir()
            a = root / "worker_0" / "predictions.jsonl"
            b = root / "worker_1" / "predictions.jsonl"
            first = {"docdb_family_id": "a", "probability_relevant": 0.9, "model_decision": 1}
            second = {"docdb_family_id": "b", "probability_relevant": 0.3, "model_decision": 0}
            with a.open("wb") as stream:
                stream.write((json.dumps(first) + "\n").encode())
                stream.write(json.dumps(second)[:12].encode())
            with b.open("wb") as stream:
                stream.write((json.dumps(second) + "\n").encode())
            counter = JournalCounter(root)
            self.assertEqual(counter.update(), 2)
            self.assertEqual(counter.processed, [1, 1])
            self.assertEqual(sum(counter.positive), 1)
            self.assertEqual(counter.update(), 2)
            # Write remaining bytes to complete the pending JSONL record.
            with a.open("ab") as stream:
                stream.write((json.dumps(second)[12:] + "\n").encode())
            self.assertEqual(counter.update(), 3)
            self.assertEqual(counter.processed, [2, 1])
            self.assertEqual(counter.update(), 3)

    def test_reject_journal_truncation(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            worker = root / "worker_0"
            worker.mkdir()
            file = worker / "predictions.jsonl"
            file.write_text(json.dumps({"docdb_family_id":"x", "probability_relevant":0.8, "model_decision":1}) + "\n")
            counter = JournalCounter(root)
            self.assertEqual(counter.update(), 1)
            file.write_text("")
            with self.assertRaisesRegex(RuntimeError, "truncated"):
                counter.update()

    def test_kaggle_notebook_uses_target_scoped_pip_instead_of_failing_venv(self):
        notebook = Path(__file__).resolve().parents[1] / "production_kernel" / "production.ipynb"
        cells = json.loads(notebook.read_text(encoding="utf-8"))["cells"]
        script = "\n".join("".join(cell["source"]) for cell in cells if cell["cell_type"] == "code")
        self.assertNotIn('"venv", str(monitor_venv)', script)
        self.assertIn('"--target", str(monitor_site)', script)
        self.assertIn('"PYTHONPATH": str(monitor_site)', script)
        self.assertIn('sys.executable, "-u", str(ROOT / "kaggle/wandb_live.py")', script)


if __name__ == "__main__":
    unittest.main()
