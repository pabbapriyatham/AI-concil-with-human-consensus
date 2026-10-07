# Data flow and provenance

ConsensusRequest validates question, context, model identities and evidence.
Provider calls run concurrently with an overall deadline and at most two retries.
Normalized immutable responses retain original text/payload and provider IDs.
Extraction records source sentence/response; relations record method/direction.
Evidence objects retain source, retrieval/publication timestamps, quality and URL.
Only SQL-current VALIDATED knowledge can enter the memory index; stale Qdrant
versions and rejected/superseded knowledge are filtered.

Aggregation records supporters, contradictions, empirical weights, evidence and
memory factors per claim. Raw confidence retains reasons and provider coverage.
Escalation broadens retrieval once and can ask one spare configured model. It
never silently calls an unconfigured provider. Human-review reasons remain visible.

Synthesis emits only structured candidate claims with supporting evidence/memory,
preserves dissent and abstains when no candidate is supported. Retrieved sources
and memory version/reviewer are inspectable. Original model responses are never
replaced by a human correction. Review creates a new version and audit transaction.

SQL persists questions, execution payloads, responses, claims and graph edges;
the payload is an explicit JSON representation of the explanation. Legacy council
conversations remain in their original JSON format.
