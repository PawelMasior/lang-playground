# Architecture Decisions

## ADR-001: Separate Skill Server

Context:
Tool-like deterministic logic should be independently testable and deployable.

Decision:
Run skills as a separate FastAPI app.

Consequences:
- Adds network boundary and serialization overhead.
- Improves modularity and reuse for non-agent clients.

## ADR-002: LangGraph For Orchestration

Context:
Need explicit state transitions and composable nodes.

Decision:
Use LangGraph with typed state dictionary and explicit edges.

Consequences:
- Slightly more boilerplate than simple chains.
- Better control over future branching and human-in-the-loop steps.

## ADR-003: LlamaIndex For Retrieval

Context:
Need simple knowledge grounding from local interview notes.

Decision:
Use LlamaIndex vector index over markdown notes.

Consequences:
- Local retrieval quality depends on notes quality.
- Easy to swap in external vector DB later.

## ADR-004: LangSmith For Tracing + Evaluation

Context:
Need observability and experiment tracking for LLM behavior.

Decision:
Decorate service and nodes with `@traceable` and provide eval uploader.

Consequences:
- Requires API key for cloud tracking.
- Strong interview signal for production awareness.
