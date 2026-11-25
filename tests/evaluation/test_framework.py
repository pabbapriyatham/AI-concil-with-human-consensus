import asyncio
import json
from pathlib import Path

import pytest

from app.evaluation.dataset import DatasetExample
from app.evaluation.metrics import classification_metrics, correctness
from app.evaluation.runner import FixtureProvider, evaluate
from app.knowledge.store import Store
from app.providers import ProviderError


def test_dataset_schema_and_categories():
    rows = [
        DatasetExample.model_validate(json.loads(line))
        for line in Path("datasets/development.jsonl").read_text().splitlines()
    ]
    assert len(rows) == 42 and len({r.category for r in rows}) == 7


def test_reproducible_exports(tmp_path, monkeypatch):
    generated = []
    generate = FixtureProvider.generate

    async def count_generation(self, model, messages, **kwargs):
        generated.append(model)
        return await generate(self, model, messages, **kwargs)

    monkeypatch.setattr(FixtureProvider, "generate", count_generation)
    store = Store("sqlite:///:memory:", initialize=True)
    result = asyncio.run(evaluate("datasets/development.jsonl", tmp_path, store=store, limit=1))
    assert set(result["summary"]) == set("ABCDEF")
    assert len(result["records"]) == 6
    assert (tmp_path / "results.csv").exists()
    assert (tmp_path / "reliability-E.svg").exists()
    assert result["configuration"]["live"] is False
    assert result["summary"]["D"]["accuracy"] == 1
    assert result["summary"]["D"]["contradiction_samples"] == 1
    assert result["summary"]["A"]["contradiction_precision"] is None
    assert len(generated) == 2 + 4 * 3 * 2
    assert all(row["consistency"] is not None for row in result["records"])
    profile = store.reliability_profiles().profile("mock:fixture-0", "synthetic-registry", "factual")
    assert profile["samples"] == 1 and profile["accuracy"] == 0


def test_metrics_and_abstention():
    assert correctness([], [], True)
    assert not correctness(["invented"], [], True)
    assert classification_metrics(2, 1, 1)["f1"] == 2 / 3


def test_f_uses_the_frozen_reviewed_snapshot(tmp_path):
    memory = tmp_path / "reviewed.jsonl"
    claim = "Registry item factual A is enabled."
    memory.write_text(
        json.dumps({
            "claim": claim,
            "reviewer": "independent fixture reviewer",
            "explanation": "Verified against the registry",
            "evidence": [{"text": claim, "source": "reviewed fixture", "source_type": "document"}],
        }) + "\n",
        encoding="utf8",
    )
    result = asyncio.run(
        evaluate("datasets/development.jsonl", tmp_path, limit=1, memory_path=memory)
    )
    assert result["configuration"]["memory_mode"] == "reviewed snapshot"
    assert len(result["configuration"]["reviewed_memory_sha256"]) == 64
    assert result["summary"]["F"]["accuracy"] == 1
    assert result["summary"]["F"]["contradiction_samples"] == 0


def test_development_overlap_uses_question_even_if_ids_differ(tmp_path):
    fixture = Path("datasets/development.jsonl")
    example = json.loads(fixture.read_text(encoding="utf8").splitlines()[0])
    example["id"] = "renamed"
    example["question"] = "  " + example["question"].upper().replace(" ", "  ")
    held_out = tmp_path / "held-out.jsonl"
    held_out.write_text(json.dumps(example), encoding="utf8")
    with pytest.raises(ValueError, match="overlap by ID or question"):
        asyncio.run(evaluate(held_out, tmp_path, development_path=fixture))


def test_provider_failures_never_score_as_correct_abstentions(tmp_path, monkeypatch):
    fixture = Path("datasets/development.jsonl")
    examples = [json.loads(line) for line in fixture.read_text(encoding="utf8").splitlines()]
    example = next(row for row in examples if row["category"] == "ambiguous")
    example.pop("fixture_responses")
    dataset = tmp_path / "study.jsonl"
    dataset.write_text(json.dumps(example), encoding="utf8")

    class Unavailable:
        async def generate(self, *args, **kwargs):
            raise ProviderError("fixture failure")

    async def council_failure(question):
        return [], [], {"response": "Unavailable"}, {}

    monkeypatch.setenv("DEV_MODE", "false")
    monkeypatch.setattr("app.evaluation.runner.get_provider", lambda _: Unavailable())
    monkeypatch.setattr("app.evaluation.runner.run_full_council", council_failure)
    result = asyncio.run(evaluate(dataset, tmp_path, live=True))
    assert all(row["system_error"] and not row["correct"] for row in result["records"])
    assert all(row["consistency"] == 0 for row in result["records"])
