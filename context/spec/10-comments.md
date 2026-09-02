# Unit 10: Comments

## Goal

Add the inline-editable comments column: empty by default, click to edit,
save persists the text — using only HTMX, no JavaScript.

## Design

The comment cell is the rightmost element in each row. When empty it shows a
muted "Add note" affordance. Clicking swaps in a small inline form; saving
posts the text and swaps back the rendered value.

## Implementation

### app/routers/items.py
- `GET /items/{id}/comment/edit` → inline edit form fragment.
- `PATCH /items/{id}/comment` with a `comment` form field → save and return
  the rendered comment cell fragment.

### crud.py
`set_item_comment(db, item, comment)`.

### Templates
- `partials/comment_cell.html` — read state (text or "Add note").
- `partials/comment_form.html` — inline input + save, `hx-patch` targeting
  the cell with `hx-swap="outerHTML"`.

## Dependencies

None new.

## Verify when done

- [ ] Clicking an empty comment cell lets the user type and save
- [ ] The saved comment persists across reloads
- [ ] Editing uses only HTMX attributes (no custom JS)
