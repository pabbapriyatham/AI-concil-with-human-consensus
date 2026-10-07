# Testing

```powershell
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m ruff check app backend tests scripts
npm.cmd run lint --prefix frontend
node --test frontend/tests/sse.test.js
npm.cmd run build --prefix frontend
.venv\Scripts\python -m scripts.demo
.venv\Scripts\python -m scripts.evaluate
```

Tests use mocked HTTP/model providers and SQLite migrations; no API money is spent.
Unit suites cover providers/retries/cache/normalization, claims, embeddings, relations/
NLI contracts, evidence, aggregation, raw confidence/calibration, versioning and reviews.
Integration covers the complete pipeline, correction reuse, stale review conflicts,
auth/request traces, path validation, atomic writes and metadata preservation.

Browser smoke: start both local servers with DEV_MODE=true, install Playwright or
set PLAYWRIGHT_MODULE to its module path, then node scripts/browser_smoke.cjs.
Edge is the default channel; BROWSER_CHANNEL may change it. Use an isolated
DATABASE_URL for browser tests: the walkthrough creates explicitly labeled test reviews.
Screenshots are stored in artifacts/. The legacy council SSE path is exercised.

PostgreSQL: set TEST_DATABASE_URL for migration/store checks against an isolated
test database. Qdrant REST currently has mocked contract coverage; use a dedicated
collection and actual service for deployment validation. Downloaded ML model behavior
and live provider availability require separate tests; mock success is not sufficient.
Full infrastructure deployment was not performed here.
