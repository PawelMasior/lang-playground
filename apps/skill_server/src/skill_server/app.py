from fastapi import FastAPI

from skill_server.core.registry import skill_registry
from skill_server.schemas.requests import SkillRequest

app = FastAPI(title="Interview Skill Server", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/skills/{skill_name}")
def execute_skill(skill_name: str, payload: SkillRequest) -> dict:
    skill = skill_registry.get(skill_name)
    if not skill:
        return {
            "skill_name": skill_name,
            "error": "unknown skill",
            "available_skills": sorted(skill_registry.keys()),
        }

    return {
        "skill_name": skill_name,
        "result": skill(payload.model_dump()),
    }
