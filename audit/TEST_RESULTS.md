# Test results · 24 November 2026

## Acceptance checks

Fixed unit of counting for the verification measure: each row is a capability, independently of how many automated cases cover it. Ten passed and six were not run at the stated fidelity.

| # | Check | Result | Evidence and scope |
|---:|---|---|---|
| 1 | Backend start and configuration | PASS | backend.main started on loopback. GET /api/consensus/config returned 200. Local dotenv parsed, two model entries and a JSON price object were readable. Test processes used explicit settings. |
| 2 | Frontend load and user journey | PASS | Built index returned 200. Headless Edge submitted a question with context, browsed the graph, recorded a correction and displayed its version on rerun. No page errors. |
| 3 | API validation and review | PASS | TestClient exercised creation, 422 input validation, review, 409 stale version, history and bearer access. |
| 4 | Local database and memory | PASS | SQLite migration, transactional versions, correction/rejection, evidence and later retrieval. File-backed SQLite also used in browser run. |
| 5 | Provider adapters and parallel mock orchestration | PASS | Five HTTP transport fixtures, three simulated responses, retry, failure handling and bounded fallback. |
| 6 | Response and claim pipeline | PASS | Raw text retention, extraction, relation/evidence signal, aggregation, confidence limits, synthesis and execution persistence. |
| 7 | Legacy Council | PASS | Browser reached stage 3 via SSE. Two standalone Node tests passed for split UTF-8/frame boundaries and incomplete streams. |
| 8 | Evaluation | PASS | 42 examples × six systems; mock runner completed and exported results. One-case export regression test also passed. |
| 9 | Offline calibration tooling | PASS | scripts/calibrate.py completed isotonic on fixture observations. Prior matching input/artifacts have 30 train and 10 test observations. Fitting, bounds and split overlap tests passed. |
| 10 | Build and static checks | PASS | Vite 7.3.7 built 207 modules, frontend ESLint emitted no diagnostics, Python Ruff returned All checks passed. |
| 11 | Live model authentication, availability, usage and cost | NOT RUN | External requests excluded. Configured credentials alone provide no functional evidence. |
| 12 | PostgreSQL migrations and concurrent updates | NOT RUN | Dedicated database test skipped. |
| 13 | Persistent Qdrant service | NOT RUN | REST contract used HTTPX MockTransport. |
| 14 | Real sentence embeddings and NLI weights | NOT RUN | Hash backend and injected named-label classifier only. |
| 15 | Held-out real accuracy and calibrated probabilities | NOT RUN | No independent real evaluation corpus or deployed calibrator. |
| 16 | Blinded human correction effectiveness | NOT RUN | Scripted reviewer and synthetic oracle. |

## Automated Python test ledger

Python 3.14.7, pytest 9.1.1. Final isolated mock run: **38 passed, 1 skipped, 1 warning** in 1.28 seconds. Test identifiers describe the behavior asserted. Starlette emitted a TestClient HTTPX deprecation warning. All integration cases other than the dedicated PostgreSQL case passed.

