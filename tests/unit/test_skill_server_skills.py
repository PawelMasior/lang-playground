from skill_server.skills.question_calibrator import run as calibrator


def test_question_calibrator_mid_level() -> None:
    payload = {
        "role": "Backend Engineer",
        "experience_years": 4,
        "topics": ["system design"],
        "question": "How to design cache?",
    }
    result = calibrator(payload)

    assert result["seniority"] == "mid"
    assert result["difficulty"] == "medium"
