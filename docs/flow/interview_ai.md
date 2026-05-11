# Interview AI API: File Guide and Runtime Flow

This document explains what each file in apps/api/src/interview_ai is for, how the modules connect, and what happens during a request.

## High-Level Purpose

The package implements a FastAPI backend for interview coaching. It combines:
- request validation and HTTP routing,
- a LangGraph pipeline,
- retrieval from local markdown notes,
- a call to an external skill server,
- and conversation memory persisted in SQLite.

## End-to-End Request Flow

1. Request reaches API router
- POST /v1/interview/run for regular JSON response.
- POST /v1/interview/stream for SSE streaming response.

2. Input is validated by Pydantic schemas
- role, experience_years, topic_focus, user_message, session_id.

3. InterviewService orchestrates the run
- applies business guardrails,
- appends user message to conversation memory,
- enriches current user message with recent history.

4. LangGraph executes nodes in sequence
- retrieve_context -> build_plan -> skill_enrichment -> generate_answer.

5. Service stores assistant answer and returns InterviewResponse
- plus metadata such as retrieved_context_chunks and used_skills.

## Package Root

### apps/api/src/interview_ai/__init__.py
- Package marker file.
- Exposes the module namespace.

### apps/api/src/interview_ai/main.py
- FastAPI entrypoint.
- Loads settings and configures LangSmith environment variables.
- Registers routers:
	- /health
	- /v1/interview
	- /graph

## API Layer

### apps/api/src/interview_ai/api/__init__.py
- Package marker for API submodule.

### apps/api/src/interview_ai/api/routers/__init__.py
- Package marker for routers.

### apps/api/src/interview_ai/api/routers/health.py
- Minimal health endpoint.
- Used by probes and local sanity checks.

### apps/api/src/interview_ai/api/routers/interview.py
- Main HTTP interface for agent execution.
- Dependency-injects InterviewService per request using settings.
- /run path:
	- executes service.run and returns InterviewResponse.
	- maps business ValueError to HTTP 400.
- /stream path:
	- emits SSE events: status, answer_chunk, final.
	- chunks answer text into word-based fragments.
	- emits structured error events on validation/business/internal failures.

### apps/api/src/interview_ai/api/routers/graph.py
- Debug/observability route for graph visualization.
- Calls service.get_graph_mermaid() and renders Mermaid HTML in-browser.
- Purpose: quickly inspect the current node topology without opening code.

## Core Configuration

### apps/api/src/interview_ai/core/__init__.py
- Package marker for core utilities.

### apps/api/src/interview_ai/core/config.py
- Centralized environment-backed settings object.
- Reads .env via pydantic-settings.
- Key settings:
	- OPENAI_API_KEY, OPENAI_MODEL
	- API_HOST, API_PORT
	- SKILL_SERVER_URL
	- MEMORY_DB_PATH
	- LANGSMITH_* values
- get_settings() is cached so the parsed settings object is reused.

## Observability

### apps/api/src/interview_ai/observability/__init__.py
- Package marker.

### apps/api/src/interview_ai/observability/langsmith_setup.py
- Sets process environment variables used by OpenAI and LangSmith clients.
- Enables tracing only when LangSmith key is configured.
- Purpose: trace graph nodes/service runs without changing business code.

## Schemas

### apps/api/src/interview_ai/schemas/__init__.py
- Package marker.

### apps/api/src/interview_ai/schemas/interview.py
- Request and response contracts for interview endpoints.
- InterviewRequest validation:
	- user_message minimum length,
	- numeric bounds for experience_years,
	- dedupe/normalize topic_focus list.
- InterviewResponse defines the stable response payload for both run and stream final metadata.

## Graph: State, Nodes, Wiring

### apps/api/src/interview_ai/agents/__init__.py
- Package marker.

### apps/api/src/interview_ai/agents/state/__init__.py
- Package marker.

### apps/api/src/interview_ai/agents/state/interview_state.py
- TypedDict contract used by graph nodes.
- Defines required keys passed between steps:
	- role, experience_years, topic_focus, user_message
	- retrieved_notes, plan, answer
	- follow_up_questions, suggested_exercises, used_skills
	- optional skill_payload

### apps/api/src/interview_ai/agents/nodes/__init__.py
- Package marker.

### apps/api/src/interview_ai/agents/nodes/interview_nodes.py
- Implements each graph node function.
- retrieve_context_node:
	- builds retrieval query from role/topics/user_message,
	- fetches notes from knowledge_search.
