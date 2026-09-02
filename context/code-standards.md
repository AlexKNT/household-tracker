# Code Standards

## General

- Keep modules small and single-purpose. One file, one responsibility
  (`models.py` = schema, `services.py` = rules, `routers/` = HTTP).
- Fix root causes; never layer workarounds or special cases in templates.
- Do not mix concerns in one route: a route parses input, calls a service,
  renders a fragment, returns HTML — and does nothing else.
- Use Python 3.11+ features where they aid clarity: `T | None` unions,
  `Literal`, `StrEnum`, `dataclasses`.

## Python & Typing

These rules are the project's bedrock — types are the first line of defense.

- **Type hints on every public function and method**, including parameters
  and return type. No bare `def` signatures.
- **No `Any`, ever.** If a type is unknown, it is a `typing` generic or a
  `Protocol`, not `Any`.
- **Give absence a type.** "No date" is `best_by_date: date | None`, not an
  empty string or a sentinel `0`.
- **Let types enforce the rules.** Categories and statuses are enums, so an
  invalid value is unrepresentable:

```python
from enum import StrEnum

class Category(StrEnum):
    MEDS = "meds"
    FOOD = "food"
    HOUSEHOLD = "household"

class Status(StrEnum):
    TO_BUY = "to_buy"
    OUT_OF_STOCK = "out_of_stock"
    EXPIRED = "expired"
    EAT_SOON = "eat_soon"
    FINE = "fine"
```

- **Make errors part of the contract.** Services raise typed exceptions
  (e.g. `ValidationError`, `ItemNotFound`); routes translate them to
  `HTTPException` with the correct status. Never return `None` to signal
  failure when an exception is clearer.
- **Handle every possible case.** `match` / `if` chains over enums must be
  exhaustive; use `assert_never` from `typing` for the unreachable branch.
- **Validate at boundaries.** All form input goes through a Pydantic model
  in `schemas.py` before any logic runs. After validation, trust the types.
- **Prefer Pydantic models and dataclasses over raw dicts** for any data
  with structure.

## SQLAlchemy

- Use SQLAlchemy 2.0 declarative style: `Mapped[...]` + `mapped_column()`.
- Model classes in `models.py`; no business logic in models (that lives in
  `services.py`).
- Use an `Enum` column type for `category`, so the DB can't hold junk.
- `nullable=False` / `nullable=True` must mirror the schema in
  `architecture.md` exactly (e.g. `best_by_date` is nullable, food-only).

## FastAPI & Routers

- Routers are thin and return HTML fragments, not JSON (see architecture
  invariants).
- One endpoint per action, HTMX-oriented:
  `POST /items`, `POST /items/{id}/increment`,
  `POST /items/{id}/decrement`, `POST /items/{id}/empty`,
  `POST /items/{id}/restock`, `PATCH /items/{id}/comment`.
- Every endpoint returns `HTMLResponse` rendered from a `templates/partials/`
  fragment, so HTMX can swap it in without a page reload.
- Raise `HTTPException` for client errors; include a message the fragment
  can display to the user.

## Templates & HTMX

- One fragment per responsibility in `templates/partials/` — row, modal,
  add form, dashboard body.
- Use `hx-post`/`hx-target`/`hx-swap` precisely; no full page reloads on
  actions, and no JavaScript beyond HTMX attributes.
- Inline editing (comment cell) uses HTMX's `hx-trigger` + `hx-put` pattern,
  not a separate JS framework.

## CSS

- Use only the custom properties defined in `ui-context.md`. No raw hex
  values outside `:root`.
- Class naming is BEM-like, keyed to status: `row--purple`, `row--out`,
  `row--yellow`, etc.
- The `flash` keyframes are the only animation in the project.

## Testing

- `pytest` + `httpx` (`TestClient`) for endpoints; plain pytest for
  `services.py`.
- Unit-test the invariants explicitly:
  - status derivation order (to-buy → out-of-stock → expired → eat-soon → fine)
  - out-of-stock is never auto-deleted
  - `best_by_date` is rejected for meds/household
  - sort order (out-of-stock → meds → food → household)
- Keep tests readable: arrange, act, assert, with one behavior per test.

## Naming & Imports

- `snake_case` for functions/variables, `PascalCase` for classes and enums,
  `UPPER_CASE` for constants.
- Import order: standard library, third-party, then local (`app.*`) modules.
- Public API surface (service functions, crud functions) gets docstrings;
  trivial helpers do not.