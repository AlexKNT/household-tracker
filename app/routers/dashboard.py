from datetime import date

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import settings
from app.crud import list_items
from app.db import get_db
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

# Daily notification modal group order.
_MODAL_GROUPS: list[tuple[str, str]] = [
    ("gone_bad", "Gone bad"),
    ("eat_soon", "Eat soon"),
    ("to_buy", "To-buy"),
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


def _modal_group_key(status: Status) -> str | None:
    """Map a status to its daily-modal group, or None when excluded."""
    if status is Status.EXPIRED:
        return "gone_bad"
    if status is Status.EAT_SOON:
        return "eat_soon"
    if status is Status.TO_BUY:
        return "to_buy"
    return None


def build_dashboard_context(items: list[Item], today: date) -> dict:
    """Group and sort items into dashboard sections and the daily modal."""
    ordered = sorted(items, key=lambda i: sort_key(i, today))

    sections: list[dict] = [
        {"key": key, "title": title, "rows": []} for key, title in _SECTIONS
    ]
    section_index = {section["key"]: section for section in sections}

    modal_groups: list[dict] = [
        {"key": key, "title": title, "items": []} for key, title in _MODAL_GROUPS
    ]
    modal_index = {group["key"]: group for group in modal_groups}

    for item in ordered:
        status = derive_status(item, today)
        remaining = days_left(item, today) if not item.is_to_buy else None
        color = status_color(status, remaining)

        section_key = "out" if status is Status.OUT_OF_STOCK else item.category.value
        section_index[section_key]["rows"].append(
            {
                "item": item,
                "color": color,
                "is_to_buy": status is Status.TO_BUY,
                "days_label": _days_label(remaining),
            }
        )

        group_key = _modal_group_key(status)
        if group_key is not None:
            modal_index[group_key]["items"].append({"name": item.name, "color": color})

    return {
        "sections": sections,
        "modal_groups": modal_groups,
        "poll_interval_s": settings.POLL_INTERVAL_S,
    }


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    items = list_items(db, date.today())
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context=build_dashboard_context(items, date.today()),
    )


@router.get("/dashboard/body", response_class=HTMLResponse)
def dashboard_body(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    items = list_items(db, date.today())
    return templates.TemplateResponse(
        request=request,
        name="partials/dashboard_body.html",
        context=build_dashboard_context(items, date.today()),
    )


@router.post("/modal/dismiss", response_class=HTMLResponse)
def dismiss_modal() -> HTMLResponse:
    """Remove the daily modal in place — HTMX swaps in the empty fragment."""
    return HTMLResponse("")
