# Database Schema — Household Inventory Tracker

Authoritative schema specification for the `items` table. Unit 02 implements
this verbatim in `app/models.py` and `app/db.py`. If this document and the
code ever disagree, this document wins until it is updated.

## 1. Overview

One table, `items`, in a single SQLite file at `data/household.db`. Single
user, single machine — no ownership columns, no foreign keys, no joins.

Status is **derived, never stored** (§4). The table stores only facts;
`app/services.py` turns those facts into statuses, colors, and sort order.

## 2. Table: items

### Columns

| column | SQLite type | Python type | null | default | constraints |
|---|---|---|---|---|---|
| id | INTEGER | `int` | no | — | PRIMARY KEY AUTOINCREMENT |
| name | TEXT | `str` | no | — | — |
| category | TEXT | `Category` (`StrEnum`) | no | — | CHECK category IN ('meds','food','household') |
| quantity | INTEGER | `int` | no | 1 | CHECK quantity >= 0 |
| best_by_date | DATE | `date \| None` | yes | NULL | food-only (app-enforced) |
| comment | TEXT | `str \| None` | yes | NULL | — |
| is_to_buy | BOOLEAN | `bool` | no | 0 (false) | — |
| created_at | DATETIME | `datetime` | no | now | — |

### SQLite type notes

- `DATE` is stored as TEXT in ISO-8601 (`YYYY-MM-DD`); SQLAlchemy's `Date`
  type handles (de)serialization. This keeps dates real — required so the
  schema stays sync-ready.
- `BOOLEAN` is stored as INTEGER 0/1; SQLAlchemy's `Boolean` maps to `bool`.
- `DATETIME` defaults to the current time via SQLAlchemy's `default=` (a
  Python-side callable), not a DB trigger.

### DDL (reference)

```sql
CREATE TABLE items (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT    NOT NULL,
    category     TEXT    NOT NULL
                 CHECK (category IN ('meds','food','household')),
    quantity     INTEGER NOT NULL DEFAULT 1
                 CHECK (quantity >= 0),
    best_by_date DATE,
    comment      TEXT,
    is_to_buy    BOOLEAN NOT NULL DEFAULT 0,
    created_at   DATETIME NOT NULL DEFAULT (datetime('now'))
);
```

### Indexes

None for v1. A single-user household inventory is tiny (tens to hundreds of
rows) and every query is a full read; no query is selective enough to
benefit. Revisit only if data volume or remote sync changes the access
pattern.

### The food-only rule

`best_by_date` is semantically NULL for meds/household. The database does
**not** enforce this — it is a cross-column rule that is awkward in SQLite —
so it is enforced in `app/schemas.py` (input validation) and re-asserted by
`app/services.py` (derivation). This is architecture invariant 2.

## 3. Category enum

| value | meaning | has best-by? |
|---|---|---|
| meds | medications | no |
| food | perishable food | yes |
| household | non-perishable goods | no |

## 4. Derived rules (the target for Unit 03)

Status is computed at read time, never written. Priority order — first match
wins:

1. `is_to_buy` → **TO_BUY** (purple)
2. `quantity == 0` → **OUT_OF_STOCK** (dark flashing red, never deleted)
3. food and `best_by_date < today` → **EXPIRED** (red; purged 7 days later)
4. food and `0 <= days_left <= 3` → **EAT_SOON** (red at 0, yellow at 1–3)
5. otherwise → **FINE** (green)

Purge: food rows are deleted when `days_left <= -7`. Out-of-stock rows are
never auto-deleted. (Fully derived from `best_by_date` — no `expired_at`
column, no write-on-read.)

The precise color mapping and sort order live in
`context/spec/03-domain-services.md` and are implemented in
`app/services.py`.

## 5. Migration strategy

**v1:** `Base.metadata.create_all(engine)` on startup.

- Rationale: one table, no existing data to migrate, single-user local app.
  A migration framework is dead weight at this stage.

**Future:** introduce Alembic when (a) the schema needs an additive or
breaking change, or (b) remote sync arrives. No action required now.

## 6. Data location & lifecycle

- File: `data/household.db`, created on startup if the directory is missing.
- Git: `data/` is gitignored (see `.gitignore`).
- Backup/export: out of scope for v1.
