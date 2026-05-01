from pydantic import BaseModel, Field, field_validator


class InterviewRequest(BaseModel):
    role: str = Field(min_length=2, max_length=120)
    experience_years: int = Field(ge=0, le=40)
    topic_focus: list[str] = Field(default_factory=list)
    user_message: str = Field(min_length=3, max_length=4000)
    session_id: str | None = Field(default=None, min_length=6, max_length=120)

    @field_validator("topic_focus")
    @classmethod
    def dedupe_topics(cls, value: list[str]) -> list[str]:
        seen: set[str] = set()
        unique: list[str] = []
        for topic in value:
            normalized = topic.strip().lower()
            if normalized and normalized not in seen:
                seen.add(normalized)
                unique.append(topic.strip())
        return unique


class InterviewResponse(BaseModel):
    plan: str
    answer: str
    follow_up_questions: list[str]
    suggested_exercises: list[str]
    used_skills: list[str]
    retrieved_context_chunks: int
    session_id: str | None = None
