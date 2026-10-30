# Deployment and execution

TIP/PATSTAT export runs within the TIP environment. Translation runs with Python >=3.12 and the private OpenAI-compatible endpoint configured locally.

The Kaggle experiment is run from the repository root with `python kaggle/run.py` after enabling GPU and Internet and attaching a translated `humanoid_100_abstracts_en.csv`. If needed, provide the `HF_TOKEN` Kaggle secret. The command installs checkpoint requirements and executes inference through a fresh Python subprocess. Its local model patch replaces exactly the upstream CUDA BF16 dtype assignment with FP16, retaining the native decision model architecture. One GPU is used. The Kaggle runtime and the complete execution path remain unverified pending a real run. See `kaggle/README.md`.
