# Unit 02: DB Implementation

## Goal

Implement the data layer exactly as specified in Unit 01: the engine and
session factory, the SQLAlchemy 2.0 model, the category enum, table
creation, and model round-trip tests.

## Design

SQLAlchemy 2.0 declarative style (`Mapped[...]` + `mapped_column`). The
`Category` enum is a `StrEnum` stored as text with a CHECK constraint so the
database cannot hold junk values. No business logic in the model — status
derivation lives in Unit 03.

## Implementation

### app/db.py
- Engine for `sqlite:///data/household.db` with `check_same_thread=False`
  (SQLite + threads).
- `SessionLocal` session factory and a `Base` declarative base.
- `get_db()` dependency yielding a session and closing it.

### app/models.py
- `Category(StrEnum)` with `MEDS`, `FOOD`, `HOUSEHOLD`.
- `Item` model with columns from Unit 01, typed with `Mapped[...]`:
  `name: Mapped[str]`, `category: Mapped[Category]` (enum column),
  `quantity: Mapped[int]` (default 1), `best_by_date: Mapped[date | None]`,
  `comment: Mapped[str | None]`, `is_to_buy: Mapped[bool]` (default False),
  `created_at: Mapped[datetime]` (default now).

### Table creation
`Base.metadata.create_all(engine)` on startup (per Unit 01's decision).

### tests/test_models.py
- Tables create cleanly.
- An item round-trips (insert → fetch → update).
- `best_by_date` accepts `None` for a med item.

## Dependencies

- `sqlalchemy` (ORM)

## Verify when done

- [ ] `Item` rows insert, fetch, and update through a session
- [ ] `best_by_date` is nullable and works for meds/household
- [ ] The database file is created under `data/`
- [ ] `pytest` model tests pass
