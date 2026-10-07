# Target architecture

One FastAPI service and existing React frontend. Preserve original council as a baseline.
Question/context -> provider orchestrator -> immutable normalized responses -> atomic claims -> embedding candidates -> structured/NLI graph -> evidence + validated memory -> aggregation -> raw confidence -> bounded escalation/human review -> constrained synthesis -> persisted execution.
PostgreSQL is source of truth; Alembic tracks schema; Qdrant stores rebuildable indexes only. Explicit SQLite/local heuristics support offline development; method labels never imply ML verification. External sources must actually be retrieved. Human review appends versions with optimistic concurrency, retaining originals. Validated memory influences future results visibly.
Compare majority (baseline only), empirical weighted, evidence-aware and knowledge-aware strategies. Confidence stays raw until held-out calibration. Dissent, missing evidence and professional risk trigger review. Save experiment configs/prompts/output/usage/timing/cost and calibration; development fixtures do not establish statistical significance.
