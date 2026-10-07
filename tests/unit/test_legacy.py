from backend.council import parse_ranking_from_text, calculate_aggregate_rankings


def test_rankings_preserved():
    text = "Review\nFINAL RANKING:\n1. Response B\n2. Response A"
    assert parse_ranking_from_text(text) == ["Response B", "Response A"]
    ranks = calculate_aggregate_rankings([{"ranking": text}], {"Response A": "a", "Response B": "b"})
    assert ranks[0]["model"] == "b"
