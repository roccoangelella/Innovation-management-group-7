"""Offline tests for single-command Kaggle setup; no network/GPU needed."""
import importlib.util
import csv
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, call

MODULE = Path(__file__).resolve().parents[1] / "run.py"
spec = importlib.util.spec_from_file_location("kaggle_run", MODULE)
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)
SCREEN = Path(__file__).resolve().parents[1] / "screen.py"
screen_spec = importlib.util.spec_from_file_location("kaggle_screen", SCREEN)
screen = importlib.util.module_from_spec(screen_spec)
screen_spec.loader.exec_module(screen)


class LauncherTests(unittest.TestCase):
    def test_challenge_cli_is_exposed_and_has_disjoint_default_output(self):
        source = MODULE.read_text(encoding="utf-8")
        self.assertIn('parser.add_argument("--challenge"', source)
        self.assertIn('"/kaggle/working/challenge_100/predictions.csv"', source)
        self.assertIn("challenge_dir / COMBINED_FILENAME", source)
        self.assertIn("args.input = args.dataset", source)
        self.assertIn("args.labels = args.dataset", source)

    def test_single_labeled_csv_is_blind_to_ground_truth(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "challenge_100_labeled.csv"
            def write(label, reason):
                with path.open("w", newline="", encoding="utf-8") as stream:
                    writer = csv.DictWriter(stream, fieldnames=[
                        "docdb_family_id", "abstract_en", "label", "needs_review",
                        "confidence", "evidence_quote", "reason"
                    ])
                    writer.writeheader()
                    writer.writerow({
                        "docdb_family_id": "123", "abstract_en": "A robot walks on two legs.",
                        "label": label, "needs_review": "0", "confidence": "high",
                        "evidence_quote": reason, "reason": reason,
                    })
            write("1", "this is a test positive label")
            first = list(screen.rows(path))
            request_1 = screen.make_request(first[0][1])
            write("0", "THIS MUST NOT LEAK INTO THE MODEL")
            second = list(screen.rows(path))
            request_2 = screen.make_request(second[0][1])
            self.assertEqual(first, second)
            self.assertEqual(request_1, request_2)
            self.assertEqual(request_1["state"], "A robot walks on two legs.")
            self.assertNotIn("label", str(request_1))
            self.assertNotIn("THIS MUST NOT LEAK", str(request_2))

    def test_preferred_input_discovery(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "outputs/sampling" / run.FILENAME
            path.parent.mkdir(parents=True)
            path.write_text("docdb_family_id,abstract_en\n1,robot\n")
            self.assertEqual(run.discover_input(root=root), path.resolve())

    def test_explicit_input_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                run.discover_input(Path(directory) / "missing.csv")

    def test_exact_fp16_conversion_and_repeat(self):
        with tempfile.TemporaryDirectory() as directory:
            model_file = Path(directory) / "source/src/pplx_decider/model.py"
            model_file.parent.mkdir(parents=True)
            original = "header\n    " + run.OLD_DTYPE + "\nfooter\n"
            model_file.write_text(original)
            run.patch_native_fp16(directory)
            self.assertNotIn(run.OLD_DTYPE, model_file.read_text())
            self.assertIn(run.NEW_DTYPE, model_file.read_text())
            run.patch_native_fp16(directory)

    def test_prepare_dependencies_uninstalls_torchaudio_before_import_check(self):
        with patch.object(run, "install") as install, patch.object(run.subprocess, "run") as execute:
            run.prepare_model_dependencies("/tmp/checkpoint")
        install.assert_called_once_with("-r", "/tmp/checkpoint/requirements.txt")
        self.assertEqual(execute.call_count, 2)
        self.assertEqual(execute.call_args_list[0], call(
            [run.sys.executable, "-m", "pip", "uninstall", "--yes", "torchaudio"],
            check=True,
        ))
        self.assertIn("from transformers import AutoProcessor", execute.call_args_list[1].args[0][-1])

    def test_skip_install_still_removes_broken_torchaudio(self):
        with patch.object(run, "install") as install, patch.object(run.subprocess, "run") as execute:
            run.prepare_model_dependencies("/tmp/checkpoint", skip_install=True)
        install.assert_not_called()
        self.assertEqual(execute.call_count, 2)

    def test_refuse_unknown_dtype_implementation(self):
        with tempfile.TemporaryDirectory() as directory:
            model_file = Path(directory) / "source/src/pplx_decider/model.py"
            model_file.parent.mkdir(parents=True)
            model_file.write_text("some other dtype assignment")
            with self.assertRaises(RuntimeError):
                run.patch_native_fp16(directory)


if __name__ == "__main__":
    unittest.main()
