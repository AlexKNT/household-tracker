"""One test per architecture invariant (Unit 13: Testing & Hardening)."""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app import services
from app.crud import list_items
from app.db import Base, get_db
from app.main import create_app
from app.models import Category, Item
from app.routers import dashboard, items as items_router
from app.schemas import ItemCreate
from app.services import Status, derive_status, sort_key, status_color

TODAY = date.today()


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
        return list(session.query(Item).filter(Item.name == name).order_by(Item.id))


# 1. Status is always derived, never stored.


def test_invariant_1_status_is_derived_never_stored() -> None:
    columns = {column.name for column in Item.__table__.columns}
    assert "status" not in columns
    assert "color" not in columns
    assert not hasattr(Item, "status")

    item = Item(
        name="Milk",
        category=Category.FOOD,
        quantity=1,
        best_by_date=TODAY + timedelta(days=5),
    )
    assert derive_status(item, TODAY) is Status.FINE

    # Changing the underlying facts changes the derived status; no stored
    # status field exists to drift out of sync.
    item.quantity = 0
    assert derive_status(item, TODAY) is Status.OUT_OF_STOCK


# 2. `best_by_date` is food-only.


def test_invariant_2_best_by_date_is_food_only() -> None:
    with pytest.raises(ValidationError):
        ItemCreate(name="Aspirin", category=Category.MEDS, best_by_date=TODAY)
    with pytest.raises(ValidationError):
        ItemCreate(name="Soap", category=Category.HOUSEHOLD, best_by_date=TODAY)

    # Defense in depth: services also ignore dates on non-food rows.
    med = Item(
        name="Aspirin",
        category=Category.MEDS,
        quantity=1,
        best_by_date=TODAY - timedelta(days=30),
    )
    assert services.days_left(med, TODAY) is None
    assert derive_status(med, TODAY) is Status.FINE


# 3. Out-of-stock items are never auto-deleted.


def test_invariant_3_out_of_stock_never_auto_deleted(db_engine: Engine) -> None:
    with Session(db_engine) as session:
        out = Item(
            name="Empty juice",
            category=Category.FOOD,
            quantity=0,
            best_by_date=TODAY - timedelta(days=30),
        )
        gone = Item(
            name="Ancient eggs",
            category=Category.FOOD,
            quantity=1,
            best_by_date=TODAY - timedelta(days=7),
        )
        session.add_all([out, gone])
        session.commit()
        out_id = out.id
        gone_id = gone.id

    with Session(db_engine) as session:
        visible = list_items(session, TODAY)
        names = {item.name for item in visible}
        assert "Empty juice" in names
        assert "Ancient eggs" not in names
        assert session.get(Item, out_id) is not None
        assert session.get(Item, gone_id) is None


# 4. Sort order is fixed and enforced server-side.


def test_invariant_4_fixed_server_side_sort() -> None:
    items = [
        Item(name="household", category=Category.HOUSEHOLD, quantity=1),
        Item(name="food-tobuy", category=Category.FOOD, quantity=1, is_to_buy=True),
        Item(
            name="food-fine",
            category=Category.FOOD,
            quantity=1,
            best_by_date=TODAY + timedelta(days=10),
        ),
        Item(
            name="food-eatsoon",
            category=Category.FOOD,
            quantity=1,
            best_by_date=TODAY + timedelta(days=2),
        ),
        Item(
            name="food-expired",
            category=Category.FOOD,
            quantity=1,
            best_by_date=TODAY - timedelta(days=2),
        ),
        Item(name="med", category=Category.MEDS, quantity=1),
        Item(name="out-stock", category=Category.FOOD, quantity=0),
    ]

    context = dashboard.build_dashboard_context(items, TODAY)
    section_keys = [section["key"] for section in context["sections"]]
    assert section_keys == ["out", "meds", "food", "household"]

    names_by_section = {
        section["key"]: [row["item"].name for row in section["rows"]]
        for section in context["sections"]
    }
    assert names_by_section["out"] == ["out-stock"]
    assert names_by_section["meds"] == ["med"]
    assert names_by_section["food"] == [
        "food-expired",
        "food-eatsoon",
        "food-fine",
        "food-tobuy",
    ]
    assert names_by_section["household"] == ["household"]


# 5. No background jobs or schedulers.


def test_invariant_5_no_background_jobs_or_schedulers() -> None:
    app = create_app()
    assert app.router.on_startup == []


# 6. Routers render fragments, not JSON.


def test_invariant_6_routers_render_fragments_not_json(
    client: TestClient, db_engine: Engine
) -> None:
    client.post(
        "/items", data={"name": "Aspirin", "category": "meds", "quantity": "2"}
    )
    item = _items_named(db_engine, "Aspirin")[0]

    responses = [
        client.get("/"),
        client.get("/dashboard/body"),
        client.post(
            "/items",
            data={
                "name": "Milk",
                "category": "food",
                "quantity": "1",
                "best_by_date": (date.today() + timedelta(days=3)).isoformat(),
            },
        ),
        client.post(f"/items/{item.id}/increment"),
        client.post(f"/items/{item.id}/decrement"),
        client.post(f"/items/{item.id}/empty"),
        client.post(f"/items/{item.id}/restock"),
        client.patch(f"/items/{item.id}/comment", data={"comment": "note"}),
        client.post("/modal/dismiss"),
    ]

    for response in responses:
        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert content_type.startswith("text/html"), content_type
        assert not response.text.lstrip().startswith(("{", "["))


# 7. Business rules live only in `services.py`.


def test_invariant_7_business_rules_live_only_in_services() -> None:
    assert derive_status.__module__ == "app.services"
    assert status_color.__module__ == "app.services"
    assert sort_key.__module__ == "app.services"

    # Routers import the service functions rather than re-implementing them.
    assert dashboard.derive_status is derive_status
    assert dashboard.status_color is status_color
    assert dashboard.sort_key is sort_key

    assert "derive_status" not in items_router.__dict__
    assert "status_color" not in items_router.__dict__
    assert "sort_key" not in items_router.__dict__
