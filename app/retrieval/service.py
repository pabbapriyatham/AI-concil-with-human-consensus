import hashlib
import os

from app.comparison.semantic import get_embeddings
from app.evidence.schemas import Evidence

from .vectors import MemoryVectors, QdrantVectors


def chunk_text(text, words=180, overlap=30):
    if words <= overlap or overlap < 0:
        raise ValueError("Chunk size must exceed nonnegative overlap")
    tokens = text.split()
    return [" ".join(tokens[start : start + words]) for start in range(0, len(tokens), words - overlap)]


class RetrievalService:
    def __init__(self, store, embeddings=None, vectors=None):
        self.store = store
        self.embeddings = embeddings or get_embeddings()
        self.vectors = vectors or (
            QdrantVectors(os.getenv("QDRANT_URL"), self.embeddings.dimension, os.getenv("QDRANT_API_KEY"))
            if os.getenv("QDRANT_URL")
            else MemoryVectors()
        )
        suffix = hashlib.sha256(self.embeddings.method.encode()).hexdigest()[:8]
        self.collections = {
            kind: f"mahthildis_{kind}_{suffix}" for kind in ["evidence", "knowledge", "claims"]
        }

    def ingest(self, text, source, source_type="document", quality=0.5, url=None):
        items = []
        for index, chunk in enumerate(chunk_text(text)):
            item = Evidence(
                text=chunk,
                source=source,
                source_type=source_type,
                source_quality=quality,
                url=url,
                provenance={"chunk_index": index, "ingestion": "text-chunk-v1"},
            )
            self.store.add_evidence(item)
            items.append(item)
        return items

    def retrieve(self, query, limit=5, minimum=0.2):
        documents = [Evidence.model_validate(p) for p in self.store.list_evidence()]
        knowledge = self.store.list_knowledge("VALIDATED")
        memory = [
            Evidence(
                evidence_id=k["knowledge_id"],
                text=k["claim"],
                source=f"human-validated knowledge {k['knowledge_id']} version {k['version']}",
                source_type="knowledge",
                source_quality=0.95,
                provenance={
                    "knowledge_id": k["knowledge_id"],
                    "version": k["version"],
                    "status": k["status"],
                    "validator": k["validator"],
                    "reason": k["reason"],
                    "evidence": k["evidence"],
                },
            )
            for k in knowledge
        ]
        items = {"evidence": documents, "knowledge": memory}
        query_vector = self.embeddings.encode([query])[0]
        result = []
        for kind, group in items.items():
            vectors = self.embeddings.encode([e.text for e in group])
            self.vectors.upsert(
                self.collections[kind],
                [
                    {
                        "id": e.evidence_id,
                        "vector": vector.tolist(),
                        "payload": {
                            "version": e.provenance.get("version"),
                            "embedding": self.embeddings.method,
                        },
                    }
                    for e, vector in zip(group, vectors)
                ],
            )
            current = {e.evidence_id: e for e in group}
            # Overfetch stale IDs; only current SQL-backed validated items are accepted.
            for hit in self.vectors.search(self.collections[kind], query_vector, limit * 3):
                item = current.get(str(hit["id"]))
                if item is None or hit["score"] < minimum:
                    continue
                if kind == "knowledge" and hit["payload"].get("version") != item.provenance["version"]:
                    continue
                result.append(item.model_copy(update={"relevance_score": min(1, max(0, hit["score"]))}))
        return sorted(result, key=lambda e: e.relevance_score, reverse=True)[: limit * 2]
