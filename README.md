# Interview AI Suite

Comprehensive interview-prep sample project using:
- LangChain for prompt/tool orchestration
- LangGraph for stateful multi-step agent flows
- LlamaIndex for knowledge retrieval from study notes
- LangSmith for tracing and evaluation
- SQLite conversation memory for persistent sessions
- Streaming responses over SSE for live UI updates

## Monorepo Layout

- `apps/api`: main agent API (FastAPI + LangGraph)
- `apps/skill_server`: separate skill server app exposing deterministic interview tools
- `packages/shared`: shared DTOs and utilities
- `evaluations`: offline + LangSmith-compatible evaluation runners
- `tests`: unit and integration tests

## Quick Start

1. Create and activate environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -e .[dev]
```

For GUI support, install UI extras:

```powershell
pip install -e .[ui]
```

3. Copy env file and set keys:

```powershell
Copy-Item .env.example .env
```

4. Run skill server:

```powershell
uvicorn skill_server.app:app --reload --port 8010
```

5. Run API:

```powershell
uvicorn interview_ai.main:app --reload --port 8000
```

6. Run tests:

```powershell
pytest
```

7. Run local evaluation:

```powershell
python evaluations/run_eval.py
```

8. Run GUI chat app:

```powershell
streamlit run apps/gui/chat_app.py
```

## Streaming Endpoint

- `POST /v1/interview/stream` returns server-sent events.
- Events: `status`, `answer_chunk`, `final`, and `error`.
- Include `session_id` in requests to persist multi-turn memory across calls.

## LangSmith Setup

Set these environment variables:
- `LANGSMITH_API_KEY`
- `LANGSMITH_PROJECT`
- `LANGSMITH_TRACING=true`

Tracing is enabled automatically when those variables are present.

## Interview Talking Points

- Clear layered architecture (API -> services -> graph/integrations)
- Multi-agent orchestration using LangGraph nodes
- Tool/skill delegation to separate skill server microservice
- Hybrid retrieval via LlamaIndex over local corpus
- Structured outputs + runtime validation with Pydantic
- Observability and experiment tracking with LangSmith
- Test pyramid: unit + integration + eval datasets
