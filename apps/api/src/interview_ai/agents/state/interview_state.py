from typing import NotRequired, TypedDict


class InterviewGraphState(TypedDict):
    role: str
    experience_years: int
    topic_focus: list[str]
    user_message: str
    retrieved_notes: list[str]
    plan: str
    answer: str
    follow_up_questions: list[str]
    suggested_exercises: list[str]
    used_skills: list[str]
    skill_payload: NotRequired[dict]
