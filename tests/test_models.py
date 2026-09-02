from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base
from app.models import Category, Item


@pytest.fixture
def db_session(tmp_path: Path) -> Session:
    """A session bound to a throwaway SQLite file per test."""
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_items_table_registered() -> None:
    assert "items" in Base.metadata.tables


def test_item_round_trip(db_session: Session) -> None:
    item = Item(
        name="Greek yogurt",
        category=Category.FOOD,
        quantity=3,
        best_by_date=date(2026, 9, 5),
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    fetched = db_session.get(Item, item.id)
    assert fetched is not None
    assert fetched.name == "Greek yogurt"
    assert fetched.category is Category.FOOD
    assert fetched.quantity == 3
    assert fetched.best_by_date == date(2026, 9, 5)

    # Update the quantity and confirm it persists.
    fetched.quantity = 2
    db_session.commit()
    db_session.refresh(fetched)
    assert fetched.quantity == 2


def test_best_by_date_nullable_for_med(db_session: Session) -> None:
    item = Item(name="Aspirin", category=Category.MEDS, quantity=2)
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    assert item.best_by_date is None


def test_schema_nullability_matches_architecture() -> None:
    columns = Item.__table__.columns
    assert columns["id"].nullable is False
    assert columns["name"].nullable is False
    assert columns["category"].nullable is False
    assert columns["quantity"].nullable is False
    assert columns["best_by_date"].nullable is True
    assert columns["comment"].nullable is True
    assert columns["is_to_buy"].nullable is False
    assert columns["created_at"].nullable is False


def test_category_enum_values() -> None:
    assert [member.value for member in Category] == ["meds", "food", "household"]


def test_defaults_on_insert(db_session: Session) -> None:
    item = Item(name="Salt", category=Category.HOUSEHOLD)
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    assert item.quantity == 1
    assert item.best_by_date is None
    assert item.comment is None
    assert item.is_to_buy is False
    assert item.created_at is not None


def test_full_round_trip_with_comment_and_to_buy(db_session: Session) -> None:
    best_by = date(2026, 9, 10)
    item = Item(
        name="Apples",
        category=Category.FOOD,
        quantity=1,
        best_by_date=best_by,
        comment="for the pie",
        is_to_buy=True,
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    fetched = db_session.get(Item, item.id)
    assert fetched is not None
    assert fetched.name == "Apples"
    assert fetched.category is Category.FOOD
    assert fetched.quantity == 1
    assert fetched.best_by_date == best_by
    assert fetched.comment == "for the pie"
    assert fetched.is_to_buy is True
    assert fetched.created_at is not None
