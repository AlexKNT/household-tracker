# Unit 09: Restock (⟳)

## Goal

Add the `⟳` button to every row; clicking it creates a purple to-buy for that
row's name and category, so an out-of-stock item (or anything) can be put
back on the shopping list.

## Design

`⟳` sits to the right of the `0` button in the row's left cluster. It POSTs
to a restock endpoint and returns the updated dashboard body, where the new
to-buy appears in its category in purple.

## Implementation

### app/routers/items.py
`POST /items/{id}/restock`:
- Read the source item, create a new item with the same name and category,
  `is_to_buy=True`, quantity 1, best_by_date None.
- Return the dashboard body fragment.

### crud.py
`restock_item(db, item)` helper (creates the to-buy).

### Templates
Add the `⟳` button to `partials/row.html` in the correct position.

## Dependencies

None new.

## Verify when done

- [ ] Clicking `⟳` creates a to-buy for the row's item
- [ ] The new to-buy appears in its category in purple and in the modal
- [ ] Restocking an out-of-stock row does not delete the original row
