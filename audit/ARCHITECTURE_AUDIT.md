# Architecture audit

## Repository and lineage

The tree has 141 tracked files at 4cd4ec5. Git history through 92e1fcc contains the upstream Council. The Mahthildis progression starts at 08f0a04, followed by the provider, normalizer, claim, comparison and later phase commits. The baseline still runs through the original chat UI. Its transport and storage have evolved. docs/UPSTREAM_README.md preserves the earlier design.

| Area | Responsibility and dependency |
|---|---|
| backend/ | FastAPI host, legacy three-stage council, JSON conversation store and compatibility transport. |
| app/ | Consensus API, provider adapters, normalization, claim analysis, retrieval, aggregation, confidence, validation, synthesis, evaluation and tracing. |
| frontend/ | React/Vite application. App.jsx selects consensus by default or legacy chat. consensusApi.js calls JSON routes. api.js and sse.js handle the council stream. |
| migrations/, alembic.ini | Alembic revision 0001 builds SQL tables and unique knowledge versions. SQLite auto-migrates. PostgreSQL needs migration at deployment. |
| data/, datasets/, artifacts/ | Local SQL and conversation state, tracked synthetic development corpus, ignored historic exports and screenshots respectively. Stored user conversation contents were outside the evidence needed for this audit. |
| scripts/, tests/ | Start, mock demo, browser smoke, calibration, evaluation and dataset tooling. Pytest unit, integration and evaluation suites, plus frontend/tests/sse.test.js. |
| docs/ | Architecture/data flow, research methods, setup, API, testing and historical verification. Prior claims were checked separately from new results. |
| Root/tooling | README, CLAUDE.md, launchers, Dockerfile, Compose, pyproject.toml, uv.lock and environment example. .venv, egg-info, caches, frontend/node_modules and dist are installed/generated material. main.py prints a greeting. backend.main is the application entry point. |

## Request flow

1. ConsensusWorkspace reads the question, text context and model selection. File reading happens in the browser. consensusApi.execute submits JSON to FastAPI.
2. Middleware establishes a request ID and enforces optional shared bearer access. app/api.py validates ConsensusRequest and resolves a cached Store. ConsensusEngine.run selects primary models, calls adapters concurrently, handles provider errors and optionally consults one fallback.
3. normalize_response preserves each raw response. extract_claims creates linked records. RetrievalService persists context as evidence, then queries documents and currently validated knowledge. Knowledge mode can introduce an explicit evidence-derived candidate.
4. RelationEngine.graph compares different responses. EvidenceEngine.verify assesses source sentences. The selected strategy combines model, evidence and memory signals. ConfidenceEngine scores claims and the answer. Low scores or contradictions can expand retrieval and consult a spare model.
5. synthesize assembles the report. Review candidates and execution records are written to SQL. The UI exposes raw responses, claim decisions, graph, evidence, conclusion and review. ReviewService appends a version and audit event. A future execution retrieves the current validated version.
6. Separately, backend/council.py collects answers, anonymously ranks responses and uses a chairman to synthesize. backend/storage.py stores conversations in JSON. This flow remains a comparison baseline. The research runner invokes both architectures.

## Route map

| Base | Operations |
|---|---|
| / | GET health/identity response |
| /api/conversations | GET list, POST create, GET /{id}, POST /{id}/message, POST /{id}/message/stream (SSE) |
| /api/consensus | GET /config, POST /executions, GET /executions/{request_id}, POST /documents, GET /knowledge, GET /knowledge/{id}/history, POST /knowledge/{id}/review |
| /ui | Optional built static frontend mount when FRONTEND_DIST_PATH exists. Docker builds assets with /ui/ base. |

## Runtime and deployment

Python 3.11+ with FastAPI, Pydantic, HTTPX, SQLAlchemy, Alembic and NumPy. React 19 and Vite use npm's lockfile. Research extras add PostgreSQL and vector tooling. ML extras add transformers and sentence-transformers. Docker builds a frontend and API image. Compose defines PostgreSQL and Qdrant services. scripts/start.ps1 launches local backend and frontend. Without -Live it inherits the environment; the local dotenv parsed as live/default. Set DEV_MODE=true in the demo process explicitly.

Configuration names include DEV_MODE, MAHTHILDIS_MODELS, MAHTHILDIS_FALLBACK, CHAIRMAN_MODEL, provider-specific API keys, MODEL_PRICES_JSON, DATABASE_URL, EMBEDDING_BACKEND/MODEL, NLI_BACKEND/MODEL, QDRANT_URL/API_KEY, API_TOKEN, PUBLIC_DEPLOYMENT, LOG_LEVEL, VITE_API_BASE, FRONTEND_DIST_PATH and POSTGRES_PASSWORD. No values from local credentials are included. HTTP/stage logs carry request IDs, durations and usage. Operational alerts, distributed tracing, per-user storage boundaries and recovery guarantees were not demonstrated.

Every major **stage** of the target architecture has a local path. Experimental validation, trustworthy source and reviewer identity, scalable retrieval and calibrated inference are the main differences between that architecture and the verified system.
