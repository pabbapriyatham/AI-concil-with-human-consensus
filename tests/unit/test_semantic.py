from app.comparison.semantic import Embeddings


def test_embedding_candidates():
    engine = Embeddings("hash")
    assert engine.match("The event happened in 2020.", "The event occurred during the year 2020.")["match"] == "SIMILAR"
    assert engine.match("The event happened in 2020.", "Apples contain dietary fibre.")["match"] == "DIFFERENT"
    assert "development" in engine.method
    assert engine.encode(["hello"]).shape == (1, 384)
