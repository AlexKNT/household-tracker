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
) -> int:
    client.post(
        "/items",
        data={"name": name, "category": category, "quantity": quantity},
    )
    return _items_named(db_engine, name)[0].id


def test_dashboard_shows_add_note_when_empty(
    client: TestClient, db_engine: Engine
) -> None:
    item_id = _add_item(db_engine, client)

    html = client.get("/").text

    assert "Add note" in html
    assert f'hx-get="/items/{item_id}/comment/edit"' in html


def test_comment_edit_renders_form(client: TestClient, db_engine: Engine) -> None:
    item_id = _add_item(db_engine, client)

    response = client.get(f"/items/{item_id}/comment/edit")

    assert response.status_code == 200
    assert 'name="comment"' in response.text
    assert f'hx-patch="/items/{item_id}/comment"' in response.text
    assert f'hx-include="#comment-input-{item_id}"' in response.text
    assert 'hx-trigger="click consume"' in response.text
    assert 'hx-swap="outerHTML"' in response.text


def test_comment_edit_prefills_existing(
    client: TestClient, db_engine: Engine
) -> None:
    item_id = _add_item(db_engine, client)
    client.patch(f"/items/{item_id}/comment", data={"comment": "take with food"})

    response = client.get(f"/items/{item_id}/comment/edit")

    assert 'value="take with food"' in response.text


def test_save_comment_returns_cell_and_persists(
    client: TestClient, db_engine: Engine
) -> None:
    item_id = _add_item(db_engine, client)

    response = client.patch(
        f"/items/{item_id}/comment", data={"comment": "for Tuesday"}
    )

    assert response.status_code == 200
    assert "row__comment" in response.text
    assert "for Tuesday" in response.text
    # The PATCH swaps only the cell, not the whole dashboard.
    assert 'id="dashboard-body"' not in response.text
    assert _items_named(db_engine, "Aspirin")[0].comment == "for Tuesday"


def test_save_comment_persists_across_reloads(
    client: TestClient, db_engine: Engine
) -> None:
    item_id = _add_item(db_engine, client)
    client.patch(f"/items/{item_id}/comment", data={"comment": "for Tuesday"})

    html = client.get("/").text

    assert "for Tuesday" in html
    assert "Add note" not in html


def test_clearing_comment_returns_to_add_note(
    client: TestClient, db_engine: Engine
) -> None:
    item_id = _add_item(db_engine, client)
    client.patch(f"/items/{item_id}/comment", data={"comment": "for Tuesday"})

    response = client.patch(f"/items/{item_id}/comment", data={"comment": "   "})

    assert response.status_code == 200
    assert "Add note" in response.text
    assert _items_named(db_engine, "Aspirin")[0].comment is None


def test_comment_whitespace_is_stripped(
    client: TestClient, db_engine: Engine
) -> None:
    item_id = _add_item(db_engine, client)

    client.patch(
        f"/items/{item_id}/comment", data={"comment": "  take with food  "}
    )

    assert _items_named(db_engine, "Aspirin")[0].comment == "take with food"


def test_comment_endpoints_404_for_missing_item(client: TestClient) -> None:
    assert client.get("/items/9999/comment/edit").status_code == 404
    assert (
        client.patch("/items/9999/comment", data={"comment": "x"}).status_code
        == 404
    )


def test_to_buy_row_also_renders_comment_cell(
    client: TestClient, db_engine: Engine
) -> None:
    client.post(
        "/items", data={"name": "Apples", "category": "food", "is_to_buy": "true"}
    )
    item_id = _items_named(db_engine, "Apples")[0].id

    html = client.get("/").text

    assert f'hx-get="/items/{item_id}/comment/edit"' in html
    assert 'hx-trigger="click consume"' in html
