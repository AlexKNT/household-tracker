# Unit 05: Notification Modal

## Goal

Show the daily notification modal on every full page load, listing exactly
three groups in order — Gone bad, Eat soon, To-buy — with a dismiss button.

## Design

The modal is rendered server-side as part of the full dashboard page only.
The 10s polling fragment must NOT re-render the modal (so it doesn't pop
back over the user every 10s); it reappears only on the next full load,
matching "every time I open the app."

## Implementation

### Modal markup
An overlay + card (`ui-context.md` "Modal" pattern) with three sections:
- **Gone bad** — items with `status == EXPIRED` (best-by passed).
- **Eat soon** — items with `status == EAT_SOON` (0–3 days left).
- **To-buy** — items with `is_to_buy`.

### Dismissal (JS-free)
A close button posts to `POST /modal/dismiss` returning an empty fragment,
replacing the modal (`hx-swap="outerHTML"`). No state is persisted — the
server re-renders the modal on the next full page load by design.

### Placement
Rendered inside `dashboard.html` (full load) but NOT inside
`partials/dashboard_body.html` (the polling fragment).

## Dependencies

None new.

## Verify when done

- [ ] Opening the app shows the modal with the three correct groups in order
- [ ] Out-of-stock and meds do NOT appear in the modal
- [ ] The modal dismisses and reappears on the next full load
- [ ] The 10s polling refresh does not re-show the modal
