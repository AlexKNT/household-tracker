from datetime import date

import pytest
from pydantic import ValidationError

from app.models import Category
from app.schemas import ItemCreate


def test_name_is_stripped() -> None:
    item = ItemCreate(name="  Milk  ", category=Category.FOOD, best_by_date=date(2026, 9, 5))
    assert item.name == "Milk"


def test_empty_name_rejected() -> None:
    with pytest.raises(ValidationError, match="Name is required"):
        ItemCreate(name="   ", category=Category.MEDS)


def test_name_over_80_chars_rejected() -> None:
    with pytest.raises(ValidationError, match="80 characters"):
        ItemCreate(name="x" * 81, category=Category.MEDS)


def test_quantity_defaults_to_one() -> None:
    item = ItemCreate(name="Aspirin", category=Category.MEDS)
    assert item.quantity == 1


def test_negative_quantity_rejected() -> None:
    with pytest.raises(ValidationError):
        ItemCreate(name="Aspirin", category=Category.MEDS, quantity=-1)


def test_category_coerced_from_string() -> None:
    item = ItemCreate(name="Milk", category="food", best_by_date=date(2026, 9, 5))
    assert item.category is Category.FOOD


def test_is_to_buy_defaults_false() -> None:
    item = ItemCreate(name="Milk", category=Category.FOOD, best_by_date=date(2026, 9, 5))
    assert item.is_to_buy is False


def test_food_requires_best_by_date() -> None:
    with pytest.raises(ValidationError, match="needs a best-by date"):
        ItemCreate(name="Milk", category=Category.FOOD)


def test_meds_reject_best_by_date() -> None:
    with pytest.raises(ValidationError, match="cannot have a best-by date"):
        ItemCreate(name="Aspirin", category=Category.MEDS, best_by_date=date(2026, 9, 5))


def test_household_reject_best_by_date() -> None:
    with pytest.raises(ValidationError, match="cannot have a best-by date"):
        ItemCreate(name="Soap", category=Category.HOUSEHOLD, best_by_date=date(2026, 9, 5))
