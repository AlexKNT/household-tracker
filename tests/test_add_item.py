from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.db import Base, get_db
from app.main import create_app
from app.models import Category, Item


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
        return list(session.query(Item).filter(Item.name == name))


def test_add_item_form_renders(client: TestClient) -> None:
    response = client.get("/items/new")
    assert response.status_code == 200
    assert 'id="add-item-form"' in response.text
    assert 'name="category"' in response.text
    assert 'name="name"' in response.text
    assert 'name="quantity"' in response.text
    # The best-by field is hidden until "food" is selected.
    assert 'name="best_by_date"' not in response.text


def test_add_item_form_shows_best_by_for_food(client: TestClient) -> None:
    response = client.get("/items/new", params={"category": "food"})
    assert response.status_code == 200
    assert 'name="best_by_date"' in response.text
    assert "required" in response.text


def test_empty_fragment_removes_modal(client: TestClient) -> None:
    response = client.get("/items/empty")
    assert response.status_code == 200
    assert response.text == ""


def test_add_food_item_succeeds_and_sorts(client: TestClient, db_engine: Engine) -> None:
    today = date.today()
    with Session(db_engine) as session:
        session.add(Item(name="Aspirin", category=Category.MEDS, quantity=2))
        session.commit()

    response = client.post(
        "/items",
        data={
            "name": "Greek yogurt",
            "category": "food",
            "quantity": "3",
            "best_by_date": (today + timedelta(days=2)).isoformat(),
        },
    )

    assert response.status_code == 200
    assert response.headers["HX-Retarget"] == "#dashboard-body"
    assert 'id="dashboard-body"' in response.text
    assert 'hx-swap-oob="delete"' in response.text
    assert "Greek yogurt" in response.text
    assert "row--yellow" in response.text
    assert "2 days left" in response.text

    # Food renders after Meds, so the new item sorts below the med.
    assert response.text.index("Aspirin") < response.text.index("Greek yogurt")

    created = _items_named(db_engine, "Greek yogurt")
    assert len(created) == 1
    assert created[0].category is Category.FOOD
    assert created[0].quantity == 3
    assert created[0].best_by_date == today + timedelta(days=2)
    assert created[0].is_to_buy is False


def test_add_med_without_date_succeeds(client: TestClient, db_engine: Engine) -> None:
    response = client.post(
        "/items",
        data={"name": "Aspirin", "category": "meds", "quantity": "2"},
    )
    assert response.status_code == 200
    assert "Aspirin" in response.text
    assert "row--green" in response.text

    created = _items_named(db_engine, "Aspirin")
    assert len(created) == 1
    assert created[0].best_by_date is None
    assert created[0].quantity == 2


def test_add_item_quantity_defaults_to_one(client: TestClient, db_engine: Engine) -> None:
    response = client.post(
        "/items",
        data={"name": "Paper towels", "category": "household"},
    )
    assert response.status_code == 200
    created = _items_named(db_engine, "Paper towels")
    assert len(created) == 1
    assert created[0].quantity == 1


def test_med_with_best_by_rejected(client: TestClient, db_engine: Engine) -> None:
    response = client.post(
        "/items",
        data={
            "name": "Aspirin",
            "category": "meds",
            "quantity": "2",
            "best_by_date": "2026-09-05",
        },
    )
    assert response.status_code == 200
    assert "cannot have a best-by date" in response.text
    assert _items_named(db_engine, "Aspirin") == []


def test_household_with_best_by_rejected(client: TestClient, db_engine: Engine) -> None:
    response = client.post(
        "/items",
        data={
            "name": "Soap",
            "category": "household",
            "quantity": "1",
            "best_by_date": "2026-09-05",
        },
    )
    assert response.status_code == 200
    assert "cannot have a best-by date" in response.text
    assert _items_named(db_engine, "Soap") == []


def test_food_without_best_by_rejected(client: TestClient, db_engine: Engine) -> None:
    response = client.post(
        "/items",
        data={"name": "Milk", "category": "food", "quantity": "1"},
    )
    assert response.status_code == 200
    assert "needs a best-by date" in response.text
    assert _items_named(db_engine, "Milk") == []


def test_empty_name_rejected(client: TestClient, db_engine: Engine) -> None:
    response = client.post(
        "/items",
        data={"name": "   ", "category": "meds", "quantity": "1"},
    )
    assert response.status_code == 200
    assert "Name is required." in response.text
    assert _items_named(db_engine, "") == []


def test_invalid_quantity_shows_error(client: TestClient, db_engine: Engine) -> None:
    response = client.post(
        "/items",
        data={"name": "Aspirin", "category": "meds", "quantity": "-1"},
    )
    assert response.status_code == 200
    assert 'id="add-item-form"' in response.text
    assert _items_named(db_engine, "Aspirin") == []
