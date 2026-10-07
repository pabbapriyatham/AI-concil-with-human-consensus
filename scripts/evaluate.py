import argparse
import asyncio
import os

from app.evaluation.runner import evaluate
from app.knowledge.store import Store

parser = argparse.ArgumentParser()
parser.add_argument("--dataset", default="datasets/development.jsonl")
parser.add_argument("--output", default="artifacts/evaluation")
parser.add_argument("--limit", type=int)
parser.add_argument(
    "--live", action="store_true", help="Uses paid configured providers; default is free fixtures"
)
parser.add_argument("--repeats", type=int, help="Consistency repetitions; default 2 offline, 1 live")
args = parser.parse_args()
os.environ["DEV_MODE"] = "false" if args.live else "true"
result = asyncio.run(
    evaluate(
        args.dataset,
        args.output,
        store=Store(initialize=True),
        live=args.live,
        limit=args.limit,
        consistency_repeats=args.repeats or (1 if args.live else 2),
    )
)
print("Experiment", result["experiment_id"])
for system, metrics in result["summary"].items():
    print(
        system,
        "accuracy",
        round(metrics["accuracy"], 3),
        "Brier",
        round(metrics["brier"], 3) if metrics["brier"] is not None else "unavailable",
        "ECE",
        round(metrics["ece"], 3) if metrics["ece"] is not None else "unavailable",
        "samples",
        metrics["samples"],
    )
print("DEVELOPMENT FIXTURES ONLY: not real-model accuracy or statistical significance.")
