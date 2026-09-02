"""Item mutation endpoints that return HTMX fragments."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.config import settings
from app.crud import activate_item, create_item, get_item, list_items
from app.db import get_db
from app.routers.dashboard import build_dashboard_context
from app.schemas import ItemActivate, ItemCreate

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


def _is_true(value: str) -> bool:
    """Parse a checkbox/form truthy string."""
    return value.strip().lower() in ("true", "on", "1", "yes")


def _form_values(
    name: str, category: str, quantity: str, best_by_date: str, is_to_buy: str
) -> dict[str, object]:
    """Values used to re-populate the form after a validation failure."""
    return {
        "name": name,
        "category": category,
        "quantity": quantity,
        "best_by_date": best_by_date,
        "is_to_buy": _is_true(is_to_buy),
    }


@router.get("/items/new", response_class=HTMLResponse)
def new_item_form(
    request: Request,
    category: str = "",
    name: str = "",
    quantity: str = "1",
    best_by_date: str = "",
    is_to_buy: str = "",
) -> HTMLResponse:
    """Return the add-item modal (used to open and to re-render it)."""
    return templates.TemplateResponse(
        request=request,
        name="partials/add_item_modal.html",
        context={
            "errors": {},
            "values": _form_values(name, category, quantity, best_by_date, is_to_buy),
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
    is_to_buy: str = Form(""),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Validate the form, create the item, and return the updated dashboard."""
    try:
        data = ItemCreate(
            name=name,
            category=category,
            quantity=quantity,
            best_by_date=best_by_date or None,
            is_to_buy=_is_true(is_to_buy),
        )
    except ValidationError as exc:
        return templates.TemplateResponse(
            request=request,
            name="partials/add_item_modal.html",
            context={
                "errors": _validation_errors(exc),
                "values": _form_values(
                    name, category, quantity, best_by_date, is_to_buy
                ),
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


@router.get("/items/{item_id}/activate", response_class=HTMLResponse)
def activate_form(
    request: Request, item_id: int, db: Session = Depends(get_db)
) -> HTMLResponse:
    """Return the buy-to-activate modal for a to-buy item."""
    item = get_item(db, item_id)
    if item is None or not item.is_to_buy:
        raise HTTPException(status_code=404, detail="To-buy item not found.")
    return templates.TemplateResponse(
        request=request,
        name="partials/activate_form.html",
        context={"item": item, "errors": {}, "values": {"best_by_date": ""}},
    )


@router.post("/items/{item_id}/activate", response_class=HTMLResponse)
def activate_item_endpoint(
    request: Request,
    item_id: int,
    best_by_date: str = Form(""),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Activate a to-buy item and return the updated dashboard body."""
    item = get_item(db, item_id)
    if item is None or not item.is_to_buy:
        raise HTTPException(status_code=404, detail="To-buy item not found.")

    try:
        data = ItemActivate(
            category=item.category,
            best_by_date=best_by_date or None,
        )
    except ValidationError as exc:
        return templates.TemplateResponse(
            request=request,
            name="partials/activate_form.html",
            context={
                "item": item,
                "errors": _validation_errors(exc),
                "values": {"best_by_date": best_by_date},
            },
        )

    activate_item(db, item, data.best_by_date)

    response = templates.TemplateResponse(
        request=request,
        name="partials/activated.html",
        context=build_dashboard_context(list_items(db), date.today()),
    )
    # The form targets the modal; on success we swap the dashboard body.
    response.headers["HX-Retarget"] = "#dashboard-body"
    return response
