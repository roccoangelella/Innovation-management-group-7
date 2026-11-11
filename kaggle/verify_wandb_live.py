"""Confirm GitHub-launched Kaggle inference publishes a nonzero count to W&B."""
import os
import time

import wandb

PROJECT = "rocchissimo936-none/humanoid-patent-filtering"


def main():
    target = os.environ["WANDB_RUN_NAME"]
    if not os.environ.get("WANDB_API_KEY"):
        raise ValueError("Missing W&B API credential")
    deadline = time.monotonic() + 30 * 60
    while time.monotonic() < deadline:
        try:
            api = wandb.Api(timeout=60)
            runs = api.runs(
                PROJECT,
                filters={"display_name": {"$eq": target}},
                per_page=5,
            )
            for run in runs:
                if run.name != target:
                    continue
                count = int(run.summary.get("documents/analyzed", 0))
                print(f"WANDB_DIRECT_COUNT={count}/237538", flush=True)
                if count > 0:
                    print(
                        "WANDB_VERIFIED_LIVE_URL=https://forge.coreweave.com/wandb/"
                        + PROJECT + "/runs/" + run.id,
                        flush=True,
                    )
                    return
            print("W&B direct counter has not yet recorded a nonzero value", flush=True)
        except Exception as exc:
            # Don't print network exception strings: they can contain request metadata.
            print(f"Transient W&B verification failure: {type(exc).__name__}", flush=True)
        time.sleep(30)
    raise TimeoutError("No nonzero analyzed-document count reached the direct W&B project within 30 minutes")


if __name__ == "__main__":
    main()
