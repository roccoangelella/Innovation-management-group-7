"""Mirror the Kaggle execution progress in W&B without exposing API tokens to Kaggle.

Runs on GitHub Actions, reads public-to-owner kernel stdout through Kaggle API,
and sends only aggregate counters to a private W&B run.
"""
import json
import os
import re
import subprocess
import sys
import time

import wandb

KERNEL = os.environ["KAGGLE_KERNEL_ID"]
INTERVAL = 40
TOTAL = 237538

def cli(*args):
    process = subprocess.run(["kaggle", "kernels", *args], text=True, capture_output=True)
    if process.returncode:
        raise RuntimeError(f"Kaggle CLI {args[0]} error: {process.stderr[-700:]}")
    return process.stdout

def start():
    key = os.environ.get("WANDB_API_KEY")
    if not key:
        raise RuntimeError("WANDB_API_KEY repository secret is required for live dashboard")
    wandb.login(key=key)
    with wandb.init(
        project="humanoid-patent-filtering",
        name="production-dual-t4-session-1",
        job_type="inference",
        config={"total_families": TOTAL, "workers": 2, "model": "pplx-decider-flash-v1.2", "threshold_exploratory": 0.5},
    ) as run:
        print("WANDB_DASHBOARD=" + run.url, flush=True)
        last_count = -1
        deadline = time.monotonic() + 340 * 60
        while time.monotonic() < deadline:
            try:
                logs = cli("logs", KERNEL)
                matches = re.findall(r"PROGRESS_JSON=(\{[^\r\n]*\})", logs)
                if matches:
                    d = json.loads(matches[-1])
                    processed = int(d["processed"])
                    if processed > last_count:
                        metrics = {
                            "families/processed": processed,
                            "families/completion_percent": float(d["percent"]),
                            "families/provisional_positive": int(d["provisional_positive"]),
                            "families/provisional_positive_fraction": float(d["provisional_positive_fraction"]),
                            "throughput/families_per_hour": float(d["rate_per_hour"]),
                            "gpu0/processed": int(d["worker_0"]),
                            "gpu1/processed": int(d["worker_1"]),
                        }
                        if d.get("eta_hours") is not None:
                            metrics["throughput/estimated_hours_remaining"] = float(d["eta_hours"])
                        for device in range(2):
                            if f"gpu_{device}_utilization_percent" in d:
                                metrics[f"gpu{device}/utilization_percent"] = float(d[f"gpu_{device}_utilization_percent"])
                                metrics[f"gpu{device}/memory_mb"] = float(d[f"gpu_{device}_memory_mb"])
                        run.log(metrics, step=processed)
                        last_count = processed
                        print("LIVE_PROGRESS=" + json.dumps(d), flush=True)
                status = cli("status", KERNEL)
                print("KAGGLE_STATUS=" + status.strip()[:240], flush=True)
                if re.search(r"KernelWorkerStatus\.COMPLETE", status):
                    run.summary["kaggle_status"] = "COMPLETE"
                    break
                if re.search(r"KernelWorkerStatus\.(ERROR|CANCELLED|CANCELED|FAILED)", status):
                    run.summary["kaggle_status"] = "FAILED"
                    raise RuntimeError("Kaggle notebook failed: " + status.strip())
            except (subprocess.CalledProcessError, json.JSONDecodeError, ValueError) as exc:
                print(f"Transient status parse error: {type(exc).__name__}", flush=True)
            time.sleep(INTERVAL)
        else:
            run.summary["kaggle_status"] = "MONITOR_TIMEOUT"
            raise RuntimeError("Monitor ended without Kaggle run reaching terminal state")
        os.makedirs("kaggle_results", exist_ok=True)
        download = subprocess.run([
            "kaggle", "kernels", "output", KERNEL,
            "-p", "kaggle_results",
            "--file-pattern", "(humanoid-checkpoint.zip|production_summary.json|session_summary.json|predictions.csv|filtered_patents.zip)",
        ], check=True)
        for name in ("production_summary.json", "session_summary.json"):
            path = os.path.join("kaggle_results", name)
            if os.path.isfile(path):
                with open(path, encoding="utf-8") as stream:
                    summary = json.load(stream)
                run.summary.update({"session_complete": name=="production_summary.json", "processed_final":summary.get("n_predictions",summary.get("processed"))})
                print("FINAL_SESSION_SUMMARY=" + json.dumps(summary), flush=True)
                break

if __name__ == "__main__":
    start()
