def keyword_recall(answer: str, expected_keywords: list[str]) -> float:
    answer_lower = answer.lower()
    if not expected_keywords:
        return 1.0

    matched = sum(1 for kw in expected_keywords if kw.lower() in answer_lower)
    return matched / len(expected_keywords)
