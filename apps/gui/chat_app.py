import json
import os
import uuid
from typing import Any

import httpx
import streamlit as st

DEFAULT_API_URL = os.getenv("GUI_API_URL", "http://127.0.0.1:8000/v1/interview/run")
DEFAULT_STREAM_URL = os.getenv("GUI_STREAM_API_URL", "http://127.0.0.1:8000/v1/interview/stream")


def _render_sidebar() -> tuple[str, int, list[str], str, str, bool]:
    st.sidebar.header("Interview Context")
    role = st.sidebar.text_input("Role", value="Backend Engineer")
    experience_years = st.sidebar.slider("Experience (years)", min_value=0, max_value=20, value=4)
    topic_input = st.sidebar.text_input("Topics (comma separated)", value="system design, python")
    api_url = st.sidebar.text_input("API URL", value=DEFAULT_API_URL)
    stream_api_url = st.sidebar.text_input("Streaming API URL", value=DEFAULT_STREAM_URL)
    use_streaming = st.sidebar.checkbox("Use streaming", value=True)

    if "chat_session_id" not in st.session_state:
        st.session_state.chat_session_id = str(uuid.uuid4())
    session_id = st.sidebar.text_input("Session ID", value=st.session_state.chat_session_id)
    st.session_state.chat_session_id = session_id

    topics = [item.strip() for item in topic_input.split(",") if item.strip()]
    return role, experience_years, topics, api_url, stream_api_url, use_streaming


def _call_agent(api_url: str, payload: dict[str, Any]) -> dict[str, Any]:
    with httpx.Client(timeout=90.0) as client:
        response = client.post(api_url, json=payload)
        response.raise_for_status()
        return response.json()


def _stream_agent(stream_api_url: str, payload: dict[str, Any]):
    with httpx.Client(timeout=120.0) as client:
        with client.stream("POST", stream_api_url, json=payload) as response:
            response.raise_for_status()

            current_event = "message"
            for line in response.iter_lines():
                if not line:
                    continue
                if line.startswith("event: "):
                    current_event = line.replace("event: ", "", 1).strip()
                    continue
                if line.startswith("data: "):
                    payload_text = line.replace("data: ", "", 1).strip()
                    yield current_event, payload_text


def _init_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []


def main() -> None:
    st.set_page_config(page_title="Interview Agent Chat", page_icon="AI", layout="wide")
    st.title("Interview Agent Chat")
    st.caption("Local GUI for your LangGraph interview agent")

    role, experience_years, topics, api_url, stream_api_url, use_streaming = _render_sidebar()
    _init_state()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_text = st.chat_input("Ask interview preparation question...")
    if not user_text:
        return

    trimmed_text = user_text.strip()
    if len(trimmed_text) < 3:
        st.warning("Message must be at least 3 characters long.")
        return

    if experience_years == 0 and any(topic.strip().lower() == "system design" for topic in topics):
        st.warning(
            "For 0 years of experience, remove 'system design' from topics or increase experience."
        )
        return

    st.session_state.messages.append({"role": "user", "content": trimmed_text})
    with st.chat_message("user"):
        st.markdown(trimmed_text)

    payload = {
        "role": role,
        "experience_years": experience_years,
        "topic_focus": topics,
        "user_message": trimmed_text,
        "session_id": st.session_state.chat_session_id,
    }

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                if use_streaming:
                    answer_parts: list[str] = []
                    meta: dict[str, Any] = {}
                    answer_placeholder = st.empty()

                    for event_name, raw_data in _stream_agent(stream_api_url, payload):
                        data = json.loads(raw_data)

                        if event_name == "answer_chunk":
                            answer_parts.append(data.get("text", ""))
                            answer_placeholder.markdown(" ".join(answer_parts).strip())
                        elif event_name == "final":
                            meta = data
                        elif event_name == "error":
                            raise httpx.HTTPError(data.get("detail", "Unknown stream error"))

                    answer = " ".join(answer_parts).strip() or "No answer returned."
                    plan = str(meta.get("plan", ""))
                    follow_up = list(meta.get("follow_up_questions", []))
                    exercises = list(meta.get("suggested_exercises", []))
                    used_skills = list(meta.get("used_skills", []))
                    st.session_state.chat_session_id = str(
                        meta.get("session_id", st.session_state.chat_session_id)
                    )
                else:
                    result = _call_agent(api_url, payload)
                    answer = result.get("answer", "No answer returned.")
                    plan = result.get("plan", "")
                    follow_up = result.get("follow_up_questions", [])
                    exercises = result.get("suggested_exercises", [])
                    used_skills = result.get("used_skills", [])
                    st.session_state.chat_session_id = str(
                        result.get("session_id", st.session_state.chat_session_id)
                    )
            except httpx.HTTPError as exc:
                st.error(f"Request failed: {exc}")
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": f"Request failed: {exc}",
                    }
                )
                return

            st.markdown("### Answer")
            st.markdown(answer)

            if plan:
                with st.expander("Plan", expanded=False):
                    st.markdown(plan)

            if follow_up:
                st.markdown("### Follow-up Questions")
                for item in follow_up:
                    st.markdown(f"- {item}")

            if exercises:
                st.markdown("### Suggested Exercises")
                for item in exercises:
                    st.markdown(f"- {item}")

            if used_skills:
                st.caption("Skills used: " + ", ".join(used_skills))

            transcript = "\n\n".join(
                [
                    "Assistant answer:",
                    answer,
                    "Plan:",
                    plan,
                ]
            )
            st.session_state.messages.append({"role": "assistant", "content": transcript})


if __name__ == "__main__":
    main()
