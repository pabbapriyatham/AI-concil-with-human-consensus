import csv
import hashlib
import json
import os
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
from app.orchestration.schemas import configured_fallback, configured_models
from app.providers import ProviderError, get_provider
from app.providers.base import ProviderResult
from app.retrieval import RetrievalService
from app.retrieval.vectors import MemoryVectors
from app.schemas import uid
from app.validation import ReviewRequest, ReviewService
from backend.config import CHAIRMAN_MODEL, COUNCIL_MODELS
from backend.council import run_full_council
from backend.openrouter import uncached_council

from .dataset import DatasetExample, ReviewedMemory
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


async def baseline_trial(system, example, models, factory, live):
    if system == "A":
        try:
            response = await factory(models[0].provider).generate(
                models[0].model, [{"role": "user", "content": example.question}]
            )
        except ProviderError:
            return [], True, None, None
        tokens = (
            response.input_tokens + response.output_tokens
            if response.input_tokens is not None and response.output_tokens is not None
            else None
        )
        cost = response.cost
    else:
        if live:
            with uncached_council():
                _, _, final, _ = await run_full_council(example.question)
            if not final.get("provenance"):
                return [], True, None, None
        else:
            async def query_model(model, messages, **kwargs):
                return {"content": example.fixture_responses[0]}

            async def query_parallel(model_ids, messages):
                ranking = "evaluating different responses" in messages[-1]["content"]
                return {
                    model: {
                        "content": "FINAL RANKING:\n1. Response A\n2. Response B\n3. Response C"
                        if ranking
                        else example.fixture_responses[index % 3]
                    }
                    for index, model in enumerate(model_ids)
                }

            with (
                patch("backend.council.query_model", query_model),
                patch("backend.council.query_models_parallel", query_parallel),
            ):
                _, _, final, _ = await run_full_council(example.question)
        response = ProviderResult("baseline", "chairman", final["response"], uid())
        tokens = cost = None if live else 0
    normalized = normalize_response(response, example.id)
    claims = [claim.claim_text for claim in extract_claims(normalized) if claim.claim_type != "uncertain"]
    return claims, False, tokens, cost


def load_dataset(raw):
    examples = [DatasetExample.model_validate_json(line) for line in raw.splitlines() if line.strip()]
    if not examples:
        raise ValueError("Empty evaluation dataset")
    if len({item.id for item in examples}) != len(examples):
        raise ValueError("Dataset example IDs must be unique")
    if len({question_key(item.question) for item in examples}) != len(examples):
        raise ValueError("Dataset questions must be unique after case and whitespace normalization")
    return examples


def question_key(question):
    return " ".join(question.casefold().split())


