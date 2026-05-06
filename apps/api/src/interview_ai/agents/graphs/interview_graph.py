from collections.abc import Awaitable, Callable
from typing import Any

from langgraph.graph import END, START, StateGraph

from interview_ai.agents.nodes.interview_nodes import (
    answer_generation_node,
    build_plan_node,
    retrieve_context_node,
    skill_enrichment_node,
)
from interview_ai.agents.state.interview_state import InterviewGraphState


class InterviewGraphRunner:
    def __init__(
        self,
        knowledge_search: Callable[[str], list[str]],
        llm_invoke: Callable[[list[Any]], str],
        skill_call: Callable[[str, dict[str, Any]], Awaitable[dict[str, Any]]],
    ) -> None:
        self._knowledge_search = knowledge_search
        self._llm_invoke = llm_invoke
        self._skill_call = skill_call
        self._graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(InterviewGraphState)

        async def skill_enrichment_step(state: InterviewGraphState) -> InterviewGraphState:
            return await skill_enrichment_node(state, self._skill_call)

        graph.add_node(
            "retrieve_context",
            lambda state: retrieve_context_node(state, self._knowledge_search),
        )
        graph.add_node(
            "build_plan",
            lambda state: build_plan_node(state, self._llm_invoke),
        )
        graph.add_node(
            "skill_enrichment",
            skill_enrichment_step,
        )
        graph.add_node(
            "generate_answer",
            lambda state: answer_generation_node(state, self._llm_invoke),
        )

        graph.add_edge(START, "retrieve_context")
        graph.add_edge("retrieve_context", "build_plan")
        graph.add_edge("build_plan", "skill_enrichment")
        graph.add_edge("skill_enrichment", "generate_answer")
        graph.add_edge("generate_answer", END)

        return graph.compile()

    def get_mermaid(self) -> str:
        return self._graph.get_graph().draw_mermaid()

    async def run(self, initial_state: InterviewGraphState) -> InterviewGraphState:
        result = await self._graph.ainvoke(initial_state)
        return result
