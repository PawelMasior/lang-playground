# Conversation Flow and Context Retrieval

This document explains how the interview agent maintains conversational context across multiple turns and how it retrieves relevant knowledge to ground its responses.

---

## Overview

Two distinct context sources are combined before every LLM call:

1. **Conversation memory** — prior turns from the current session, stored in SQLite.
2. **Knowledge retrieval** — relevant chunks from curated markdown notes, fetched via LlamaIndex vector search.

Both are merged into `state["user_message"]` and `state["retrieved_notes"]` before any LLM prompt is formatted.

---

## Part 1 — Conversation Memory

### Storage

**File:** `apps/api/src/interview_ai/repositories/conversation_repository.py`

Every user/assistant exchange is persisted in SQLite at `data/interview_memory.db` (path configurable via `MEMORY_DB_PATH`).

Schema:
```sql
CREATE TABLE conversation_messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT NOT NULL,
    role        TEXT NOT NULL,
    content     TEXT NOT NULL,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

Thread safety: all writes go through a `threading.Lock` to prevent concurrent write corruption in the same process.

---

### Write path

**File:** `apps/api/src/interview_ai/services/interview_service.py` — `run()`

```
1. User message arrives
   └── append_message(session_id, "user", user_message)

2. Graph executes and produces an answer
   └── append_message(session_id, "assistant", answer)
```

Both writes happen around the graph call, not inside it. The graph itself has no awareness of SQLite.

---

### Read path — history stitching

After the new user message is stored, the last 10 rows for the session are fetched:

```python
recent_messages = self._conversation_repo.fetch_recent_messages(session_id, limit=10)
```

**File:** `apps/api/src/interview_ai/repositories/conversation_repository.py` — `fetch_recent_messages()`

The query orders by `id DESC LIMIT 10`, then reverses in Python to restore chronological order.

The messages are formatted and prepended to the current user input:

```
Conversation history:
User: <oldest kept turn>
Assistant: <response>
User: <next turn>
Assistant: <response>
...

Latest user request:
<current message>
```

This enriched string becomes `state["user_message"]` — the LLM receives full session context without any graph-level memory mechanism.

---

### Session identity

`session_id` is a string sent by the client or auto-generated per request if absent:

```python
session_id = request.session_id or str(uuid4())
```

The GUI generates a UUID on first load and sends it with every message. This is how turns within one chat window share history. Without a consistent `session_id` each call is effectively stateless.

---

### Window size and implications

| Parameter | Value | Effect |
|---|---|---|
| `limit` in `fetch_recent_messages` | 10 rows | At most 5 user + 5 assistant turns included |
| Older history | Silently dropped | No summarisation; old turns are gone from context |
| No `session_id` reuse | Fresh `uuid4()` every call | Single-turn, no memory |

---

## Part 2 — Knowledge Retrieval (RAG)

### Source documents

**Directory:** `evaluations/prompts/notes/`

Currently contains:
- `python_backend.md` — typed interfaces, input validation, retries, testing, trade-off thinking.
- `system_design.md` — requirements, scale assumptions, architecture, CAP theorem, observability.

Any `*.md` file added to this directory is automatically included on the next process start (the engine is cached in memory after first initialisation).

---

### Indexing

**File:** `apps/api/src/interview_ai/integrations/llamaindex/knowledge_base.py` — `_ensure_engine()`

On the first call to `search()`:

1. `SimpleDirectoryReader` loads all `*.md` files from the directory.
2. `VectorStoreIndex.from_documents(docs)` embeds each document chunk (OpenAI embeddings via `OPENAI_API_KEY`).
3. A query engine is built with `similarity_top_k=4`.
4. The engine is stored on the instance (`self._query_engine`) and reused for the lifetime of the process — no re-indexing until restart.

If the directory does not exist or contains no markdown files, `search()` returns a single placeholder string.

---

### Query construction

**File:** `apps/api/src/interview_ai/agents/nodes/interview_nodes.py` — `retrieve_context_node()`

```python
query = f"{state['role']} {' '.join(state['topic_focus'])} {state['user_message']}"
```

The query is deliberately broad — role, all topics, and the full (history-enriched) user message — so the cosine similarity search can surface relevant passages from any part of the notes. Because `user_message` already contains prior turns, the retrieval is implicitly session-aware even though the vector index has no session concept.

---

### Retrieval result

The query engine returns the top 4 most similar passages as a single string. `knowledge_base.search()` then:

1. Splits by newline.
2. Strips empty lines.
3. Returns the first 4 non-empty chunks as `list[str]`.

These are written to `state["retrieved_notes"]`.

---

## Part 3 — How Both Sources Feed the LLM

### In `build_plan` (Node 2)

**File:** `apps/api/src/interview_ai/integrations/langchain/prompting.py` — `PLANNER_PROMPT`

```
User message: {user_message}          <- full conversation history + current input
Retrieved context:
{context}                             <- retrieved_notes joined with \n
```

The planner receives the entire prior conversation (via `user_message`) and topic-relevant note passages (via `context`).

---

### In `generate_answer` (Node 4)

**File:** `apps/api/src/interview_ai/integrations/langchain/prompting.py` — `ANSWER_PROMPT`

```
User message: {user_message}          <- same enriched string
Plan:
{plan}                                <- output from build_plan
Retrieved context:
{context}                             <- same retrieved_notes
```

The answer node sees the same two context sources plus the plan from the previous node. No third LLM call is made; the retrieved notes and conversation history do not change between nodes.

---

## Part 4 — Full Turn Sequence (Two Requests)

```
Request 1  (session_id = "abc")
  ├── No prior history -> user_message = raw input only
  ├── retrieve_context -> cosine search query uses raw input
  │     retrieved_notes = up to 4 chunks from notes/*.md
  ├── build_plan       -> PLANNER_PROMPT(user_message, retrieved_notes) -> plan
  ├── skill_enrichment -> question_calibrator(experience_years) -> skill_payload
  ├── generate_answer  -> ANSWER_PROMPT(user_message, plan, retrieved_notes) -> answer
  └── SQLite writes:
        ("abc", "user",      raw_input)
        ("abc", "assistant", answer)

Request 2  (session_id = "abc")
  ├── fetch_recent_messages("abc", limit=10)
  │     -> "User: <turn1>\nAssistant: <turn1_answer>"
  ├── user_message = history block + "\n\nLatest user request:\n" + current_input
  ├── retrieve_context -> cosine search query now includes prior turns
  │     retrieved_notes may differ from Request 1 (richer query)
  ├── build_plan       -> plan is now context-aware of prior exchange
  ├── skill_enrichment -> unchanged deterministic logic
  ├── generate_answer  -> answer is coherent with conversation so far
  └── SQLite writes:
        ("abc", "user",      current_input)
        ("abc", "assistant", new_answer)
```

---

## Part 5 — What Is Not in Context

| Item | Status |
|---|---|
| `skill_payload` from `question_calibrator` | Stored in state but not injected into LLM prompts |
| Turns older than the last 10 rows | Silently discarded; no summarisation |
| Notes added after process start | Not picked up until restart (engine cached in memory) |
| Conversations under different `session_id`s | Completely isolated; no cross-session retrieval |
