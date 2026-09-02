"""Pydantic schemas for form input validation."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models import Category


class ItemCreate(BaseModel):
    """Validated input for creating an item.

    `best_by_date` is food-only (architecture invariant 2). For a normal
    item it is required for food and forbidden for meds/household. For a
    to-buy item it is optional: food defaults to today, meds/household
    keep `None`.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str
    category: Category
    quantity: int = Field(default=1, ge=0)
    best_by_date: date | None = None
    is_to_buy: bool = False

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        if not value:
            raise ValueError("Name is required.")
        if len(value) > 80:
            raise ValueError("Name must be 80 characters or fewer.")
        return value

    @model_validator(mode="after")
    def _enforce_food_only(self) -> "ItemCreate":
        if self.is_to_buy:
            if self.category is Category.FOOD and self.best_by_date is None:
                self.best_by_date = date.today()
            elif self.category is not Category.FOOD and self.best_by_date is not None:
                raise ValueError("Meds and household items cannot have a best-by date.")
            return self

        if self.category is Category.FOOD:
            if self.best_by_date is None:
                raise ValueError("Food needs a best-by date.")
        elif self.best_by_date is not None:
            raise ValueError("Meds and household items cannot have a best-by date.")
        return self


class ItemActivate(BaseModel):
    """Validated input for activating a to-buy item.

    The router supplies the item's category; food purchases require a
    best-by date and meds/household must not receive one (invariant 2).
    """

    category: Category
    best_by_date: date | None = None

    @model_validator(mode="after")
    def _enforce_food_only(self) -> "ItemActivate":
        if self.category is Category.FOOD:
            if self.best_by_date is None:
                raise ValueError("Food needs a best-by date.")
        elif self.best_by_date is not None:
            raise ValueError("Meds and household items cannot have a best-by date.")
        return self