async def evaluate(
    dataset,
    output,
    store=None,
    live=False,
    limit=None,
    consistency_repeats=2,
    memory_path=None,
    development_path=None,
):
    path = Path(dataset)
    raw = path.read_bytes()
    examples = load_dataset(raw)
    if limit is not None:
        if limit < 1:
            raise ValueError("Evaluation limit must be positive")
        examples = examples[:limit]
    if consistency_repeats < 1:
        raise ValueError("Consistency repetitions must be positive")
    if not live and any(item.fixture_responses is None for item in examples):
        raise ValueError("Offline evaluation requires fixture_responses on every selected example")
    development_bytes = None
    if development_path:
        development_bytes = Path(development_path).read_bytes()
        development = load_dataset(development_bytes)
        if {item.id for item in examples} & {item.id for item in development} or {
            question_key(item.question) for item in examples
        } & {question_key(item.question) for item in development}:
            raise ValueError("Evaluation and development datasets overlap by ID or question")
    memory_bytes = Path(memory_path).read_bytes() if memory_path else b""
    reviewed_memory = [
        ReviewedMemory.model_validate_json(line)
        for line in memory_bytes.splitlines()
        if line.strip()
    ]
    if memory_path and not reviewed_memory:
        raise ValueError("Reviewed memory file contains no entries")
    fallback = None
    if live:
        models = configured_models()[:3]
        fallback = configured_fallback()
        if (
            os.getenv("DEV_MODE", "").lower() == "true"
            or any(model.provider == "mock" for model in models)
            or (fallback and fallback.provider == "mock")
            or any(model.startswith("mock:") for model in [*COUNCIL_MODELS, CHAIRMAN_MODEL])
        ):
            raise ValueError("Live evaluation requires real provider selections and disabled mock mode")
    else:
        models = [ModelSpec(provider="mock", model=f"fixture-{i}") for i in range(3)]
    memory_mode = "reviewed snapshot" if reviewed_memory else "empty" if live else "synthetic oracle"
    experiment_id = uid()
    tracker = store or Store("sqlite:///:memory:", initialize=True)
    records = []
    for example in examples:
        provider = FixtureProvider(example)
        factory = get_provider if live else lambda _, provider=provider: provider
        for system in ["A", "B", "C", "D", "E", "F"]:
            # Isolation prevents cross-ablation evidence or memory leakage.
            work = Store("sqlite:///:memory:", initialize=True)
            start = time.perf_counter()
            relation_found, review_required, explanation, tokens, cost = False, False, 0.0, 0, 0.0
            confidence = 0.5
            result = None
            if system in {"A", "B"}:
                prediction, failed, tokens, cost = await baseline_trial(system, example, models, factory, live)
            else:
                if system == "F" and reviewed_memory:
                    reviewer = ReviewService(work)
                    for entry in reviewed_memory:
                        item = work.create_knowledge(entry.claim)
                        reviewer.review(
                            item["knowledge_id"],
                            ReviewRequest(action="ACCEPT", expected_version=1, **entry.model_dump(exclude={"claim"})),
                        )
                elif system == "F" and not live and example.ground_truth:
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
                    work,
                    provider_factory=factory,
                    confidence_enabled=system in {"E", "F"},
                    use_cache=False,
                    retrieval=RetrievalService(work, vectors=MemoryVectors()),
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
                execution = result["execution"]
                tokens = execution["input_tokens"] + execution["output_tokens"] if execution["usage_complete"] else None
                cost = result["execution"]["total_cost"]
                failed = not any(response["provider"] != "knowledge" for response in result["responses"])
                if failed:
                    prediction = []
            latency = time.perf_counter() - start
            correct = not failed and correctness(prediction, example.expected_claims, example.ground_truth is None)
            pred, gold = (
                {normalize_claim(t) for t in prediction},
                {normalize_claim(t) for t in example.expected_claims},
            )
            # Fixture labels describe the scripted responses only, not live generations.
            contradiction_expected = (
                example.fixture_contradiction_expected
                if not live and not failed and result is not None and not (system == "F" and reviewed_memory)
                else None
            )
            consistency = None
            repeat_tokens, repeat_cost, repeat_latency = 0, 0.0, 0.0
            if consistency_repeats > 1:
                matches = 0
                for _ in range(consistency_repeats - 1):
                    repeat_start = time.perf_counter()
                    if result is None:
                        claims, repeat_failed, usage, price = await baseline_trial(system, example, models, factory, live)
                    else:
                        repeated = await engine.run(request)
                        execution = repeated["execution"]
                        usage = execution["input_tokens"] + execution["output_tokens"] if execution["usage_complete"] else None
                        price = execution["total_cost"]
                        repeat_failed = not any(r["provider"] != "knowledge" for r in repeated["responses"])
                        selected = set(repeated["synthesis"]["supporting_claim_ids"])
                        claims = [claim["claim_text"] for claim in repeated["claims"] if claim["claim_id"] in selected]
                    repeat_tokens = repeat_tokens + usage if repeat_tokens is not None and usage is not None else None
                    repeat_cost = repeat_cost + price if repeat_cost is not None and price is not None else None
                    repeat_latency += time.perf_counter() - repeat_start
                    matches += int(not failed and not repeat_failed and {normalize_claim(c) for c in claims} == pred)
                consistency = matches / (consistency_repeats - 1)
            records.append(
                {
                    "example_id": example.id,
                    "question": example.question,
                    "system": system,
                    "category": example.category,
                    "prediction": sorted(pred),
                    "answer_claims": prediction,
                    "system_error": failed,
                    "correct": correct,
                    "score": confidence,
                    "latency": latency,
                    "tokens": tokens,
                    "cost": cost,
                    "claim_tp": len(pred & gold),
                    "claim_fp": len(pred - gold),
                    "claim_fn": len(gold - pred),
                    "contradiction_labeled": contradiction_expected is not None,
                    "contradiction_tp": int(relation_found and contradiction_expected is True),
                    "contradiction_fp": int(relation_found and contradiction_expected is False),
                    "contradiction_fn": int(not relation_found and contradiction_expected is True),
                    "error_detection_labeled": result is not None and not failed,
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
        "dataset_sha256": hashlib.sha256(raw).hexdigest(),
        "configuration": {
            "live": live,
            "development_dataset_sha256": hashlib.sha256(development_bytes).hexdigest() if development_bytes else None,
            "models": [m.model_dump() for m in models],
            "fallback": fallback.model_dump() if fallback else None,
            "baseline_council_models": COUNCIL_MODELS if live else None,
            "baseline_chairman": CHAIRMAN_MODEL if live else None,
            "prompt_version": "answer-v1",
            "embedding_method": result["explanation"]["embedding_method"],
            "nli_method": result["explanation"]["nli_method"],
            "consistency_repeats": consistency_repeats,
            "memory_mode": memory_mode,
            "reviewed_memory_sha256": hashlib.sha256(memory_bytes).hexdigest() if reviewed_memory else None,
            "systems": {
                "A": "single model",
                "B": "original council",
                "C": "claim comparison/weighted aggregation",
                "D": "C + evidence",
                "E": "D + confidence",
                "F": f"E with {memory_mode} memory",
            },
        },
        "summary": summary,
        "records": records,
        "limitations": [
            "Exact claim-set scoring does not resolve equivalent paraphrases or evidence quality.",
            "Reviewed memory must be frozen without access to the evaluation labels. The runner records its hash.",
            "A/B score 0.5 is an uninformative baseline, not a model confidence prediction.",
            "Explanation completeness is a schema-coverage proxy, not a human quality judgment.",
        ] + ([] if live else ["Fixture provider runs do not establish real-model performance."]),
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
