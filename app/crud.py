"""Data-access helpers: queries and mutations over `Item` rows."""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Item
from app.schemas import ItemCreate


def list_items(db: Session) -> list[Item]:
    """Return every item in unspecified order (sorting lives in services)."""
    return list(db.scalars(select(Item)))


def create_item(db: Session, data: ItemCreate) -> Item:
    """Persist a validated item and return the refreshed row."""
    item = Item(
        name=data.name,
        category=data.category,
        quantity=data.quantity,
        best_by_date=data.best_by_date,
        is_to_buy=data.is_to_buy,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_item(db: Session, item_id: int) -> Item | None:
    """Fetch one item by id, or None when it does not exist."""
    return db.get(Item, item_id)


def activate_item(db: Session, item: Item, best_by_date: date | None) -> Item:
    """Convert a to-buy item into an active item.

    Quantity stays 1 (a fresh purchase). The best-by date is stored for
    food and remains None for meds/household.
    """
    item.is_to_buy = False
    item.best_by_date = best_by_date
    db.commit()
    db.refresh(item)
    return item


def increment_item(db: Session, item: Item) -> Item:
    """Add one to the item's quantity and persist."""
    item.quantity += 1
    db.commit()
    db.refresh(item)
    return item


def decrement_item(db: Session, item: Item) -> Item:
    """Remove one from quantity, clamped at zero, and persist."""
    item.quantity = max(0, item.quantity - 1)
    db.commit()
    db.refresh(item)
    return item


def set_item_empty(db: Session, item: Item) -> Item:
    """Set the item's quantity to zero and persist."""
    item.quantity = 0
    db.commit()
    db.refresh(item)
    return item
