# API

Original GET /, GET/POST /api/conversations, GET /api/conversations/{uuid},
POST /api/conversations/{uuid}/message and /message/stream remain. Conversation
IDs are UUID-validated; metadata persists; JSON writes are atomic/thread-serialized.
SSE emits complete stages and the frontend preserves split frames and UTF-8.

Mahthildis:

| Method | Route | Purpose |
|---|---|---|
| GET | /api/consensus/config | Models and honest local/live capability labels |
| POST | /api/consensus/executions | Run validated ConsensusRequest |
| GET | /api/consensus/executions/{id} | Immutable saved explanation |
| GET | /api/consensus/knowledge?status=VALIDATED | Current knowledge |
| GET | /api/consensus/knowledge/{id}/history | All versions |
| POST | /api/consensus/knowledge/{id}/review | Append review/version |
| POST | /api/consensus/documents | Ingest named source text/chunks |

Execution body: question, optional context/models/evidence/domain/category, mode
CHEAP/BALANCED/HIGH_ACCURACY, aggregation majority/weighted/evidence/knowledge,
allow_escalation and timeout. CHEAP starts two models; other modes start three.
Escalation can broaden evidence once and consult at most one spare configured model.
At most eight model selections, 30 evidence inputs and 120 analyzed claims; raw
responses remain preserved. Unknown token/cost fields stay explicitly incomplete.
Evidence of type knowledge cannot be injected externally; it comes from reviewed SQL.

Review body: action, expected_version, reviewer, explanation, optional corrected_claim
and evidence. Correction requires text; adding evidence requires evidence. Missing
knowledge returns 404; stale versions 409; input failures 422.

Set API_TOKEN to require Authorization: Bearer TOKEN on /api routes. The frontend
can use its local access-token input; provider credentials stay on the backend.
X-Request-ID matches saved consensus IDs and structured trace entries.
Swagger schema: /docs. No arbitrary URL fetch/crawler or model-generated code execution.
