# Unit 03: Domain Services

## Goal

Implement `app/services.py` as the single source of truth for business rules:
status derivation, days-left math, color mapping, sort order, and the purge
window. Exhaustively unit-tested.

## Design

Pure functions that take an item and "today" and return plain values — no DB
access, no HTTP. This makes them trivially testable and keeps the invariants
in one place. `Category` lives in `models.py`; the domain `Status` enum lives
here.

## Implementation

### Status enum
`Status(StrEnum)`: `TO_BUY`, `OUT_OF_STOCK`, `EXPIRED`, `EAT_SOON`, `FINE`.

### derive_status(item, today) -> Status
Priority order (first match wins):
1. `is_to_buy` → `TO_BUY`
2. `quantity == 0` → `OUT_OF_STOCK`
3. food with `best_by_date < today` → `EXPIRED`
4. food with `0 <= days_left <= 3` → `EAT_SOON`
5. otherwise → `FINE` (includes meds/household with quantity > 0)

### days_left(item, today) -> int | None
`(best_by_date - today).days` for food, `None` otherwise.

### status_color(status, days_left) -> str
Returns the `ui-context.md` token key:
- `TO_BUY` → purple · `OUT_OF_STOCK` → out (dark flashing red)
- `EXPIRED` → red · `EAT_SOON` → red when `days_left == 0`, else yellow
- `FINE` → green

### sort_key(item, today)
Enforce the fixed dashboard order in a single comparable key:
out-of-stock first, then category order (meds → food → household), then
urgency (expired/eat-soon first by days_left ascending, then fine, then
to-buy), then name ascending for stable ordering.

### Purge predicates
- `is_expired(item, today)`: food and `days_left < 0`.
- `should_purge(item, today)`: food and `days_left <= -7` (a week past
  best-by). Pure derivation — no `expired_at` column, no write-on-read.

### tests/test_services.py
Cover every branch and the invariant boundaries:
- all five statuses; `days_left` at −7, −1, 0, 1, 3, 4
- out-of-stock beats expired; to-buy beats out-of-stock
- meds/household never get `EXPIRED`/`EAT_SOON`
- sort order and purge window

## Dependencies

None new (uses `sqlalchemy` models and stdlib `datetime`).

## Verify when done

- [ ] Every status transition and color rule is unit-tested
- [ ] Sort order is enforced in code and tested
- [ ] No status/color/sort logic exists outside `services.py`
