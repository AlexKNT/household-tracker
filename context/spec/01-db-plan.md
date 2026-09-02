# Unit 01: DB Plan

## Goal

Produce a written, unambiguous database specification — exact columns, types,
constraints, indexes — that Unit 02 implements verbatim. This unit writes
documentation and makes the migration decision; it writes no application
code.

## Design

Single table `items`. Status is derived, never stored (`architecture.md`
invariant 1). Best-by dates are food-only. The plan must make every
nullability and default explicit so the ORM model has zero ambiguity.

## Implementation

### Schema spec (the deliverable)

| column | type | null | default | constraint |
|---|---|---|---|---|
| id | INTEGER | no | — | PRIMARY KEY autoincrement |
| name | TEXT | no | — | — |
| category | TEXT (enum) | no | — | CHECK in ('meds','food','household') |
| quantity | INTEGER | no | 1 | CHECK (quantity >= 0) |
| best_by_date | DATE | yes | NULL | food-only (app-enforced) |
| comment | TEXT | yes | NULL | — |
| is_to_buy | BOOLEAN | no | 0 (false) | — |
| created_at | DATETIME | no | now | — |

### Derived rules (documented, not stored)

Record the status priority, color mapping, sort order, and purge window
exactly as they will be implemented in Unit 03, so there is one source of
truth to code against.

### Migration decision

Document the choice and its reasoning. For v1: use
`Base.metadata.create_all()` on startup — appropriate for a single-user,
single-machine SQLite app with one table and no data to migrate. Record that
Alembic is the upgrade path if schema changes or remote sync are ever
introduced.

### Data location

`data/household.db`, gitignored. The `data/` directory is created by the app
if missing.

## Dependencies

None — documentation only.

## Verify when done

- [ ] Every column, type, nullability, and default is pinned in writing
- [ ] Nullability matches `architecture.md` (best_by_date nullable, food-only)
- [ ] Derived status/color/sort/purge rules are recorded as the code target
- [ ] Migration strategy is chosen and its reasoning documented
