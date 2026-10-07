import argparse
import asyncio
import os
from app.evaluation.runner import evaluate
from app.knowledge.store import Store

parser = argparse.ArgumentParser()
parser.add_argument("--dataset", default="datasets/development.jsonl")
parser.add_argument("--output", default="artifacts/evaluation")
parser.add_argument("--limit", type=int)
parser.add_argument("--live", action="store_true", help="Uses paid configured providers; default is free fixtures")
args = parser.parse_args()
os.environ["DEV_MODE"] = "false" if args.live else "true"
result = asyncio.run(evaluate(args.dataset, args.output, store=Store(initialize=True),
                             live=args.live, limit=args.limit))
print("Experiment", result["experiment_id"])
for system, metrics in result["summary"].items():
    print(system, "accuracy", round(metrics["accuracy"], 3), "Brier", round(metrics["brier"], 3),
          "ECE", round(metrics["ece"], 3), "samples", metrics["samples"])
print("DEVELOPMENT FIXTURES ONLY: not real-model accuracy or statistical significance.")
