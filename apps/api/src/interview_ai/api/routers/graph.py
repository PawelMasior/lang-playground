from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from interview_ai.core.config import Settings, get_settings
from interview_ai.services.interview_service import InterviewService

router = APIRouter()

_MERMAID_HTML_TEMPLATE = (
    "<!DOCTYPE html>"
    '<html lang="en"><head>'
    '<meta charset="UTF-8" />'
    "<title>Interview Graph</title>"
    '<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>'
    "<style>"
    "body { font-family: sans-serif; padding: 2rem; background: #f9f9f9; }"
    "h1 { font-size: 1.25rem; margin-bottom: 1rem; }"
    ".mermaid { background: #fff; border: 1px solid #ddd; border-radius: 8px;"
    " padding: 1.5rem; display: inline-block; }"
    "</style></head><body>"
    "<h1>Interview Agent Graph</h1>"
    '<div class="mermaid">%%DIAGRAM%%</div>'
    "<script>mermaid.initialize({ startOnLoad: true, theme: 'default' });</script>"
    "</body></html>"
)


def get_service(settings: Settings = Depends(get_settings)) -> InterviewService:  # noqa: B008
    return InterviewService(settings)


@router.get("/mermaid", response_class=HTMLResponse)
def graph_mermaid(service: InterviewService = Depends(get_service)) -> HTMLResponse:  # noqa: B008
        diagram = service.get_graph_mermaid()
        html = _MERMAID_HTML_TEMPLATE.replace("%%DIAGRAM%%", diagram)
        return HTMLResponse(html)
