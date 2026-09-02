"""Endpoint tests for every mutation via httpx (Unit 13: Testing & Hardening)."""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.db import Base, get_db
from app.main import create_app
from app.models import Item


@pytest.fixture
def db_engine(tmp_path) -> Engine:
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def client(db_engine: Engine) -> TestClient:
    def override_get_db():
        with Session(db_engine) as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c


def _items_named(db_engine: Engine, name: str) -> list[Item]:
    with Session(db_engine) as session:
        return list(
            session.query(Item).filter(Item.name == name).order_by(Item.id)
        )


def _add_item(
    client: TestClient,
    db_engine: Engine,
    name: str = "Aspirin",
    category: str = "meds",
    quantity: str = "2",
    best_by_date: str | None = None,
) -> int:
    data: dict[str, str] = {
        "name": name,
        "category": category,
        "quantity": quantity,
    }
    if best_by_date is not None:
        data["best_by_date"] = best_by_date
    client.post("/items", data=data)
    return _items_named(db_engine, name)[-1].id


def _add_to_buy(client: TestClient, name: str = "Apples", category: str = "food") -> None:
    client.post(
        "/items", data={"name": name, "category": category, "is_to_buy": "true"}
    )


# --- Add item ---


def test_add_food_item_succeeds(client: TestClient, db_engine: Engine) -> None:
    best_by = date.today() + timedelta(days=2)
    response = client.post(
        "/items",
        data={
            "name": "Milk",
            "category": "food",
            "quantity": "2",
            "best_by_date": best_by.isoformat(),
        },
    )

    assert response.status_code == 200
    assert response.headers["HX-Retarget"] == "#dashboard-body"
    assert "Milk" in response.text
    assert "row--yellow" in response.text

    created = _items_named(db_engine, "Milk")
    assert len(created) == 1
    assert created[0].quantity == 2
    assert created[0].best_by_date == best_by


def test_add_med_without_date_succeeds(client: TestClient, db_engine: Engine) -> None:
    response = client.post(
        "/items", data={"name": "Aspirin", "category": "meds", "quantity": "3"}
    )

    assert response.status_code == 200
    assert "row--green" in response.text
    created = _items_named(db_engine, "Aspirin")
    assert len(created) == 1
    assert created[0].best_by_date is None
    assert created[0].quantity == 3


def test_add_household_defaults_quantity_to_one(
    client: TestClient, db_engine: Engine
) -> None:
    response = client.post("/items", data={"name": "Soap", "category": "household"})

    assert response.status_code == 200
    assert _items_named(db_engine, "Soap")[0].quantity == 1


def test_add_food_without_best_by_rejected(
    client: TestClient, db_engine: Engine
) -> None:
    response = client.post("/items", data={"name": "Milk", "category": "food"})

    assert response.status_code == 200
    assert "needs a best-by date" in response.text
    assert _items_named(db_engine, "Milk") == []


def test_add_med_with_best_by_rejected(
    client: TestClient, db_engine: Engine
) -> None:
    response = client.post(
        "/items",
        data={"name": "Aspirin", "category": "meds", "best_by_date": "2026-09-05"},
    )

    assert response.status_code == 200
    assert "cannot have a best-by date" in response.text
    assert _items_named(db_engine, "Aspirin") == []


def test_add_household_with_best_by_rejected(
    client: TestClient, db_engine: Engine
) -> None:
    response = client.post(
        "/items",
        data={"name": "Soap", "category": "household", "best_by_date": "2026-09-05"},
    )

    assert response.status_code == 200
    assert "cannot have a best-by date" in response.text
    assert _items_named(db_engine, "Soap") == []


def test_add_empty_name_rejected(client: TestClient, db_engine: Engine) -> None:
    response = client.post(
        "/items", data={"name": "   ", "category": "meds", "quantity": "1"}
    )

    assert response.status_code == 200
    assert "Name is required." in response.text
    assert _items_named(db_engine, "Aspirin") == []


