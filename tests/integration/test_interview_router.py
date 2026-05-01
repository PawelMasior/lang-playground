from fastapi.testclient import TestClient
from interview_ai.api.routers.interview import get_service
from interview_ai.main import app
from interview_ai.schemas.interview import InterviewRequest, InterviewResponse


class FakeInterviewService:
    async def run(self, request: InterviewRequest) -> InterviewResponse:
        return InterviewResponse(
            plan=f"Plan for {request.role}",
            answer="Use structure, clarity, and trade-off framing.",
            follow_up_questions=[
                "What assumptions are you making?",
                "How would you scale this?",
                "What would you monitor?",
            ],
            suggested_exercises=[
                "Design a rate limiter.",
                "Write validation tests.",
                "Explain API versioning strategy.",
            ],
            used_skills=["question_calibrator"],
            retrieved_context_chunks=2,
            session_id=request.session_id or "test-session",
        )


def test_interview_endpoint_with_override() -> None:
    app.dependency_overrides[get_service] = lambda: FakeInterviewService()
    client = TestClient(app)

    payload = {
        "role": "Backend Engineer",
        "experience_years": 3,
        "topic_focus": ["python", "apis"],
        "user_message": "How to answer architecture questions?",
        "session_id": "session-a",
    }

    response = client.post("/v1/interview/run", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["used_skills"] == ["question_calibrator"]
    assert body["retrieved_context_chunks"] == 2
    assert body["session_id"] == "session-a"

    app.dependency_overrides.clear()


def test_interview_stream_endpoint_with_override() -> None:
    app.dependency_overrides[get_service] = lambda: FakeInterviewService()
    client = TestClient(app)

    payload = {
        "role": "Backend Engineer",
        "experience_years": 3,
        "topic_focus": ["python", "apis"],
        "user_message": "How to answer architecture questions?",
        "session_id": "session-stream",
    }

    response = client.post("/v1/interview/stream", json=payload)
    assert response.status_code == 200
    assert "event: answer_chunk" in response.text
    assert "event: final" in response.text

    app.dependency_overrides.clear()
