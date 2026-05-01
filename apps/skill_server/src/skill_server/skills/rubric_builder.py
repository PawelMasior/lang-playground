def run(payload: dict) -> dict:
    role = payload.get("role", "engineer")
    topics = payload.get("topics", [])

    criteria = [
        f"Technical accuracy for {role}",
        "Communication clarity",
        "Problem decomposition",
        "Trade-off reasoning",
    ]

    if topics:
        criteria.append(f"Depth in {topics[0]}")

    return {
        "rubric": [{"criterion": c, "score_range": "1-5"} for c in criteria],
        "pass_threshold": 16,
    }
