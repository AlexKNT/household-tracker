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


def test_dashboard_lists_items_and_sections(client: TestClient, db_engine: Engine) -> None:
    today = date.today()
    with Session(db_engine) as session:
        session.add_all(
            [
                Item(name="Aspirin", category=Category.MEDS, quantity=2),
                Item(
                    name="Greek yogurt",
                    category=Category.FOOD,
                    quantity=3,
                    best_by_date=today + timedelta(days=2),
                ),
                Item(name="Paper towels", category=Category.HOUSEHOLD, quantity=1),
            ]
        )
        session.commit()

    html = client.get("/").text
    assert "Aspirin" in html
    assert "Greek yogurt" in html
    assert "Paper towels" in html
    assert "Out of stock" in html
    assert "Meds" in html
    assert "Food" in html
    assert "Household" in html


def test_dashboard_row_colors(client: TestClient, db_engine: Engine) -> None:
    today = date.today()
    with Session(db_engine) as session:
        session.add_all(
            [
                Item(name="Eat soon", category=Category.FOOD, quantity=1, best_by_date=today + timedelta(days=2)),
                Item(name="Fine", category=Category.FOOD, quantity=1, best_by_date=today + timedelta(days=10)),
                Item(name="Expired", category=Category.FOOD, quantity=1, best_by_date=today - timedelta(days=1)),
                Item(name="To buy", category=Category.FOOD, quantity=1, is_to_buy=True),
                Item(name="Gone", category=Category.FOOD, quantity=0),
            ]
        )
        session.commit()

    html = client.get("/").text
    assert "row--yellow" in html
    assert "row--green" in html
    assert "row--red" in html
    assert "row--purple" in html
    assert "row--out" in html


def test_out_of_stock_section_comes_first(client: TestClient, db_engine: Engine) -> None:
    with Session(db_engine) as session:
        session.add_all(
            [
                Item(name="Aspirin", category=Category.MEDS, quantity=2),
                Item(name="Milk", category=Category.FOOD, quantity=0),
            ]
        )
        session.commit()

    html = client.get("/").text
    out_idx = html.index("Out of stock")
    meds_idx = html.index("Meds")
    milk_idx = html.index("Milk")
    assert out_idx < milk_idx < meds_idx


def test_dashboard_body_partial(client: TestClient, db_engine: Engine) -> None:
    with Session(db_engine) as session:
        session.add(Item(name="Aspirin", category=Category.MEDS, quantity=2))
        session.commit()

    response = client.get("/dashboard/body")
    assert response.status_code == 200
    assert "Aspirin" in response.text
    assert 'hx-get="/dashboard/body"' in response.text
    assert 'hx-trigger="every 10s"' in response.text


def test_dashboard_empty_state(client: TestClient) -> None:
    html = client.get("/").text
    assert "No out of stock items." in html
    assert "No meds items." in html
    assert "No food items." in html
    assert "No household items." in html
