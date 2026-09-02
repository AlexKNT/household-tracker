from datetime import date, timedelta

from app.models import Category, Item
from app.services import (
    Status,
    days_left,
    derive_status,
    is_expired,
    should_purge,
    sort_key,
    status_color,
)

TODAY = date(2026, 9, 3)


def make_item(**overrides: object) -> Item:
    kwargs: dict[str, object] = dict(
        name="item",
        category=Category.FOOD,
        quantity=1,
        best_by_date=None,
        is_to_buy=False,
    )
    kwargs.update(overrides)
    return Item(**kwargs)


# --- days_left ---


def test_days_left_for_food() -> None:
    item = make_item(best_by_date=TODAY + timedelta(days=3))
    assert days_left(item, TODAY) == 3


def test_days_left_zero_on_best_by_day() -> None:
    item = make_item(best_by_date=TODAY)
    assert days_left(item, TODAY) == 0


def test_days_left_none_for_non_food() -> None:
    med = make_item(category=Category.MEDS, best_by_date=TODAY)
    assert days_left(med, TODAY) is None


def test_days_left_none_when_no_date() -> None:
    food = make_item(best_by_date=None)
    assert days_left(food, TODAY) is None


# --- derive_status ---


def test_derive_to_buy() -> None:
    assert derive_status(make_item(is_to_buy=True), TODAY) is Status.TO_BUY


def test_derive_out_of_stock() -> None:
    assert derive_status(make_item(quantity=0), TODAY) is Status.OUT_OF_STOCK


def test_derive_expired() -> None:
    item = make_item(best_by_date=TODAY - timedelta(days=1))
    assert derive_status(item, TODAY) is Status.EXPIRED


def test_derive_eat_soon_today() -> None:
    item = make_item(best_by_date=TODAY)
    assert derive_status(item, TODAY) is Status.EAT_SOON


def test_derive_eat_soon_three_days() -> None:
    item = make_item(best_by_date=TODAY + timedelta(days=3))
    assert derive_status(item, TODAY) is Status.EAT_SOON


def test_derive_fine_four_days() -> None:
    item = make_item(best_by_date=TODAY + timedelta(days=4))
    assert derive_status(item, TODAY) is Status.FINE


def test_derive_fine_for_med_and_household() -> None:
    assert derive_status(make_item(category=Category.MEDS), TODAY) is Status.FINE
    assert derive_status(make_item(category=Category.HOUSEHOLD), TODAY) is Status.FINE


# --- priority ---


def test_to_buy_beats_out_of_stock() -> None:
    item = make_item(is_to_buy=True, quantity=0)
    assert derive_status(item, TODAY) is Status.TO_BUY


def test_out_of_stock_beats_expired() -> None:
    item = make_item(quantity=0, best_by_date=TODAY - timedelta(days=2))
    assert derive_status(item, TODAY) is Status.OUT_OF_STOCK


def test_non_food_never_expires() -> None:
    med = make_item(category=Category.MEDS, best_by_date=TODAY - timedelta(days=30))
    assert derive_status(med, TODAY) is Status.FINE


# --- status_color ---


def test_status_colors() -> None:
    assert status_color(Status.TO_BUY, None) == "purple"
    assert status_color(Status.OUT_OF_STOCK, None) == "out"
    assert status_color(Status.EXPIRED, -1) == "red"
    assert status_color(Status.EAT_SOON, 0) == "red"
    assert status_color(Status.EAT_SOON, 2) == "yellow"
    assert status_color(Status.FINE, 10) == "green"


# --- sort_key ---


def test_sort_order() -> None:
    items = [
        make_item(name="household", category=Category.HOUSEHOLD),
        make_item(name="food-tobuy", is_to_buy=True),
        make_item(name="food-fine", best_by_date=TODAY + timedelta(days=10)),
        make_item(name="food-eatsoon", best_by_date=TODAY + timedelta(days=2)),
        make_item(name="food-expired", best_by_date=TODAY - timedelta(days=2)),
        make_item(name="food-expired-older", best_by_date=TODAY - timedelta(days=5)),
        make_item(name="med", category=Category.MEDS),
        make_item(name="out-stock", quantity=0),
    ]
    ordered = sorted(items, key=lambda i: sort_key(i, TODAY))
    assert [i.name for i in ordered] == [
        "out-stock",
        "med",
        "food-expired-older",
        "food-expired",
        "food-eatsoon",
        "food-fine",
        "food-tobuy",
        "household",
    ]


# --- expiry / purge ---


def test_expiry_and_purge_window() -> None:
    expired = make_item(best_by_date=TODAY - timedelta(days=1))
    assert is_expired(expired, TODAY) is True
    assert should_purge(expired, TODAY) is False

    at_six = make_item(best_by_date=TODAY - timedelta(days=6))
    assert should_purge(at_six, TODAY) is False

    at_seven = make_item(best_by_date=TODAY - timedelta(days=7))
    assert should_purge(at_seven, TODAY) is True


def test_non_food_never_expires_or_purges() -> None:
    med = make_item(category=Category.MEDS, best_by_date=TODAY - timedelta(days=100))
    assert is_expired(med, TODAY) is False
    assert should_purge(med, TODAY) is False
