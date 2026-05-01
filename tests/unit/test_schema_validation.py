from interview_ai.schemas.interview import InterviewRequest


def test_topic_dedupe() -> None:
    req = InterviewRequest(
        role="Backend Engineer",
        experience_years=3,
        topic_focus=["Python", "python", " API "],
        user_message="How should I prepare?",
    )

    assert req.topic_focus == ["Python", "API"]
