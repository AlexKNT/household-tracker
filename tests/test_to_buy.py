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


def _add_to_buy(client: TestClient, name: str = "Apples", category: str = "food") -> None:
    client.post("/items", data={"name": name, "category": category, "is_to_buy": "true"})


# --- Adding a to-buy ---


def test_add_to_buy_food_defaults_to_today(
    client: TestClient, db_engine: Engine
) -> None:
    response = client.post(
        "/items", data={"name": "Apples", "category": "food", "is_to_buy": "true"}
    )

    assert response.status_code == 200
    assert response.headers["HX-Retarget"] == "#dashboard-body"
    assert "row--purple" in response.text
    assert "to buy" in response.text

    created = _items_named(db_engine, "Apples")
    assert len(created) == 1
    assert created[0].is_to_buy is True
    assert created[0].category is Category.FOOD
    assert created[0].quantity == 1
    assert created[0].best_by_date == date.today()


def test_add_to_buy_keeps_explicit_date(
    client: TestClient, db_engine: Engine
) -> None:
    best_by = date.today() + timedelta(days=7)
    response = client.post(
        "/items",
        data={
            "name": "Apples",
            "category": "food",
            "is_to_buy": "true",
            "best_by_date": best_by.isoformat(),
        },
    )

    assert response.status_code == 200
    created = _items_named(db_engine, "Apples")
    assert len(created) == 1
    assert created[0].is_to_buy is True
    assert created[0].best_by_date == best_by


def test_add_to_buy_med_rejects_best_by_date(
    client: TestClient, db_engine: Engine
) -> None:
    response = client.post(
        "/items",
        data={
            "name": "Ibuprofen",
            "category": "meds",
            "is_to_buy": "true",
            "best_by_date": "2026-09-05",
        },
    )

    assert response.status_code == 200
    assert "cannot have a best-by date" in response.text
    assert _items_named(db_engine, "Ibuprofen") == []


def test_add_form_hides_quantity_and_best_by_for_to_buy(
    client: TestClient,
) -> None:
    response = client.get(
        "/items/new", params={"category": "food", "is_to_buy": "true"}
    )

    assert response.status_code == 200
    assert 'name="is_to_buy"' in response.text
    assert "checked" in response.text
    assert 'name="quantity"' not in response.text
    assert 'name="best_by_date"' not in response.text


# --- Rendering ---


def test_to_buy_row_shows_no_quantity_or_days(
    client: TestClient, db_engine: Engine
) -> None:
    _add_to_buy(client)

    html = client.get("/").text
    assert "to buy" in html
    assert "left" not in html
    assert "days" not in html
    assert "best by" not in html


def test_to_buy_sorts_within_category(
    client: TestClient, db_engine: Engine
) -> None:
    client.post(
        "/items",
        data={
            "name": "Yogurt",
            "category": "food",
            "quantity": "1",
            "best_by_date": (date.today() + timedelta(days=10)).isoformat(),
        },
    )
    _add_to_buy(client, name="Apples")
    client.post("/items", data={"name": "Soap", "category": "household"})

    html = client.get("/").text
    # Active food sorts before the purple to-buy, which stays in Food and
    # sorts before Household.
    assert html.index("Yogurt") < html.index("Apples") < html.index("Soap")


def test_to_buy_appears_in_modal_to_buy_group(
    client: TestClient, db_engine: Engine
) -> None:
    _add_to_buy(client)

    html = client.get("/").text
    start = html.index('id="notification-modal"')
    end = html.index("<!-- /notification-modal -->")
    modal = html[start:end]

    assert "Apples" in modal
    assert modal.index("To-buy") < modal.index("Apples")


# --- Activate flow ---


def test_activate_form_renders_for_food(
    client: TestClient, db_engine: Engine
) -> None:
    _add_to_buy(client)
    item = _items_named(db_engine, "Apples")[0]

    response = client.get(f"/items/{item.id}/activate")

    assert response.status_code == 200
    assert 'id="activate-form"' in response.text
    assert 'name="best_by_date"' in response.text


def test_activate_food_converts_to_green(
    client: TestClient, db_engine: Engine
) -> None:
    _add_to_buy(client)
    item = _items_named(db_engine, "Apples")[0]
    best_by = date.today() + timedelta(days=5)

    response = client.post(
        f"/items/{item.id}/activate", data={"best_by_date": best_by.isoformat()}
    )

    assert response.status_code == 200
    assert response.headers["HX-Retarget"] == "#dashboard-body"
    assert 'id="dashboard-body"' in response.text
    assert 'hx-swap-oob="delete"' in response.text
    assert "row--green" in response.text
    assert "to buy" not in response.text

    activated = _items_named(db_engine, "Apples")[0]
    assert activated.is_to_buy is False
    assert activated.quantity == 1
    assert activated.best_by_date == best_by


def test_activate_food_missing_date_rejected(
    client: TestClient, db_engine: Engine
) -> None:
    _add_to_buy(client)
    item = _items_named(db_engine, "Apples")[0]

    response = client.post(f"/items/{item.id}/activate", data={})

    assert response.status_code == 200
    assert 'id="activate-form"' in response.text
    assert "needs a best-by date" in response.text
    assert _items_named(db_engine, "Apples")[0].is_to_buy is True


def test_activate_non_food_to_buy(
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
    assert activated.quantity == 1


def test_activate_404_for_missing_item(client: TestClient) -> None:
    assert client.get("/items/9999/activate").status_code == 404
    assert client.post("/items/9999/activate", data={}).status_code == 404


def test_activate_404_for_non_to_buy_item(
    client: TestClient, db_engine: Engine
) -> None:
    client.post("/items", data={"name": "Aspirin", "category": "meds"})
    item = _items_named(db_engine, "Aspirin")[0]

    assert client.get(f"/items/{item.id}/activate").status_code == 404
    assert client.post(f"/items/{item.id}/activate", data={}).status_code == 404
