# Unit 06: Add Item

## Goal

Add items through a modal form: category, name, quantity, and — for food
only — a best-by date. `POST /items` validates with Pydantic and returns an
HTMX fragment that inserts the new row in its sorted position.

## Design

The header's "Add item" button opens a modal (HTMX fetch of the form). The
form submits as url-encoded and returns the updated dashboard body so sort
order is preserved. Validation errors return the form fragment with inline
messages.

## Implementation

### app/schemas.py
`ItemCreate(BaseModel)`:
- `name: str` (1–80 chars, stripped)
- `category: Category`
- `quantity: int` (default 1, ge 0)
- `best_by_date: date | None` (default None)
- `is_to_buy: bool` (default False)

A `model_validator` enforces the food-only rule: best_by_date required for
food, must be None for meds/household.

### app/routers/items.py
- `GET /items/new` → add-item form fragment (opens the modal).
- `POST /items` → validate, create via `crud.py`, return the dashboard body
  fragment so the new row lands in its correct sorted spot.
- On validation failure return the form fragment with error messages.

### app/crud.py
`create_item(db, data)` and `list_items(db)` helpers.

## Dependencies

- `python-multipart` (FastAPI form parsing)

## Verify when done

- [ ] Adding a food item places it correctly sorted and colored, no reload
- [ ] A best-by date on a med/household item is rejected
- [ ] Invalid/empty input shows an inline validation error, not a crash
