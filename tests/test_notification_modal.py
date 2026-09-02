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


def _modal_fragment(html: str) -> str:
    """Extract just the modal markup from the full page."""
    start = html.index('id="notification-modal"')
    end = html.index("<!-- /notification-modal -->")
    return html[start:end]


def test_modal_renders_on_full_load(client: TestClient) -> None:
    html = client.get("/").text
    assert 'id="notification-modal"' in html
    assert "Needs attention" in html
    assert "Gone bad" in html
    assert "Eat soon" in html
    assert "To-buy" in html


def test_modal_groups_appear_in_order(client: TestClient) -> None:
    html = client.get("/").text
    assert html.index("Gone bad") < html.index("Eat soon") < html.index("To-buy")


def test_modal_lists_only_relevant_items(client: TestClient, db_engine: Engine) -> None:
    today = date.today()
    with Session(db_engine) as session:
        session.add_all(
            [
                Item(
                    name="Old cheese",
                    category=Category.FOOD,
                    quantity=1,
                    best_by_date=today - timedelta(days=1),
                ),
                Item(
                    name="Yogurt",
                    category=Category.FOOD,
                    quantity=1,
                    best_by_date=today + timedelta(days=2),
                ),
                Item(
                    name="Paper towels",
                    category=Category.HOUSEHOLD,
                    quantity=1,
                    is_to_buy=True,
                ),
                Item(name="Aspirin", category=Category.MEDS, quantity=2),
                Item(name="Milk", category=Category.FOOD, quantity=0),
            ]
        )
        session.commit()

    modal = _modal_fragment(client.get("/").text)

    assert "Old cheese" in modal
    assert "Yogurt" in modal
    assert "Paper towels" in modal

    # Regular meds and out-of-stock rows stay on the dashboard, not the modal.
    assert "Aspirin" not in modal
    assert "Milk" not in modal

    # Items land in their group, which is ordered gone-bad → eat-soon → to-buy.
    assert modal.index("Old cheese") < modal.index("Eat soon")
    assert modal.index("Eat soon") < modal.index("Yogurt") < modal.index("To-buy")
    assert modal.index("To-buy") < modal.index("Paper towels")


def test_modal_not_in_polling_fragment(client: TestClient) -> None:
    body = client.get("/dashboard/body").text
    assert "Gone bad" not in body
    assert "Eat soon" not in body
    assert "To-buy" not in body


def test_modal_dismiss_returns_empty(client: TestClient) -> None:
    response = client.post("/modal/dismiss")
    assert response.status_code == 200
    assert response.text == ""


def test_modal_reappears_on_next_full_load(client: TestClient) -> None:
    assert "Gone bad" in client.get("/").text
    client.post("/modal/dismiss")
    assert "Gone bad" in client.get("/").text
