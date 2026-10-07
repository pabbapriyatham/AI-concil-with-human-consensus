from app.knowledge.store import Store
from app.validation import ReviewService, ReviewRequest
from app.retrieval import RetrievalService
from app.retrieval.service import chunk_text
from app.evidence import EvidenceEngine
from app.claims.schemas import Claim


def test_correction_retrieved_and_rejection_removed():
    store = Store("sqlite:///:memory:", initialize=True)
    item = store.create_knowledge("The event happened in 2020.")
    reviews = ReviewService(store)
    reviews.review(item["knowledge_id"], ReviewRequest(action="CORRECT", expected_version=1, reviewer="human",
                   explanation="Official source", corrected_claim="The event happened in 2021."))
    retrieval = RetrievalService(store)
    results = retrieval.retrieve("The event happened in 2020.")
    assert results[0].text == "The event happened in 2021."
    claim = Claim(response_id="r", model="m", claim_text="The event happened in 2020.",
                  normalized_claim="event", claim_type="temporal")
    assert EvidenceEngine().assess(claim, results[0]).verdict == "CONTRADICTS"
    reviews.review(item["knowledge_id"], ReviewRequest(action="REJECT", expected_version=2,
                   reviewer="human", explanation="Review overturned"))
    assert retrieval.retrieve("The event happened in 2020.") == []


def test_chunks_and_document_retrieval():
    assert chunk_text("a b c d e", words=3, overlap=1) == ["a b c", "c d e", "e"]
    store = Store("sqlite:///:memory:", initialize=True)
    service = RetrievalService(store)
    service.ingest("The Eiffel Tower was completed in 1889.", "supplied record")
    assert service.retrieve("Eiffel Tower completed")[0].source == "supplied record"
