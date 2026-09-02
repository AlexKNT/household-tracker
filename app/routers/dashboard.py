from datetime import date

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import Item
from app.services import Status, days_left, derive_status, sort_key, status_color

router = APIRouter()

templates = Jinja2Templates(directory=str(settings.BASE_DIR / "app" / "templates"))

# Fixed dashboard section order.
_SECTIONS: list[tuple[str, str]] = [
    ("out", "Out of stock"),
    ("meds", "Meds"),
    ("food", "Food"),
    ("household", "Household"),
]


def _days_label(remaining: int | None) -> str | None:
    """Human-readable countdown for the row's meta line."""
    if remaining is None:
        return None
    if remaining < 0:
        return f"{-remaining} days past"
    if remaining == 0:
        return "today"
    if remaining == 1:
        return "1 day left"
    return f"{remaining} days left"


def _build_context(items: list[Item], today: date) -> dict:
    """Group and sort items into dashboard sections."""
    sections: list[dict] = [
        {"key": key, "title": title, "rows": []} for key, title in _SECTIONS
    ]
    index = {section["key"]: section for section in sections}

    for item in sorted(items, key=lambda i: sort_key(i, today)):
        status = derive_status(item, today)
        remaining = days_left(item, today)
        key = "out" if status is Status.OUT_OF_STOCK else item.category.value
        index[key]["rows"].append(
            {
                "item": item,
                "color": status_color(status, remaining),
                "is_to_buy": status is Status.TO_BUY,
                "days_label": _days_label(remaining),
            }
        )

    return {
        "sections": sections,
        "poll_interval_s": settings.POLL_INTERVAL_S,
    }


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    items = list(db.scalars(select(Item)))
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context=_build_context(items, date.today()),
    )


@router.get("/dashboard/body", response_class=HTMLResponse)
def dashboard_body(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    items = list(db.scalars(select(Item)))
    return templates.TemplateResponse(
        request=request,
        name="partials/dashboard_body.html",
        context=_build_context(items, date.today()),
    )
