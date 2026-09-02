# Progress Tracker

Update this file after every meaningful implementation
change.

## Current Phase

- Build phase 3 — Write Path (units 06–10 complete)

## Current Goal

- Unit 10 — Comments

## Completed

- Six-file context system authored (`project-overview.md`,
  `architecture.md`, `ui-context.md`, `code-standards.md`,
  `ai-workflow-rules.md`); `AGENTS.md` aligned to the portfolio intent.
- Build plan (`context/spec/00-build-plan.md`) and all 15 unit specs authored.
- Unit 00 — Project Scaffold: `app/` skeleton, templates, vendored HTMX,
  CSS reset, pytest harness; smoke test passes.
- Unit 01 — DB Plan: `docs/schema.md` authored (columns, DDL, derived
  rules, migration strategy).
- Unit 02 — DB Implementation: `db.py`, `models.py` (`Category` + `Item`),
  create_all on startup; model tests pass.
- Unit 03 — Domain Services: `services.py` (status/color/sort/expiry);
  18 service tests pass.
- Unit 04 — Dashboard: `GET /` + `/dashboard/body`, grouped/sorted/colored
  rows with HTMX polling; 5 dashboard tests pass.
- Unit 05 — Notification Modal: `partials/notification_modal.html` (gone
  bad / eat soon / to-buy) rendered on full loads only; JS-free dismiss via
  `POST /modal/dismiss`; 6 modal tests pass.
- Unit 06 — Add Item: `app/schemas.py` (`ItemCreate` with food-only
  `best_by_date` rule), `app/crud.py`, `app/routers/items.py`
  (`GET /items/new`, `GET /items/empty`, `POST /items`), add-item modal
  fragment, `python-multipart` dependency; 15 new tests pass (54 total).
- Unit 07 — To-Buy: `is_to_buy` toggle on the add form (hides
  quantity/best-by), purple rows with the "to buy" label, clickable purple
  rows opening `GET /items/{id}/activate`, and `POST /items/{id}/activate`
  converting a purchase to an active green item (`partials/activate_form.html`,
  `partials/activated.html`); 16 new tests pass (70 total).
- Unit 08 — Quantity Controls: `POST /items/{id}/increment`,
  `POST /items/{id}/decrement` (clamped at 0), and `POST /items/{id}/empty`
  endpoints returning the dashboard body fragment; `+`/`-`/`0` buttons wired
  in `row.html` (disabled on to-buy rows), out-of-stock rows re-sort to the
  top; 8 new tests pass (78 total).
- Unit 09 — Restock (⟳): `crud.restock_item` creates a purple to-buy
  (same name/category, quantity 1, no best-by) without touching the source
  row; `POST /items/{id}/restock` returns the dashboard body fragment; the
  `⟳` button is wired next to `0` (disabled on to-buy rows); 7 new tests
  pass (85 total).
- Unit 10 — Comments: `crud.set_item_comment` persists a free-text note
  (`CommentUpdate` strips whitespace and maps empty back to `None`);
  `GET /items/{id}/comment/edit` returns the inline editor and
  `PATCH /items/{id}/comment` returns the rendered comment cell fragment
  (`partials/comment_cell.html`, `partials/comment_form.html`); `row.html`
  includes the cell for every row; 9 new tests pass (94 total).

## In Progress

- None — between units.

## Next Up

- Unit 11 — Expiry Lifecycle (`context/spec/11-expiry-lifecycle.md`)

## Open Questions

- None blocking v1. Deferred: remote sync, per-medication schedules,
  Alembic migrations, data import/export.

## Architecture Decisions

- FastAPI + Uvicorn + SQLAlchemy 2.0 + SQLite + Jinja2 + HTMX + plain CSS
  (portfolio-grade, no frontend build step).
- Status is always derived, never stored; expiry purge is derived from
  `best_by_date` (deleted 7 days past best-by) — no `expired_at` column.
- `Base.metadata.create_all()` on startup for v1; Alembic as the future path.
- Single user, single machine, no auth; remote sync deferred.

## Session Notes

- Unit 10 complete: the comment cell is a self-contained `row__comment`
  fragment rendered via `{% set item = row.item %}` + `{% include %}` so the
  same templates serve both the dashboard and the router's direct cell
  renders. The edit form saves via a `type="button"` with `hx-patch` +
  `hx-include="#comment-input-{id}"`; both the read cell and the Save button
  use `hx-trigger="click consume"` so clicks never bubble into a to-buy
  row's `hx-get` activate handler. `PATCH` returns only the cell fragment
  (no `HX-Retarget`), swapped in with `hx-swap="outerHTML"`.
- Unit 09 complete: `POST /items/{id}/restock` reads the source item via
  `get_item`, calls `crud.restock_item`, and returns
  `partials/dashboard_body.html` (no `HX-Retarget`; the `⟳` button targets
  `#dashboard-body` with `outerHTML`). Restocked to-buys store
  `best_by_date=None` even for food (they re-enter the activate flow to
  collect a date on purchase). The `⟳` button stays disabled on to-buy rows
  so it cannot double-fire the row's activate `hx-get` via click bubbling.
- Unit 08 complete: quantity-control endpoints return the dashboard body
  fragment (`partials/dashboard_body.html`) so an emptied row immediately
  re-sorts into the Out of stock section. `decrement_item` clamps at 0 via
  `max(0, quantity - 1)`. `+`/`-`/`0` buttons are wired with
  `hx-target="#dashboard-body" hx-swap="outerHTML"`; to-buy rows keep the
  buttons disabled (quantity is hidden there and the row itself carries the
  activate `hx-get`).
- Unit 07 complete: `POST /items` accepts `is_to_buy` (checkbox value
  `"true"`), `ItemCreate` defaults a food to-buy's date to today while
  keeping the food-only rule, `build_dashboard_context` suppresses
  `days_label` for to-buy rows, and the activate endpoints 404 for
  non-to-buy items. To-buy rows render purple with "to buy" and open the
  buy-to-activate modal via an `hx-get` on the `<li>`.
- Unit 06 complete: `POST /items` validates through `ItemCreate`
  (Pydantic), creates via `crud.create_item`, and returns
  `partials/items_created.html` (dashboard body + `hx-swap-oob="delete"`
  for the modal) with an `HX-Retarget: #dashboard-body` header. The add
  form re-renders via `GET /items/new` when the category changes so the
  best-by field only shows for food. Validation errors re-render the modal
  with inline messages; apostrophes avoided in messages (Jinja escapes `'`
  to `&#39;`).

- Unit 05 complete: notification modal renders on full page loads only
  (not the 10s polling fragment); groups are gone-bad / eat-soon / to-buy;
  dismiss posts to `/modal/dismiss` returning an empty fragment.
- Unit 04 complete: dashboard renders via `dashboard.py` + `partials/`
  (dashboard_body.html, row.html); polling every 10s.
- Unit 03 complete: `app/services.py` is the single source of truth for
  status/color/sort/expiry; pure functions, 18 tests.
- Unit 02 complete: SQLAlchemy 2.0 engine + model live in `app/db.py` and
  `app/models.py`; tables created idempotently on startup.
- Unit 01 complete: schema plan lives in `docs/schema.md`; Unit 02
  implements it verbatim.
- Unit 00 complete. Run the app with
  `.venv\Scripts\python.exe -m uvicorn app.main:app --reload`
  (deps live in the venv; the system Python has none of them).
- Minor: starlette 1.6.0 emits a deprecation warning about `httpx` in
  TestClient (suggests `httpx2`). Harmless for now; revisit in Unit 13.
