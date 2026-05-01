from pathlib import Path


class PromptRepository:
    def __init__(self, base_dir: str = "evaluations/prompts") -> None:
        self._base_dir = Path(base_dir)

    def list_prompt_files(self) -> list[str]:
        if not self._base_dir.exists():
            return []
        return sorted(str(path) for path in self._base_dir.rglob("*.md"))
