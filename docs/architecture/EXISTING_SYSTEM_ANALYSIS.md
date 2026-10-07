# Existing system analysis

Baseline: 92e1fcc, inspected 7 October 2026. Original D:/ai council is Windows read-only; development uses a separate clone preserving history.

## Architecture, components and data flow
React 19/Vite 7 -> FastAPI :8001 -> concurrent OpenRouter first opinions -> anonymous peer ranking -> chairman synthesis -> JSON conversation storage. SSE emits finished stages. No previous conversation context reaches models.
backend/config.py hardcodes openai/gpt-5.1, google/gemini-3-pro-preview, anthropic/claude-sonnet-4.5, x-ai/grok-4. Chairman uses Gemini; titles Gemini 2.5 Flash. These are baseline IDs, not verified current availability. openrouter.py uses httpx/asyncio.gather; errors print and return None. council.py owns prompts, parsing and average rank. main.py exposes health, conversation list/create/get, batch message and SSE message APIs. storage.py synchronously writes non-atomic JSON in data/conversations; ranking metadata is not persisted. No database, authentication, migrations, retry/cache/cost accounting or structured logging.

## Frontend and dependencies
App manages conversation/SSE state; Sidebar lists chats; ChatInterface uses Stage1 response tabs, Stage2 raw reviews and parsed ranks, Stage3 chairman markdown. Light CSS/blue theme. Input vanishes after first question. SSE parser loses split frames. API URL is hardcoded. Python >=3.10: FastAPI, uvicorn, dotenv, httpx, Pydantic (uv.lock). React/React DOM/react-markdown, Vite/ESLint/plugins (npm lock). start.sh starts both servers; root main.py is an unused greeting. No tests; CLAUDE.md references an absent connectivity script.

## Strengths and reusable components
Retain original council as research baseline, anonymous reviews, async concurrency, ranking parser, chairman prompts, JSON chats, existing APIs, sidebar, tabs and markdown. Raw output inspection is already useful explainability.

## Limitations and planned changes
Modify transport behind a common interface; retain legacy shape. Add normalization/provenance, request IDs, bounded retries, cache/usage/cost. Fix metadata persistence, IDs and SSE framing. Add consensus mode to the existing UI.
Create app/providers, claims, comparison, evidence, knowledge, aggregation, confidence, validation, retrieval, orchestration, synthesis and evaluation. Add PostgreSQL/SQLAlchemy/Alembic, Qdrant adapter, optional embedding/NLI models, audit/version history, raw confidence/calibration, empirical reliability, tests, dataset, Docker and docs. No destructive rewrite or silent data migration.
