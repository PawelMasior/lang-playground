from fastapi import FastAPI

from interview_ai.api.routers.graph import router as graph_router
from interview_ai.api.routers.health import router as health_router
from interview_ai.api.routers.interview import router as interview_router
from interview_ai.core.config import get_settings
from interview_ai.observability.langsmith_setup import configure_langsmith

settings = get_settings()
configure_langsmith(settings)

app = FastAPI(title="Interview AI API", version="0.1.0")
app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(interview_router, prefix="/v1/interview", tags=["interview"])
app.include_router(graph_router, prefix="/graph", tags=["graph"])
