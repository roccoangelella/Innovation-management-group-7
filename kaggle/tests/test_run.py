"""Offline tests for single-command Kaggle setup; no network/GPU needed."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / "run.py"
spec = importlib.util.spec_from_file_location("kaggle_run", MODULE)
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)


class LauncherTests(unittest.TestCase):
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

    def test_refuse_unknown_dtype_implementation(self):
        with tempfile.TemporaryDirectory() as directory:
            model_file = Path(directory) / "source/src/pplx_decider/model.py"
            model_file.parent.mkdir(parents=True)
            model_file.write_text("some other dtype assignment")
            with self.assertRaises(RuntimeError):
                run.patch_native_fp16(directory)


if __name__ == "__main__":
    unittest.main()
