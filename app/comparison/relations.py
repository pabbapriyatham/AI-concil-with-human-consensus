import os
import re
from itertools import combinations
from typing import Literal
from pydantic import Field
from app.schemas import StrictModel, uid
from app.claims.normalizer import normalize_claim
from .semantic import canonical, get_embeddings

RelationType = Literal["SUPPORT", "ENTAILMENT", "AGREEMENT", "PARTIAL_AGREEMENT",
                       "NEUTRAL", "DIVERGENCE", "CONTRADICTION", "DUPLICATE", "UNSUPPORTED"]


class Relation(StrictModel):
    relation_id: str = Field(default_factory=uid)
    source_claim: str
    target_claim: str
    relation_type: RelationType
    confidence: float = Field(ge=0, le=1)
    method: str
    provenance: dict = Field(default_factory=dict)


def structured(a, b):
    """Only compare values when subjects AND predicate skeletons match."""
    a, b = normalize_claim(canonical(a)), normalize_claim(canonical(b))
    if a == b:
        return "AGREEMENT", 1.0
    if re.sub(r"\b(?:not|never)\s*", "", a) == re.sub(r"\b(?:not|never)\s*", "", b):
        return "CONTRADICTION", 0.9
    nums_a, nums_b = re.findall(r"\b\d+(?:\.\d+)?\b", a), re.findall(r"\b\d+(?:\.\d+)?\b", b)
    if nums_a and nums_b and nums_a != nums_b:
        skeleton_a = re.sub(r"\b\d+(?:\.\d+)?\b", "<value>", a)
        skeleton_b = re.sub(r"\b\d+(?:\.\d+)?\b", "<value>", b)
        # Different quantities/ranges/comparators are not automatically contradictions.
        if skeleton_a == skeleton_b and not re.search(r"\b(about|approximately|between|at least|over|under|may)\b", a + " " + b):
            return "CONTRADICTION", 0.9
    pattern = r"(.+? (?:is|was) (?:located|situated) in) (.+)"
    ma, mb = re.fullmatch(pattern, a), re.fullmatch(pattern, b)
    if ma and mb and ma[1] == mb[1] and ma[2] != mb[2]:
        # Cities vs countries can both be true; leave to NLI instead.
        return "DIVERGENCE", 0.6
    return None


class NLI:
    """Model card: named labels, never infer opaque LABEL_0 order."""
    def __init__(self, classifier=None):
        self.model_id = os.getenv("NLI_MODEL", "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli")
        if classifier is None:
            from transformers import pipeline
            classifier = pipeline("text-classification", model=self.model_id)
        self.classifier = classifier

    def predict(self, premise, hypothesis):
        scores = self.classifier({"text": premise, "text_pair": hypothesis}, top_k=None)
        if scores and isinstance(scores[0], list):
            scores = scores[0]
        winner = max(scores, key=lambda x: x["score"])
        label = winner["label"].lower()
        labels = {"entailment": "ENTAILMENT", "neutral": "NEUTRAL", "contradiction": "CONTRADICTION"}
        if label not in labels:
            raise ValueError("NLI model must provide named entailment/neutral/contradiction labels")
        return labels[label], float(winner["score"])


class RelationEngine:
    def __init__(self, embeddings=None, nli=None):
        self.embeddings = embeddings or get_embeddings()
        self.nli = nli
        if nli is None and os.getenv("NLI_BACKEND", "structured") == "transformers":
            self.nli = NLI()

    def compare_text(self, a, b):
        relation = structured(a, b)
        if relation:
            return *relation, "structured-v1"
        match = self.embeddings.match(a, b)
        if match["match"] == "DIFFERENT":
            return "NEUTRAL", 0.5, self.embeddings.method
        if self.nli:
            kind, score = self.nli.predict(a, b)
            return kind, score, self.nli.model_id
        # Similarity alone does not prove factual equivalence.
        return ("PARTIAL_AGREEMENT" if match["match"] == "SIMILAR" else "DIVERGENCE",
                min(0.65, max(0.0, match["similarity"])), self.embeddings.method)

    def graph(self, claims):
        edges = []
        for a, b in combinations(claims, 2):
            if a.response_id == b.response_id:
                continue
            kind, score, method = self.compare_text(a.claim_text, b.claim_text)
            if kind != "NEUTRAL":
                edges.append(Relation(source_claim=a.claim_id, target_claim=b.claim_id,
                                      relation_type=kind, confidence=score, method=method,
                                      provenance={"models": [a.model, b.model], "direction": "source_to_target"}))
        return edges