| Suite file | Test / asserted behavior | Result |
|---|---|---|
| `tests/evaluation/test_framework.py` | `test_dataset_schema_and_categories` | PASS |
| `tests/evaluation/test_framework.py` | `test_reproducible_exports` | PASS |
| `tests/evaluation/test_framework.py` | `test_metrics_and_abstention` | PASS |
| `tests/integration/test_memory.py` | `test_correction_retrieved_and_rejection_removed` | PASS |
| `tests/integration/test_memory.py` | `test_chunks_and_document_retrieval` | PASS |
| `tests/integration/test_pipeline.py` | `test_end_to_end_and_memory` | PASS |
| `tests/integration/test_pipeline.py` | `test_api_input_and_review` | PASS |
| `tests/integration/test_pipeline.py` | `test_escalation_bounded` | PASS |
| `tests/integration/test_postgres.py` | `test_postgresql_migration_and_versions` | NOT RUN — dedicated PostgreSQL URL absent |
| `tests/integration/test_provider_fallback.py` | `test_failed_providers_consult_router_only_once` | PASS |
| `tests/integration/test_provider_fallback.py` | `test_legacy_uses_native_providers_and_one_fallback` | PASS |
| `tests/integration/test_security.py` | `test_storage_path_and_metadata` | PASS |
| `tests/integration/test_security.py` | `test_optional_auth_and_trace` | PASS |
| `tests/integration/test_security.py` | `test_untrusted_memory_and_timezone_rejected` | PASS |
| `tests/unit/test_aggregation.py` | `test_evidence_overrides_majority` | PASS |
| `tests/unit/test_aggregation.py` | `test_empirical_reliability` | PASS |
| `tests/unit/test_calibration.py` | `test_metrics_boundaries` | PASS |
| `tests/unit/test_calibration.py` | `test_fits_and_leakage` | PASS |
| `tests/unit/test_claims.py` | `test_compound_atomic_and_dedup` | PASS |
| `tests/unit/test_claims.py` | `test_subjectivity_and_qualifiers` | PASS |
| `tests/unit/test_confidence.py` | `test_raw_confidence_caps_and_coverage` | PASS |
| `tests/unit/test_evidence.py` | `test_support_contradict_insufficient` | PASS |
| `tests/unit/test_knowledge.py` | `test_versioning_and_stale_updates` | PASS |
| `tests/unit/test_legacy.py` | `test_rankings_preserved` | PASS |
| `tests/unit/test_normalization.py` | `test_raw_provenance_and_immutability` | PASS |
| `tests/unit/test_providers.py` | `test_mock_and_cache` | PASS |
| `tests/unit/test_providers.py` | `test_adapters[openai-data0-yes]` | PASS |
| `tests/unit/test_providers.py` | `test_adapters[groq-data1-yes]` | PASS |
| `tests/unit/test_providers.py` | `test_adapters[openrouter-data2-yes]` | PASS |
| `tests/unit/test_providers.py` | `test_adapters[anthropic-data3-yes]` | PASS |
| `tests/unit/test_providers.py` | `test_adapters[gemini-data4-yes]` | PASS |
| `tests/unit/test_providers.py` | `test_failure_sanitized` | PASS |
| `tests/unit/test_providers.py` | `test_retry` | PASS |
| `tests/unit/test_qdrant.py` | `test_qdrant_rest_contract` | PASS |
| `tests/unit/test_relations.py` | `test_date_contradiction_and_neutral` | PASS |
| `tests/unit/test_relations.py` | `test_nli_named_labels` | PASS |
| `tests/unit/test_semantic.py` | `test_embedding_candidates` | PASS |
| `tests/unit/test_validation.py` | `test_complete_review_history` | PASS |
| `tests/unit/test_validation.py` | `test_required_correction` | PASS |

## Functional probes and failed attempts

- PASS: identical-predicate historical dates 1999 versus 2001 produced CONTRADICTION, structured-v1, 0.9. FAIL against the expected contradiction: “The lamp is on.” versus “The lamp is off.” produced DIVERGENCE, 0.65 on the default backend. These two probes are examples, not a detection rate.
- FAIL with blank MODEL_PRICES_JSON: 12 failures, 26 pass, one skip. The audit process's attempt to clear the variable exposed an empty string to json.loads. A valid empty object gave the final green run. The checked local dotenv had a valid object. This is a configuration-handling defect, not evidence that the user's current settings fail.
- Sandbox loopback initially prevented Windows asyncio socket-pair initialization. Reran locally in an isolated temporary source copy with mock providers and no user database. Headless smoke used the existing script, temporary screenshots, a file-backed database and the built frontend on port 5173. The mock run used three explicitly selected IDs.
- An early shell did not stop when a previous command's temporary path was unavailable. Its attempted dependency copy onto itself was rejected. Vite consequently regenerated the ignored frontend/dist in the working tree. Project source was untouched. The final Python, benchmark and browser runs used fresh isolated storage.
- No current online package advisory check, Docker image deployment, performance/load run, or assistive-technology test. Historical artifacts/frontend-audit.json lists 16 findings (11 high); docs/development/VERIFICATION_REPORT.md claims zero after updates. Neither establishes the current lockfile's vulnerability count.

## Full synthetic benchmark

| System | Exact answer-set accuracy | Brier | ECE |
|---|---:|---:|---:|
| A single model fixture | .143 | .250 | .500 |
| B Council chairman fixture | .143 | .250 | .500 |
| C weighted claims | .000 | .296 | .505 |
| D evidence | 1.000 | .588 | .767 |
| E evidence and confidence | 1.000 | .090 | .300 |
| F oracle memory | 1.000 | .000* | .020 |

42 cases per system. Values are rounded as printed by scripts/evaluate.py (*rounded Brier). Calibration metrics cover cases with factual predictions. A/B use a constant 0.5. C/D scores come from the confidence ablation. The Council fixture chairman returns the first scripted response. F is given the answer through a synthetic correction. None of these rows measures general LLM accuracy.
