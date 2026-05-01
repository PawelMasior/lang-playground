from fastapi.testclient import TestClient
from skill_server.app import app


def test_skill_endpoint() -> None:
    client = TestClient(app)
    payload = {
        "role": "Backend Engineer",
        "experience_years": 2,
        "topics": ["python"],
        "question": "How to validate input?",
    }

    response = client.post("/v1/skills/question_calibrator", json=payload)
    assert response.status_code == 200

    body = response.json()
    assert body["skill_name"] == "question_calibrator"
    assert "result" in body
