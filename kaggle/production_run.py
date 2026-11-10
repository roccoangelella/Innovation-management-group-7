"""Launch full-corpus, two-T4 Perplexity Decider screening on Kaggle.

python kaggle/production_run.py --input /kaggle/input/translated/humanoid_patents_en.zip
python kaggle/production_run.py --input ... --translation-summary ... --check
"""

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path

import production
import run as pilot


@contextmanager
def exclusive_run(output_dir):
    """Prevent concurrent notebooks from writing into the same worker journals."""
    folder = Path(output_dir).expanduser().resolve()
    folder.mkdir(parents=True, exist_ok=True)
    lock = folder / ".screening.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise RuntimeError(f"Another screening run may be active: {lock}. Check for active workers before removing stale lock") from exc
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(str(os.getpid()) + "\n")
        yield
    finally:
        lock.unlink(missing_ok=True)


def translation_expected_rows(path, expected_rows=None):
    if not path:
        return expected_rows
    summary = json.loads(Path(path).read_text(encoding="utf-8"))
    if summary.get("incomplete") != 0 or summary.get("stop_reason"):
        raise ValueError("Translation summary reports incomplete/aborted work; do not screen a partial dataset")
    completed = summary.get("completed")
    if type(completed) is not int or completed <= 0:
        raise ValueError("Translation summary has no valid completed count")
    if expected_rows is not None and expected_rows != completed:
        raise ValueError("--expected-rows contradicts the translation summary")
    return completed


def t4_devices():
    """Return the underlying device IDs, respecting an existing visible-device mask."""
    import torch
    if not torch.cuda.is_available() or torch.cuda.device_count() != 2:
        raise RuntimeError("Production requires exactly TWO visible CUDA GPUs. Select Kaggle GPU T4 x2")
    for i in range(2):
        name = torch.cuda.get_device_name(i)
        mem = torch.cuda.get_device_properties(i).total_memory / 1024**3
        print(f"GPU {i}: {name}, {mem:.1f} GiB", flush=True)
        if "T4" not in name or mem < 12:
            raise RuntimeError("Production runner is validated only for two T4 GPUs with >=12 GiB each")
    mask = os.environ.get("CUDA_VISIBLE_DEVICES", "").strip()
    if not mask:
        return ("0", "1")
    ids = tuple(part.strip() for part in mask.split(","))
    if len(ids) != 2 or not all(ids):
        raise RuntimeError("CUDA_VISIBLE_DEVICES must name exactly two GPUs")
    return ids


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Translation CSV or ZIP containing exactly one translated CSV")
    parser.add_argument("--production-dir", default="/kaggle/working/humanoid-production")
    parser.add_argument("--translation-summary", help="Optional translation progress.summary.json; requires incomplete=0")
    parser.add_argument("--expected-rows", type=int, help="Optional independently verified number of eligible families")
    parser.add_argument("--check", action="store_true", help="Validate and shard input without model/network/GPU")
    parser.add_argument("--skip-install", action="store_true", help="Reuse already installed checkpoint dependencies")
    parser.add_argument("--checkpoint", default="/kaggle/working/pplx-decider-flash-v1.2-fp16")
    args = parser.parse_args()
    if args.expected_rows is not None and args.expected_rows <= 0:
        parser.error("--expected-rows must be positive")
    if os.sys.version_info < (3, 12):
        raise RuntimeError("Python 3.12+ is required")

    expected = translation_expected_rows(args.translation_summary, args.expected_rows)
    with exclusive_run(args.production_dir):
        plan = production.prepare(args.input, args.production_dir, pilot.REVISION, expected_rows=expected)
        if args.check:
            print("Preflight successful. No GPU/model was used.", flush=True)
            return
        devices = t4_devices()
        if not args.skip_install:
            pilot.install("huggingface-hub==1.31.0")
        from huggingface_hub import snapshot_download
        checkpoint = Path(args.checkpoint).expanduser().resolve()
        snapshot_download(repo_id=pilot.MODEL_ID, revision=pilot.REVISION,
                          local_dir=checkpoint, token=pilot.get_token())
        pilot.patch_native_fp16(checkpoint)
        pilot.prepare_model_dependencies(checkpoint, skip_install=args.skip_install)
        if production.sha256(plan["input"]) != json.loads((plan["dir"] / "production_manifest.json").read_text())["input_sha256"]:
            raise ValueError("Source dataset changed during setup")
        production.run_workers(plan, checkpoint, pilot.REVISION, devices)
        production.merge(plan)


if __name__ == "__main__":
    main()
