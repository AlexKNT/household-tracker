"""Data-access helpers: queries and mutations over `Item` rows."""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Item
from app.schemas import ItemCreate
from app.services import should_purge


def list_items(db: Session, today: date) -> list[Item]:
    """Return visible items, purging date-expired rows at read time.

    Food rows a week past their best-by date are deleted here (lazy purge);
    out-of-stock rows (`quantity == 0`) are never auto-deleted. Sorting
    lives in `services.sort_key`.
    """
    items = list(db.scalars(select(Item)))
    purge_ids = {
        item.id
        for item in items
        if item.quantity != 0 and should_purge(item, today)
    }
    if purge_ids:
        surviving = [item for item in items if item.id not in purge_ids]
        for item in items:
            if item.id in purge_ids:
                db.delete(item)
        db.commit()
        return surviving
    return items


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


def restock_item(db: Session, item: Item) -> Item:
    """Create a to-buy reminder for the item and return the new row."""
    to_buy = Item(
        name=item.name,
        category=item.category,
        quantity=1,
        best_by_date=None,
        is_to_buy=True,
    )
    db.add(to_buy)
    db.commit()
    db.refresh(to_buy)
    return to_buy


def set_item_comment(db: Session, item: Item, comment: str | None) -> Item:
    """Replace the item's comment (`None` clears it) and persist."""
    item.comment = comment
    db.commit()
    db.refresh(item)
    return item
