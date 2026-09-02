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
        return list(
            session.query(Item).filter(Item.name == name).order_by(Item.id)
        )


def _add_item(
    db_engine: Engine,
    client: TestClient,
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


def test_restock_creates_to_buy_for_item(
    client: TestClient, db_engine: Engine
) -> None:
    item_id = _add_item(db_engine, client)

    response = client.post(f"/items/{item_id}/restock")

    assert response.status_code == 200
    assert 'id="dashboard-body"' in response.text
    assert "row--purple" in response.text
    assert "to buy" in response.text

    items = _items_named(db_engine, "Aspirin")
    assert len(items) == 2
    to_buy = items[1]
    assert to_buy.is_to_buy is True
    assert to_buy.quantity == 1
    assert to_buy.best_by_date is None
    assert to_buy.category is Category.MEDS


def test_restock_food_keeps_no_best_by_date(
    client: TestClient, db_engine: Engine
) -> None:
    today = date.today()
    item_id = _add_item(
        db_engine,
        client,
        name="Milk",
        category="food",
        quantity="3",
        best_by_date=(today + timedelta(days=5)).isoformat(),
    )

    client.post(f"/items/{item_id}/restock")

    items = _items_named(db_engine, "Milk")
    assert len(items) == 2
    to_buy = items[1]
    assert to_buy.is_to_buy is True
    assert to_buy.category is Category.FOOD
    assert to_buy.best_by_date is None


def test_restock_out_of_stock_keeps_original_row(
    client: TestClient, db_engine: Engine
) -> None:
    item_id = _add_item(db_engine, client, quantity="1")
    client.post(f"/items/{item_id}/empty")

    response = client.post(f"/items/{item_id}/restock")

    assert response.status_code == 200
    assert "row--out" in response.text
    assert "row--purple" in response.text

    items = _items_named(db_engine, "Aspirin")
    assert len(items) == 2
    active = next(i for i in items if not i.is_to_buy)
    to_buy = next(i for i in items if i.is_to_buy)
    assert active.quantity == 0
    assert to_buy.quantity == 1


def test_restock_appears_in_modal_to_buy_group(
    client: TestClient, db_engine: Engine
) -> None:
    item_id = _add_item(db_engine, client, name="Soap", category="household")

    client.post(f"/items/{item_id}/restock")

    html = client.get("/").text
    start = html.index('id="notification-modal"')
    end = html.index("<!-- /notification-modal -->")
    modal = html[start:end]

    assert modal.index("To-buy") < modal.index("Soap")


def test_restock_404_for_missing_item(client: TestClient) -> None:
    assert client.post("/items/9999/restock").status_code == 404


def test_row_renders_restock_button(
    client: TestClient, db_engine: Engine
) -> None:
    item_id = _add_item(db_engine, client)

    html = client.get("/").text

    assert f'hx-post="/items/{item_id}/restock"' in html


def test_to_buy_row_has_no_active_restock_button(
    client: TestClient, db_engine: Engine
) -> None:
    client.post(
        "/items", data={"name": "Apples", "category": "food", "is_to_buy": "true"}
    )
    item_id = _items_named(db_engine, "Apples")[0].id

    html = client.get("/").text

    assert f'hx-post="/items/{item_id}/restock"' not in html
