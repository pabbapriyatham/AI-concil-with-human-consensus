# Setup

Python >=3.11 and Node >=22. Recommended ML runtime: Python 3.11/3.12; this workstation
used Python 3.14 for portable offline verification. Windows application control blocked
SciPy/native SQLAlchemy 2.1; SQLAlchemy 2.0.44 and portable hash vectors work here.

From the project root in PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev,research]"
Copy-Item .env.example .env
npm.cmd ci --prefix frontend
.\scripts\start.ps1
```

Default .env.example uses DEV_MODE=true, SQLite and portable hash vectors. Fixture
questions cover the Eiffel Tower; other questions abstain. Model/provider prices
are never guessed. Never commit .env or put provider keys in VITE_* variables.

For live providers, populate backend-only keys, choose current model IDs in
MAHTHILDIS_MODELS, set DEV_MODE=false, and start with scripts/start.ps1 -Live.
Provider IDs are configuration examples, not verified account availability.

PostgreSQL/Qdrant:

```powershell
docker compose up -d
# Set DATABASE_URL=postgresql+psycopg://mahthildis:PASSWORD@localhost:5432/mahthildis in .env
# Set QDRANT_URL=http://localhost:6333
.venv\Scripts\python -m alembic upgrade head
```

Set POSTGRES_PASSWORD before compose. PostgreSQL migrations are explicit; only
SQLite auto-migrates for local development/tests. Qdrant collections are rebuilt
from SQL and keyed to embedding method. Back up SQL and legacy data/conversations.

ML: install .[ml], set EMBEDDING_BACKEND=sentence-transformers and
NLI_BACKEND=transformers. First use downloads model weights. Offline rules/hash
have limited extraction/paraphrase/contradiction recall. Actual model downloads
and PostgreSQL/Qdrant container integration were not available on this workstation.

Dockerfile includes frontend under /ui and backend :8001; run migrations before
connecting a production database. It is supplied for deployment testing, not a claim
that deployment was executed here. Keep local services on loopback. For public access,
set PUBLIC_DEPLOYMENT=true and API_TOKEN, and use HTTPS/access controls.

Original D:/ai council was Windows read-only. Work is on codex/mahthildis in a
separate clone with original Git history. To transfer after fixing folder permission,
fetch this clone's codex/mahthildis branch from the original checkout and fast-forward
a new branch; inspect the diff first. No original data was deleted or migrated.
