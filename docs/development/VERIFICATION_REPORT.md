# Verification report — 7 October 2026

## Verified locally

- 34 Python tests passed; one opt-in PostgreSQL service test skipped.
- Ruff checks pass; frontend ESLint and production Vite build pass.
- Two SSE tests cover JSON/frame/UTF-8 splits and incomplete streams.
- Final headless Edge walkthrough passes: responses, claims, graph, correction,
  append-only history, future memory, original council streaming and mobile layout.
- npm audit reports zero known vulnerabilities after compatible dependency updates.
- uv lock is synchronized; editable project installation succeeds.
- Alembic PostgreSQL DDL export includes every entity and knowledge version constraint.
- Full 42-example A–F offline evaluation exports 252 primary result rows, repeated
  consistency checks, JSON/CSV and SVG reliability diagrams.
- Held-out isotonic calibration demo exports JSON/SVG and persists experiment metrics.
- Original council mock demo and complete consensus example execute successfully.
- UUID path checks, atomic UTF-8 JSON writes, metadata persistence, optional bearer
  access, forged-memory rejection, timezone validation and request IDs are tested.

## Not verified live

No provider credentials were used, no paid calls made. Native REST adapters have
mocked contract coverage; account/model availability still needs live validation.
PostgreSQL and Qdrant services are not installed/configured here; Docker deployment
and actual-service integration were not run. SQL schema was checked offline and
through SQLite migrations; Qdrant REST has mocked contract coverage.
Sentence Transformers and Transformer NLI weights were not downloaded. Offline
matching/extraction/contradictions are explicitly labeled development methods.
No production calibrator is enabled; synthetic fixtures cannot establish real-world
accuracy, statistical significance or human-review effectiveness.

## Workspace and data

Original D:/ai council remains unchanged because Windows grants read-only access.
Implementation lives in a history-preserving writable clone on codex/mahthildis.
Each phase has a separate tested commit. The upstream README is preserved.
Initial browser fixture validations in the development database were retired through
new SUPERSEDED versions, retaining audit history. Final browser validation uses
data/browser-smoke.db, separate from the normal app database.

## Follow-up deployment validation

Configure backend-only provider credentials/current IDs, run PostgreSQL/Qdrant,
apply tracked migrations, enable downloaded ML backends and run opt-in integration
checks. Replace/extend synthetic development data with independently labeled
research data. Estimate source quality and reliability empirically; fit and evaluate
calibration on separate samples before making calibrated-probability claims.
