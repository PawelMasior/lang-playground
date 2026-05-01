from dataclasses import dataclass, field


@dataclass(slots=True)
class CandidateProfile:
    role: str
    experience_years: int
    topic_focus: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SkillResult:
    skill_name: str
    payload: dict
