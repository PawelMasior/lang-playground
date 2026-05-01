# API Examples

## Run Interview Agent

Request:

```http
POST /v1/interview/run
Content-Type: application/json

{
  "role": "Backend Engineer",
  "experience_years": 4,
  "topic_focus": ["system design", "python"],
  "user_message": "How should I structure my answer for a design interview question?"
}
```

Response shape:

```json
{
  "plan": "...",
  "answer": "...",
  "follow_up_questions": ["..."],
  "suggested_exercises": ["..."],
  "used_skills": ["question_calibrator"],
  "retrieved_context_chunks": 3
}
```

## Run Skill Directly

Request:

```http
POST /v1/skills/question_calibrator
Content-Type: application/json

{
  "role": "Backend Engineer",
  "experience_years": 5,
  "topics": ["system design"],
  "question": "How to discuss scaling strategy?"
}
```
