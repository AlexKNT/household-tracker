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
