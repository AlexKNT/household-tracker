# Unit 08: Quantity Controls

## Goal

Implement the `+`, `-`, and set-to-0 row controls as HTMX POST endpoints that
update quantity and re-render the dashboard — with out-of-stock (dark
flashing red, top of list, never deleted) when quantity reaches 0.

## Design

Three buttons in the row's left cluster (`ui-context.md` row anatomy). Each
POSTs to an endpoint and returns the dashboard body fragment so a 0-count row
re-sorts to the top immediately. Quantity is clamped at 0 — `-` at 0 is a
no-op.

## Implementation

### app/routers/items.py
- `POST /items/{id}/increment` → `quantity += 1`
- `POST /items/{id}/decrement` → `max(0, quantity - 1)`
- `POST /items/{id}/empty` → `quantity = 0`

### Behavior
- After any of these, return the dashboard body fragment (not just the row)
  so sort order updates when an item becomes out-of-stock.
- A row with `quantity == 0` renders `row--out` (dark flashing red) via the
  `derive_status` → `OUT_OF_STOCK` path and `status_color`.

### crud.py
`increment_item`, `decrement_item`, `set_item_empty` helpers.

## Dependencies

None new.

## Verify when done

- [ ] `+` and `-` update quantity and re-render in place
- [ ] `-` never goes below 0
- [ ] Setting to 0 makes the row dark flashing red and moves it to the top
- [ ] An out-of-stock row persists across reloads
