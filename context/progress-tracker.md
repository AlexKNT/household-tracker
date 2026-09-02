# Progress Tracker

Update this file after every meaningful implementation
change.

## Current Phase

- Build complete — all 15 units (00–14) implemented and verified

## Current Goal

- None — project complete

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
- Unit 11 — Expiry Lifecycle: lazy 7-day purge in `crud.list_items`
  (deletes food rows `days_left <= -7`, never touches `quantity == 0`
  rows); `services.is_expired`/`should_purge` derive expiry from
  `best_by_date`; dashboard and item routers list through `list_items` so
  every read purges; 5 new tests pass (99 total).
- Unit 12 — UI Polish & Responsive: full visual layer from
  `ui-context.md` in `app/static/css/styles.css` — `:root` tokens
  (neutrals, status triples, out-of-stock, actions, radii), sticky header
  with the Add button, category sections, status rows (background / left
  border / name text triples), the 2×3 control cluster (`+`/`−` stacked,
  `0` below, `⟳` right of `0`), quantity badge + days/date meta, comment
  cell, modal cards with sticky headers, empty states, global
  `focus-visible` rings, and a 640px breakpoint that stacks controls and
  meta. The only animation is `@keyframes flash` on `.row--out` (with a
  `prefers-reduced-motion` opt-out). Templates cleaned up
  (`dashboard.html` SVG `+` glyph, `row.html` control/meta classes) and an
  inline SVG favicon added to `base.html`. All 99 tests still pass; no
  browser console errors on a manual pass at desktop and mobile widths.
- Unit 13 — Testing & Hardening: completed the test suite to the
  spec's coverage targets. `tests/test_services.py` now covers every
  status branch and day boundary (−7, −1, 0, 1, 3, 4) plus full color
  mapping, sort order, and the purge window. `tests/test_models.py`
  gained schema-nullability assertions (matching `docs/schema.md`),
  category-enum values, insert defaults, and a full round-trip with
  comment + to-buy. Added `tests/test_endpoints.py` (every mutation via
  httpx: add, activate, increment/decrement/empty, restock, comment,
  dismiss modal) and `tests/test_invariants.py` (one asserting test per
  architecture invariant). 169 tests pass with no failures.
- Unit 14 — Docs & Final Review: authored `README.md` at the project
  root (description + ADHD context, stack table, setup for
  Windows/macOS/Linux, `pytest`, feature tour), audited all seven
  architecture invariants against code, verified all eight success
  criteria in `project-overview.md`, and synced `code-standards.md`
  (`hx-patch`) and `architecture.md` (static tree) with the
  implementation. 169 tests pass.

## In Progress

- None.

## Next Up

- None — project complete. Optional polish if reopened (see Open
  Questions).

## Open Questions

- Comment editor vs polling: the 10s dashboard poll replaces
  `#dashboard-body` while the inline comment editor is open, discarding
  an in-progress note (observed in a Unit 12 browser pass). Unit 14 was
  docs-only per its spec, so this remains open and non-blocking for v1.
  Candidate fixes (pause polling while `.row__comment--editing` exists, or
  move the editor out of the polled fragment) still apply.
- Deferred: remote sync, per-medication schedules, Alembic migrations,
  data import/export.

## Architecture Decisions

- FastAPI + Uvicorn + SQLAlchemy 2.0 + SQLite + Jinja2 + HTMX + plain CSS
  (portfolio-grade, no frontend build step).
- Status is always derived, never stored; expiry purge is derived from
  `best_by_date` (deleted 7 days past best-by) — no `expired_at` column.
- `Base.metadata.create_all()` on startup for v1; Alembic as the future path.
- Single user, single machine, no auth; remote sync deferred.

## Session Notes

- Unit 14 complete: `README.md` authored at the project root (one-line
  description + ADHD context, stack table with rationale pointing to
  `context/architecture.md`, venv + `pip install -r requirements.txt` +
  `uvicorn app.main:app --reload` setup for Windows/macOS/Linux, `pytest`
  instructions, and a feature tour walking the full item lifecycle).
  Invariants audit confirmed all seven `architecture.md` invariants hold:
  1. Status derived never stored — `services.derive_status` (no status
     column on `models.Item`); `dashboard.build_dashboard_context` derives.
  2. `best_by_date` food-only — `schemas.ItemCreate._enforce_food_only` +
     `ItemActivate._enforce_food_only`; `services.days_left` returns None
     for meds/household.
  3. Out-of-stock never auto-deleted — `crud.list_items` guards
     `item.quantity != 0`; only `services.should_purge` (days <= −7)
     deletes.
  4. Sort order server-side — `services.CATEGORY_ORDER` + `_URGENCY` +
     `sort_key`; `dashboard.build_dashboard_context` sorts.
  5. No background jobs — no scheduler dependencies; time logic runs
     lazily in handlers via `date.today()`; HTMX polling is client-side.
  6. Routers render fragments — every endpoint uses
     `response_class=HTMLResponse` / `TemplateResponse`; no JSON responses.
  7. Business rules in `services.py` — `derive_status`/`status_color`/
     `sort_key`/`days_left`/`is_expired`/`should_purge`; routers/templates
     call them and re-implement nothing (the purge's `quantity != 0` guard
     sits at the delete site in `crud.list_items` as documented, outside
     status/color/sort logic).
  All eight `project-overview.md` success criteria are demonstrably true.
  Docs sync: fixed `code-standards.md` (`hx-put` → `hx-patch` to match the
  PATCH comment endpoint) and `architecture.md` (static tree now lists
  `js/htmx.min.js`). `pytest` passes: 169 tests, 0 failures.
- Unit 12 complete: `styles.css` rewritten as the full visual layer.
  Every hex value lives on `:root` (verified by grep); the only animation
  is `flash` on `.row--out` plus a `prefers-reduced-motion` override.
  `--backdrop`, `--shadow`, and `--shadow-header` are token-level derived
  values (rgba) added to `:root` so no raw colors appear in component
  rules. `row.html` controls now use `btn--ctl` placed with
  `grid-template-areas` (literal ui-context layout: `+`/`−` stacked, `0`
  below, `⟳` right of `0`), and meta renders as a badge + days + date.
  `base.html` gained a data-URI SVG favicon so the browser no longer 404s
  `/favicon.ico`. Verified in a live browser at 390px and 1280px:
  sticky header, status triples, modals, comment edit/save, activate
  modal, quantity controls, flash animation (`flash / 1.4s / infinite`),
  and zero console errors on a clean load.
- Unit 11 complete: the 7-day purge runs lazily inside `crud.list_items`,
  which now takes `today` and deletes food rows where `should_purge` is
  true while skipping `quantity == 0` rows (out-of-stock is never
  auto-deleted). `services.is_expired`/`should_purge` were already present
  from Unit 03 and stay pure `days_left` predicates per spec; the quantity
  guard lives at the delete site, not in the predicate. `GET /`,
  `GET /dashboard/body`, and every item mutation re-render now list via
  `list_items(db, date.today())`, so purged rows disappear on any read.
  `tests/test_expiry.py` covers −1 visible, −7 purged, −6 survives,
  out-of-stock never purged, and meds/household never purged (99 total).
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
  TestClient (suggests `httpx2`). Still present at Unit 13; harmless.
- Unit 13 complete: test suite expanded per spec — `test_services.py`
  day-boundary/color/purge parameterization, `test_models.py`
  nullability + defaults + round-trip, new `test_endpoints.py` (all
  mutations via httpx) and new `test_invariants.py` (one test per
  invariant 1–7). 169 tests pass, 0 failures.
