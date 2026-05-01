from evaluations.metrics.keyword_recall import keyword_recall


def test_keyword_recall() -> None:
    answer = "Discuss requirements and scalability trade-offs clearly."
    expected = ["requirements", "trade-offs", "scalability", "latency"]

    score = keyword_recall(answer, expected)
    assert score == 0.75