def test_add_negative_quantity_rejected(client: TestClient, db_engine: Engine) -> None:
    response = client.post(
        "/items", data={"name": "Aspirin", "category": "meds", "quantity": "-1"}
    )

    assert response.status_code == 200
    assert 'id="add-item-form"' in response.text
    assert _items_named(db_engine, "Aspirin") == []


# --- Activate (buy to-activate) ---


def test_activate_food_sets_best_by(client: TestClient, db_engine: Engine) -> None:
    _add_to_buy(client)
    item = _items_named(db_engine, "Apples")[0]
    best_by = date.today() + timedelta(days=5)

    response = client.post(
        f"/items/{item.id}/activate", data={"best_by_date": best_by.isoformat()}
    )

    assert response.status_code == 200
    assert "row--green" in response.text
    activated = _items_named(db_engine, "Apples")[0]
    assert activated.is_to_buy is False
    assert activated.best_by_date == best_by


def test_activate_food_missing_date_rejected(
    client: TestClient, db_engine: Engine
) -> None:
    _add_to_buy(client)
    item = _items_named(db_engine, "Apples")[0]

    response = client.post(f"/items/{item.id}/activate", data={})

    assert response.status_code == 200
    assert "needs a best-by date" in response.text
    assert _items_named(db_engine, "Apples")[0].is_to_buy is True


def test_activate_non_food_needs_no_date(
    client: TestClient, db_engine: Engine
) -> None:
    _add_to_buy(client, name="Soap", category="household")
    item = _items_named(db_engine, "Soap")[0]

    response = client.post(f"/items/{item.id}/activate", data={})

    assert response.status_code == 200
    assert "row--green" in response.text
    activated = _items_named(db_engine, "Soap")[0]
    assert activated.is_to_buy is False
    assert activated.best_by_date is None


def test_activate_404_for_missing_or_non_to_buy(
    client: TestClient, db_engine: Engine
) -> None:
    assert client.get("/items/9999/activate").status_code == 404
    assert client.post("/items/9999/activate", data={}).status_code == 404

    client.post("/items", data={"name": "Aspirin", "category": "meds"})
    item = _items_named(db_engine, "Aspirin")[0]
    assert client.post(f"/items/{item.id}/activate", data={}).status_code == 404


# --- Quantity controls ---


def test_increment_updates_quantity(client: TestClient, db_engine: Engine) -> None:
    item_id = _add_item(client, db_engine, quantity="2")

    response = client.post(f"/items/{item_id}/increment")

    assert response.status_code == 200
    assert "3 left" in response.text
    assert _items_named(db_engine, "Aspirin")[-1].quantity == 3


def test_decrement_updates_quantity(client: TestClient, db_engine: Engine) -> None:
    item_id = _add_item(client, db_engine, quantity="2")

    response = client.post(f"/items/{item_id}/decrement")

    assert response.status_code == 200
    assert "1 left" in response.text
    assert _items_named(db_engine, "Aspirin")[-1].quantity == 1


def test_decrement_at_zero_is_no_op(client: TestClient, db_engine: Engine) -> None:
    item_id = _add_item(client, db_engine, quantity="1")

    client.post(f"/items/{item_id}/decrement")
    response = client.post(f"/items/{item_id}/decrement")

    assert response.status_code == 200
    assert "row--out" in response.text
    assert _items_named(db_engine, "Aspirin")[-1].quantity == 0


def test_empty_moves_row_to_out_of_stock_section(
    client: TestClient, db_engine: Engine
) -> None:
    today = date.today()
    _add_item(client, db_engine, name="Aspirin", quantity="2")
    food_id = _add_item(
        client,
        db_engine,
        name="Milk",
        category="food",
        quantity="3",
        best_by_date=(today + timedelta(days=5)).isoformat(),
    )

    response = client.post(f"/items/{food_id}/empty")

    assert response.status_code == 200
    assert "row--out" in response.text
    assert response.text.index("Milk") < response.text.index("Aspirin")
    assert _items_named(db_engine, "Milk")[-1].quantity == 0


def test_quantity_controls_404_for_missing_item(client: TestClient) -> None:
    assert client.post("/items/9999/increment").status_code == 404
    assert client.post("/items/9999/decrement").status_code == 404
    assert client.post("/items/9999/empty").status_code == 404


