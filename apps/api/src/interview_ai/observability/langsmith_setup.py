import os

from interview_ai.core.config import Settings


def configure_langsmith(settings: Settings) -> None:
    if settings.openai_api_key:
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key

    if not settings.langsmith_api_key:
        return

    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    os.environ["LANGSMITH_TRACING"] = "true" if settings.langsmith_tracing else "false"
