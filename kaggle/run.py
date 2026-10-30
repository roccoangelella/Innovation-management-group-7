"""One-command Kaggle launcher: locate data, install dependencies, load FP16 Decider, run scoring.

Usage from repo root: python kaggle/run.py
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys

MODEL_ID = "perplexity-ai/pplx-decider-flash-v1.2"
# Known model source release, including the native decision readout and attention.
REVISION = "6d771ad7b5ecff5e93b8fc7b90d4c5ccc341954d"
FILENAME = "humanoid_100_abstracts_en.csv"
OLD_DTYPE = 'dtype = torch.bfloat16 if self.device.type == "cuda" else torch.float32'
NEW_DTYPE = 'dtype = torch.float16 if self.device.type == "cuda" else torch.float32'


def discover_input(specified=None, root=None):
    """Fail on missing/ambiguous translated samples instead of guessing."""
    if specified:
        path = Path(specified).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Translated CSV not found: {path}")
        return path

    root = Path(root or Path(__file__).resolve().parents[1])
    preferred = [
        root / "outputs/sampling" / FILENAME,
        Path("/kaggle/working") / FILENAME,
    ]
    for candidate in preferred:
        if candidate.is_file():
            return candidate.resolve()
    matches = sorted(Path("/kaggle/input").glob(f"**/{FILENAME}")) if Path("/kaggle/input").is_dir() else []
    if len(matches) == 1:
        return matches[0].resolve()
    if matches:
        raise ValueError("Multiple translated sample CSVs found; use --input to select one: " + ", ".join(map(str, matches)))
    raise FileNotFoundError(
        f"No {FILENAME} found. Attach the translated 100-family CSV as a Kaggle Dataset "
        "or supply --input. The un-translated humanoid_patents.zip cannot be scored."
    )


def patch_native_fp16(checkpoint):
    """Enable true FP16 compute in the pinned native loader, rather than BF16 on T4.

    Perplexity's model.py chooses BF16 unconditionally on CUDA in this release.
    Modify only a local snapshot and fail if the source differs; preserve native
    noncausal attention, readout and request protocol intact.
    """
    model_py = Path(checkpoint) / "source" / "src" / "pplx_decider" / "model.py"
    if not model_py.is_file():
        raise FileNotFoundError(f"Native loader not found at {model_py}")
    source = model_py.read_text(encoding="utf-8")
    if source.count(OLD_DTYPE) == 1:
        model_py.write_text(source.replace(OLD_DTYPE, NEW_DTYPE), encoding="utf-8")
    elif source.count(NEW_DTYPE) != 1:
        raise RuntimeError("Native loader dtype implementation changed; refusing an unverified FP16 conversion.")
    return model_py


def check_environment():
    if sys.version_info < (3, 12):
        raise RuntimeError("This release requires Python 3.12+; select an appropriate Kaggle runtime.")
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError("No CUDA GPU found. Enable GPU acceleration in Kaggle Notebook settings.")
    memory_gib = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
    device_name = torch.cuda.get_device_name(0)
    print(f"GPU cuda:0: {device_name}, {memory_gib:.1f} GiB; requested FP16", flush=True)
    if memory_gib < 12:
        raise RuntimeError("GPU memory <12 GiB; this ~9 GiB model plus runtime memory is unlikely to fit.")
    return device_name


def get_token():
    token = os.environ.get("HF_TOKEN")
    if token:
        return token
    try:
        from kaggle_secrets import UserSecretsClient
        return UserSecretsClient().get_secret("HF_TOKEN")
    except (ImportError, KeyError, RuntimeError, ValueError):
        return None


def install(*args):
    subprocess.run([sys.executable, "-m", "pip", "install", "--disable-pip-version-check", *args], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="Translated 100-family CSV. Auto-discovered when omitted.")
    parser.add_argument("--output", default="/kaggle/working/predictions.csv")
    parser.add_argument("--checkpoint", default="/kaggle/working/pplx-decider-flash-v1.2-fp16")
    parser.add_argument("--skip-install", action="store_true", help="Only if model dependencies are already installed")
    parser.add_argument("--check", action="store_true", help="Check the CSV path without downloading or loading a model")
    args = parser.parse_args()

    input_path = discover_input(args.input)
    # Validate the sample *before* downloading approximately 9 GB of weights.
    from screen import rows
    examples = list(rows(input_path))
    print(f"Input: {input_path} ({len(examples)} translated records)", flush=True)
    if args.check:
        return

    check_environment()
    checkpoint = Path(args.checkpoint).expanduser().resolve()
    if not args.skip_install:
        install("huggingface-hub==1.31.0")
    from huggingface_hub import snapshot_download
    token = get_token()
    print("Downloading/checking pinned Perplexity Decider checkpoint...", flush=True)
    snapshot_download(repo_id=MODEL_ID, revision=REVISION, local_dir=checkpoint, token=token)
    patch_native_fp16(checkpoint)
    if not args.skip_install:
        install("-r", str(checkpoint / "requirements.txt"))
    print("Starting native FP16 decision inference...", flush=True)
    subprocess.run([
        sys.executable, str(Path(__file__).with_name("screen.py")),
        "--input", str(input_path),
        "--checkpoint", str(checkpoint),
        "--output", str(Path(args.output).expanduser().resolve()),
        "--model-revision", REVISION,
    ], check=True)


if __name__ == "__main__":
    main()
