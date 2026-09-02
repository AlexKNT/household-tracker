# Unit 07: To-Buy

## Goal

Support purple shopping-list items: adding a missing item as a to-buy, and
the buy-to-activate flow that converts a purchased to-buy into a normal
(green) item with a best-by date.

## Design

A to-buy is an item row with `is_to_buy=True`, rendered purple. It shows no
quantity and no days-left; instead it displays "to buy". Clicking a purple
row opens a small modal asking for the best-by date; saving activates it.

## Implementation

### Adding a to-buy
Reuse `POST /items` with `is_to_buy=true` (Unit 06). For a to-buy, the
best-by date is optional (defaults to today per the product spec) and
quantity defaults to 1. The add-item form gains a "This is a to-buy" toggle
that hides the best-by/quantity fields.

### Activate flow
- `POST /items/{id}/activate` with a `best_by_date` form field.
- Sets `is_to_buy=False` and stores the best-by date; quantity stays 1.
- Returns the updated dashboard body; the row now renders green.

### Templates
- `partials/row.html` renders the purple state and the "to buy" label.
- `partials/activate_form.html` — the small best-by modal.

## Dependencies

None new.

## Verify when done

- [ ] A to-buy renders purple and sorts within its category
- [ ] Clicking a purple row prompts for best-by and converts it to green
- [ ] To-buy items appear in the daily modal's "To-buy" group
