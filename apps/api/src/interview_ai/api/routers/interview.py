import json
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from interview_ai.core.config import Settings, get_settings
from interview_ai.schemas.interview import InterviewRequest, InterviewResponse
from interview_ai.services.interview_service import InterviewService

router = APIRouter()


def get_service(settings: Settings = Depends(get_settings)) -> InterviewService:  # noqa: B008
    return InterviewService(settings)


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _chunk_text(text: str, chunk_size: int = 80) -> list[str]:
    words = text.split()
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for word in words:
        next_len = current_len + len(word) + (1 if current else 0)
        if next_len > chunk_size and current:
            chunks.append(" ".join(current))
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
            current_len = next_len

    if current:
        chunks.append(" ".join(current))

    return chunks or [""]


@router.post("/run", response_model=InterviewResponse)
async def run_interview_agent(
    request: InterviewRequest,
    service: InterviewService = Depends(get_service),  # noqa: B008
) -> InterviewResponse:
    try:
        return await service.run(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/stream")
async def stream_interview_agent(
    request: InterviewRequest,
    service: InterviewService = Depends(get_service),  # noqa: B008
) -> StreamingResponse:
    async def event_generator() -> AsyncGenerator[str, None]:
        yield _sse("status", {"message": "running"})

        try:
            response = await service.run(request)
        except ValueError as exc:
            yield _sse("error", {"detail": str(exc)})
            return
        except Exception:  # pragma: no cover - defensive stream safety
            yield _sse("error", {"detail": "Internal server error during streaming."})
            return

        for chunk in _chunk_text(response.answer):
            yield _sse("answer_chunk", {"text": chunk})

        yield _sse(
            "final",
            {
                "plan": response.plan,
                "follow_up_questions": response.follow_up_questions,
                "suggested_exercises": response.suggested_exercises,
                "used_skills": response.used_skills,
                "retrieved_context_chunks": response.retrieved_context_chunks,
                "session_id": response.session_id,
            },
        )

    return StreamingResponse(event_generator(), media_type="text/event-stream")
