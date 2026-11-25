import argparse
import asyncio
import os

from app.evaluation.runner import evaluate
from app.knowledge.store import Store

parser = argparse.ArgumentParser()
parser.add_argument("--dataset", help="Evaluation JSONL. Defaults to the synthetic dataset for offline runs.")
parser.add_argument("--output", default="artifacts/evaluation")
parser.add_argument("--limit", type=int)
parser.add_argument(
    "--live", action="store_true", help="Uses paid configured providers; default is free fixtures"
)
parser.add_argument("--repeats", type=int, help="Consistency repetitions; default 2 offline, 1 live")
parser.add_argument("--memory", help="JSONL file containing an independently reviewed memory snapshot")
parser.add_argument("--development-dataset", help="Reject overlap by example ID or normalized question")
args = parser.parse_args()
if args.live and not args.dataset:
    parser.error("--live requires an explicit --dataset")
os.environ["DEV_MODE"] = "false" if args.live else "true"
result = asyncio.run(
    evaluate(
        args.dataset or "datasets/development.jsonl",
        args.output,
        store=Store(initialize=True),
        live=args.live,
        limit=args.limit,
        consistency_repeats=args.repeats if args.repeats is not None else (1 if args.live else 2),
        memory_path=args.memory,
        development_path=args.development_dataset,
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
print("Live run. Automated exact-match scores require independent review." if args.live else
      "DEVELOPMENT FIXTURES ONLY: not real-model accuracy or statistical significance.")