# --- Restock (⟳) ---


def test_restock_creates_to_buy(client: TestClient, db_engine: Engine) -> None:
    item_id = _add_item(client, db_engine)

    response = client.post(f"/items/{item_id}/restock")

    assert response.status_code == 200
    assert "row--purple" in response.text
    items = _items_named(db_engine, "Aspirin")
    assert len(items) == 2
    to_buy = items[-1]
    assert to_buy.is_to_buy is True
    assert to_buy.quantity == 1
    assert to_buy.best_by_date is None


def test_restock_food_keeps_no_best_by_date(
    client: TestClient, db_engine: Engine
) -> None:
    today = date.today()
    item_id = _add_item(
        client,
        db_engine,
        name="Milk",
        category="food",
        quantity="3",
        best_by_date=(today + timedelta(days=5)).isoformat(),
    )

    client.post(f"/items/{item_id}/restock")

    items = _items_named(db_engine, "Milk")
    to_buy = items[-1]
    assert to_buy.is_to_buy is True
    assert to_buy.best_by_date is None


def test_restock_out_of_stock_keeps_source_row(
    client: TestClient, db_engine: Engine
) -> None:
    item_id = _add_item(client, db_engine, quantity="1")
    client.post(f"/items/{item_id}/empty")

    response = client.post(f"/items/{item_id}/restock")

    assert response.status_code == 200
    assert "row--out" in response.text
    assert "row--purple" in response.text
    items = _items_named(db_engine, "Aspirin")
    active = next(i for i in items if not i.is_to_buy)
    assert active.quantity == 0


def test_restock_404_for_missing_item(client: TestClient) -> None:
    assert client.post("/items/9999/restock").status_code == 404


# --- Comments ---


def test_save_comment_returns_cell_and_persists(
    client: TestClient, db_engine: Engine
) -> None:
    item_id = _add_item(client, db_engine)

    response = client.patch(
        f"/items/{item_id}/comment", data={"comment": "for Tuesday"}
    )

    assert response.status_code == 200
    assert "for Tuesday" in response.text
    # The PATCH swaps only the cell, not the whole dashboard body.
    assert 'id="dashboard-body"' not in response.text
    assert _items_named(db_engine, "Aspirin")[-1].comment == "for Tuesday"


def test_empty_comment_clears_to_none(client: TestClient, db_engine: Engine) -> None:
    item_id = _add_item(client, db_engine)
    client.patch(f"/items/{item_id}/comment", data={"comment": "for Tuesday"})

    response = client.patch(f"/items/{item_id}/comment", data={"comment": "   "})

    assert response.status_code == 200
    assert "Add note" in response.text
    assert _items_named(db_engine, "Aspirin")[-1].comment is None


def test_comment_whitespace_is_stripped(
    client: TestClient, db_engine: Engine
) -> None:
    item_id = _add_item(client, db_engine)

    client.patch(f"/items/{item_id}/comment", data={"comment": "  note  "})

    assert _items_named(db_engine, "Aspirin")[-1].comment == "note"


def test_comment_edit_form_renders(client: TestClient, db_engine: Engine) -> None:
    item_id = _add_item(client, db_engine)

    response = client.get(f"/items/{item_id}/comment/edit")

    assert response.status_code == 200
    assert 'name="comment"' in response.text


def test_comment_endpoints_404_for_missing_item(client: TestClient) -> None:
    assert client.get("/items/9999/comment/edit").status_code == 404
    assert (
        client.patch("/items/9999/comment", data={"comment": "x"}).status_code
        == 404
    )


# --- Daily modal dismiss ---


def test_dismiss_modal_returns_empty_fragment(client: TestClient) -> None:
    response = client.post("/modal/dismiss")

    assert response.status_code == 200
    assert response.text == ""


def test_modal_reappears_on_next_full_load(client: TestClient) -> None:
    assert 'id="notification-modal"' in client.get("/").text
    client.post("/modal/dismiss")
    assert 'id="notification-modal"' in client.get("/").text
