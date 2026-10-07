import csv
import hashlib
import json
import time
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import insert

from app.claims import extract_claims
from app.claims.normalizer import normalize_claim
from app.confidence.calibration import reliability_svg
from app.knowledge import database as db
from app.knowledge.store import Store
from app.normalization import normalize_response
from app.orchestration import ConsensusEngine, ConsensusRequest, ModelSpec
from app.orchestration.engine import cache
from app.providers import get_provider
from app.providers.base import ProviderResult
from app.schemas import uid
from app.validation import ReviewRequest, ReviewService
from backend.council import run_full_council

from .dataset import DatasetExample
from .metrics import correctness, summarize


class FixtureProvider:
    def __init__(self, example):
        self.example = example

    async def generate(self, model, messages, **kwargs):
        index = int(model[-1]) if model[-1].isdigit() else 0
        return ProviderResult(
            "fixture",
            model,
            self.example.fixture_responses[index % 3],
            uid(),
            0,
            0,
            0,
            0,
            {"mock": True, "dataset_id": self.example.id},
        )


async def evaluate(dataset, output, store=None, live=False, limit=None, consistency_repeats=2):
    path = Path(dataset)
    examples = [
        DatasetExample.model_validate(json.loads(line))
        for line in path.read_text(encoding="utf8").splitlines()
        if line.strip()
    ]
    if limit:
        examples = examples[:limit]
    if not examples:
        raise ValueError("Empty evaluation dataset")
    experiment_id = uid()
    tracker = store or Store("sqlite:///:memory:", initialize=True)
    records = []
    for example in examples:
        provider = FixtureProvider(example)
        factory = get_provider if live else lambda _, provider=provider: provider
        if live:
            from app.orchestration.schemas import configured_models

            models = configured_models()[:3]
        else:
            models = [ModelSpec(provider="mock", model=f"fixture-{i}") for i in range(3)]
        for system in ["A", "B", "C", "D", "E", "F"]:
            # Isolation prevents cross-ablation evidence or memory leakage.
            work = Store("sqlite:///:memory:", initialize=True)
            cache.entries.clear()
            start = time.perf_counter()
            relation_found, review_required, explanation, tokens, cost = False, False, 0.0, 0, 0.0
            confidence = 0.5
            result = None
            if system == "A":
                response = await factory(models[0].provider).generate(
                    models[0].model, [{"role": "user", "content": example.question}]
                )
                normalized = normalize_response(response, example.id)
                prediction = [c.claim_text for c in extract_claims(normalized) if c.claim_type != "uncertain"]
                cost, tokens = response.cost, (response.input_tokens or 0) + (response.output_tokens or 0)
            elif system == "B":
                if live:
                    first, second, final, _ = await run_full_council(example.question)
                    cost = None  # baseline format lacks comprehensive billing metadata
                else:

                    async def query_model(model, messages, example=example, **kwargs):
                        text = messages[-1]["content"]
                        if "Chairman of an LLM Council" in text:
                            return {"content": example.fixture_responses[0]}
                        return {"content": example.fixture_responses[0]}

                    async def query_parallel(model_ids, messages, example=example):
                        ranking = "evaluating different responses" in messages[-1]["content"]
                        return {
                            m: {
                                "content": "FINAL RANKING:\n1. Response A\n2. Response B\n3. Response C\n4. Response D"
                                if ranking
                                else example.fixture_responses[i % 3]
                            }
                            for i, m in enumerate(model_ids)
                        }

                    with (
                        patch("backend.council.query_model", query_model),
                        patch("backend.council.query_models_parallel", query_parallel),
                    ):
                        first, second, final, _ = await run_full_council(example.question)
                normalized = normalize_response(
                    ProviderResult("baseline", "chairman", final["response"], uid()), example.id
                )
                prediction = [c.claim_text for c in extract_claims(normalized) if c.claim_type != "uncertain"]
            else:
                if system == "F" and example.ground_truth:
                    # Repeated-fact memory experiment, explicitly an oracle development reviewer.
                    item = work.create_knowledge(example.fixture_responses[0])
                    ReviewService(work).review(
                        item["knowledge_id"],
                        ReviewRequest(
                            action="CORRECT",
                            expected_version=1,
                            reviewer="synthetic oracle reviewer",
                            explanation="Development ground-truth fixture; not actual human performance.",
                            corrected_claim=example.ground_truth,
                        ),
                    )
                strategy = "weighted" if system == "C" else "knowledge" if system == "F" else "evidence"
                request = ConsensusRequest(
                    question=example.question,
                    models=models,
                    aggregation=strategy,
                    evidence=example.evidence if system in {"D", "E", "F"} else [],
                    allow_escalation=False,
                    category=example.category,
                    domain=example.domain,
                )
                engine = ConsensusEngine(
                    work, provider_factory=factory, confidence_enabled=system in {"E", "F"}
                )
                result = await engine.run(request)
                ids = set(result["synthesis"]["supporting_claim_ids"])
                prediction = [c["claim_text"] for c in result["claims"] if c["claim_id"] in ids]
                confidence = result["confidence"]["raw_confidence"]
                relation_found = any(r["relation_type"] == "CONTRADICTION" for r in result["relations"])
                review_required = result["review"]["required"]
                explanation = (
                    sum(
                        bool(result.get(key))
                        for key in ["responses", "claims", "decisions", "confidence", "explanation"]
                    )
                    / 5
                )
                tokens = result["execution"]["input_tokens"] + result["execution"]["output_tokens"]
                cost = result["execution"]["total_cost"]
            latency = time.perf_counter() - start
            correct = correctness(prediction, example.expected_claims, example.ground_truth is None)
            pred, gold = (
                {normalize_claim(t) for t in prediction},
                {normalize_claim(t) for t in example.expected_claims},
            )
            contradiction_expected = example.category != "ambiguous"
            consistency = None
            repeat_tokens, repeat_cost, repeat_latency = 0, 0.0, 0.0
            if result is not None and consistency_repeats > 1:
                repeated_sets = [pred]
                for _ in range(consistency_repeats - 1):
                    repeated = await engine.run(request)
                    repeat_tokens += (
                        repeated["execution"]["input_tokens"] + repeated["execution"]["output_tokens"]
                    )
                    repeat_latency += repeated["execution"]["latency"]
                    if repeated["execution"]["total_cost"] is None:
                        repeat_cost = None
                    elif repeat_cost is not None:
                        repeat_cost += repeated["execution"]["total_cost"]
                    selected = set(repeated["synthesis"]["supporting_claim_ids"])
                    repeated_sets.append(
                        {
                            normalize_claim(c["claim_text"])
                            for c in repeated["claims"]
                            if c["claim_id"] in selected
                        }
                    )
                consistency = sum(p == pred for p in repeated_sets[1:]) / (len(repeated_sets) - 1)
            records.append(
                {
                    "example_id": example.id,
                    "system": system,
                    "category": example.category,
                    "prediction": sorted(pred),
                    "correct": correct,
                    "score": confidence,
                    "latency": latency,
                    "tokens": tokens,
                    "cost": cost,
                    "claim_tp": len(pred & gold),
                    "claim_fp": len(pred - gold),
                    "claim_fn": len(gold - pred),
                    "contradiction_tp": int(relation_found and contradiction_expected),
                    "contradiction_fp": int(relation_found and not contradiction_expected),
                    "contradiction_fn": int(not relation_found and contradiction_expected),
                    "error_detect_tp": int(review_required and not correct),
                    "error_detect_fp": int(review_required and correct),
                    "error_detect_fn": int(not review_required and not correct),
                    "explanation_completeness": explanation,
                    "consistency": consistency,
                    "execution_id": result["request_id"] if result else None,
                    "consistency_tokens": repeat_tokens,
                    "consistency_cost": repeat_cost,
                    "consistency_latency": repeat_latency,
                    "model_observations": [
                        {
                            "model": response["model"],
                            "domain": example.domain,
                            "category": example.category,
                            "correct": correctness(
                                [
                                    c["claim_text"]
                                    for c in result["claims"]
                                    if c["response_id"] == response["response_id"]
                                    and c["claim_type"] != "uncertain"
                                ],
                                example.expected_claims,
                                example.ground_truth is None,
                            ),
                        }
                        for response in (result["responses"] if result else [])
                        if response["provider"] != "knowledge"
                    ],
                }
            )
    summary = {
        system: summarize([r for r in records if r["system"] == system])
        for system in ["A", "B", "C", "D", "E", "F"]
    }
    artifact = {
        "experiment_id": experiment_id,
        "dataset": str(path),
        "dataset_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "configuration": {
            "live": live,
            "models": [m.model_dump() for m in models],
            "prompt_version": "answer-v1",
            "consistency_repeats": consistency_repeats,
            "systems": {
                "A": "single model",
                "B": "original council",
                "C": "claim comparison/weighted aggregation",
                "D": "C + evidence",
                "E": "D + confidence",
                "F": "E + prior validated memory",
            },
        },
        "summary": summary,
        "records": records,
        "limitations": [
            "Controlled synthetic dataset; not statistically significant.",
            "Mock provider and chairman decisions exercise the harness; they do not estimate real model performance.",
            "System F uses an oracle development reviewer on repeated facts; evaluate real human review separately.",
            "A/B score 0.5 is an uninformative baseline, not a model confidence prediction.",
            "Explanation completeness is a schema-coverage proxy, not a human quality judgment.",
        ],
    }
    with tracker.engine.begin() as conn:
        conn.execute(insert(db.experiments).values(id=experiment_id, payload=artifact))
        for system, values in summary.items():
            for name, value in values.items():
                if isinstance(value, (float, int)):
                    conn.execute(
                        insert(db.metrics).values(
                            id=uid(), experiment_id=experiment_id, name=f"{system}.{name}", value=value
                        )
                    )
    target = Path(output)
    target.mkdir(parents=True, exist_ok=True)
    (target / "experiment.json").write_text(json.dumps(artifact, indent=2), encoding="utf8")
    with (target / "results.csv").open("w", newline="", encoding="utf8") as file:
        writer = csv.DictWriter(file, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    for system, values in summary.items():
        (target / f"reliability-{system}.svg").write_text(reliability_svg(values), encoding="utf8")
    return artifact
