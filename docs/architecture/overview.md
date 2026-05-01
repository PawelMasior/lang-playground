# Architecture Overview

## Goals

- Demonstrate practical GenAI backend architecture for interviews.
- Show layered design, validation, observability, and testing discipline.
- Combine deterministic skill tools with LLM-driven reasoning.

## Components

- API app (`apps/api`)
- Skill server app (`apps/skill_server`)
- Shared package (`packages/shared`)
- Evaluation harness (`evaluations`)
- Tests (`tests`)

## Request Flow

1. User calls `POST /v1/interview/run`.
2. API validates payload with Pydantic.
3. LangGraph runs node sequence:
   - retrieval node (LlamaIndex)
   - planning node (LangChain prompt + LLM)
   - skill enrichment node (HTTP call to skill server)
   - answer node (LangChain prompt + LLM)
4. Final structured response is returned.
5. LangSmith traces each decorated node and service run.

## Why This Architecture Works In Interviews

- Easy to discuss bounded contexts and separation of concerns.
- Shows capability for both monolith and microservice collaboration.
- Demonstrates evaluation mindset using dataset-driven metrics.
- Provides extensibility points: new skills, graph branches, retrieval backends.
