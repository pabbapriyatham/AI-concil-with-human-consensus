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

## Gemini + Groq + OpenRouter

Put your keys in the root `.env` file (backend only):

```dotenv
GEMINI_API_KEY=your-google-ai-studio-key
GROQ_API_KEY=your-groqcloud-key
OPENROUTER_API_KEY=your-openrouter-key
DEV_MODE=false
MAHTHILDIS_MODELS=gemini:gemini-3.8-flash,groq:openai/gpt-oss-120b
MAHTHILDIS_FALLBACK=openrouter:openrouter/free
CHAIRMAN_MODEL=gemini:gemini-3.8-flash
```

Gemini is the primary model and original council chairman; Groq provides the
second answer. OpenRouter is consulted once on provider failure, including exhausted
rate-limit retries. Its answer retains OpenRouter provenance and is counted once.
Both the consensus workspace and original council support this configuration.
The original council also uses the configured chairman for conversation titles.
Restart the backend after editing keys or model IDs: `scripts/start.ps1 -Live`.
The start script honors `.env` by default; `-Live` explicitly disables mock mode.

Model IDs were checked against the official model catalogs on 10 October 2026:
[Gemini](https://ai.google.dev/gemini-api/docs/models),
[Groq](https://console.groq.com/docs/models), and
[OpenRouter free router](https://openrouter.ai/docs/guides/routing/routers/free-router).
Account access and free-tier quotas still need verification with your keys.
No live provider requests were made during configuration. This change adds text
generation; news retrieval, image inputs and voice interfaces are separate features.

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

The complete project now lives in D:/ai council on codex/mahthildis with original
Git history preserved. Folder permissions allow the current user to modify it.
The move included dependencies, artifacts and development data; 16,862 files were
hash-verified before removing the old development copy. The Python environment
was repaired for the new path, and Python tests, SSE tests and the frontend build passed.
