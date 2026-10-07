from abc import ABC, abstractmethod

import httpx
import numpy as np


class VectorStore(ABC):
    @abstractmethod
    def upsert(self, collection, records):
        pass

    @abstractmethod
    def search(self, collection, vector, limit=5):
        pass


class MemoryVectors(VectorStore):
    """Rebuildable development index; SQL remains source of truth."""

    def __init__(self):
        self.collections = {}

    def upsert(self, collection, records):
        target = self.collections.setdefault(collection, {})
        for record in records:
            target[record["id"]] = record

    def search(self, collection, vector, limit=5):
        ranked = [
            {
                "id": record["id"],
                "score": float(np.dot(vector, record["vector"])),
                "payload": record.get("payload", {}),
            }
            for record in self.collections.get(collection, {}).values()
        ]
        return sorted(ranked, key=lambda r: r["score"], reverse=True)[:limit]


class QdrantVectors(VectorStore):
    """REST adapter; indexes identifiers/version metadata, never full SQL records."""

    def __init__(self, url, dimension, api_key=None, client=None):
        self.dimension = dimension
        self.client = client or httpx.Client(
            base_url=url.rstrip("/") + "/", timeout=20, headers={"api-key": api_key} if api_key else {}
        )
        self.ready = set()

    def ensure(self, collection):
        if collection in self.ready:
            return
        response = self.client.get(f"collections/{collection}")
        if response.status_code == 404:
            response = self.client.put(
                f"collections/{collection}", json={"vectors": {"size": self.dimension, "distance": "Cosine"}}
            )
        response.raise_for_status()
        self.ready.add(collection)

    def upsert(self, collection, records):
        self.ensure(collection)
        if records:
            response = self.client.put(
                f"collections/{collection}/points", params={"wait": "true"}, json={"points": records}
            )
            response.raise_for_status()

    def search(self, collection, vector, limit=5):
        self.ensure(collection)
        response = self.client.post(
            f"collections/{collection}/points/query",
            json={"query": list(vector), "limit": limit, "with_payload": True},
        )
        response.raise_for_status()
        return response.json()["result"]["points"]
