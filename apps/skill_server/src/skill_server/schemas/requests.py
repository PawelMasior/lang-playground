from pydantic import BaseModel, Field


class SkillRequest(BaseModel):
    role: str = Field(min_length=2, max_length=120)
    experience_years: int = Field(ge=0, le=40)
    topics: list[str] = Field(default_factory=list)
    question: str = Field(min_length=3, max_length=4000)
