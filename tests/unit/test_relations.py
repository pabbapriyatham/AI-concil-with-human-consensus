from app.comparison.relations import NLI, RelationEngine
from app.comparison.semantic import Embeddings


def test_date_contradiction_and_neutral():
    engine = RelationEngine(Embeddings("hash"))
    assert (
        engine.compare_text("The tower was completed in 1889.", "The tower was completed in 1888.")[0]
        == "CONTRADICTION"
    )
    assert engine.compare_text("Paris is not in France.", "Paris is in France.")[0] == "CONTRADICTION"
    assert (
        engine.compare_text("The tower was completed in 1889.", "The bridge was completed in 1888.")[0]
        != "CONTRADICTION"
    )
    assert (
        engine.compare_text("The tower is 300 metres tall.", "The tower is 330 feet tall.")[0]
        != "CONTRADICTION"
    )
    assert engine.compare_text("Cats are animals.", "A river flows east.")[0] == "NEUTRAL"


def test_nli_named_labels():
    nli = NLI(
        lambda *a, **k: [{"label": "contradiction", "score": 0.91}, {"label": "neutral", "score": 0.09}]
    )
    assert nli.predict("a", "b") == ("CONTRADICTION", 0.91)
