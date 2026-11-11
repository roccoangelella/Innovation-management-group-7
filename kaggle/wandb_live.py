"""Live W&B metrics from Kaggle's append-only, two-GPU prediction journals.

No patent content or identifiers leave Kaggle: only counters and rates.
"""
import argparse
import json
import os
from pathlib import Path
import signal
import time

TOTAL = 237538
STOP = False


def on_stop(_signal, _frame):
    global STOP
    STOP = True


class JournalCounter:
    def __init__(self, root):
        self.root = Path(root)
        self.offsets = [0, 0]
        self.processed = [0, 0]
        self.positive = [0, 0]

    def update(self):
        """Read appended *complete* JSONL records; never count torn writes."""
        for worker in range(2):
            path = self.root / f"worker_{worker}" / "predictions.jsonl"
            if not path.is_file():
                continue
            if path.stat().st_size < self.offsets[worker]:
                raise RuntimeError(f"GPU {worker} journal was truncated: inconsistent progress")
            with path.open("rb") as stream:
                stream.seek(self.offsets[worker])
                while True:
                    line = stream.readline()
                    if not line or not line.endswith(b"\n"):
                        break
                    record = json.loads(line)
                    if not isinstance(record, dict) or set(record) != {"docdb_family_id", "probability_relevant", "model_decision"}:
                        raise ValueError("Invalid prediction journal schema")
                    if record["model_decision"] not in (0, 1):
                        raise ValueError("Invalid model_decision")
                    self.processed[worker] += 1
                    self.positive[worker] += int(record["model_decision"])
                    self.offsets[worker] = stream.tell()
        count = sum(self.processed)
        if count > TOTAL:
            raise RuntimeError("Journal has more predictions than eligible patent families")
        return count


def serve(root, interval, signal_file, run_name, total=TOTAL):
    if not os.environ.get("WANDB_API_KEY"):
        raise RuntimeError("WANDB_API_KEY is unavailable inside the Kaggle runtime")
    import wandb

    counter = JournalCounter(root)
    start = time.monotonic()
    previous_count = 0
    previous_time = start
    with wandb.init(
        entity="rocchissimo936-none",
        project="humanoid-patent-filtering",
        name=run_name,
        job_type="native-decider-inference",
        config={"total_families": total, "model": "pplx-decider-flash-v1.2",
                "workers": 2, "threshold_exploratory": 0.5,
                "metric_note": "Progress from written GPU prediction journals; not accuracy."},
    ) as run:
        ready = Path(signal_file)
        ready.parent.mkdir(parents=True, exist_ok=True)
        ready.write_text(json.dumps({"url": run.url}) + "\n", encoding="utf-8")
        print("WANDB_LIVE_URL=" + str(run.url), flush=True)
        while True:
            processed = counter.update()
            now = time.monotonic()
            dt = max(now - previous_time, 0.001)
            speed = max(processed - previous_count, 0) / dt
            positive = sum(counter.positive)
            run.log({
                "documents/analyzed": processed,
                "documents/total": total,
                "documents/remaining": total - processed,
                "documents/percent": 100 * processed / total,
                "workers/t4_0_analyzed": counter.processed[0],
                "workers/t4_1_analyzed": counter.processed[1],
                "throughput/documents_per_second": speed,
                "decisions/provisional_positive": positive,
            })
            print(f"WANDB_PROGRESS analyzed={processed}/{total} worker0={counter.processed[0]} worker1={counter.processed[1]}", flush=True)
            previous_time = now
            previous_count = processed
            if STOP or processed >= total:
                run.summary["documents_analyzed_final"] = processed
                break
            time.sleep(interval)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--production-dir", required=True)
    p.add_argument("--ready-file", required=True)
    p.add_argument("--run-name", default="production-dual-t4-direct")
    p.add_argument("--interval", type=float, default=30)
    args = p.parse_args()
    if args.interval < 1:
        p.error("interval must be >= 1 second")
    signal.signal(signal.SIGTERM, on_stop)
    signal.signal(signal.SIGINT, on_stop)
    serve(args.production_dir, args.interval, args.ready_file, args.run_name)


if __name__ == "__main__":
    main()