- build_plan_node:
	- formats planner prompt,
	- calls llm_invoke,
	- stores plan text.
- skill_enrichment_node:
	- builds payload with role, experience_years, topics, question,
	- calls skill server question_calibrator,
	- records used skill and returned skill_payload.
- answer_generation_node:
	- formats answer prompt,
	- calls llm,
	- parses sections ANSWER, FOLLOW_UP, EXERCISES,
	- applies defaults if parsing yields empty lists.
- Includes small helper parser _extract_list_section.
- Node functions are annotated with @traceable for LangSmith spans.

### apps/api/src/interview_ai/agents/graphs/__init__.py
- Package marker.

### apps/api/src/interview_ai/agents/graphs/interview_graph.py
- Declares graph topology and compiles it.
- Injects concrete adapters for retrieval, llm invocation, and skill calls.
- Graph path is linear:
	- START -> retrieve_context -> build_plan -> skill_enrichment -> generate_answer -> END
- Exposes:
	- run(initial_state): asynchronous graph execution,
	- get_mermaid(): Mermaid diagram text for visualization endpoint.

## Service Layer

### apps/api/src/interview_ai/services/__init__.py
- Package marker.

### apps/api/src/interview_ai/services/interview_service.py
- Main orchestration unit for business logic.
- Responsibilities:
	- initialize dependencies (KB, skill client, LLM, repository, graph),
	- enforce business guardrail for beginner + system design combination,
	- create/reuse session_id,
	- append user/assistant messages to memory DB,
	- build conversation history context,
	- map final graph state to InterviewResponse.
- Also exposes get_graph_mermaid for /graph/mermaid route.

### apps/api/src/interview_ai/services/skill_client.py
- Thin async HTTP client for external skill server.
- Calls /v1/skills/{skill_name} with a JSON payload.
- Raises on non-2xx responses.
- Purpose: keep transport logic isolated from node/business code.

## Integration Adapters

### apps/api/src/interview_ai/integrations/__init__.py
- Package marker.

### apps/api/src/interview_ai/integrations/langchain/__init__.py
- Package marker.

### apps/api/src/interview_ai/integrations/langchain/prompting.py
- Prompt templates used by planning and answer nodes.
- Keeps prompt text centralized for easy iteration and testing.

### apps/api/src/interview_ai/integrations/langchain/llm_provider.py
- Builds ChatOpenAI model instance from settings.
- Validates API key presence.
- Central place for model and temperature defaults.

### apps/api/src/interview_ai/integrations/langgraph/__init__.py
- Package marker for future langgraph-specific helpers.

### apps/api/src/interview_ai/integrations/llamaindex/__init__.py
- Package marker.

### apps/api/src/interview_ai/integrations/llamaindex/knowledge_base.py
- Local RAG adapter over markdown files.
- Loads notes from evaluations/prompts/notes.
- Builds in-memory VectorStoreIndex on first query.
- Runs similarity search (top_k=4) and returns context chunks for prompts.
- Returns fallback message when no notes are present.

## Persistence / Repositories

### apps/api/src/interview_ai/repositories/__init__.py
- Package marker.

### apps/api/src/interview_ai/repositories/conversation_repository.py
- SQLite persistence for chat memory.
- Ensures schema exists at startup.
- Thread-safe writes via lock.
- Reads most recent N messages for context stitching.

### apps/api/src/interview_ai/repositories/prompt_repository.py
- Utility for listing markdown prompt files under evaluations/prompts.
- Not currently used by the live request path, but useful for tooling/admin scenarios.

## Domain Models

### apps/api/src/interview_ai/domain/__init__.py
- Package marker.

### apps/api/src/interview_ai/domain/models.py
- Dataclasses for domain-oriented structures:
	- CandidateProfile
	- SkillResult
- Currently lightly used; intended as typed domain entities for future expansion.

## What each major piece is for

- Routers: HTTP protocol handling and transport-level concerns.
- Schemas: strict request/response contracts.
- Service: orchestration and business rules.
- Graph + nodes: deterministic pipeline of reasoning steps.
- Integrations: adapters to external frameworks/services.
- Repositories: persistence and data access.
- Observability: tracing and runtime diagnostics.

This separation keeps the system testable: each layer has one job, and dependencies are passed down rather than hard-coded inside node logic.
