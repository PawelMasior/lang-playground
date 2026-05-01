from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

from interview_ai.core.config import Settings


class LlmProvider:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def get_chat_model(self) -> BaseChatModel:
        if not self._settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for LLM-backed flow.")

        return ChatOpenAI(
            model=self._settings.openai_model,
            api_key=self._settings.openai_api_key,
            temperature=0.2,
        )
