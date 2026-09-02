from __future__ import annotations

from datetime import date
from enum import StrEnum

from app.config import settings
from app.models import Category, Item


class Status(StrEnum):
    """Derived lifecycle state of an item (never stored)."""

    TO_BUY = "to_buy"
    OUT_OF_STOCK = "out_of_stock"
    EXPIRED = "expired"
    EAT_SOON = "eat_soon"
    FINE = "fine"


# Dashboard section order: out-of-stock is handled separately, then the
# categories run meds → food → household.
CATEGORY_ORDER: dict[Category, int] = {
    Category.MEDS: 0,
    Category.FOOD: 1,
    Category.HOUSEHOLD: 2,
}

# Within a category, urgency order.
_URGENCY: dict[Status, int] = {
    Status.EXPIRED: 0,
    Status.EAT_SOON: 1,
    Status.FINE: 2,
    Status.TO_BUY: 3,
}

_NO_DAYS = 10**9  # sentinel: items without a best-by date sort after dated ones


def days_left(item: Item, today: date) -> int | None:
    """Whole days until best-by for food; None for meds/household."""
    if item.category is Category.FOOD and item.best_by_date is not None:
        return (item.best_by_date - today).days
    return None


def derive_status(item: Item, today: date) -> Status:
    """Compute the item's status. The first matching rule wins."""
    if item.is_to_buy:
        return Status.TO_BUY
    if item.quantity == 0:
        return Status.OUT_OF_STOCK
    days = days_left(item, today)
    if days is None:
        return Status.FINE
    if days < 0:
        return Status.EXPIRED
    if days <= settings.EAT_SOON_DAYS:
        return Status.EAT_SOON
    return Status.FINE


def status_color(status: Status, remaining_days: int | None) -> str:
    """Return the `ui-context.md` color token key for a status."""
    if status is Status.TO_BUY:
        return "purple"
    if status is Status.OUT_OF_STOCK:
        return "out"
    if status is Status.EXPIRED:
        return "red"
    if status is Status.EAT_SOON:
        return "red" if remaining_days == 0 else "yellow"
    return "green"


def sort_key(item: Item, today: date) -> tuple[int, int, int, str]:
    """Deterministic dashboard sort key."""
    status = derive_status(item, today)
    if status is Status.OUT_OF_STOCK:
        section = 0
        urgency = 0
    else:
        section = CATEGORY_ORDER[item.category] + 1
        urgency = _URGENCY[status]
    days = days_left(item, today)
    return (section, urgency, days if days is not None else _NO_DAYS, item.name)


def is_expired(item: Item, today: date) -> bool:
    """True when the best-by date has passed (food only)."""
    days = days_left(item, today)
    return days is not None and days < 0


def should_purge(item: Item, today: date) -> bool:
    """True when an expired food item is a week past its best-by date."""
    days = days_left(item, today)
    return days is not None and days <= -settings.PURGE_AFTER_DAYS
