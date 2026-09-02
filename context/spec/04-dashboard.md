# Unit 04: Dashboard

## Goal

Render the grouped, sorted, color-coded dashboard at `GET /`, with HTMX
polling for live refresh and friendly empty states. Read-only; no mutations.

## Design

Server-rendered HTML with HTMX. The page body is a fragment that polls
itself every 10s (`hx-trigger="every 10s"`), so day rollovers and countdowns
update without a full reload. Category sections appear in fixed order
(out-of-stock → meds → food → household), each a stack of rows sorted by
`services.sort_key`.

## Implementation

### routers/dashboard.py
- Query all items, call `derive_status`/`days_left`/`sort_key` from
  `services.py`, group by section, and render.
- Return the full page on `GET /` and a partial `dashboard_body` fragment for
  the polling refresh (a separate `GET /dashboard/body` route).

### templates/dashboard.html
- Extends `base.html`; sticky header with title + placeholder Add button.
- Includes `partials/dashboard_body.html`.

### templates/partials/dashboard_body.html
- One block per section; rows rendered from `partials/row.html`.
- Root element carries `hx-get="/dashboard/body"`,
  `hx-trigger="every 10s"`, `hx-swap="outerHTML"`.

### templates/partials/row.html
- Row anatomy per `ui-context.md`: button cluster, name, meta (quantity +
  days left + best-by date), comment cell. Status classes `row--purple`,
  `row--out`, `row--red`, `row--yellow`, `row--green` set from the color
  token returned by `status_color`.

### Empty states
- Friendly per-section and whole-page empty states.

## Dependencies

None new.

## Verify when done

- [ ] Page renders out-of-stock → meds → food → household with correct colors
- [ ] Food rows show "N days left" and the best-by date
- [ ] The dashboard auto-refreshes within 10s
- [ ] Empty states render when there are no items
