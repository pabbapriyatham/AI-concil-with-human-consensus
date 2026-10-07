# Mahthildis Multi-Model Consensus Engine

An incremental extension of Karpathy's LLM Council: claim-level comparisons,
evidence-aware aggregation, raw confidence, versioned human review and reusable
validated knowledge. The original council, UI components and Git history are preserved.

## Current status

Working **offline research prototype**, with native OpenAI/Gemini/Anthropic/OpenRouter
adapters and PostgreSQL/Qdrant/ML integration paths. Mock end-to-end flows are verified.
Live providers, downloaded embedding/NLI weights, PostgreSQL and Qdrant services still
need deployment validation. No claim of calibrated correctness or research superiority.

The original `D:\ai council` is Windows read-only. This implementation is in a
separate writable clone on branch `codex/mahthildis`; see setup docs for transfer.

## Run locally (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev,research]"
Copy-Item .env.example .env
npm.cmd ci --prefix frontend
.\scripts\start.ps1
```

Open http://localhost:5173. Backend API/schema: http://localhost:8001/docs.
The default development mode makes no paid calls. Try the Eiffel Tower question;
paste source text to inspect evidence, correct a claim, then rerun to see memory.
Other mock questions abstain instead of fabricating answers. For real providers,
configure backend-only keys and current model IDs, then set DEV_MODE=false.

## What is implemented

- Provider contract, bounded deadlines/retries, cache, sanitized errors and provenance.
- Immutable normalized responses and typed atomic claims with source provenance.
- Embedding candidate matching, structured contradictions and optional NLI.
- Explainable claim graph, retrieved evidence and transparent aggregation factors.
- Four aggregation strategies; empirical reliability from persisted labeled experiments.
- Raw confidence, Brier/ECE/reliability diagrams, isotonic and Platt experiments.
- PostgreSQL-compatible tracked schema; SQLite development fallback.
- Append-only review/version history; stale-update protection and validated-memory retrieval.
- Qdrant REST abstraction with current-version checks; portable development index.
- Bounded retrieval/model escalation, abstention and traceable structured synthesis.
- Existing React UI extended with claims, graph, evidence, review, memory and cost details.
- Six-system evaluation harness, 42 controlled synthetic examples and CSV/JSON exports.
- Optional API access token, UUID validation, atomic legacy storage and split-safe SSE.

## Verify

```powershell
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m ruff check app backend tests scripts
npm.cmd run lint --prefix frontend
node --test frontend/tests/sse.test.js
npm.cmd run build --prefix frontend
.venv\Scripts\python -m scripts.demo
.venv\Scripts\python -m scripts.evaluate
```

Synthetic/mock evaluation numbers test the harness; they are not real-model results.
Calibration is diagnostic and is not automatically applied to production answers.
Rules/hash matching have limited semantic recall; enable downloaded ML adapters for
research and evaluate them independently. Sources and human review can also be wrong.
There is no web crawler, external search connector, per-user authentication or OCR.
Native provider stream methods currently expose a buffered fallback.

## Documentation

- [Baseline analysis](docs/architecture/EXISTING_SYSTEM_ANALYSIS.md)
- [Target architecture](docs/architecture/TARGET_ARCHITECTURE.md)
- [Implementation plan](docs/architecture/IMPLEMENTATION_PLAN.md)
- [Data flow](docs/architecture/DATA_FLOW.md) and [decisions](docs/architecture/DECISIONS.md)
- [Setup](docs/development/SETUP.md), [API](docs/development/API.md), [testing](docs/development/TESTING.md)
- [Phase verification log](docs/development/PHASE_LOG.md)
- [Research questions](docs/research/RESEARCH_QUESTIONS.md), [evaluation](docs/research/EVALUATION.md)
- [Aggregation](docs/research/AGGREGATION.md), [confidence](docs/research/CONFIDENCE.md), [human validation](docs/research/HUMAN_VALIDATION.md)

Upstream: https://github.com/karpathy/llm-council. Original README is retained in
[docs/UPSTREAM_README.md](docs/UPSTREAM_README.md). This is decision support, not an
autonomous authority; professional/high-risk questions require appropriate human review.
