from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import settings

router = APIRouter()

templates = Jinja2Templates(
    directory=str(settings.BASE_DIR / "app" / "templates")
)


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"poll_interval_s": settings.POLL_INTERVAL_S},
    )
