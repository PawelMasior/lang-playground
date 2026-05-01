from langsmith import traceable

from interview_ai.agents.state.interview_state import InterviewGraphState
from interview_ai.integrations.langchain.prompting import ANSWER_PROMPT, PLANNER_PROMPT


@traceable(name="retrieve_context_node")
def retrieve_context_node(
    state: InterviewGraphState,
    knowledge_search: callable,
) -> InterviewGraphState:
    query = f"{state['role']} {' '.join(state['topic_focus'])} {state['user_message']}"
    notes = knowledge_search(query)
    state["retrieved_notes"] = notes
    return state


@traceable(name="build_plan_node")
def build_plan_node(
    state: InterviewGraphState,
    llm_invoke: callable,
) -> InterviewGraphState:
    prompt = PLANNER_PROMPT.format_messages(
        role=state["role"],
        experience_years=state["experience_years"],
        topic_focus=", ".join(state["topic_focus"]) or "general",
        user_message=state["user_message"],
        context="\n".join(state["retrieved_notes"]),
    )
    state["plan"] = llm_invoke(prompt)
    return state


@traceable(name="skill_enrichment_node")
async def skill_enrichment_node(
    state: InterviewGraphState,
    skill_call: callable,
) -> InterviewGraphState:
    payload = {
        "role": state["role"],
        "experience_years": state["experience_years"],
        "topics": state["topic_focus"],
        "question": state["user_message"],
    }
    result = await skill_call("question_calibrator", payload)
    state["used_skills"] = ["question_calibrator"]
    state["skill_payload"] = result
    return state


def _extract_list_section(lines: list[str], section: str) -> list[str]:
    capture = False
    values: list[str] = []
    for line in lines:
        marker = line.strip().upper()
        if marker.startswith(f"{section}:"):
            capture = True
            continue
        if capture and marker.endswith(":") and marker[:-1] in {"ANSWER", "FOLLOW_UP", "EXERCISES"}:
            break
        if capture and line.strip().startswith("-"):
            values.append(line.strip().lstrip("-").strip())
    return values


@traceable(name="answer_generation_node")
def answer_generation_node(
    state: InterviewGraphState,
    llm_invoke: callable,
) -> InterviewGraphState:
    prompt = ANSWER_PROMPT.format_messages(
        role=state["role"],
        experience_years=state["experience_years"],
        topic_focus=", ".join(state["topic_focus"]) or "general",
        user_message=state["user_message"],
        plan=state["plan"],
        context="\n".join(state["retrieved_notes"]),
    )
    raw = llm_invoke(prompt)

    lines = raw.splitlines()
    answer_start = raw.find("ANSWER:")
    follow_start = raw.find("FOLLOW_UP:")

    if answer_start >= 0 and follow_start > answer_start:
        answer = raw[answer_start + len("ANSWER:"):follow_start].strip()
    else:
        answer = raw.strip()

    state["answer"] = answer
    state["follow_up_questions"] = _extract_list_section(lines, "FOLLOW_UP")[:3]
    state["suggested_exercises"] = _extract_list_section(lines, "EXERCISES")[:3]

    if not state["follow_up_questions"]:
        state["follow_up_questions"] = ["Can you explain your trade-offs in this solution?"]
    if not state["suggested_exercises"]:
        state["suggested_exercises"] = ["Implement a minimal version with tests."]

    return state
