"""Pydantic schemas for form input validation."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models import Category


class ItemCreate(BaseModel):
    """Validated input for creating an item.

    `best_by_date` is food-only: required for food, forbidden for meds and
    household (architecture invariant 2). `is_to_buy` is accepted for
    forward compatibility with Unit 07 but is not exposed by this form yet.
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
        if self.category is Category.FOOD:
            if self.best_by_date is None:
                raise ValueError("Food needs a best-by date.")
        elif self.best_by_date is not None:
            raise ValueError("Meds and household items cannot have a best-by date.")
        return self
