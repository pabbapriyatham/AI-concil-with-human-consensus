from sqlalchemy import select, insert, update
from . import database as db
from app.schemas import uid, now
from app.claims.normalizer import normalize_claim

STATUSES = {"UNVERIFIED", "SUPPORTED", "VALIDATED", "DISPUTED", "REJECTED", "SUPERSEDED"}


class StaleVersion(ValueError):
    pass


class Store:
    def __init__(self, url=None, initialize=False):
        self.engine = db.make_engine(url)
        if initialize:
            db.migrate(self.engine)

    def create_knowledge(self, claim, status="UNVERIFIED", confidence=0.0, evidence=None, provenance=None):
        if status not in STATUSES:
            raise ValueError("Invalid knowledge status")
        knowledge_id = uid()
        timestamp = now().isoformat()
        payload = {"knowledge_id": knowledge_id, "claim": claim,
                   "normalized_claim": normalize_claim(claim), "status": status,
                   "validation_state": "unreviewed", "confidence": confidence,
                   "evidence": evidence or [], "provenance": provenance or {},
                   "created_at": timestamp, "updated_at": timestamp, "version": 1,
                   "previous_version": None, "supersedes": None, "reason": "model-generated", "validator": None}
        with self.engine.begin() as conn:
            conn.execute(insert(db.knowledge_items).values(id=knowledge_id, current_version=1))
            conn.execute(insert(db.knowledge_versions).values(id=uid(), knowledge_id=knowledge_id, version=1,
                         status=status, normalized_claim=payload["normalized_claim"], payload=payload))
        return payload

    def history(self, knowledge_id):
        with self.engine.connect() as conn:
            return list(conn.execute(select(db.knowledge_versions.c.payload).where(
                db.knowledge_versions.c.knowledge_id == knowledge_id).order_by(db.knowledge_versions.c.version)).scalars())

    def current(self, knowledge_id):
        with self.engine.connect() as conn:
            stmt = select(db.knowledge_versions.c.payload).join(db.knowledge_items,
                (db.knowledge_items.c.id == db.knowledge_versions.c.knowledge_id) &
                (db.knowledge_items.c.current_version == db.knowledge_versions.c.version))
            return conn.execute(stmt.where(db.knowledge_items.c.id == knowledge_id)).scalar_one_or_none()

    def append_version(self, knowledge_id, expected_version, changes, validator, reason, audit=None):
        old = self.current(knowledge_id)
        if old is None:
            raise KeyError(knowledge_id)
        if old["version"] != expected_version:
            raise StaleVersion("Knowledge changed; refresh before reviewing")
        allowed = {"claim", "status", "confidence", "evidence", "validation_state", "provenance"}
        if set(changes) - allowed or changes.get("status", old["status"]) not in STATUSES:
            raise ValueError("Invalid version changes")
        payload = {**old, **changes, "version": expected_version + 1,
                   "previous_version": expected_version, "supersedes": f"{knowledge_id}:{expected_version}",
                   "updated_at": now().isoformat(), "validator": validator, "reason": reason}
        payload["normalized_claim"] = normalize_claim(payload["claim"])
        with self.engine.begin() as conn:
            changed = conn.execute(update(db.knowledge_items).where(
                db.knowledge_items.c.id == knowledge_id,
                db.knowledge_items.c.current_version == expected_version).values(current_version=expected_version + 1))
            if changed.rowcount != 1:
                raise StaleVersion("Concurrent knowledge update")
            conn.execute(insert(db.knowledge_versions).values(id=uid(), knowledge_id=knowledge_id,
                version=payload["version"], status=payload["status"],
                normalized_claim=payload["normalized_claim"], payload=payload))
            if audit is not None:
                conn.execute(insert(db.validations).values(id=uid(), knowledge_id=knowledge_id, payload=audit))
        return payload

    def list_knowledge(self, status=None):
        with self.engine.connect() as conn:
            stmt = select(db.knowledge_versions.c.payload).join(db.knowledge_items,
                (db.knowledge_items.c.id == db.knowledge_versions.c.knowledge_id) &
                (db.knowledge_items.c.current_version == db.knowledge_versions.c.version))
            if status:
                stmt = stmt.where(db.knowledge_versions.c.status == status)
            return list(conn.execute(stmt).scalars())

    def add_evidence(self, item):
        payload = item.model_dump(mode="json")
        with self.engine.begin() as conn:
            if not conn.execute(select(db.evidence.c.id).where(db.evidence.c.id == item.evidence_id)).first():
                conn.execute(insert(db.evidence).values(id=item.evidence_id, source=item.source, payload=payload))

    def list_evidence(self):
        with self.engine.connect() as conn:
            return list(conn.execute(select(db.evidence.c.payload)).scalars())

    def save_execution(self, result, question, request):
        with self.engine.begin() as conn:
            conn.execute(insert(db.questions).values(id=result["question_id"], content=question, payload=request))
            conn.execute(insert(db.executions).values(id=result["request_id"], question_id=result["question_id"], payload=result))
            for response in result["responses"]:
                conn.execute(insert(db.responses).values(id=response["response_id"], execution_id=result["request_id"], payload=response))
            for claim in result["claims"]:
                conn.execute(insert(db.claims).values(id=claim["claim_id"], execution_id=result["request_id"], response_id=claim["response_id"], payload=claim))
            for relation in result["relations"]:
                conn.execute(insert(db.relations).values(id=relation["relation_id"], execution_id=result["request_id"], payload=relation))

    def execution(self, request_id):
        with self.engine.connect() as conn:
            return conn.execute(select(db.executions.c.payload).where(db.executions.c.id == request_id)).scalar_one_or_none()
