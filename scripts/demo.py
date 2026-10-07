"""Free end-to-end example. Use --live only after configuring provider credentials."""

import argparse
import asyncio
import json
import os
from pathlib import Path

from app.evidence import Evidence
from app.knowledge.store import Store
from app.orchestration import ConsensusEngine, ConsensusRequest


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--output", default="artifacts/demo.json")
    args = parser.parse_args()
    if not args.live:
        os.environ["DEV_MODE"] = "true"
    store = Store("sqlite:///:memory:", initialize=True)
    result = await ConsensusEngine(store).run(
        ConsensusRequest(
            question="When was the Eiffel Tower completed and where is it located?",
            evidence=[
                Evidence(
                    text="The Eiffel Tower was completed in 1889. The Eiffel Tower is located in Paris.",
                    source="supplied development fixture (not independently retrieved)",
                    source_type="dataset",
                    source_quality=1,
                )
            ],
        )
    )
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2), encoding="utf8")
    print(result["synthesis"]["text"])
    print("Saved full trace:", target.resolve())


if __name__ == "__main__":
    asyncio.run(main())
