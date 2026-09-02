"""Item mutation endpoints that return HTMX fragments."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.config import settings
from app.crud import create_item, list_items
from app.db import get_db
from app.routers.dashboard import build_dashboard_context
from app.schemas import ItemCreate

router = APIRouter()

templates = Jinja2Templates(directory=str(settings.BASE_DIR / "app" / "templates"))


def _validation_errors(exc: ValidationError) -> dict[str, str]:
    """Flatten a Pydantic `ValidationError` to `{field: first message}`.

    Model-level errors (empty `loc`) land under the `__form__` key and are
    rendered at the top of the form.
    """
    errors: dict[str, str] = {}
    for error in exc.errors():
        loc = error.get("loc", ())
        field = str(loc[0]) if loc else "__form__"
        errors.setdefault(field, error.get("msg", "Invalid value"))
    return errors


def _form_values(
    name: str, category: str, quantity: str, best_by_date: str
) -> dict[str, str]:
    """Values used to re-populate the form after a validation failure."""
    return {
        "name": name,
        "category": category,
        "quantity": quantity,
        "best_by_date": best_by_date,
    }


@router.get("/items/new", response_class=HTMLResponse)
def new_item_form(
    request: Request,
    category: str = "",
    name: str = "",
    quantity: str = "1",
    best_by_date: str = "",
) -> HTMLResponse:
    """Return the add-item modal (used to open and to re-render it)."""
    return templates.TemplateResponse(
        request=request,
        name="partials/add_item_modal.html",
        context={
            "errors": {},
            "values": _form_values(name, category, quantity, best_by_date),
        },
    )


@router.get("/items/empty", response_class=HTMLResponse)
def empty_fragment() -> HTMLResponse:
    """Return an empty fragment so HTMX can remove the add-item modal."""
    return HTMLResponse("")


@router.post("/items", response_class=HTMLResponse)
def create_item_endpoint(
    request: Request,
    name: str = Form(""),
    category: str = Form(""),
    quantity: str = Form("1"),
    best_by_date: str = Form(""),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Validate the form, create the item, and return the updated dashboard."""
    try:
        data = ItemCreate(
            name=name,
            category=category,
            quantity=quantity,
            best_by_date=best_by_date or None,
        )
    except ValidationError as exc:
        return templates.TemplateResponse(
            request=request,
            name="partials/add_item_modal.html",
            context={
                "errors": _validation_errors(exc),
                "values": _form_values(name, category, quantity, best_by_date),
            },
        )

    create_item(db, data)

    response = templates.TemplateResponse(
        request=request,
        name="partials/items_created.html",
        context=build_dashboard_context(list_items(db), date.today()),
    )
    # The form normally targets the modal; on success we swap the dashboard.
    response.headers["HX-Retarget"] = "#dashboard-body"
    return response
