from uuid import uuid4

from langsmith import traceable

from interview_ai.agents.graphs.interview_graph import InterviewGraphRunner
from interview_ai.agents.state.interview_state import InterviewGraphState
from interview_ai.core.config import Settings
from interview_ai.integrations.langchain.llm_provider import LlmProvider
from interview_ai.integrations.llamaindex.knowledge_base import StudyKnowledgeBase
from interview_ai.repositories.conversation_repository import ConversationRepository
from interview_ai.schemas.interview import InterviewRequest, InterviewResponse
from interview_ai.services.skill_client import SkillClient


class InterviewService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._kb = StudyKnowledgeBase("evaluations/prompts/notes")
        self._skill_client = SkillClient(settings.skill_server_url)
        self._llm_model = LlmProvider(settings).get_chat_model()
        self._conversation_repo = ConversationRepository(settings.memory_db_path)

        self._graph = InterviewGraphRunner(
            knowledge_search=self._kb.search,
            llm_invoke=self._invoke_llm,
            skill_call=self._skill_client.call,
        )

    def get_graph_mermaid(self) -> str:
        return self._graph.get_mermaid()

    def _invoke_llm(self, messages) -> str:
        response = self._llm_model.invoke(messages)
        return response.content if isinstance(response.content, str) else str(response.content)

    def _build_history_context(self, session_id: str, latest_message: str) -> str:
        recent_messages = self._conversation_repo.fetch_recent_messages(session_id, limit=10)
        if not recent_messages:
            return latest_message

        history = "\n".join(f"{role.title()}: {content}" for role, content in recent_messages)
        return f"Conversation history:\n{history}\n\nLatest user request:\n{latest_message}"

    @traceable(name="interview_service_run")
    async def run(self, request: InterviewRequest) -> InterviewResponse:
        if request.experience_years == 0 and "system design" in {
            topic.lower() for topic in request.topic_focus
        }:
            raise ValueError("System design focus for 0 years experience is too broad.")

        session_id = request.session_id or str(uuid4())
        self._conversation_repo.append_message(session_id, "user", request.user_message)

        enriched_user_message = self._build_history_context(session_id, request.user_message)

        initial_state: InterviewGraphState = {
            "role": request.role,
            "experience_years": request.experience_years,
            "topic_focus": request.topic_focus,
            "user_message": enriched_user_message,
            "retrieved_notes": [],
            "plan": "",
            "answer": "",
            "follow_up_questions": [],
            "suggested_exercises": [],
            "used_skills": [],
        }

        final_state = await self._graph.run(initial_state)
        self._conversation_repo.append_message(session_id, "assistant", final_state["answer"])

        return InterviewResponse(
            plan=final_state["plan"],
            answer=final_state["answer"],
            follow_up_questions=final_state["follow_up_questions"],
            suggested_exercises=final_state["suggested_exercises"],
            used_skills=final_state["used_skills"],
            retrieved_context_chunks=len(final_state["retrieved_notes"]),
            session_id=session_id,
        )
