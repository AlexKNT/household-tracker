# Progress Tracker

Update this file after every meaningful implementation
change.

## Current Phase

- Build phase 3 — Write Path (implementing units 06–10 in order)

## Current Goal

- Unit 07 — To-Buy

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

## In Progress

- None — between units.

## Next Up

- Unit 07 — To-Buy (`context/spec/07-to-buy.md`)

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
