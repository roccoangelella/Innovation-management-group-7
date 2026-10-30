# Kaggle notebook cells (copy each section into a cell).
# First add this GitHub folder to your notebook, or clone your own repository.

# %% Setup (run once; restart kernel if pip says so)
from huggingface_hub import snapshot_download
from pathlib import Path
import subprocess
import sys

checkpoint = Path("/kaggle/working/pplx-decider-flash-v1.2")
snapshot_download("perplexity-ai/pplx-decider-flash-v1.2", local_dir=checkpoint)
subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(checkpoint / "requirements.txt")])
# If installing the requirements replaces torch or other loaded packages,
# restart the notebook kernel before running inference.

# %% Inference: edit the input dataset path to match the Kaggle sidebar
subprocess.check_call([
    sys.executable, "kaggle/screen.py",
    "--input", "/kaggle/input/translated-sample/humanoid_100_abstracts_en.csv",
    "--checkpoint", str(checkpoint),
    "--output", "/kaggle/working/predictions.csv",
])

# %% Optional evaluation, only after manual labels are available
# subprocess.check_call([
#     sys.executable, "kaggle/evaluate.py",
#     "--predictions", "/kaggle/working/predictions.csv",
#     "--labels", "/kaggle/input/patent-labels/labels.csv",
#     "--output", "/kaggle/working/evaluation.json",
# ])
