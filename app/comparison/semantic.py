import hashlib
import os
import re
from functools import lru_cache

import numpy as np


def canonical(text):
    text = text.lower()
    for pattern, replacement in [
        (r"\b(occurred|took place)\b", "happened"),
        (r"\bduring the year\b", "in"),
        (r"\bfinished\b", "completed"),
    ]:
        text = re.sub(pattern, replacement, text)
    return text


class Embeddings:
    def __init__(self, backend=None, model=None):
        self.backend = backend or os.getenv("EMBEDDING_BACKEND", "hash")
        self.model_id = model or os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        if self.backend == "sentence-transformers":
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(self.model_id)
            self.dimension = self.model.get_sentence_embedding_dimension()
        elif self.backend == "hash":
            self.model = None
            self.dimension = 384
        else:
            raise ValueError("Unknown embedding backend")
        self.method = self.model_id if self.backend != "hash" else "development-hash-ngrams-v1"

    def encode(self, texts):
        if not texts:
            return np.empty((0, self.dimension))
        if self.backend == "hash":
            vectors = np.zeros((len(texts), self.dimension))
            for index, text in enumerate(texts):
                tokens = re.findall(r"\w+", canonical(text))
                features = tokens + [a + " " + b for a, b in zip(tokens, tokens[1:])]
                for feature in features:
                    slot = (
                        int.from_bytes(hashlib.sha256(feature.encode()).digest()[:4], "big") % self.dimension
                    )
                    vectors[index, slot] += 1
                norm = np.linalg.norm(vectors[index])
                if norm:
                    vectors[index] /= norm
            return vectors
        return self.model.encode(texts, normalize_embeddings=True)

    def similarity(self, a, b):
        vectors = self.encode([a, b])
        return float(np.clip(np.dot(vectors[0], vectors[1]), -1, 1))

    def match(self, a, b):
        score = self.similarity(a, b)
        label = "SIMILAR" if score >= 0.82 else "POSSIBLE_MATCH" if score >= 0.45 else "DIFFERENT"
        return {"match": label, "similarity": score, "method": self.method}


@lru_cache(maxsize=4)
def get_embeddings(backend=None):
    return Embeddings(backend)
