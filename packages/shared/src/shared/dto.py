from dataclasses import dataclass


@dataclass(slots=True)
class EvaluationRecord:
    prompt: str
    expected_keywords: list[str]
    role: str
    experience_years: int
    topic_focus: list[str]
