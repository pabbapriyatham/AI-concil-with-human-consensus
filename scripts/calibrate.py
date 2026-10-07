"""Fit on training observations, save held-out results and JSON-only parameters."""

import argparse
import json
from pathlib import Path

from sqlalchemy import insert

from app.confidence.calibration import held_out_experiment, reliability_svg
from app.knowledge import database as db
from app.knowledge.store import Store
from app.schemas import uid

parser = argparse.ArgumentParser()
parser.add_argument(
    "observations", help='JSONL rows: {"id":str,"score":float,"correct":0|1,"split":"train"|"test"}'
)
parser.add_argument("--method", choices=["isotonic", "platt"], default="isotonic")
parser.add_argument("--output", default="artifacts/calibration")
args = parser.parse_args()
rows = [json.loads(line) for line in Path(args.observations).read_text().splitlines() if line.strip()]
result = held_out_experiment(
    [r for r in rows if r["split"] == "train"], [r for r in rows if r["split"] == "test"], args.method
)
identity = uid()
result.update(experiment_id=identity, observation_source=args.observations)
store = Store(initialize=True)
with store.engine.begin() as conn:
    conn.execute(insert(db.experiments).values(id=identity, payload={"type": "calibration", **result}))
    for stage in ["raw", "calibrated"]:
        for metric in ["brier", "ece"]:
            conn.execute(
                insert(db.metrics).values(
                    id=uid(), experiment_id=identity, name=f"{stage}.{metric}", value=result[stage][metric]
                )
            )
target = Path(args.output)
target.mkdir(parents=True, exist_ok=True)
(target / "calibration.json").write_text(json.dumps(result, indent=2), encoding="utf8")
(target / "raw.svg").write_text(reliability_svg(result["raw"]), encoding="utf8")
(target / "calibrated.svg").write_text(reliability_svg(result["calibrated"]), encoding="utf8")
print("Saved held-out calibration experiment", identity, "to", target)
