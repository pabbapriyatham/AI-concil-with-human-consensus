# Implementation plan

For each phase: tests, example, docs, commit; no paid automated calls.
0 analysis; 1 providers/retries/cache/mock; 2 normalization; 3 atomic claims; 4 embeddings; 5 NLI/relations; 6 evidence; 7 PostgreSQL/versioning; 8 aggregation/reliability; 9 raw confidence; 10 calibration; 11 human review; 12 RAG/memory; 13 escalation/synthesis/API; 14 explainability UI; 15 experiments/dataset; 16 polish.
Existing APIs/dependencies/models/storage/UI/reuse are listed in EXISTING_SYSTEM_ANALYSIS.md. Missing core dependencies: SQLAlchemy, Alembic, psycopg, pytest, Ruff, NumPy, scikit-learn. Optional ML/retrieval: sentence-transformers, transformers/torch, qdrant-client.
New consensus endpoints coexist with original conversations. SQL storage and legacy JSON remain separate until a tested migration is requested. Verify normalization, compound/subjective claims, equivalence/neutral/contradiction, evidence overrides, append-only history/stale reviews, raw confidence, held-out calibration, retrieval of corrections, end-to-end API, frontend and reproducible experiments. Record unavailable live providers/PostgreSQL/Qdrant/ML weights honestly.
