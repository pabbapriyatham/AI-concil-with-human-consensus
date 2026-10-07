# Human validation and memory

ACCEPT/CORRECT creates VALIDATED versions; REJECT creates REJECTED; MARK_UNCERTAIN
creates DISPUTED. ADD_EVIDENCE and ADD_EXPLANATION preserve current status.
Every action requires reviewer, explanation and expected version. Stale updates return
409. Version and audit append atomically; original model text and old claims remain.

Only the latest SQL-current VALIDATED version enters semantic memory. Qdrant results
must match that version; rejected/stale items cannot reappear. Retrieval and evidence
assessment can support or contradict fresh model claims. If a correction introduces
a missing candidate, it is visibly attributed to human-validated memory, never a model.
Synthesis explicitly states memory influence and exposes reviewer/version/reason.

Reviewer names identify locally supplied reviewers, not independently verified
identities. API_TOKEN protects the service with a shared access token, not per-user
roles. Human decisions can be wrong; keep evidence, review provenance and revision.
Historical executions remain snapshots; rerunning uses current reviewed knowledge.
