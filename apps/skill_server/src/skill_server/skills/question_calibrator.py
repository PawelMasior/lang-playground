def run(payload: dict) -> dict:
    years = int(payload.get("experience_years", 0))
    topics = payload.get("topics", [])

    seniority = "junior"
    if years >= 7:
        seniority = "senior"
    elif years >= 3:
        seniority = "mid"

    difficulty = "easy"
    if seniority == "mid":
        difficulty = "medium"
    if seniority == "senior":
        difficulty = "hard"

    return {
        "seniority": seniority,
        "difficulty": difficulty,
        "recommended_depth": "concept + trade-offs + implementation",
        "focus_topics": topics[:5],
    }
