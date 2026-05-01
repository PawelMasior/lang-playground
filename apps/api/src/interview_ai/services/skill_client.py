from typing import Any

import httpx


class SkillClient:
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    async def call(self, skill_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self._base_url}/v1/skills/{skill_name}",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
