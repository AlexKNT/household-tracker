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


def _add(db_engine: Engine, **overrides: object) -> Item:
    """Insert an item directly, bypassing form validation."""
    kwargs: dict[str, object] = dict(
        name="item",
        category=Category.FOOD,
        quantity=1,
        best_by_date=None,
        is_to_buy=False,
    )
    kwargs.update(overrides)
    item = Item(**kwargs)
    with Session(db_engine) as session:
        session.add(item)
        session.commit()
        session.refresh(item)
    return item


def test_expired_item_at_one_day_past_is_visible(
    client: TestClient, db_engine: Engine
) -> None:
    today = date.today()
    _add(db_engine, name="Old milk", best_by_date=today - timedelta(days=1))

    html = client.get("/").text

    assert "Old milk" in html
    assert "row--red" in html


def test_item_purged_exactly_seven_days_past_best_by(
    client: TestClient, db_engine: Engine
) -> None:
    today = date.today()
    item = _add(db_engine, name="Ancient eggs", best_by_date=today - timedelta(days=7))

    html = client.get("/").text

    assert "Ancient eggs" not in html
    with Session(db_engine) as session:
        assert session.get(Item, item.id) is None


def test_item_survives_at_six_days_past_best_by(
    client: TestClient, db_engine: Engine
) -> None:
    today = date.today()
    item = _add(db_engine, name="Stale bread", best_by_date=today - timedelta(days=6))

    html = client.get("/").text

    assert "Stale bread" in html
    with Session(db_engine) as session:
        assert session.get(Item, item.id) is not None


def test_out_of_stock_never_purged_regardless_of_age(
    client: TestClient, db_engine: Engine
) -> None:
    today = date.today()
    item = _add(
        db_engine,
        name="Empty juice",
        quantity=0,
        best_by_date=today - timedelta(days=30),
    )

    html = client.get("/").text

    assert "Empty juice" in html
    assert "row--out" in html
    with Session(db_engine) as session:
        assert session.get(Item, item.id) is not None


def test_meds_and_household_never_expire_or_purge(
    client: TestClient, db_engine: Engine
) -> None:
    today = date.today()
    old = today - timedelta(days=30)
    med = _add(db_engine, name="Aspirin", category=Category.MEDS, best_by_date=old)
    household = _add(
        db_engine, name="Dish soap", category=Category.HOUSEHOLD, best_by_date=old
    )

    html = client.get("/").text

    assert "Aspirin" in html
    assert "Dish soap" in html
    assert "row--green" in html
    with Session(db_engine) as session:
        assert session.get(Item, med.id) is not None
        assert session.get(Item, household.id) is not None
