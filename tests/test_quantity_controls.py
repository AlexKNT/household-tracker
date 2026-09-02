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
        return list(session.query(Item).filter(Item.name == name))


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
    return _items_named(db_engine, name)[0].id


def test_increment_updates_quantity_and_rerenders(
    client: TestClient, db_engine: Engine
) -> None:
    item_id = _add_item(db_engine, client, quantity="2")

    response = client.post(f"/items/{item_id}/increment")

    assert response.status_code == 200
    assert 'id="dashboard-body"' in response.text
    assert "3 left" in response.text
    assert _items_named(db_engine, "Aspirin")[0].quantity == 3


def test_decrement_updates_quantity(
    client: TestClient, db_engine: Engine
) -> None:
    item_id = _add_item(db_engine, client, quantity="2")

    response = client.post(f"/items/{item_id}/decrement")

    assert response.status_code == 200
    assert "1 left" in response.text
    assert _items_named(db_engine, "Aspirin")[0].quantity == 1


def test_decrement_never_goes_below_zero(
    client: TestClient, db_engine: Engine
) -> None:
    item_id = _add_item(db_engine, client, quantity="1")

    client.post(f"/items/{item_id}/decrement")
    response = client.post(f"/items/{item_id}/decrement")

    assert response.status_code == 200
    assert "row--out" in response.text
    assert _items_named(db_engine, "Aspirin")[0].quantity == 0


def test_empty_sets_quantity_to_zero_and_moves_to_top(
    client: TestClient, db_engine: Engine
) -> None:
    today = date.today()
    _add_item(db_engine, client, name="Aspirin", quantity="2")
    food_id = _add_item(
        db_engine,
        client,
        name="Milk",
        category="food",
        quantity="3",
        best_by_date=(today + timedelta(days=5)).isoformat(),
    )

    response = client.post(f"/items/{food_id}/empty")

    assert response.status_code == 200
    assert "row--out" in response.text
    # Out-of-stock section renders before meds, so the emptied food moves up.
    assert response.text.index("Milk") < response.text.index("Aspirin")
    assert _items_named(db_engine, "Milk")[0].quantity == 0


def test_out_of_stock_persists_across_reloads(
    client: TestClient, db_engine: Engine
) -> None:
    item_id = _add_item(db_engine, client, quantity="1")
    client.post(f"/items/{item_id}/empty")

    html = client.get("/").text

    assert "row--out" in html
    assert "Aspirin" in html
    assert _items_named(db_engine, "Aspirin")[0].quantity == 0


def test_quantity_endpoints_404_for_missing_item(client: TestClient) -> None:
    assert client.post("/items/9999/increment").status_code == 404
    assert client.post("/items/9999/decrement").status_code == 404
    assert client.post("/items/9999/empty").status_code == 404


def test_row_renders_active_quantity_buttons(
    client: TestClient, db_engine: Engine
) -> None:
    item_id = _add_item(db_engine, client, quantity="1")

    html = client.get("/").text

    assert f'hx-post="/items/{item_id}/increment"' in html
    assert f'hx-post="/items/{item_id}/decrement"' in html
    assert f'hx-post="/items/{item_id}/empty"' in html


def test_to_buy_row_has_no_active_quantity_controls(
    client: TestClient, db_engine: Engine
) -> None:
    client.post(
        "/items", data={"name": "Apples", "category": "food", "is_to_buy": "true"}
    )
    item_id = _items_named(db_engine, "Apples")[0].id

    html = client.get("/").text

    assert f'hx-post="/items/{item_id}/increment"' not in html
    assert f'hx-post="/items/{item_id}/decrement"' not in html
    assert f'hx-post="/items/{item_id}/empty"' not in html
