import asyncio
from pathlib import Path
from app.evaluation.runner import evaluate
from app.evaluation.metrics import correctness, classification_metrics
from app.evaluation.dataset import DatasetExample
import json


def test_dataset_schema_and_categories():
    rows = [DatasetExample.model_validate(json.loads(line)) for line in Path("datasets/development.jsonl").read_text().splitlines()]
    assert len(rows) == 42 and len({r.category for r in rows}) == 7


def test_reproducible_exports(tmp_path):
    result = asyncio.run(evaluate("datasets/development.jsonl", tmp_path, limit=1))
    assert set(result["summary"]) == set("ABCDEF")
    assert len(result["records"]) == 6
    assert (tmp_path / "results.csv").exists()
    assert (tmp_path / "reliability-E.svg").exists()
    assert result["configuration"]["live"] is False
    assert result["summary"]["D"]["accuracy"] == 1


def test_metrics_and_abstention():
    assert correctness([], [], True)
    assert not correctness(["invented"], [], True)
    assert classification_metrics(2, 1, 1)["f1"] == 2 / 3
